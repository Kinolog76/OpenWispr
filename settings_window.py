"""A small Tk settings window for OpenWispr, opened from the tray icon."""

import threading
import tkinter as tk
from tkinter import ttk

import config

BG = "#f4f6f8"
CARD = "#ffffff"
TEXT = "#2c3e50"
MUTED = "#7f8c8d"
ACCENT = "#2ecc71"

MODELS = ["tiny", "base", "small", "medium", "large-v3"]
DEVICES = ["cpu", "cuda"]
COMPUTES = ["int8", "float16", "int8_float16"]
LANGS = ["auto", "ru", "en", "uk", "de", "fr", "es", "it", "pl"]


def open_settings(app):
    """Open the settings window in its own thread (one instance at a time)."""
    if getattr(app, "_settings_open", False):
        return
    app._settings_open = True

    def run():
        try:
            root = tk.Tk()
            _build(root, dict(app.cfg), app.apply_config)
            root.mainloop()
        finally:
            app._settings_open = False

    threading.Thread(target=run, daemon=True).start()


def _style(root):
    root.configure(bg=BG)
    st = ttk.Style(root)
    try:
        st.theme_use("clam")
    except tk.TclError:
        pass
    st.configure(".", background=BG, foreground=TEXT, font=("Segoe UI", 10))
    st.configure("Card.TLabelframe", background=CARD, borderwidth=0)
    st.configure("Card.TLabelframe.Label", background=BG, foreground=TEXT,
                 font=("Segoe UI Semibold", 10))
    st.configure("TLabelframe", background=CARD)
    st.configure("TLabelframe.Label", background=BG, foreground=TEXT,
                 font=("Segoe UI Semibold", 10))
    st.configure("TCheckbutton", background=CARD)
    st.configure("Muted.TLabel", background=CARD, foreground=MUTED,
                 font=("Segoe UI", 8))
    st.configure("Title.TLabel", background=BG, foreground=TEXT,
                 font=("Segoe UI Semibold", 16))
    st.configure("Accent.TButton", background=ACCENT, foreground="white",
                 font=("Segoe UI Semibold", 10), borderwidth=0, padding=8)
    st.map("Accent.TButton", background=[("active", "#27ae60")])
    st.configure("Status.TLabel", background=BG, foreground=ACCENT,
                 font=("Segoe UI", 9))


def _section(parent, title):
    frame = ttk.LabelFrame(parent, text=title, padding=12)
    frame.pack(fill="x", padx=16, pady=(0, 12))
    frame.columnconfigure(1, weight=1)
    return frame


def _hint(parent, text, row):
    ttk.Label(parent, text=text, style="Muted.TLabel").grid(
        row=row, column=0, columnspan=2, sticky="w", pady=(0, 8))


