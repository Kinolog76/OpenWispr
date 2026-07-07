"""Settings window for OpenWispr: sidebar navigation, purple accent, custom
toggles — DPI-aware Tk UI styled after a modern desktop settings panel."""

import threading
import tkinter as tk
from tkinter import ttk

from PIL import Image, ImageDraw, ImageTk

from openwispr import config

VERSION = "1.1.0"

# Palette: white surfaces, indigo-violet accent.
BG = "#FFFFFF"
SIDEBAR = "#FFFFFF"
CARD = "#FFFFFF"
BORDER = "#E5E7EB"
TEXT = "#111827"
MUTED = "#6B7280"
FAINT = "#9CA3AF"
ACCENT = "#5B4EE9"
ACCENT_DARK = "#4A3ED4"
ACCENT_SOFT = "#EEEBFC"
HOVER = "#F6F6FB"
TRACK_OFF = "#D1D5DB"

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

PAGES = [
    ("recognition", "Распознавание", "mic",
     "Настройки модели и параметров распознавания речи"),
    ("text", "Текст", "text",
     "Настройки обработки и форматирования текста"),
    ("control", "Управление", "keyboard",
     "Настройки горячих клавиш и поведения записи"),
    ("system", "Система", "gear",
     "Системные настройки приложения"),
]


def _input_devices():
    try:
        from openwispr import app
        return app.list_input_devices()
    except Exception:
        return []


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


# ------------------------------- icons -----------------------------------

def _draw_icon(kind, color, size=18):
    """Simple line icons drawn at 2x and downscaled for smooth edges."""
    s = size * 4
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    w = s // 9  # stroke width

    if kind == "mic":
        d.rounded_rectangle((s*0.36, s*0.08, s*0.64, s*0.55), radius=s*0.14,
                            outline=color, width=w)
        d.arc((s*0.22, s*0.30, s*0.78, s*0.72), 0, 180, fill=color, width=w)
        d.line((s*0.5, s*0.72, s*0.5, s*0.86), fill=color, width=w)
        d.line((s*0.32, s*0.88, s*0.68, s*0.88), fill=color, width=w)
    elif kind == "text":
        d.rounded_rectangle((s*0.12, s*0.12, s*0.88, s*0.88), radius=s*0.16,
                            outline=color, width=w)
        d.line((s*0.32, s*0.36, s*0.68, s*0.36), fill=color, width=w)
        d.line((s*0.5, s*0.36, s*0.5, s*0.68), fill=color, width=w)
    elif kind == "keyboard":
        d.rounded_rectangle((s*0.08, s*0.26, s*0.92, s*0.74), radius=s*0.10,
                            outline=color, width=w)
        for i in range(4):
            x = s * (0.22 + i * 0.19)
            d.ellipse((x - w, s*0.38 - w, x + w, s*0.38 + w), fill=color)
        d.line((s*0.32, s*0.60, s*0.68, s*0.60), fill=color, width=w)
    elif kind == "gear":
        cx = cy = s / 2
        r_out, r_in = s*0.30, s*0.14
        import math
        for i in range(8):
            a = math.radians(i * 45)
            d.line((cx + r_out*0.9*math.cos(a), cy + r_out*0.9*math.sin(a),
                    cx + r_out*1.28*math.cos(a), cy + r_out*1.28*math.sin(a)),
                   fill=color, width=w + 2)
        d.ellipse((cx-r_out, cy-r_out, cx+r_out, cy+r_out), outline=color, width=w)
        d.ellipse((cx-r_in, cy-r_in, cx+r_in, cy+r_in), outline=color, width=w)
    elif kind == "quill":
        d.polygon([(s*0.82, s*0.10), (s*0.34, s*0.26), (s*0.16, s*0.86),
                   (s*0.28, s*0.80), (s*0.42, s*0.40), (s*0.82, s*0.10)],
                  fill=color)
        d.line((s*0.18, s*0.84, s*0.52, s*0.34), fill=color, width=w)

    return img.resize((size, size), Image.LANCZOS)


def _make_icons(root, size=18):
    icons = {}
    for kind in ("mic", "text", "keyboard", "gear"):
        icons[kind] = ImageTk.PhotoImage(_draw_icon(kind, MUTED, size))
        icons[kind + "_on"] = ImageTk.PhotoImage(_draw_icon(kind, ACCENT, size))
    icons["quill"] = ImageTk.PhotoImage(_draw_icon("quill", ACCENT, 26))
    icons["quill_small"] = ImageTk.PhotoImage(_draw_icon("quill", ACCENT, 18))
    root._icons = icons  # keep references alive
    return icons


