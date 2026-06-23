<div align="center">

# 🎙️ OpenWispr

**Free, offline, system-wide voice dictation for Windows.**

Hold a hotkey, speak, release — your words are transcribed locally and typed
into whatever app has focus. A free, open-source take on the core
[Wispr Flow](https://wisprflow.ai/) experience.

![platform](https://img.shields.io/badge/platform-Windows-0078D6)
![python](https://img.shields.io/badge/python-3.10%E2%80%933.12-blue)
![license](https://img.shields.io/badge/license-MIT-green)
![offline](https://img.shields.io/badge/100%25-offline-success)

</div>

---

## ✨ Features

- 🗣️ **Dictate anywhere** — works in any window: browser, Word, chat apps, IDEs.
- 🔒 **Fully offline** — speech recognition runs locally via
  [faster-whisper](https://github.com/SYSTRAN/faster-whisper). No cloud, no API
  keys, no subscription. Your audio never leaves your machine.
- 🌍 **Multilingual** — Russian, Ukrainian, English and ~90 more languages.
- ⌨️ **Your hotkey** — push-to-talk (hold) or toggle (tap on/off); pick any
  modifier combo (default `Ctrl+Win`).
- 🎛️ **Settings UI** — click the tray icon to tweak model, language, hotkey,
  autostart and more. No config files to edit by hand.
- 🚀 **Autostart** — optionally launch silently with Windows.
- 🔔 **At-a-glance status** — tray icon turns green (ready), red (recording),
  blue (processing).
- 📋 **Layout-proof paste** — inserts via the clipboard, reliable for Cyrillic
  and emoji.

## 🚀 Install

### Option A — installer (recommended for users)

Grab **`OpenWispr-Setup.exe`** from the [Releases](../../releases) page and run
it. Installs like a normal app (Start menu, optional desktop shortcut and
autostart, uninstaller). No admin rights, no Python required.

> First launch downloads the Whisper model (~460 MB for `small`) to
> `%USERPROFILE%\.cache\huggingface`. Needs internet once, then fully offline.

### Option B — from source

```powershell
git clone https://github.com/<you>/OpenWispr.git
cd OpenWispr
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python flow.py
```

Or just double-click **`run.bat`** (creates the venv and installs deps on first
run). Requires [Python 3.10+](https://www.python.org/downloads/).

## 🎧 Usage

1. Launch — the tray icon goes grey (loading) then **green** (ready).
2. Put your cursor in any text field.
3. **Hold `Ctrl+Win`**, speak, then release.
4. The icon turns **blue** while transcribing; text appears at your cursor.

**Click the tray icon** to open settings. Right-click → **Выход** to quit.

## 🎛️ Settings

Everything is configurable from the tray settings window (stored in
`%APPDATA%\OpenWispr\config.json`):

| Setting | What it does |
|---|---|
| **Model** | `tiny`/`base`/`small`/`medium`/`large-v3` — bigger = more accurate, slower. |
| **Device** | `cpu`, or `cuda` for an NVIDIA GPU (needs CUDA libraries). |
| **Compute** | `int8` for CPU, `float16` for GPU. |
| **Language** | A code like `ru`/`en` is faster and more accurate than auto-detect. |
| **Beam size** | `1` = fastest, `5` = slightly more accurate. |
| **Hotkey** | Any combo of Ctrl/Win/Alt/Shift; push-to-talk or toggle. |
| **Paste mode** | Clipboard `Ctrl+V` (default) or character-by-character typing. |
| **Autostart** | Launch with Windows. |

> Model / device changes reload the model after saving; hotkey, language and
> the rest apply immediately.

### GPU acceleration (NVIDIA)

Set device `cuda` and compute `float16`, then install the CUDA runtime:

```powershell
pip install nvidia-cublas-cu12 nvidia-cudnn-cu12
```

## 🛠️ Build the installer

```powershell
build.bat                                   # PyInstaller -> dist\OpenWispr\
"%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" installer.iss   # -> Output\OpenWispr-Setup.exe
```

- **PyInstaller** bundles the app into `dist\OpenWispr\OpenWispr.exe`
  (see [`OpenWispr.spec`](OpenWispr.spec)).
- **[Inno Setup](https://jrsoftware.org/isdl.php)** wraps it into the installer
  (see [`installer.iss`](installer.iss)).
- The build needs **Python 3.12** — Python 3.10.0 has a `dis` bug that breaks
  PyInstaller. The app itself runs fine on 3.10+.

## 🧩 Tech stack

faster-whisper · sounddevice · pynput · pyperclip · pystray · Pillow ·
tkinter (settings UI) — all local, no network at runtime.

## 🔐 Privacy

Audio is captured, transcribed on-device, and discarded. Nothing is uploaded.
The only network access is the one-time model download on first run.

## 🤝 Contributing

Issues and PRs welcome. Ideas: voice commands ("new line"), macOS/Linux
support, AI text cleanup, a richer overlay UI.

## 📄 License

[MIT](LICENSE) — do what you like. Not affiliated with Wispr Flow.
