"""Settings window for OpenWispr: flat, tabbed, DPI-aware Tk UI."""

import threading
import tkinter as tk
from tkinter import ttk

from openwispr import config


def _input_devices():
    try:
        from openwispr import app
        return app.list_input_devices()
    except Exception:
        return []

# Flat design palette: neutral surfaces, teal accent.
BG = "#F5F7F8"
CARD = "#FFFFFF"
BORDER = "#E2E8F0"
TEXT = "#0F172A"
MUTED = "#475569"
ACCENT = "#0D9488"
ACCENT_DARK = "#0F766E"
ACCENT_SOFT = "#CCFBF1"
OK = "#0D9488"

FONT = "Segoe UI"

MODELS = ["tiny", "base", "small", "medium", "large-v3", "large-v3-turbo"]
MODEL_HINTS = {
    "tiny": "~75 МБ · очень быстро, черновое качество",
    "base": "~140 МБ · быстро, простые фразы",
    "small": "~460 МБ · баланс скорости и качества",
    "medium": "~1.5 ГБ · точно, медленнее на CPU",
    "large-v3": "~3 ГБ · максимум качества, медленно на CPU",
    "large-v3-turbo": "~1.6 ГБ · качество large, быстрее medium",
}
DEVICES = ["cpu", "cuda"]
COMPUTES = ["int8", "float16", "int8_float16"]
LANGS = ["auto", "ru", "en", "uk", "de", "fr", "es", "it", "pl"]
MOD_KEYS = ("ctrl", "win", "alt", "shift")
MOD_LABELS = {"ctrl": "Ctrl", "win": "Win", "alt": "Alt", "shift": "Shift"}


def _enable_dpi_awareness():
    """Crisp text on high-DPI displays; no-op if already set or unsupported."""
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass


def open_settings(app):
    """Open the settings window in its own thread (one instance at a time)."""
    if getattr(app, "_settings_open", False):
        return
    app._settings_open = True

    def run():
        try:
            _enable_dpi_awareness()
            root = tk.Tk()
            _build(root, dict(app.cfg), app.apply_config,
                   model_ready_fn=app.model_ready.is_set)
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

    st.configure(".", background=BG, foreground=TEXT, font=(FONT, 10),
                 borderwidth=0, focuscolor=ACCENT)
    st.configure("TFrame", background=BG)
    st.configure("Card.TFrame", background=CARD)

    # Notebook: flat tabs, selected tab merges with the white card below.
    st.configure("TNotebook", background=BG, borderwidth=0, tabmargins=(16, 8, 16, 0))
    st.configure("TNotebook.Tab", background=BG, foreground=MUTED,
                 font=(FONT, 10), padding=(16, 8), borderwidth=0)
    st.map("TNotebook.Tab",
           background=[("selected", CARD)],
           foreground=[("selected", ACCENT_DARK)],
           expand=[("selected", (0, 0, 0, 0))])

    st.configure("Card.TLabel", background=CARD, foreground=TEXT)
    st.configure("Head.TLabel", background=CARD, foreground=TEXT,
                 font=(FONT + " Semibold", 10))
    st.configure("Muted.TLabel", background=CARD, foreground=MUTED, font=(FONT, 8))
    st.configure("Title.TLabel", background=BG, foreground=TEXT,
                 font=(FONT + " Semibold", 15))
    st.configure("Sub.TLabel", background=BG, foreground=MUTED, font=(FONT, 9))
    st.configure("Status.TLabel", background=BG, foreground=OK, font=(FONT, 9))
    st.configure("Combo.TLabel", background=CARD, foreground=ACCENT_DARK,
                 font=(FONT + " Semibold", 11))

    st.configure("TCheckbutton", background=CARD, foreground=TEXT)
    st.map("TCheckbutton", background=[("active", CARD)])
    st.configure("TRadiobutton", background=CARD, foreground=TEXT)
    st.map("TRadiobutton", background=[("active", CARD)])

    # Hotkey chips: indicator-less checkbuttons that fill with the accent.
    st.configure("Chip.Toolbutton", background=BG, foreground=MUTED,
                 font=(FONT + " Semibold", 10), padding=(14, 6), borderwidth=0)
    st.map("Chip.Toolbutton",
           background=[("selected", ACCENT), ("active", ACCENT_SOFT)],
           foreground=[("selected", "#FFFFFF"), ("active", ACCENT_DARK)])

    st.configure("TCombobox", fieldbackground="#FFFFFF", background="#FFFFFF",
                 arrowcolor=MUTED, bordercolor=BORDER, lightcolor=BORDER,
                 darkcolor=BORDER, padding=4)
    st.map("TCombobox",
           fieldbackground=[("readonly", "#FFFFFF")],
           selectbackground=[("readonly", "#FFFFFF")],
           selectforeground=[("readonly", TEXT)])
    st.configure("TEntry", fieldbackground="#FFFFFF", bordercolor=BORDER,
                 lightcolor=BORDER, darkcolor=BORDER, padding=4)
    st.configure("Horizontal.TScale", background=CARD, troughcolor=BORDER)

    st.configure("Accent.TButton", background=ACCENT, foreground="#FFFFFF",
                 font=(FONT + " Semibold", 10), borderwidth=0, padding=(18, 8))
    st.map("Accent.TButton", background=[("active", ACCENT_DARK)])
    st.configure("Ghost.TButton", background=BG, foreground=MUTED,
                 font=(FONT, 10), borderwidth=0, padding=(14, 8))
    st.map("Ghost.TButton", background=[("active", "#E8EDF0")],
           foreground=[("active", TEXT)])


