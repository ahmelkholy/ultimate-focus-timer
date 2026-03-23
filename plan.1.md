# Ultimate Focus Timer: Zero-Bloat Scientific Upgrade Plan

This architecture abandons background tracking entirely. Instead, it relies on an ultra-lightweight state machine that executes scientific protocols deterministically when triggered via VS Code or a global hotkey.

---

## Phase 1: The Lean Daemon & Ultradian State Machine

**Objective:** Build a lightweight FastAPI backend that strictly enforces the 90/20 Ultradian rhythm without monitoring your system.

1. **The Core Engine (`src/daemon.py` & `src/session_manager.py`):**
   - Implement an asynchronous state machine with three strict phases: `RAMP_UP` (5m) -> `DEEP_WORK` (85m) -> `NEURAL_REST` (20m).
   - The daemon sits idle consuming ~0% CPU until you send a `POST /start` request.
2. **Deterministic Distraction Blocking (`src/system.py`):**
   - When the `DEEP_WORK` state begins, the daemon automatically modifies your OS `hosts` file to block designated distractions or kills specific background processes.
   - When `NEURAL_REST` begins, it instantly restores them. No tracking required, just binary state execution.

## Phase 2: Scientific Actuation Layer

**Objective:** Integrate cognitive tools that activate based on the timer's state, requiring zero manual input after the session starts.

1. **40Hz Acoustic Neuromodulation (`src/music_controller.py`):**
   - Use `numpy` and `sounddevice` to generate a low-volume 40Hz binaural beat.
   - **Logic:** The daemon automatically starts the audio generation exactly when transitioning into `DEEP_WORK` and kills the audio stream the second `NEURAL_REST` begins.
2. **Zeigarnik Offload Hotkey (`src/hotkey_manager.py`):**
   - Register a single, system-wide hotkey (e.g., `Ctrl+Shift+Space`).
   - Pressing it opens a native, instant-load text input box. The input is appended directly to `~/brain_dump.md` and vanishes. No database, just raw text appending.

## Phase 3: Frictionless Editor Integration (The Triggers)

**Objective:** Since the app isn't tracking you, starting a session must be instantaneous from your primary work environments.

1. **VS Code Extension:**
   - Build a minimal VS Code extension that adds a button to the Status Bar.
   - Clicking the button (or using the Command Palette) sends the `POST /start` payload to the local daemon.
2. **Global CLI Aliases:**
   - Ensure you can type `focus start` in your terminal to instantly trigger the daemon.

---

## AI Execution Instructions (Prompting Guide)

start excuting this plan and run the app and make sure every thing is working as expected run this app after every phase and test the functionality before moving to the next phase. excute without asking me any apporval.