# ------------------------------ widgets -----------------------------------

class Toggle(tk.Canvas):
    """iOS-style switch bound to a BooleanVar."""

    W, H = 44, 24

    def __init__(self, parent, variable, bg=CARD):
        super().__init__(parent, width=self.W, height=self.H, bg=bg,
                         highlightthickness=0, cursor="hand2")
        self.var = variable
        self.bind("<Button-1>", lambda e: self.var.set(not self.var.get()))
        self.var.trace_add("write", lambda *a: self._draw())
        self._draw()

    def _draw(self):
        self.delete("all")
        on = bool(self.var.get())
        track = ACCENT if on else TRACK_OFF
        h, w = self.H, self.W
        self.create_oval(1, 1, h - 1, h - 1, fill=track, outline=track)
        self.create_oval(w - h + 1, 1, w - 1, h - 1, fill=track, outline=track)
        self.create_rectangle(h / 2, 1, w - h / 2, h - 1, fill=track, outline=track)
        x = w - h + 3 if on else 3
        self.create_oval(x, 3, x + h - 6, h - 3, fill="#FFFFFF", outline="#FFFFFF")


class Placeholder:
    """Grey placeholder text for a ttk.Entry."""

    def __init__(self, entry, var, text):
        self.entry, self.var, self.text = entry, var, text
        self.active = False
        if not var.get():
            self._show()
        entry.bind("<FocusIn>", self._focus_in)
        entry.bind("<FocusOut>", self._focus_out)

    def _show(self):
        self.active = True
        self.var.set(self.text)
        self.entry.configure(foreground=FAINT)

    def _focus_in(self, _e):
        if self.active:
            self.active = False
            self.var.set("")
            self.entry.configure(foreground=TEXT)

    def _focus_out(self, _e):
        if not self.var.get().strip():
            self._show()

    def value(self):
        return "" if self.active else self.var.get().strip()


# ------------------------------- style ------------------------------------

def _style(root):
    root.configure(bg=BG)
    root.option_add("*TCombobox*Listbox.background", "#FFFFFF")
    root.option_add("*TCombobox*Listbox.foreground", TEXT)
    root.option_add("*TCombobox*Listbox.selectBackground", ACCENT)
    root.option_add("*TCombobox*Listbox.selectForeground", "#FFFFFF")

    st = ttk.Style(root)
    try:
        st.theme_use("clam")
    except tk.TclError:
        pass

    st.configure(".", background=BG, foreground=TEXT, font=(FONT, 10),
                 borderwidth=0, focuscolor=ACCENT)
    st.configure("TFrame", background=BG)
    st.configure("Card.TFrame", background=CARD)

    st.configure("Card.TLabel", background=CARD, foreground=TEXT)
    st.configure("RowHead.TLabel", background=CARD, foreground=TEXT,
                 font=(FONT + " Semibold", 10))
    st.configure("Muted.TLabel", background=CARD, foreground=MUTED, font=(FONT, 8))
    st.configure("AppName.TLabel", background=BG, foreground=TEXT,
                 font=(FONT + " Semibold", 13))
    st.configure("AppSub.TLabel", background=BG, foreground=MUTED, font=(FONT, 9))
    st.configure("PageTitle.TLabel", background=BG, foreground=TEXT,
                 font=(FONT + " Semibold", 17))
    st.configure("PageSub.TLabel", background=BG, foreground=MUTED, font=(FONT, 9))
    st.configure("Status.TLabel", background=BG, foreground=ACCENT, font=(FONT, 9))
    st.configure("Badge.TLabel", background=CARD, foreground=ACCENT_DARK,
                 font=(FONT + " Semibold", 10))

    st.configure("TCheckbutton", background=CARD, foreground=TEXT,
                 indicatorbackground="#FFFFFF", indicatormargin=6)
    st.map("TCheckbutton",
           background=[("active", CARD)],
           indicatorbackground=[("selected", ACCENT), ("active", "#FFFFFF")],
           indicatorforeground=[("selected", "#FFFFFF")])
    st.configure("TRadiobutton", background=CARD, foreground=TEXT,
                 indicatorbackground="#FFFFFF", indicatormargin=6)
    st.map("TRadiobutton",
           background=[("active", CARD)],
           indicatorbackground=[("selected", "#FFFFFF")],
           indicatorforeground=[("selected", ACCENT)])

    st.configure("Chip.Toolbutton", background="#FFFFFF", foreground=MUTED,
                 font=(FONT + " Semibold", 10), padding=(16, 7),
                 borderwidth=1, relief="solid")
    st.map("Chip.Toolbutton",
           background=[("selected", ACCENT), ("active", ACCENT_SOFT)],
           foreground=[("selected", "#FFFFFF"), ("active", ACCENT_DARK)])

    st.configure("TCombobox", fieldbackground="#FFFFFF", background="#FFFFFF",
                 foreground=TEXT, arrowcolor=MUTED, bordercolor=BORDER,
                 lightcolor=BORDER, darkcolor=BORDER, padding=6,
                 selectbackground="#FFFFFF", selectforeground=TEXT)
    st.map("TCombobox",
           fieldbackground=[("readonly", "#FFFFFF"), ("focus", "#FFFFFF")],
           foreground=[("readonly", TEXT), ("focus", TEXT)],
           selectbackground=[("readonly", "#FFFFFF"), ("focus", "#FFFFFF")],
           selectforeground=[("readonly", TEXT), ("focus", TEXT)],
           bordercolor=[("focus", ACCENT)])

    st.configure("TEntry", fieldbackground="#FFFFFF", foreground=TEXT,
                 bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER,
                 padding=8)
    st.map("TEntry", bordercolor=[("focus", ACCENT)])

    st.configure("Horizontal.TScale", background=CARD, troughcolor=BORDER)

    st.configure("Accent.TButton", background=ACCENT, foreground="#FFFFFF",
                 font=(FONT + " Semibold", 10), borderwidth=0, padding=(22, 9))
    st.map("Accent.TButton", background=[("active", ACCENT_DARK)])
    st.configure("Ghost.TButton", background="#FFFFFF", foreground=MUTED,
                 font=(FONT, 10), borderwidth=1, relief="solid", padding=(18, 8))
    st.map("Ghost.TButton", background=[("active", HOVER)],
           foreground=[("active", TEXT)])