def _card(parent):
    """White content card that fills a notebook tab."""
    outer = tk.Frame(parent, bg=CARD, highlightbackground=BORDER,
                     highlightthickness=1)
    outer.pack(fill="both", expand=True)
    inner = ttk.Frame(outer, style="Card.TFrame", padding=16)
    inner.pack(fill="both", expand=True)
    inner.columnconfigure(1, weight=1)
    return inner


def _row(card, row, label, widget, hint=None):
    """Label left, control right, muted hint underneath."""
    ttk.Label(card, text=label, style="Card.TLabel").grid(
        row=row, column=0, sticky="w", pady=(0, 2))
    widget.grid(row=row, column=1, sticky="e", pady=(0, 2))
    if hint:
        h = ttk.Label(card, text=hint, style="Muted.TLabel")
        h.grid(row=row + 1, column=0, columnspan=2, sticky="w", pady=(0, 10))
        return h
    return None


def _check(card, row, text, var, hint=None):
    c = ttk.Checkbutton(card, text=text, variable=var, cursor="hand2")
    c.grid(row=row, column=0, columnspan=2, sticky="w", pady=(0, 2))
    if hint:
        ttk.Label(card, text=hint, style="Muted.TLabel").grid(
            row=row + 1, column=0, columnspan=2, sticky="w", pady=(0, 10))


def _center(root, w, h):
    root.update_idletasks()
    x = (root.winfo_screenwidth() - w) // 2
    y = (root.winfo_screenheight() - h) // 3
    root.geometry(f"{w}x{h}+{x}+{y}")


