"""
OpenWispr - free, offline, system-wide voice dictation for Windows.

Hold a hotkey, speak, release: your words are transcribed locally with
faster-whisper and inserted into whatever app has focus. Lives in the system
tray; click the icon to open settings.

    python -m openwispr             run with tray
    python -m openwispr --settings  open the settings window only
    python -m openwispr --selftest  record 5s and transcribe (mic/model check)
"""

import os
import sys
import time
import glob
import queue
import logging
import threading

import numpy as np
import sounddevice as sd
from pynput import keyboard
import pyperclip
from PIL import Image, ImageDraw
import pystray


def _add_nvidia_dll_dirs():
    """Put pip-installed CUDA/cuDNN DLLs (nvidia-cublas-cu12, nvidia-cudnn-cu12,
    ...) on PATH so ctranslate2 can find them via device='cuda'.

    ctranslate2 loads these with plain LoadLibrary, which only searches PATH -
    os.add_dll_directory is not enough. pip installs them under
    <site-packages>/nvidia/<pkg>/bin with no matching system-wide install, so
    without this GPU mode fails with "cublas64_12.dll is not found".
    """
    dirs = []
    for entry in sys.path:
        dirs += glob.glob(os.path.join(entry, "nvidia", "*", "bin"))
    if dirs:
        os.environ["PATH"] = os.pathsep.join(dirs) + os.pathsep + os.environ["PATH"]


_add_nvidia_dll_dirs()

from faster_whisper import WhisperModel

from openwispr import config, settings_window, textproc

try:
    import winsound
except ImportError:
    winsound = None

# Set OPENWISPR_LOG=1 to write flow.log (next to this module) for debugging.
ENABLE_LOG = os.environ.get("OPENWISPR_LOG") == "1"
LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "flow.log")
if ENABLE_LOG:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler(LOG_PATH, encoding="utf-8"),
                  logging.StreamHandler()],
    )
else:
    logging.basicConfig(level=logging.CRITICAL, handlers=[logging.NullHandler()])
log = logging.getLogger("openwispr")

SAMPLE_RATE = 16000
CHANNELS = 1

# Physical 'V' key by virtual-key code, so Ctrl+V paste works on any keyboard
# layout (pressing the character 'v' fails under non-Latin layouts).
PASTE_VK = keyboard.KeyCode.from_vk(0x56)

_MOD_ALIASES = {
    keyboard.Key.ctrl: "ctrl", keyboard.Key.ctrl_l: "ctrl", keyboard.Key.ctrl_r: "ctrl",
    keyboard.Key.cmd: "win", keyboard.Key.cmd_l: "win", keyboard.Key.cmd_r: "win",
    keyboard.Key.alt: "alt", keyboard.Key.alt_l: "alt", keyboard.Key.alt_r: "alt",
    keyboard.Key.alt_gr: "alt",
    keyboard.Key.shift: "shift", keyboard.Key.shift_l: "shift", keyboard.Key.shift_r: "shift",
}


def _mod_name(key):
    return _MOD_ALIASES.get(key)


def _make_icon(color):
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((10, 10, 54, 54), fill=color)
    d.rounded_rectangle((26, 18, 38, 42), radius=6, fill=(255, 255, 255, 230))
    d.rectangle((30, 40, 34, 52), fill=(255, 255, 255, 230))
    return img


ICON_LOADING = _make_icon((149, 165, 166, 255))  # grey
ICON_IDLE = _make_icon((46, 204, 113, 255))       # green
ICON_REC = _make_icon((231, 76, 60, 255))         # red
ICON_BUSY = _make_icon((52, 152, 219, 255))       # blue


def _resample(audio, src_rate, dst_rate):
    if src_rate == dst_rate or len(audio) == 0:
        return audio
    n = int(round(len(audio) * dst_rate / src_rate))
    if n <= 0:
        return audio
    x_old = np.linspace(0.0, 1.0, num=len(audio), endpoint=False)
    x_new = np.linspace(0.0, 1.0, num=n, endpoint=False)
    return np.interp(x_new, x_old, audio).astype(np.float32)


