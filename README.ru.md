<div align="center">

# 🎙️ OpenWispr

**Бесплатный офлайн-голосовой ввод текста для Windows.**

Зажми клавишу, говори, отпусти — речь распознаётся локально и вставляется
в любое активное окно. Свободная open-source-версия идеи
[Wispr Flow](https://wisprflow.ai/).

![platform](https://img.shields.io/badge/platform-Windows-0078D6)
![python](https://img.shields.io/badge/python-3.10%E2%80%933.12-blue)
![license](https://img.shields.io/badge/license-MIT-green)
![offline](https://img.shields.io/badge/100%25-offline-success)

[English](README.md) · **Русский**

</div>

---

## ✨ Возможности

- 🗣️ **Ввод в любом окне** — браузер, Word, мессенджеры, IDE.
- 🔒 **Полностью офлайн** — распознавание локально через
  [faster-whisper](https://github.com/SYSTRAN/faster-whisper). Без облака,
  ключей и подписки. Звук не покидает компьютер.
- 🌍 **Много языков** — русский, украинский, английский и ещё ~90.
- ⌨️ **Свой хоткей** — зажать-и-держать или переключатель; любая комбинация
  модификаторов (по умолчанию `Ctrl+Win`).
- 🎛️ **Окно настроек** — клик по иконке в трее: модель, язык, хоткей,
  автозапуск. Конфиги руками править не нужно.
- 🚀 **Автозапуск** — опционально стартует тихо вместе с Windows.
- 🔔 **Статус по цвету иконки** — зелёная (готов), красная (запись),
  синяя (обработка).
- 📋 **Вставка под любую раскладку** — через буфер обмена, надёжно для
  кириллицы и эмодзи.

## 🚀 Установка

### Вариант А — установщик (проще всего)

Скачай **`OpenWispr-Setup.exe`** со страницы [Releases](../../releases) и запусти.
Ставится как обычная программа (меню Пуск, опционально ярлык на рабочий стол и
автозапуск, деинсталлятор). Без прав админа, Python не нужен.

> Первый запуск скачает модель Whisper (~460 МБ для `small`) в
> `%USERPROFILE%\.cache\huggingface`. Нужен интернет один раз — дальше офлайн.

### Вариант Б — из исходников

```powershell
git clone https://github.com/<логин>/OpenWispr.git
cd OpenWispr
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m openwispr
```

Или двойной клик по **`scripts\run.bat`** (создаст окружение и поставит
зависимости при первом запуске). Нужен [Python 3.10+](https://www.python.org/downloads/).

## 🎧 Как пользоваться

1. Запусти — иконка в трее серая (загрузка), затем **зелёная** (готов).
2. Поставь курсор в любое поле ввода.
3. **Зажми `Ctrl+Win`**, говори, отпусти.
4. Иконка синеет на время распознавания, текст появляется у курсора.

**Клик по иконке в трее** — окно настроек. Правый клик → **Выход**.

## 🎛️ Настройки

Всё меняется в окне настроек из трея (хранится в
`%APPDATA%\OpenWispr\config.json`):

| Настройка | Что делает |
|---|---|
| **Модель** | `tiny`/`base`/`small`/`medium`/`large-v3` — больше = точнее, но медленнее. |
| **Устройство** | `cpu` или `cuda` (NVIDIA GPU, нужны библиотеки CUDA). |
| **Точность** | `int8` для CPU, `float16` для GPU. |
| **Язык** | Код вроде `ru`/`en` быстрее и точнее автоопределения. |
| **Beam** | `1` — быстрее, `5` — чуть точнее. |
| **Хоткей** | Любая комбинация Ctrl/Win/Alt/Shift; держать или переключать. |
| **Вставка** | Буфер `Ctrl+V` (по умолч.) или посимвольный ввод. |
| **Автозапуск** | Старт вместе с Windows. |

> Смена модели/устройства перезагружает модель после сохранения; хоткей,
> язык и остальное применяются сразу.

### Ускорение на GPU (NVIDIA)

Поставь устройство `cuda` и точность `float16`, затем установи рантайм CUDA:

```powershell
pip install nvidia-cublas-cu12 nvidia-cudnn-cu12
```

## 🛠️ Сборка установщика

```powershell
scripts\build.bat                                                          # PyInstaller -> dist\OpenWispr\
"%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" packaging\installer.iss     # -> Output\OpenWispr-Setup.exe
```

- **PyInstaller** пакует приложение в `dist\OpenWispr\OpenWispr.exe`
  (см. [`packaging/OpenWispr.spec`](packaging/OpenWispr.spec)).
- **[Inno Setup](https://jrsoftware.org/isdl.php)** оборачивает в установщик
  (см. [`packaging/installer.iss`](packaging/installer.iss)).
- Для сборки нужен **Python 3.12** — в Python 3.10.0 есть баг `dis`, который
  ломает PyInstaller. Само приложение работает и на 3.10+.

## 📁 Структура проекта

```
openwispr/    app.py · config.py · settings_window.py · __main__.py   (приложение)
packaging/    OpenWispr.spec · installer.iss · make_icon_file.py · OpenWispr.vbs
scripts/      run.bat · build.bat · install-autostart.bat · remove-autostart.bat
```

## 🔐 Приватность

Звук пишется, распознаётся на устройстве и сразу отбрасывается. Ничего не
загружается в сеть. Единственный сетевой запрос — разовое скачивание модели при
первом запуске.

## 🤝 Вклад

Issues и PR приветствуются. Идеи: голосовые команды («новая строка»), поддержка
macOS/Linux, ИИ-чистка текста, графический оверлей.

## 📄 Лицензия

[MIT](LICENSE). Не связано с Wispr Flow.
