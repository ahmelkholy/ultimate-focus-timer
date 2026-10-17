"""Compact music controls driven by the player's cached events."""

import logging
import queue
import threading
import tkinter as tk
from tkinter import ttk


def clock_text(seconds):
    seconds = max(0, int(seconds or 0))
    return f"{seconds // 60}:{seconds % 60:02d}"


class MusicPanel(tk.Frame):
    def __init__(
        self,
        parent,
        controller,
        config,
        add_link,
        select_playlist,
        select_session=None,
        on_action=None,
    ):
        self.dark = config.get("dark_theme", True)
        self.bg = "#222830" if self.dark else "#f0f3f6"
        self.fg = "#f4f6f8" if self.dark else "#17212b"
        self.muted = "#a4afbc" if self.dark else "#5f6b78"
        self.accent = "#94d8c1" if self.dark else "#176f58"
        super().__init__(parent, bg=self.bg, padx=12, pady=10)
        self.controller = controller
        self.on_action = on_action
        self._worker_lock = threading.Lock()
        self._worker = None
        self._actions = queue.Queue()
        self._closed = False
        self.bind("<Destroy>", self._on_destroy, add="+")
        self._volume_drag = False
        self._seek_drag = False
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self._label("FOCUS AUDIO", 10, bold=True).grid(row=0, column=0, sticky="w")
        self.status_label = self._label("Ready", 10, color=self.accent)
        self.status_label.grid(row=0, column=1, sticky="e")
        self.title_label = self._label("Choose your focus music", 13, bold=True)
        self.title_label.configure(wraplength=320, justify="left")
        self.title_label.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 2))
        self.source_label = self._label(
            "A little space to concentrate.", 9, color=self.muted
        )
        self.source_label.grid(row=2, column=0, columnspan=2, sticky="w")

        timeline = tk.Frame(self, bg=self.bg)
        timeline.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        timeline.columnconfigure(1, weight=1)
        self.elapsed = tk.Label(
            timeline, text="0:00", bg=self.bg, fg=self.muted, font=("Arial", 9)
        )
        self.elapsed.grid(row=0, column=0)
        self.position = tk.DoubleVar()
        self.seek_slider = ttk.Scale(timeline, from_=0, to=1, variable=self.position)
        self.seek_slider.grid(row=0, column=1, sticky="ew", padx=6)
        self.seek_slider.bind(
            "<ButtonPress-1>", lambda e: setattr(self, "_seek_drag", True)
        )
        self.seek_slider.bind("<ButtonRelease-1>", self._seek)
        self.duration_label = tk.Label(
            timeline, text="—", bg=self.bg, fg=self.muted, font=("Arial", 9)
        )
        self.duration_label.grid(row=0, column=2)

        transport = tk.Frame(self, bg=self.bg)
        transport.grid(row=4, column=0, columnspan=2, pady=6)
        self.previous = ttk.Button(
            transport,
            text="‹ Prev",
            width=6,
            command=lambda: self.run(controller.previous_track),
        )
        self.previous.grid(row=0, column=0, padx=3)
        self.play_button = ttk.Button(
            transport,
            text="Play",
            width=9,
            command=self.toggle,
            style="MusicPlay.TButton",
        )
        self.play_button.grid(row=0, column=1, padx=3)
        self.next = ttk.Button(
            transport,
            text="Next ›",
            width=6,
            command=lambda: self.run(controller.next_track),
        )
        self.next.grid(row=0, column=2, padx=3)
        self.stop = ttk.Button(
            transport,
            text="Stop",
            width=5,
            command=lambda: self.run(controller.stop_music),
        )
        self.stop.grid(row=0, column=3, padx=3)

        volume_row = tk.Frame(self, bg=self.bg)
        volume_row.grid(row=5, column=0, columnspan=2, sticky="ew")
        volume_row.columnconfigure(1, weight=1)
        tk.Label(
            volume_row, text="Volume", bg=self.bg, fg=self.muted, font=("Arial", 9)
        ).grid(row=0, column=0)
        self.volume = tk.DoubleVar(value=config.get("classical_music_volume", 30))
        self.volume_slider = ttk.Scale(
            volume_row,
            from_=0,
            to=100,
            variable=self.volume,
            command=self._volume_preview,
        )
        self.volume_slider.grid(row=0, column=1, sticky="ew", padx=6)
        self.volume_label = tk.Label(
            volume_row,
            text=f"{int(self.volume.get())}%",
            bg=self.bg,
            fg=self.muted,
            width=4,
            font=("Arial", 9),
        )
        self.volume_label.grid(row=0, column=2)
        self.volume_slider.bind(
            "<ButtonPress-1>", lambda e: setattr(self, "_volume_drag", True)
        )
        self.volume_slider.bind("<ButtonRelease-1>", self._set_volume)
        self.volume_slider.bind("<KeyRelease>", self._set_volume)

        self.playlist_var = tk.StringVar()
        self.playlist_combo = ttk.Combobox(
            self, textvariable=self.playlist_var, state="readonly", width=12
        )
        self.playlist_combo.grid(row=6, column=0, sticky="ew", pady=(8, 0), padx=(0, 6))
        self.playlist_combo.bind("<<ComboboxSelected>>", select_playlist)
        ttk.Button(self, text="Add link…", command=add_link).grid(
            row=6, column=1, sticky="e", pady=(8, 0)
        )
        self.device_button = ttk.Menubutton(self, text="Output: System default")
        self.device_menu = tk.Menu(self.device_button, tearoff=False)
        self.device_button.configure(menu=self.device_menu)
        self.device_button.grid(row=7, column=0, sticky="ew", pady=(6, 0), padx=(0, 6))
        self.session_button = ttk.Menubutton(self, text="YouTube: Guest")
        session_menu = tk.Menu(self.session_button, tearoff=False)
        if select_session:
            session_menu.add_command(
                label="Chrome session (local cookies)",
                command=lambda: select_session("chrome"),
            )
            session_menu.add_command(
                label="Play without sign-in", command=lambda: select_session("")
            )
        self.session_button.configure(menu=session_menu)
        self.session_button.grid(row=7, column=1, sticky="ew", pady=(6, 0))
        self._devices = None
        self.bind(
            "<Configure>",
            lambda e: (
                self.title_label.configure(wraplength=max(160, e.width - 24)),
                self.source_label.configure(wraplength=max(160, e.width - 24)),
            ),
        )

    def _label(self, text, size, bold=False, color=None):
        return tk.Label(
            self,
            text=text,
            bg=self.bg,
            fg=color or self.fg,
            anchor="w",
            font=("Arial", size, "bold" if bold else "normal"),
        )

    def _on_destroy(self, event):
        if event.widget is self:
            self._closed = True
            self._actions.put(None)

    def run(self, action):
        """Queue requests in order so a new link cannot be silently discarded."""
        if self._closed:
            return
        self._actions.put(action)
        # User actions wake a sleeping GUI; workers never touch Tk widgets.
        if self.on_action:
            self.on_action()
        with self._worker_lock:
            if self._worker is None:
                self._worker = threading.Thread(target=self._run_actions, daemon=True)
                self._worker.start()

    def _run_actions(self):
        while True:
            action = self._actions.get()
            if action is None or self._closed:
                return
            try:
                action()
            except Exception as exc:
                self.controller.last_error = (
                    "The player could not finish this action. Retry playback."
                )
                self.controller.playback_state = "error"
                logging.getLogger(__name__).warning(
                    "Music action failed: %s", type(exc).__name__
                )

    def toggle(self):
        state = self.controller.playback_state
        if state == "loading":
            return
        action = (
            self.controller.pause_music
            if state == "playing"
            else (
                self.controller.resume_music
                if state == "paused"
                else self.controller.start_music
            )
        )
        self.run(action)

    def _volume_preview(self, value):
        self.volume_label.configure(text=f"{round(float(value))}%")

    def _set_volume(self, event=None):
        value = round(self.volume.get())
        self._volume_drag = False
        self.run(lambda: self.controller.set_volume(value))

    def _seek(self, event=None):
        value = self.position.get()
        self._seek_drag = False
        self.run(lambda: self.controller.seek(value))

    def refresh(self, status):
        state = status["state"]
        labels = {
            "loading": "Connecting…",
            "playing": "Playing",
            "paused": "Paused",
            "stopped": "Ready",
            "error": "Unable to play",
        }
        self.status_label.configure(
            text=(
                "Buffering…"
                if state == "playing" and status.get("buffering")
                else labels.get(state, "Ready")
            )
        )
        self.title_label.configure(
            text=status.get("current_track")
            or (
                "Finding your music…"
                if state == "loading"
                else "Choose your focus music"
            )
        )
        source = (
            "YouTube" if "youtu" in (status.get("current_playlist") or "") else "Music"
        )
        if status.get("source_kind") == "radio":
            source = "YouTube Radio"
        count = status.get("playlist_count", 0)
        if count > 1:
            source += f" · {status.get('playlist_index', 1)} / {count}"
        browser = status.get("youtube_browser", "")
        self.session_button.configure(
            text="YouTube: Chrome" if browser == "chrome" else "YouTube: Guest"
        )
        if browser == "chrome" and source.startswith("YouTube"):
            source += " · Chrome"
        self.source_label.configure(
            text=(
                status["error"]
                if state == "error"
                else f"{source} · {status.get('route', 'Auto')} connection"
            )
        )
        self.play_button.configure(
            text=(
                "Pause"
                if state == "playing"
                else (
                    "Resume"
                    if state == "paused"
                    else "Retry" if state == "error" else "Play"
                )
            ),
            state="disabled" if state == "loading" else "normal",
        )
        active = status["is_playing"]
        self.stop.configure(state="normal" if active else "disabled")
        queued = status.get("playlist_count", 0) > 1
        for button in (self.previous, self.next):
            button.configure(state="normal" if active and queued else "disabled")
        duration = status.get("duration", 0)
        position = status.get("position", 0) if active else 0
        self.elapsed.configure(text=clock_text(position))
        self.duration_label.configure(
            text=(
                clock_text(duration)
                if duration
                else "Live" if state == "playing" else "—"
            )
        )
        self.seek_slider.configure(
            to=max(1, duration), state="normal" if active and duration else "disabled"
        )
        if not self._seek_drag:
            self.position.set(position)
        if not self._volume_drag:
            self.volume.set(status["volume"])
            self._volume_preview(status["volume"])
        devices = status.get("devices", [])
        if devices != self._devices:
            self._devices = list(devices)
            self.device_menu.delete(0, "end")
            for device in devices:
                self.device_menu.add_command(
                    label=device["description"],
                    command=lambda name=device["name"]: self.run(
                        lambda: self.controller.set_audio_device(name)
                    ),
                )
        chosen = next(
            (d["description"] for d in devices if d["name"] == status.get("device")),
            "System default",
        )
        self.device_button.configure(text=f"Output: {chosen}")
