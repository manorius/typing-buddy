import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox

try:
    from .preferences import load_preferences, save_preferences
    from .simulator import TypingSimulator, make_system_sender
except ImportError:
    # Allow running as a script: python typing_buddy/main.py
    import os, sys
    sys.path.append(os.path.dirname(__file__))
    from preferences import load_preferences, save_preferences  # type: ignore
    from simulator import TypingSimulator, make_system_sender  # type: ignore

APP_TITLE = "Typing Buddy"


class TypingBuddyApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_TITLE)
        self.minsize(820, 520)

        # State
        self._prefs = load_preferences()
        self._countdown_seconds = tk.IntVar(value=self._prefs.get("countdown", 3))
        self._wpm = tk.IntVar(value=self._prefs.get("wpm", 120))
        self._status = tk.StringVar(value="Ready")
        self._progress = tk.StringVar(value="")
        self._typing_thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._countdown_active = False

        self._build_ui()

    def _build_ui(self) -> None:
        pad = {"padx": 8, "pady": 8}

        # Top controls
        top = ttk.Frame(self)
        top.pack(fill=tk.X, **pad)

        ttk.Label(top, text="Speed (WPM):").grid(row=0, column=0, sticky="w")
        wpm_scale = ttk.Scale(top, from_=20, to=220, orient=tk.HORIZONTAL,
                              command=lambda v: self._wpm.set(int(float(v))))
        wpm_scale.set(self._wpm.get())
        wpm_scale.grid(row=0, column=1, sticky="ew", padx=(6, 12))

        ttk.Label(top, textvariable=self._wpm, width=5, anchor="e").grid(row=0, column=2)

        ttk.Label(top, text="Countdown (s):").grid(row=0, column=3, sticky="w", padx=(18, 0))
        self._countdown_box = ttk.Spinbox(top, from_=0, to=15, width=5, textvariable=self._countdown_seconds)
        self._countdown_box.grid(row=0, column=4, sticky="w", padx=(6, 0))

        # Buttons
        btns = ttk.Frame(top)
        btns.grid(row=0, column=5, sticky="e")
        self._btn_type = ttk.Button(btns, text="Type", command=self._on_type)
        self._btn_type.grid(row=0, column=0, padx=3)
        self._btn_preview = ttk.Button(btns, text="Preview", command=self._on_preview)
        self._btn_preview.grid(row=0, column=1, padx=3)
        self._btn_stop = ttk.Button(btns, text="Stop", command=self._on_stop, state=tk.DISABLED)
        self._btn_stop.grid(row=0, column=2, padx=3)
        self._btn_save = ttk.Button(btns, text="Save Settings", command=self._on_save)
        self._btn_save.grid(row=0, column=3, padx=3)

        top.columnconfigure(1, weight=1)
        top.columnconfigure(5, weight=0)

        # Text areas
        body = ttk.PanedWindow(self, orient=tk.VERTICAL)
        body.pack(fill=tk.BOTH, expand=True, **pad)

        input_frame = ttk.Labelframe(body, text="Text to type")
        self._input = tk.Text(input_frame, wrap=tk.WORD, height=12)
        self._input.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        preview_frame = ttk.Labelframe(body, text="Preview output (local, not system-wide)")
        self._preview = tk.Text(preview_frame, wrap=tk.WORD, height=10, state=tk.NORMAL)
        self._preview.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        body.add(input_frame)
        body.add(preview_frame)

        # Status bar
        status = ttk.Frame(self)
        status.pack(fill=tk.X, side=tk.BOTTOM)
        ttk.Label(status, textvariable=self._status).pack(side=tk.LEFT, padx=8)
        ttk.Label(status, textvariable=self._progress).pack(side=tk.RIGHT, padx=8)

        self._set_status("Ready. Paste your text, then click Type. A countdown lets you focus the target field.")

    # UI State helpers
    def _set_status(self, text: str) -> None:
        self._status.set(text)

    def _set_progress(self, cur: int, total: int) -> None:
        self._progress.set(f"{cur}/{total}")

    def _set_controls_enabled(self, enabled: bool) -> None:
        state = tk.NORMAL if enabled else tk.DISABLED
        self._btn_type.config(state=state)
        self._btn_preview.config(state=state)
        self._btn_save.config(state=state)
        self._countdown_box.config(state=state)

    # Actions
    def _on_save(self) -> None:
        save_preferences({"wpm": self._wpm.get(), "countdown": self._countdown_seconds.get()})
        messagebox.showinfo(APP_TITLE, "Settings saved.")

    def _on_stop(self) -> None:
        self._stop_event.set()
        self._countdown_active = False
        self._set_status("Stopping…")

    def _on_type(self) -> None:
        # Lazy import to allow app to open without dependency
        try:
            from pynput.keyboard import Controller  # type: ignore
        except Exception:
            messagebox.showerror(APP_TITLE, "Missing dependency: pynput.\n\nInstall with:\n\n  pip install -r requirements.txt")
            return

        text = self._input.get("1.0", tk.END)
        if not text.strip():
            messagebox.showwarning(APP_TITLE, "Please enter some text to type.")
            return

        self._stop_event = threading.Event()
        self._set_controls_enabled(False)
        self._btn_stop.config(state=tk.NORMAL)
        seconds = max(0, int(self._countdown_seconds.get()))
        self._countdown_active = True
        self._do_countdown(seconds, lambda: self._start_system_typing(text))

    def _on_preview(self) -> None:
        text = self._input.get("1.0", tk.END)
        if not text.strip():
            messagebox.showwarning(APP_TITLE, "Please enter some text to preview.")
            return
        self._preview.config(state=tk.NORMAL)
        self._preview.delete("1.0", tk.END)
        self._stop_event = threading.Event()
        self._set_controls_enabled(False)
        self._btn_stop.config(state=tk.NORMAL)
        self._set_status("Preview typing…")
        self._set_progress(0, len(text))
        self._typing_thread = threading.Thread(target=self._run_preview_sim, args=(text,), daemon=True)
        self._typing_thread.start()

    # Countdown and typing
    def _do_countdown(self, seconds: int, on_finish) -> None:
        if not self._countdown_active:
            self._finish(False)
            return
        if seconds <= 0:
            self._set_status("Typing… Focus should now be on the target field.")
            on_finish()
            return
        self._set_status(f"Starting in {seconds}… Switch to your target field now.")
        self.after(1000, lambda: self._do_countdown(seconds - 1, on_finish))

    def _start_system_typing(self, text: str) -> None:
        try:
            from pynput.keyboard import Controller  # type: ignore
        except Exception:
            messagebox.showerror(APP_TITLE, "Missing dependency: pynput.\n\nInstall with:\n\n  pip install -r requirements.txt")
            self._finish(False)
            return
        ctrl = Controller()
        sender = make_system_sender(ctrl)
        self._set_progress(0, len(text))

        def on_progress(cur: int, total: int) -> None:
            self.after(0, lambda: self._set_progress(cur, total))

        def on_done(completed: bool) -> None:
            self.after(0, lambda: self._finish(completed))

        sim = TypingSimulator(
            text=text,
            wpm=self._wpm.get(),
            send_char=sender,
            should_stop=lambda: self._stop_event.is_set(),
            on_progress=on_progress,
            on_done=on_done,
        )
        self._set_status("Typing…")
        self._typing_thread = threading.Thread(target=sim.run, daemon=True)
        self._typing_thread.start()

    def _run_preview_sim(self, text: str) -> None:
        def send_to_widget(ch: str) -> None:
            self.after(0, lambda: (self._preview.insert(tk.END, ch), self._preview.see(tk.END)))

        def on_progress(cur: int, total: int) -> None:
            self.after(0, lambda: self._set_progress(cur, total))

        def on_done(completed: bool) -> None:
            self.after(0, lambda: self._finish(completed))

        sim = TypingSimulator(
            text=text,
            wpm=self._wpm.get(),
            send_char=send_to_widget,
            should_stop=lambda: self._stop_event.is_set(),
            on_progress=on_progress,
            on_done=on_done,
        )
        sim.run()

    def _finish(self, completed: bool) -> None:
        msg = "Done" if completed else "Stopped"
        self._set_status(msg)
        self._btn_stop.config(state=tk.DISABLED)
        self._set_controls_enabled(True)


def main() -> None:
    app = TypingBuddyApp()
    app.mainloop()


if __name__ == "__main__":
    main()