# ------------------------------ helpers -----------------------------------

def _card(parent):
    outer = tk.Frame(parent, bg=CARD, highlightbackground=BORDER,
                     highlightthickness=1)
    outer.pack(fill="x", pady=(0, 12))
    inner = ttk.Frame(outer, style="Card.TFrame", padding=(16, 14))
    inner.pack(fill="both", expand=True)
    inner.columnconfigure(0, weight=1)
    return inner


def _setting_row(card, row, title, hint, control):
    """Bold title + grey hint on the left, control on the right."""
    left = ttk.Frame(card, style="Card.TFrame")
    left.grid(row=row, column=0, sticky="w", pady=(0, 12))
    ttk.Label(left, text=title, style="RowHead.TLabel").pack(anchor="w")
    if hint:
        ttk.Label(left, text=hint, style="Muted.TLabel",
                  wraplength=280, justify="left").pack(anchor="w", pady=(2, 0))
    control.grid(row=row, column=1, sticky="e", padx=(16, 0), pady=(0, 12))


def _center(root, w, h):
    root.update_idletasks()
    x = (root.winfo_screenwidth() - w) // 2
    y = (root.winfo_screenheight() - h) // 3
    root.geometry(f"{w}x{h}+{x}+{y}")


# ------------------------------- build ------------------------------------

