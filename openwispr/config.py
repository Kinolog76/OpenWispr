"""Persistent settings for OpenWispr, stored as JSON in %APPDATA%\\OpenWispr."""

import json
import os
import sys
import subprocess

APP_NAME = "OpenWispr"

DEFAULTS = {
    "model_size": "small",      # tiny | base | small | medium | large-v3 | large-v3-turbo
    "device": "cpu",            # cpu | cuda
    "compute_type": "int8",     # int8 (cpu) | float16 (gpu) | int8_float16
    "language": "ru",           # "" = auto-detect, else ru/en/uk/...
    "input_device": "",         # "" = system default mic, else device name
    "beam_size": 5,             # 1 = fastest, 5 = noticeably more accurate
    "vad_filter": True,         # trim silence (tuned padding keeps quiet speech)
    "auto_punctuation": True,   # nudge the model to punctuate via initial prompt
    "spoken_punctuation": False,  # say "запятая" / "comma" to insert punctuation
    "custom_words": "",         # comma-separated names/terms fed to the model
    "hotkey_mods": ["ctrl", "win"],   # any of: ctrl, win, alt, shift
    "push_to_talk": True,       # True = hold combo; False = tap to toggle
    "paste_mode": True,         # True = clipboard Ctrl+V; False = type chars
    "restore_clipboard": True,
}

_CREATE_NO_WINDOW = 0x08000000


def config_dir():
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    path = os.path.join(base, APP_NAME)
    os.makedirs(path, exist_ok=True)
    return path


def config_path():
    return os.path.join(config_dir(), "config.json")


def load():
    cfg = dict(DEFAULTS)
    try:
        with open(config_path(), "r", encoding="utf-8") as f:
            data = json.load(f)
        for key in DEFAULTS:
            if key in data:
                cfg[key] = data[key]
    except (FileNotFoundError, ValueError, OSError):
        pass
    return cfg


def save(cfg):
    data = {key: cfg.get(key, DEFAULTS[key]) for key in DEFAULTS}
    with open(config_path(), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# --------------------------- Windows autostart ---------------------------

def _startup_shortcut():
    appdata = os.environ.get("APPDATA", "")
    return os.path.join(
        appdata, "Microsoft", "Windows", "Start Menu",
        "Programs", "Startup", APP_NAME + ".lnk",
    )


def _startup_target():
    """What the autostart shortcut should launch."""
    if getattr(sys, "frozen", False):
        return sys.executable  # the installed OpenWispr.exe
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    vbs = os.path.join(repo_root, "packaging", "OpenWispr.vbs")  # silent dev launcher
    return vbs if os.path.exists(vbs) else sys.executable


def autostart_enabled():
    return os.path.exists(_startup_shortcut())


def set_autostart(enabled):
    link = _startup_shortcut()
    if not enabled:
        try:
            os.remove(link)
        except FileNotFoundError:
            pass
        return
    target = _startup_target()
    workdir = os.path.dirname(target)
    ps = (
        "$w=New-Object -ComObject WScript.Shell;"
        "$l=$w.CreateShortcut('%s');"
        "$l.TargetPath='%s';"
        "$l.WorkingDirectory='%s';"
        "$l.Save()" % (link, target, workdir)
    )
    subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps],
        creationflags=_CREATE_NO_WINDOW,
        check=False,
    )