# Segments that Whisper itself marks as likely non-speech are dropped: this
# is where hallucinated phrases on silence/breath noise come from.
NO_SPEECH_MAX = 0.6
LOGPROB_MIN = -1.0

# Padding keeps quiet speech at utterance edges; short min-silence still cuts
# the long pauses that make Whisper hallucinate.
VAD_PARAMETERS = {"min_silence_duration_ms": 300, "speech_pad_ms": 400}


def transcribe(model, cfg, audio):
    """Run the model and return cleaned text (shared by app and selftest)."""
    language = cfg["language"] or None
    prompt = textproc.initial_prompt(
        language if cfg["auto_punctuation"] else None,
        cfg["custom_words"],
    )
    segments, info = model.transcribe(
        audio,
        language=language,
        vad_filter=cfg["vad_filter"],
        vad_parameters=VAD_PARAMETERS,
        beam_size=cfg["beam_size"],
        initial_prompt=prompt,
        condition_on_previous_text=False,
        temperature=0.0,
    )
    parts = []
    for s in segments:
        if s.no_speech_prob > NO_SPEECH_MAX and s.avg_logprob < LOGPROB_MIN:
            log.info("dropped segment (no_speech=%.2f logprob=%.2f): %s",
                     s.no_speech_prob, s.avg_logprob, s.text)
            continue
        parts.append(s.text)
    text = textproc.clean(" ".join(parts),
                          spoken_punctuation=cfg["spoken_punctuation"],
                          ensure_period=cfg["auto_punctuation"])
    return text, info


def beep(freq, dur=120):
    if winsound is not None:
        try:
            winsound.Beep(freq, dur)
        except Exception:
            pass


def _clean_device_name(name):
    """Some devices (Bluetooth) embed newlines/driver junk in their names."""
    return " ".join(name.split())


def resolve_input_device(name):
    """Map a saved device name to a sounddevice index; None = system default."""
    if not name:
        return None
    try:
        for i, dev in enumerate(sd.query_devices()):
            if (dev["max_input_channels"] > 0
                    and _clean_device_name(dev["name"]) == name):
                return i
    except Exception:
        log.exception("could not enumerate audio devices")
    log.warning("input device %r not found; using default", name)
    return None


# Windows pseudo-devices that just alias the system default input.
_DEVICE_ALIASES = ("Microsoft Sound Mapper", "Первичный драйвер",
                   "Primary Sound Capture")


def list_input_devices():
    """Unique input device names (Windows lists each across several host APIs)."""
    names = []
    try:
        for dev in sd.query_devices():
            name = _clean_device_name(dev["name"])
            if (dev["max_input_channels"] > 0 and name not in names
                    and not name.startswith(_DEVICE_ALIASES)):
                names.append(name)
    except Exception:
        pass
    return names


class Recorder:
    """Captures microphone audio into memory while recording."""

    def __init__(self):
        self._frames = []
        self._stream = None
        self.recording = False
        self._rate = SAMPLE_RATE
        self._device = None
        self._lock = threading.Lock()

    def _callback(self, indata, frames, time_info, status):
        if status:
            log.warning("audio status: %s", status)
        if self.recording:
            self._frames.append(indata.copy())

    def _open_stream(self):
        try:
            stream = sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS,
                                    device=self._device,
                                    dtype="float32", callback=self._callback)
            stream.start()
            self._stream = stream
            return SAMPLE_RATE
        except Exception as e:
            log.warning("16 kHz failed (%s); using device default", e)
            if self._device is not None:
                rate = int(sd.query_devices(self._device)["default_samplerate"])
            else:
                rate = int(sd.query_devices(kind="input")["default_samplerate"])
            stream = sd.InputStream(samplerate=rate, channels=CHANNELS,
                                    device=self._device,
                                    dtype="float32", callback=self._callback)
            stream.start()
            self._stream = stream
            return rate

    def start(self, device=None):
        with self._lock:
            if self.recording:
                return
            self._frames = []
            self._device = device
            self.recording = True
            try:
                self._rate = self._open_stream()
            except Exception:
                self.recording = False
                self._stream = None
                log.exception("could not open microphone")
                return
        beep(880)

    def stop(self):
        with self._lock:
            if not self.recording:
                return None
            self.recording = False
            try:
                if self._stream is not None:
                    self._stream.stop()
                    self._stream.close()
            finally:
                self._stream = None
            frames, rate = self._frames, self._rate
            self._frames = []
        beep(440)
        if not frames:
            return None
        audio = np.concatenate(frames, axis=0).flatten().astype(np.float32)
        return _resample(audio, rate, SAMPLE_RATE)


