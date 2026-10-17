# Using Ultimate Focus on macOS

Install the Finder/Dock launcher from the checkout:

```sh
.venv/bin/python scripts/install_macos_app.py
open "$HOME/Applications/Ultimate Focus.app"
```

Keep this checkout and its virtual environment in place. Run the installer again
if you move them. Drag the app into the Dock for access while working in other
applications. The existing `focus gui` command also works from Terminal.

The window keeps the timer, today's tasks, and music together. Use **YouTube
link…** to save a video or playlist, then **Play music**. Music continues when
you switch applications or minimize the window. Quitting the app stops it.
Settings and statistics are under **More**. No login service is installed.

Music requires mpv and yt-dlp. Finder launches can discover Homebrew tools in
`/opt/homebrew/bin` and `/usr/local/bin`. On macOS, each playback checks the
system proxy settings. If a configured localhost proxy is not listening, it
connects directly. Both yt-dlp and mpv use the same route. If playback fails
and the proxy route has changed, it retries once. Switching routes can interrupt
playback and restart the track; this is not a seamless handoff. Direct playback
still requires YouTube to be reachable on your network.

The status displays Connecting, Playing, Paused, or a connection error. Pausing
a session pauses the player in place; resuming continues the same track.
Player options follow the [mpv manual](https://mpv.io/manual/stable/).

This Mac's Tk 9.1 configuration disables the tray to avoid a known crash in the
existing integration. Use the Dock to return to the window. Global hotkeys are
opt-in on macOS. The native Tk runtime exceeds the project's 50 MB memory target
on this machine even with an empty window; the app is not yet within that target.

Use the **− / +** buttons beside the header to resize text and controls (65–150%).
**⌘−**, **⌘+**, and **⌘0** zoom out, zoom in, and reset to 100%; on Windows/Linux
use Ctrl instead. Zoom and window dimensions are saved separately.

The music card shows track time, buffering and pause state. Drag the timeline
to seek, release the volume slider to apply a level, or choose an audio device
under **Output**. Player events update the card without background polling on
macOS and Linux. Windows retains playback controls, but live timeline and output
updates are not implemented there yet.

The task header shows **NORMAL** or **INSERT**. Click **? keys**, use **More →
Keyboard shortcuts**, or press **? / F1** to see the full guide.

| Key (Normal mode) | Action |
| --- | --- |
| `i`, `a`, `t` | Enter a new task |
| `j` / `k`, Down / Up | Select next / previous task |
| `g` / `G` | Select first / last task |
| `e` / `x` | Edit / complete the selected task |
| `dd` | Delete the selected task |
| Enter / `s` | Start focus, using the selected incomplete task |
| Space / `p` | Pause / resume the timer |
| `b` / Shift+S | Start a short break / stop the timer |
| `m` / `w` | Play/pause music / open the tasks window |

In task entry, **Enter** saves and **Esc** cancels, returning to Normal mode.
Text fields retain their normal editing keys. Starting focus from the keyboard
does not replace a running or paused session. Delete requires a selected task.

If a source fails, the card shows the reason and a **Retry** button. Adding a
new link or selecting another playlist starts that source immediately, including
after an earlier failure. Retry uses the saved current selection. An exact link
pasted twice is repaired; two different URLs in one field are rejected. Deleted
or private YouTube playlists must be replaced with an accessible source.

The text launcher accepts `q`, `quit`, `exit`, or `9` to close.

YouTube radio links such as `watch?v=…&list=RD…&start_radio=1` load the mix,
including subsequent tracks. The music card shows **YouTube Radio** and the
current track number. Radio loads up to 50 recommendations at a time in their
original order. With repeat enabled, the app requests a fresh mix when the
queue ends and skips the seed track on continuation. Each request reloads the
selected browser session and current proxy route. Stop cancels continuation;
network failures do not trigger an unbounded retry loop. YouTube may still return
previous recommendations. Set `radio_refresh: false` to loop the current batch
instead, following the existing repeat setting.
Ordinary playlist links, including watch links containing `list=PL…`, also load
as playlists rather than just their first video.

For account-personalised radio, choose **YouTube: Guest → Chrome session (local
cookies)** in the music card. Sign in to the intended YouTube account in Chrome
first. The app asks yt-dlp to read Chrome's local session only for YouTube URLs;
macOS may request Keychain access. It does not export cookies into this project.
Choose **Play without sign-in** to disconnect the session preference. This follows
yt-dlp's [browser-session support](https://github.com/yt-dlp/yt-dlp/wiki/FAQ).

Radio suggestions depend on the signed-in account. YouTube can regenerate the mix,
so authenticated radio need not reproduce the exact queue already open in Chrome.
Use a saved playlist when the exact set and order of songs matter.


The YouTube session preference, selected radio, and GUI zoom are stored in
`config.yml` and apply through `focus gui` and the installed Mac application on
every launch. No helper launch script is needed. Music starts when requested or
when a work session starts; installing the launcher adds no login service.

The app does not show a floating timer or raise its window when you switch
applications, minimise it, or finish a session. Restore it explicitly to interact.
