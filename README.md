# typing-buddy

A Python desktop app that simulates human-like typing into any focused application.

## Features
- Paste or write the text to type
- Adjustable speed (WPM)
- Countdown timer so you can focus the target field
- Human-like typing: variable delays, short stops, bursts, occasional longer pauses
- Newlines are sent as soft breaks (Shift+Enter) to avoid accidental submits
- System-wide typing using `pynput`
- Stop/cancel at any time
- Preview mode (types into the app locally)
- Saves preferences (WPM, countdown)

## Requirements
- Python 3.9+
- Dependencies:
  - `pynput`

Install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate   # on Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

## Run

Option 1: run the module

```bash
python -m typing_buddy
```

Option 2: run the file

```bash
python typing_buddy/main.py
```

PowerShell (Windows) direct run:

```powershell
python .\typing_buddy\main.py
```

If `python -m typing_buddy` fails with `No module named typing_buddy.__main__`, you can run the module explicitly:

```powershell
python -m typing_buddy.main
```


If you encounter an "attempted relative import with no known parent package" error, prefer the module form above: `python -m typing_buddy`.

## How to use
1. Paste your text into the top text box.
2. Set your desired speed (WPM) and the countdown seconds.
3. Click "Type".
4. During the countdown, switch to the target app and click into the field where you want the text to be typed.
5. The app will type into the currently focused field. Use "Stop" to cancel.
6. Use "Preview" to test the typing behavior inside the app without sending system-wide keystrokes.

## Notes
- System-wide typing sends keystrokes to the currently focused application. Make sure the focus is in the correct input field.
- On some Linux environments (Wayland), global input may require additional permissions or running under XWayland. If typing does not work, try an X11 session or check your compositor's settings.
- Preferences are saved to `~/.typing_buddy/config.json`.