def _build(root, cfg, on_save, model_ready_fn=None):
    root.title("OpenWispr — настройки")
    root.minsize(460, 480)
    _style(root)

    # --- Header ---
    header = ttk.Frame(root)
    header.pack(fill="x", padx=20, pady=(16, 6))
    ttk.Label(header, text="OpenWispr", style="Title.TLabel").pack(side="left")
    ttk.Label(header, text="  локальный голосовой ввод", style="Sub.TLabel").pack(
        side="left", pady=(5, 0))

    # --- Bottom bar (packed before tabs so it never gets pushed out) ---
    bottom = ttk.Frame(root)
    bottom.pack(fill="x", side="bottom", padx=20, pady=(10, 16))
    status = ttk.Label(bottom, text="", style="Status.TLabel")
    status.pack(side="left")

    # --- Tabs ---
    nb = ttk.Notebook(root)
    nb.pack(fill="both", expand=True, padx=20, pady=(6, 0))

    tab_rec = ttk.Frame(nb)
    tab_txt = ttk.Frame(nb)
    tab_ctl = ttk.Frame(nb)
    tab_sys = ttk.Frame(nb)
    nb.add(tab_rec, text="Распознавание")
    nb.add(tab_txt, text="Текст")
    nb.add(tab_ctl, text="Управление")
    nb.add(tab_sys, text="Система")

    # ============ Tab: Распознавание ============
    rec = _card(tab_rec)

    # Model label + load-status dot share the left cell.
    mrow = ttk.Frame(rec, style="Card.TFrame")
    ttk.Label(mrow, text="Модель", style="Card.TLabel").pack(side="left")
    model_dot = tk.Label(mrow, text="", bg=CARD, font=(FONT, 9))
    model_dot.pack(side="left", padx=(8, 0))
    mrow.grid(row=0, column=0, sticky="w", pady=(0, 2))

    model_var = tk.StringVar(value=cfg["model_size"])
    model_cb = ttk.Combobox(rec, textvariable=model_var, values=MODELS,
                            state="readonly", width=16, cursor="hand2")
    model_cb.grid(row=0, column=1, sticky="e", pady=(0, 2))
    model_hint = ttk.Label(rec, text=MODEL_HINTS.get(cfg["model_size"], ""),
                           style="Muted.TLabel")
    model_hint.grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 10))

    def on_model_change(_e=None):
        model_hint.config(text=MODEL_HINTS.get(model_var.get(), ""))
    model_cb.bind("<<ComboboxSelected>>", on_model_change)

    def poll_model_status():
        if model_ready_fn is None:
            return
        if model_ready_fn():
            model_dot.config(text="● загружена", fg=ACCENT)
        else:
            model_dot.config(text="◌ загрузка…", fg=MUTED)
        root.after(1000, poll_model_status)
    poll_model_status()

    lang_var = tk.StringVar(value=cfg["language"] or "auto")
    lang_cb = ttk.Combobox(rec, textvariable=lang_var, values=LANGS, width=16,
                           cursor="hand2")
    _row(rec, 4, "Язык", lang_cb,
         "Код языка (ru, en…) быстрее и точнее. auto — определять по речи.")

    device_var = tk.StringVar(value=cfg["device"])
    device_cb = ttk.Combobox(rec, textvariable=device_var, values=DEVICES,
                             state="readonly", width=16, cursor="hand2")
    _row(rec, 6, "Устройство", device_cb,
         "cuda — NVIDIA GPU (нужны библиотеки CUDA). Иначе cpu.")

    compute_var = tk.StringVar(value=cfg["compute_type"])
    compute_cb = ttk.Combobox(rec, textvariable=compute_var, values=COMPUTES,
                              state="readonly", width=16, cursor="hand2")
    _row(rec, 8, "Вычисления", compute_cb, "int8 для CPU, float16 для GPU.")

    # Beam: slider with a live value label.
    beam_var = tk.IntVar(value=cfg["beam_size"])
    beam_box = ttk.Frame(rec, style="Card.TFrame")
    beam_label = ttk.Label(beam_box, text=str(beam_var.get()), style="Combo.TLabel",
                           width=2, anchor="e")
    beam_scale = ttk.Scale(beam_box, from_=1, to=5, orient="horizontal", length=120,
                           value=cfg["beam_size"], cursor="hand2",
                           command=lambda v: (beam_var.set(round(float(v))),
                                              beam_label.config(text=str(round(float(v))))))
    beam_scale.pack(side="left", padx=(0, 8))
    beam_label.pack(side="left")
    _row(rec, 10, "Точность (beam)", beam_box,
         "1 — максимально быстро, 5 — максимально точно.")

    vad_var = tk.BooleanVar(value=cfg["vad_filter"])
    _check(rec, 12, "Фильтр тишины (VAD)", vad_var,
           "Обрезает паузы — меньше «галлюцинаций» на тишине.")

    # ============ Tab: Текст ============
    txt = _card(tab_txt)

    punct_var = tk.BooleanVar(value=cfg["auto_punctuation"])
    _check(txt, 0, "Автопунктуация", punct_var,
           "Модель сама ставит запятые, точки и заглавные буквы.")

    spoken_var = tk.BooleanVar(value=cfg["spoken_punctuation"])
    _check(txt, 2, "Голосовые команды пунктуации", spoken_var,
           "Скажите «запятая», «точка», «новая строка» — вставится знак.")

    ttk.Label(txt, text="Свой словарь", style="Head.TLabel").grid(
        row=4, column=0, columnspan=2, sticky="w", pady=(8, 2))
    words_var = tk.StringVar(value=cfg["custom_words"])
    ttk.Entry(txt, textvariable=words_var).grid(
        row=5, column=0, columnspan=2, sticky="ew", pady=(0, 2))
    ttk.Label(txt,
              text="Имена и термины через запятую — модель будет их узнавать.\n"
                   "Например: Владислав, Kubernetes, OpenWispr, деплой, пул-реквест",
              style="Muted.TLabel", justify="left").grid(
        row=6, column=0, columnspan=2, sticky="w")

    # ============ Tab: Управление ============
    ctl = _card(tab_ctl)

    ttk.Label(ctl, text="Горячая клавиша", style="Head.TLabel").grid(
        row=0, column=0, columnspan=2, sticky="w", pady=(0, 6))

    mods_now = set(cfg["hotkey_mods"])
    mod_vars = {}
    chip_row = ttk.Frame(ctl, style="Card.TFrame")
    chip_row.grid(row=1, column=0, columnspan=2, sticky="w")
    combo_label = ttk.Label(ctl, text="", style="Combo.TLabel")
    combo_label.grid(row=2, column=0, columnspan=2, sticky="w", pady=(8, 2))

    def update_combo_label():
        picked = [MOD_LABELS[m] for m in MOD_KEYS if mod_vars[m].get()]
        combo_label.config(text=" + ".join(picked) if picked
                           else "Выберите хотя бы одну клавишу")

    for i, name in enumerate(MOD_KEYS):
        var = tk.BooleanVar(value=name in mods_now)
        mod_vars[name] = var
        ttk.Checkbutton(chip_row, text=MOD_LABELS[name], variable=var,
                        style="Chip.Toolbutton", cursor="hand2",
                        command=update_combo_label).grid(
            row=0, column=i, padx=(0, 8))
    update_combo_label()

    ttk.Label(ctl, text="Держите комбинацию и говорите.", style="Muted.TLabel").grid(
        row=3, column=0, columnspan=2, sticky="w", pady=(0, 12))

    ttk.Label(ctl, text="Режим записи", style="Head.TLabel").grid(
        row=4, column=0, columnspan=2, sticky="w", pady=(0, 4))
    ptt_var = tk.BooleanVar(value=cfg["push_to_talk"])
    ttk.Radiobutton(ctl, text="Зажать и держать (push-to-talk)",
                    variable=ptt_var, value=True, cursor="hand2").grid(
        row=5, column=0, columnspan=2, sticky="w")
    ttk.Radiobutton(ctl, text="Нажать — начать, нажать — остановить",
                    variable=ptt_var, value=False, cursor="hand2").grid(
        row=6, column=0, columnspan=2, sticky="w", pady=(0, 12))

    ttk.Label(ctl, text="Вставка текста", style="Head.TLabel").grid(
        row=7, column=0, columnspan=2, sticky="w", pady=(0, 4))
    paste_var = tk.BooleanVar(value=cfg["paste_mode"])
    _check(ctl, 8, "Через буфер обмена (Ctrl+V)", paste_var,
           "Надёжно для кириллицы. Иначе печатает посимвольно.")
    restore_var = tk.BooleanVar(value=cfg["restore_clipboard"])
    _check(ctl, 10, "Восстанавливать буфер после вставки", restore_var)

    # ============ Tab: Система ============
    sysf = _card(tab_sys)

    mic_names = _input_devices()
    mic_var = tk.StringVar(
        value=cfg["input_device"] if cfg["input_device"] in mic_names
        else "По умолчанию")
    mic_cb = ttk.Combobox(sysf, textvariable=mic_var,
                          values=["По умолчанию"] + mic_names,
                          state="readonly", width=26, cursor="hand2")
    _row(sysf, 0, "Микрофон", mic_cb,
         "«По умолчанию» — системный микрофон Windows.")

    auto_var = tk.BooleanVar(value=config.autostart_enabled())
    _check(sysf, 2, "Запускать вместе с Windows", auto_var,
           "Тихий старт в трее при входе в систему.")

    # ============ Save / Close ============
    def do_save():
        mods = [m for m, v in mod_vars.items() if v.get()] or ["ctrl", "win"]
        lang = lang_var.get().strip()
        new = {
            "model_size": model_var.get(),
            "device": device_var.get(),
            "compute_type": compute_var.get(),
            "language": "" if lang == "auto" else lang,
            "input_device": "" if mic_var.get() == "По умолчанию" else mic_var.get(),
            "beam_size": int(beam_var.get()),
            "vad_filter": vad_var.get(),
            "auto_punctuation": punct_var.get(),
            "spoken_punctuation": spoken_var.get(),
            "custom_words": words_var.get().strip(),
            "hotkey_mods": mods,
            "push_to_talk": ptt_var.get(),
            "paste_mode": paste_var.get(),
            "restore_clipboard": restore_var.get(),
        }
        config.set_autostart(auto_var.get())
        on_save(new)
        status.config(text="Сохранено ✓")
        status.after(2500, lambda: status.config(text=""))

    ttk.Button(bottom, text="Закрыть", style="Ghost.TButton", cursor="hand2",
               command=root.destroy).pack(side="right")
    ttk.Button(bottom, text="Сохранить", style="Accent.TButton", cursor="hand2",
               command=do_save).pack(side="right", padx=(0, 8))

    _center(root, 480, 560)


def run_standalone():
    """Open the settings window on the main thread (`python -m openwispr --settings`)."""
    _enable_dpi_awareness()
    root = tk.Tk()
    _build(root, dict(config.load()), lambda c: config.save(c))
    root.mainloop()


def _selftest():
    root = tk.Tk()
    root.withdraw()
    _build(root, dict(config.DEFAULTS), lambda c: None)
    root.update()
    root.destroy()
    print("SETTINGS UI OK")


if __name__ == "__main__":
    _selftest()