class App:
    """Tray app: model, recorder, global hotkey, transcription worker."""

    def __init__(self):
        self.cfg = config.load()
        self.model = None
        self.model_ready = threading.Event()
        self.recorder = Recorder()
        self.kb = keyboard.Controller()
        self.work = queue.Queue()
        self._mods_held = set()
        self._combo_active = False
        self._settings_open = False
        self.required_mods = frozenset(self.cfg["hotkey_mods"])
        self.icon = pystray.Icon(
            "OpenWispr", ICON_LOADING, "OpenWispr",
            menu=pystray.Menu(
                pystray.MenuItem("Настройки…", self._open_settings, default=True),
                pystray.MenuItem(self._status_text, None, enabled=False),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Выход", self._on_quit),
            ),
        )

    # ----- labels / state -----
    def _hotkey_label(self):
        return "+".join(m.capitalize() for m in self.cfg["hotkey_mods"])

    def _ready_title(self):
        verb = "держите" if self.cfg["push_to_talk"] else "нажмите"
        return f"OpenWispr — готов ({verb} {self._hotkey_label()})"

    def _status_text(self, item):
        if not self.model_ready.is_set():
            return "Загрузка модели…"
        verb = "держать" if self.cfg["push_to_talk"] else "нажать"
        return f"Готов — {verb} {self._hotkey_label()}"

    def _set_icon(self, image, title):
        self.icon.icon = image
        self.icon.title = title

    # ----- model -----
    def _load_model(self):
        self.model_ready.clear()
        self._set_icon(ICON_LOADING, "OpenWispr — загрузка модели…")
        log.info("loading %s on %s (%s)", self.cfg["model_size"],
                 self.cfg["device"], self.cfg["compute_type"])
        try:
            self.model = WhisperModel(self.cfg["model_size"],
                                      device=self.cfg["device"],
                                      compute_type=self.cfg["compute_type"])
        except Exception:
            log.exception("failed to load model")
            self._set_icon(ICON_LOADING, "OpenWispr — ошибка загрузки модели")
            return
        self.model_ready.set()
        self._set_icon(ICON_IDLE, self._ready_title())
        self.icon.update_menu()
        log.info("model ready")

    def _reload_model_async(self):
        threading.Thread(target=self._load_model, daemon=True).start()

    # ----- settings -----
    def _open_settings(self, icon=None, item=None):
        settings_window.open_settings(self)

    def apply_config(self, new):
        old = self.cfg
        model_changed = any(new[k] != old[k] for k in
                            ("model_size", "device", "compute_type"))
        self.cfg = new
        config.save(new)
        self.required_mods = frozenset(new["hotkey_mods"])
        if self.model_ready.is_set():
            self._set_icon(ICON_IDLE, self._ready_title())
        self.icon.update_menu()
        if model_changed:
            self._reload_model_async()

    # ----- transcription worker -----
    def _worker(self):
        while True:
            audio = self.work.get()
            if audio is None:
                return
            try:
                self._process(audio)
            finally:
                if not self.recorder.recording:
                    self._set_icon(ICON_IDLE, self._ready_title())

    def _process(self, audio):
        if len(audio) / SAMPLE_RATE < 0.3:
            return
        try:
            text, _ = transcribe(self.model, self.cfg, audio)
        except Exception:
            log.exception("transcription error")
            return
        if text:
            log.info("recognized: %s", text)
            self._insert(text)

    def _insert(self, text):
        try:
            if self.cfg["paste_mode"]:
                previous = None
                if self.cfg["restore_clipboard"]:
                    try:
                        previous = pyperclip.paste()
                    except Exception:
                        previous = None
                pyperclip.copy(text)
                time.sleep(0.08)
                for k in (keyboard.Key.cmd, keyboard.Key.cmd_l, keyboard.Key.cmd_r,
                          keyboard.Key.alt, keyboard.Key.alt_gr, keyboard.Key.shift):
                    try:
                        self.kb.release(k)
                    except Exception:
                        pass
                self.kb.press(keyboard.Key.ctrl)
                self.kb.press(PASTE_VK)
                self.kb.release(PASTE_VK)
                self.kb.release(keyboard.Key.ctrl)
                time.sleep(0.15)
                if self.cfg["restore_clipboard"] and previous is not None:
                    time.sleep(0.3)
                    try:
                        pyperclip.copy(previous)
                    except Exception:
                        pass
            else:
                self.kb.type(text)
        except Exception:
            log.exception("failed to insert text")

    # ----- hotkey -----
    def _on_press(self, key):
        name = _mod_name(key)
        if not name or name in self._mods_held:
            return
        self._mods_held.add(name)
        self._update_combo()

    def _on_release(self, key):
        name = _mod_name(key)
        if not name:
            return
        self._mods_held.discard(name)
        self._update_combo()

    def _update_combo(self):
        active = self.required_mods.issubset(self._mods_held)
        if active == self._combo_active:
            return
        self._combo_active = active
        if not self.model_ready.is_set():
            if active:
                beep(220)
            return
        device = resolve_input_device(self.cfg["input_device"])
        if self.cfg["push_to_talk"]:
            if active:
                self.recorder.start(device)
                self._set_icon(ICON_REC, "OpenWispr — запись")
            else:
                self._stop_and_send()
        elif active:
            if self.recorder.recording:
                self._stop_and_send()
            else:
                self.recorder.start(device)
                self._set_icon(ICON_REC, "OpenWispr — запись")

    def _stop_and_send(self):
        audio = self.recorder.stop()
        if audio is not None:
            self._set_icon(ICON_BUSY, "OpenWispr — обработка…")
            self.work.put(audio)
        else:
            self._set_icon(ICON_IDLE, self._ready_title())

    # ----- lifecycle -----
    def _on_quit(self, icon, item):
        try:
            self.work.put(None)
        except Exception:
            pass
        icon.visible = False
        icon.stop()
        os._exit(0)

    def _setup(self, icon):
        icon.visible = True
        threading.Thread(target=self._worker, daemon=True).start()
        threading.Thread(target=self._load_model, daemon=True).start()
        listener = keyboard.Listener(on_press=self._on_press, on_release=self._on_release)
        listener.daemon = True
        listener.start()

    def run(self):
        self.icon.run(setup=self._setup)


def selftest(seconds=5):
    cfg = config.load()
    print("Default input:", sd.query_devices(kind="input")["name"])
    print(f"Loading model '{cfg['model_size']}'...")
    model = WhisperModel(cfg["model_size"], device=cfg["device"],
                         compute_type=cfg["compute_type"])
    print(f"\n>>> RECORDING {seconds}s - SPEAK NOW <<<\n")
    rec = Recorder()
    rec.start()
    if not rec.recording:
        print("ERROR: microphone did not open.")
        return
    time.sleep(seconds)
    audio = rec.stop()
    if audio is None:
        print("ERROR: no audio captured.")
        return
    text, info = transcribe(model, cfg, audio)
    print("\n==== RESULT (lang=%s) ====" % getattr(info, "language", "?"))
    print(text or "(nothing recognized)")


def main():
    if "--selftest" in sys.argv:
        selftest()
    elif "--settings" in sys.argv:
        settings_window.run_standalone()
    else:
        App().run()


if __name__ == "__main__":
    main()