def _build(root, cfg, on_save):
    root.title("OpenWispr — настройки")
    root.geometry("470x720")
    root.minsize(440, 600)
    _style(root)

    ttk.Label(root, text="OpenWispr", style="Title.TLabel").pack(
        anchor="w", padx=16, pady=(16, 2))
    ttk.Label(root, text="Голосовой ввод — настройки",
              background=BG, foreground=MUTED).pack(anchor="w", padx=16, pady=(0, 12))

    # --- Recognition ---
    rec = _section(root, "Распознавание")
    ttk.Label(rec, text="Модель").grid(row=0, column=0, sticky="w")
    model_var = tk.StringVar(value=cfg["model_size"])
    ttk.Combobox(rec, textvariable=model_var, values=MODELS, state="readonly",
                 width=16).grid(row=0, column=1, sticky="e")
    _hint(rec, "Больше = точнее, но медленнее. small — баланс.", 1)

    ttk.Label(rec, text="Устройство").grid(row=2, column=0, sticky="w")
    device_var = tk.StringVar(value=cfg["device"])
    ttk.Combobox(rec, textvariable=device_var, values=DEVICES, state="readonly",
                 width=16).grid(row=2, column=1, sticky="e")
    _hint(rec, "cuda — NVIDIA GPU (нужны библиотеки CUDA). Иначе cpu.", 3)

    ttk.Label(rec, text="Точность вычислений").grid(row=4, column=0, sticky="w")
    compute_var = tk.StringVar(value=cfg["compute_type"])
    ttk.Combobox(rec, textvariable=compute_var, values=COMPUTES, state="readonly",
                 width=16).grid(row=4, column=1, sticky="e")
    _hint(rec, "int8 для CPU, float16 для GPU.", 5)

    ttk.Label(rec, text="Язык").grid(row=6, column=0, sticky="w")
    lang_var = tk.StringVar(value=cfg["language"] or "auto")
    ttk.Combobox(rec, textvariable=lang_var, values=LANGS, width=16).grid(
        row=6, column=1, sticky="e")
    _hint(rec, "Код языка ускоряет и улучшает распознавание. auto — определять.", 7)

    ttk.Label(rec, text="Ширина поиска (beam)").grid(row=8, column=0, sticky="w")
    beam_var = tk.IntVar(value=cfg["beam_size"])
    tk.Spinbox(rec, from_=1, to=5, textvariable=beam_var, width=15,
               relief="flat").grid(row=8, column=1, sticky="e")
    _hint(rec, "1 — быстрее, 5 — чуть точнее.", 9)

    vad_var = tk.BooleanVar(value=cfg["vad_filter"])
    ttk.Checkbutton(rec, text="Фильтр тишины (VAD)", variable=vad_var).grid(
        row=10, column=0, columnspan=2, sticky="w")
    _hint(rec, "Обрезает паузы, но может срезать тихую речь.", 11)

    # --- Hotkey ---
    hk = _section(root, "Горячая клавиша")
    ttk.Label(hk, text="Комбинация:").grid(row=0, column=0, columnspan=2, sticky="w")
    mods_now = set(cfg["hotkey_mods"])
    mod_vars = {}
    mod_row = ttk.Frame(hk)
    mod_row.grid(row=1, column=0, columnspan=2, sticky="w", pady=4)
    for i, name in enumerate(("ctrl", "win", "alt", "shift")):
        var = tk.BooleanVar(value=name in mods_now)
        mod_vars[name] = var
        ttk.Checkbutton(mod_row, text=name.capitalize(), variable=var).grid(
            row=0, column=i, padx=(0, 10))
    _hint(hk, "Держи все отмеченные клавиши, чтобы диктовать.", 2)

    ptt_var = tk.BooleanVar(value=cfg["push_to_talk"])
    ttk.Radiobutton(hk, text="Зажать и держать (push-to-talk)",
                    variable=ptt_var, value=True).grid(
        row=3, column=0, columnspan=2, sticky="w")
    ttk.Radiobutton(hk, text="Нажать / нажать (переключатель)",
                    variable=ptt_var, value=False).grid(
        row=4, column=0, columnspan=2, sticky="w")

    # --- Output ---
    out = _section(root, "Вставка текста")
    paste_var = tk.BooleanVar(value=cfg["paste_mode"])
    ttk.Checkbutton(out, text="Через буфер обмена (Ctrl+V)",
                    variable=paste_var).grid(row=0, column=0, columnspan=2, sticky="w")
    _hint(out, "Надёжно для кириллицы. Иначе печатает посимвольно.", 1)
    restore_var = tk.BooleanVar(value=cfg["restore_clipboard"])
    ttk.Checkbutton(out, text="Восстанавливать буфер после вставки",
                    variable=restore_var).grid(row=2, column=0, columnspan=2, sticky="w")

    # --- System ---
    sysf = _section(root, "Система")
    auto_var = tk.BooleanVar(value=config.autostart_enabled())
    ttk.Checkbutton(sysf, text="Запускать вместе с Windows",
                    variable=auto_var).grid(row=0, column=0, columnspan=2, sticky="w")

    status = ttk.Label(root, text="", style="Status.TLabel")
    status.pack(anchor="w", padx=16)

    def do_save():
        mods = [m for m, v in mod_vars.items() if v.get()] or ["ctrl", "win"]
        lang = lang_var.get().strip()
        new = {
            "model_size": model_var.get(),
            "device": device_var.get(),
            "compute_type": compute_var.get(),
            "language": "" if lang == "auto" else lang,
            "beam_size": int(beam_var.get()),
            "vad_filter": vad_var.get(),
            "hotkey_mods": mods,
            "push_to_talk": ptt_var.get(),
            "paste_mode": paste_var.get(),
            "restore_clipboard": restore_var.get(),
        }
        config.set_autostart(auto_var.get())
        on_save(new)
        status.config(text="Сохранено. Модель/устройство — после перезагрузки модели.")

    btns = ttk.Frame(root)
    btns.pack(fill="x", padx=16, pady=16, side="bottom")
    ttk.Button(btns, text="Закрыть", command=root.destroy).pack(side="right")
    ttk.Button(btns, text="Сохранить", style="Accent.TButton",
               command=do_save).pack(side="right", padx=(0, 8))


def run_standalone():
    """Open the settings window on the main thread (for `flow.py --settings`)."""
    root = tk.Tk()
    _build(root, dict(config.load()), lambda c: config.save(c))
    root.mainloop()


def _selftest():
    """Build the UI on a hidden root to verify it renders without errors."""
    root = tk.Tk()
    root.withdraw()
    _build(root, dict(config.DEFAULTS), lambda c: None)
    root.update()
    root.destroy()
    print("SETTINGS UI OK")


if __name__ == "__main__":
    _selftest()