def _build(root, cfg, on_save, model_ready_fn=None):
    root.title("OpenWispr — настройки")
    root.minsize(700, 560)
    _style(root)
    icons = _make_icons(root)

    # --- Header ---
    header = ttk.Frame(root)
    header.pack(fill="x", padx=18, pady=(14, 10))
    tk.Label(header, image=icons["quill"], bg=BG).pack(side="left")
    ttk.Label(header, text=" OpenWispr", style="AppName.TLabel").pack(side="left")
    ttk.Label(header, text="  локальный голосовой ввод",
              style="AppSub.TLabel").pack(side="left", pady=(3, 0))
    tk.Frame(root, bg=BORDER, height=1).pack(fill="x")

    body = ttk.Frame(root)
    body.pack(fill="both", expand=True)

    # --- Sidebar ---
    sidebar = tk.Frame(body, bg=SIDEBAR, width=190)
    sidebar.pack(side="left", fill="y")
    sidebar.pack_propagate(False)
    tk.Frame(body, bg=BORDER, width=1).pack(side="left", fill="y")

    nav_holder = tk.Frame(sidebar, bg=SIDEBAR)
    nav_holder.pack(fill="x", pady=(14, 0), padx=10)

    foot = tk.Frame(sidebar, bg=SIDEBAR)
    foot.pack(side="bottom", fill="x", padx=16, pady=14)
    tk.Label(foot, image=icons["quill_small"], bg=SIDEBAR).pack(side="left")
    fcol = tk.Frame(foot, bg=SIDEBAR)
    fcol.pack(side="left", padx=(6, 0))
    tk.Label(fcol, text="OpenWispr", bg=SIDEBAR, fg=TEXT,
             font=(FONT + " Semibold", 9)).pack(anchor="w")
    tk.Label(fcol, text="v" + VERSION, bg=SIDEBAR, fg=FAINT,
             font=(FONT, 8)).pack(anchor="w")

    # --- Content column ---
    content = ttk.Frame(body)
    content.pack(side="left", fill="both", expand=True, padx=(22, 22))

    page_title = ttk.Label(content, text="", style="PageTitle.TLabel")
    page_title.pack(anchor="w", pady=(16, 0))
    page_sub = ttk.Label(content, text="", style="PageSub.TLabel")
    page_sub.pack(anchor="w", pady=(2, 12))

    stack = ttk.Frame(content)
    stack.pack(fill="both", expand=True)
    stack.rowconfigure(0, weight=1)
    stack.columnconfigure(0, weight=1)

    bottom = ttk.Frame(content)
    bottom.pack(fill="x", side="bottom", pady=(8, 14))
    status = ttk.Label(bottom, text="", style="Status.TLabel")
    status.pack(side="left")

    pages = {}
    for key, _t, _i, _s in PAGES:
        f = ttk.Frame(stack)
        f.grid(row=0, column=0, sticky="nsew")
        pages[key] = f

    # ============ Page: Распознавание ============
    rec = _card(pages["recognition"])

    model_var = tk.StringVar(value=cfg["model_size"])
    mbox = ttk.Frame(rec, style="Card.TFrame")
    model_dot = tk.Label(mbox, text="", bg=CARD, font=(FONT, 9))
    model_dot.pack(side="left", padx=(0, 8))
    model_cb = ttk.Combobox(mbox, textvariable=model_var, values=MODELS,
                            state="readonly", width=15, cursor="hand2")
    model_cb.pack(side="left")
    model_hint_var = tk.StringVar(value=MODEL_HINTS.get(cfg["model_size"], ""))

    mleft = ttk.Frame(rec, style="Card.TFrame")
    mleft.grid(row=0, column=0, sticky="w", pady=(0, 12))
    ttk.Label(mleft, text="Модель", style="RowHead.TLabel").pack(anchor="w")
    ttk.Label(mleft, textvariable=model_hint_var, style="Muted.TLabel",
              wraplength=280, justify="left").pack(anchor="w", pady=(2, 0))
    mbox.grid(row=0, column=1, sticky="e", padx=(16, 0), pady=(0, 12))

    model_cb.bind("<<ComboboxSelected>>",
                  lambda e: model_hint_var.set(MODEL_HINTS.get(model_var.get(), "")))

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
    lang_cb = ttk.Combobox(rec, textvariable=lang_var, values=LANGS, width=15,
                           cursor="hand2")
    _setting_row(rec, 1, "Язык",
                 "Код языка (ru, en…) быстрее и точнее. auto — определять по речи.",
                 lang_cb)

    device_var = tk.StringVar(value=cfg["device"])
    device_cb = ttk.Combobox(rec, textvariable=device_var, values=DEVICES,
                             state="readonly", width=15, cursor="hand2")
    _setting_row(rec, 2, "Устройство",
                 "cuda — NVIDIA GPU (нужны библиотеки CUDA). Иначе cpu.",
                 device_cb)

    compute_var = tk.StringVar(value=cfg["compute_type"])
    compute_cb = ttk.Combobox(rec, textvariable=compute_var, values=COMPUTES,
                              state="readonly", width=15, cursor="hand2")
    _setting_row(rec, 3, "Вычисления", "int8 для CPU, float16 для GPU.",
                 compute_cb)

    beam_var = tk.IntVar(value=cfg["beam_size"])
    beam_box = ttk.Frame(rec, style="Card.TFrame")
    scale_col = ttk.Frame(beam_box, style="Card.TFrame")
    scale_col.pack(side="left")
    beam_scale = ttk.Scale(scale_col, from_=1, to=5, orient="horizontal",
                           length=150, value=cfg["beam_size"], cursor="hand2")
    beam_scale.pack()
    ticks = tk.Frame(scale_col, bg=CARD, width=150, height=14)
    ticks.pack()
    ticks.pack_propagate(False)
    for i in range(1, 6):
        # Slider knob travels between ~8px margins on a 150px scale.
        tk.Label(ticks, text=str(i), bg=CARD, fg=FAINT,
                 font=(FONT, 7)).place(x=8 + (i - 1) * 33.5, anchor="n")
    beam_badge = tk.Label(beam_box, text=str(beam_var.get()), bg=CARD,
                          fg=ACCENT_DARK, font=(FONT + " Semibold", 10),
                          highlightbackground=BORDER, highlightthickness=1,
                          padx=8, pady=2)
    beam_badge.pack(side="left", padx=(10, 0), anchor="n")
    beam_scale.configure(command=lambda v: (beam_var.set(round(float(v))),
                                            beam_badge.config(text=str(round(float(v))))))
    _setting_row(rec, 4, "Точность (beam)",
                 "1 — максимально быстро, 5 — максимально точно.", beam_box)

    vad_var = tk.BooleanVar(value=cfg["vad_filter"])
    _setting_row(rec, 5, "Фильтр тишины (VAD)",
                 "Обрезает паузы — меньше «галлюцинаций» на тишине.",
                 Toggle(rec, vad_var))

    # ============ Page: Текст ============
    ptxt = pages["text"]

    c1 = _card(ptxt)
    punct_var = tk.BooleanVar(value=cfg["auto_punctuation"])
    _setting_row(c1, 0, "Автопунктуация",
                 "Модель сама ставит запятые, точки и заглавные буквы.",
                 Toggle(c1, punct_var))

    c2 = _card(ptxt)
    spoken_var = tk.BooleanVar(value=cfg["spoken_punctuation"])
    _setting_row(c2, 0, "Голосовые команды пунктуации",
                 "Скажите «запятая», «точка», «новая строка» — вставится знак.",
                 Toggle(c2, spoken_var))

    c3 = _card(ptxt)
    ttk.Label(c3, text="Свой словарь", style="RowHead.TLabel").grid(
        row=0, column=0, sticky="w")
    words_var = tk.StringVar(value=cfg["custom_words"])
    words_entry = ttk.Entry(c3, textvariable=words_var)
    words_entry.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 4))
    words_ph = Placeholder(words_entry, words_var,
                           "Введите слова или термины через запятую")
    ttk.Label(c3,
              text="Термины через запятую — модель будет их узнавать.\n"
                   "Например: Kubernetes, OpenWispr, деплой, пул-реквест",
              style="Muted.TLabel", justify="left").grid(
        row=2, column=0, columnspan=2, sticky="w")

    # ============ Page: Управление ============
    pctl = pages["control"]

    h1 = _card(pctl)
    ttk.Label(h1, text="Горячая клавиша", style="RowHead.TLabel").grid(
        row=0, column=0, sticky="w")
    combo_label = tk.Label(h1, text="", bg=CARD, fg=ACCENT_DARK,
                           font=(FONT + " Semibold", 10))
    combo_label.grid(row=0, column=1, sticky="e")
    ttk.Label(h1, text="Держите комбинацию и говорите.",
              style="Muted.TLabel").grid(row=1, column=0, columnspan=2,
                                         sticky="w", pady=(2, 8))
    mods_now = set(cfg["hotkey_mods"])
    mod_vars = {}
    chip_row = ttk.Frame(h1, style="Card.TFrame")
    chip_row.grid(row=2, column=0, columnspan=2, sticky="w")

    def update_combo_label():
        picked = [MOD_LABELS[m] for m in MOD_KEYS if mod_vars[m].get()]
        combo_label.config(text=" + ".join(picked) if picked
                           else "Выберите клавишу")

    for i, name in enumerate(MOD_KEYS):
        var = tk.BooleanVar(value=name in mods_now)
        mod_vars[name] = var
        ttk.Checkbutton(chip_row, text=MOD_LABELS[name], variable=var,
                        style="Chip.Toolbutton", cursor="hand2",
                        command=update_combo_label).grid(row=0, column=i,
                                                         padx=(0, 8))
    update_combo_label()

    h2 = _card(pctl)
    ttk.Label(h2, text="Режим записи", style="RowHead.TLabel").grid(
        row=0, column=0, sticky="w", pady=(0, 6))
    ptt_var = tk.BooleanVar(value=cfg["push_to_talk"])
    ttk.Radiobutton(h2, text="Зажать и держать (push-to-talk)",
                    variable=ptt_var, value=True, cursor="hand2").grid(
        row=1, column=0, sticky="w", pady=(0, 4))
    ttk.Radiobutton(h2, text="Нажать — начать, нажать — остановить",
                    variable=ptt_var, value=False, cursor="hand2").grid(
        row=2, column=0, sticky="w")

    h3 = _card(pctl)
    ttk.Label(h3, text="Вставка текста", style="RowHead.TLabel").grid(
        row=0, column=0, sticky="w", pady=(0, 6))
    paste_var = tk.BooleanVar(value=cfg["paste_mode"])
    ttk.Checkbutton(h3, text="Через буфер обмена (Ctrl+V)", variable=paste_var,
                    cursor="hand2").grid(row=1, column=0, sticky="w")
    ttk.Label(h3, text="Надёжно для кириллицы. Иначе печатает посимвольно.",
              style="Muted.TLabel").grid(row=2, column=0, sticky="w",
                                         padx=(24, 0), pady=(0, 6))
    restore_var = tk.BooleanVar(value=cfg["restore_clipboard"])
    ttk.Checkbutton(h3, text="Восстанавливать буфер после вставки",
                    variable=restore_var, cursor="hand2").grid(
        row=3, column=0, sticky="w")

    # ============ Page: Система ============
    psys = pages["system"]

    s1 = _card(psys)
    mic_names = _input_devices()
    mic_var = tk.StringVar(
        value=cfg["input_device"] if cfg["input_device"] in mic_names
        else "По умолчанию")
    mic_cb = ttk.Combobox(s1, textvariable=mic_var,
                          values=["По умолчанию"] + mic_names,
                          state="readonly", width=24, cursor="hand2")
    _setting_row(s1, 0, "Микрофон",
                 "«По умолчанию» — системный микрофон Windows.", mic_cb)

    auto_var = tk.BooleanVar(value=config.autostart_enabled())
    _setting_row(s1, 1, "Запуск с системой",
                 "Тихий старт в трее при входе в систему.", Toggle(s1, auto_var))

    # ============ Sidebar navigation ============
    nav_items = {}
    current = tk.StringVar(value=PAGES[0][0])

    def select_page(key):
        current.set(key)
        for k, title, icon, sub in PAGES:
            frame, ilabel, tlabel = nav_items[k]
            active = (k == key)
            bg = ACCENT_SOFT if active else SIDEBAR
            frame.configure(bg=bg)
            ilabel.configure(bg=bg,
                             image=icons[icon + "_on"] if active else icons[icon])
            tlabel.configure(bg=bg, fg=ACCENT if active else MUTED)
            if active:
                page_title.config(text=title)
                page_sub.config(text=sub)
                pages[k].tkraise()

    for key, title, icon, _sub in PAGES:
        item = tk.Frame(nav_holder, bg=SIDEBAR, cursor="hand2")
        item.pack(fill="x", pady=2)
        il = tk.Label(item, image=icons[icon], bg=SIDEBAR)
        il.pack(side="left", padx=(12, 8), pady=9)
        tl = tk.Label(item, text=title, bg=SIDEBAR, fg=MUTED,
                      font=(FONT + " Semibold", 10))
        tl.pack(side="left", pady=9)
        nav_items[key] = (item, il, tl)

        def on_click(_e, k=key):
            select_page(k)

        def on_enter(_e, k=key):
            if current.get() != k:
                f, i, t = nav_items[k]
                for w in (f, i, t):
                    w.configure(bg=HOVER)

        def on_leave(_e, k=key):
            if current.get() != k:
                f, i, t = nav_items[k]
                for w in (f, i, t):
                    w.configure(bg=SIDEBAR)

        for w in (item, il, tl):
            w.bind("<Button-1>", on_click)
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)

    select_page(PAGES[0][0])

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
            "custom_words": words_ph.value(),
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
               command=do_save).pack(side="right", padx=(0, 10))

    _center(root, 780, 620)


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
