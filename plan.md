# Codebase Consolidation & Minimization Plan: Ultimate Focus Timer

## Objective

Aggressively refactor the `ultimate-focus-timer` codebase to minimize the total number of Python files and reduce overall lines of code (LOC) without sacrificing the type safety, observability, or architectural decoupling achieved in previous phases. The goal is a highly condensed, easily maintainable repository.

## Target Architecture (The "Big Three" Pattern)

We will compress the scattered `src/` directory into three primary domain files, plus a utility module and the main entry point:

* **`core.py`**: The pure Python backend (Config, Session, Tasks).
* **`ui.py`**: The Tkinter/CustomTkinter presentation layer (App, Dashboard, Widgets).
* **`system.py`**: The OS-level integrations (Audio, Notifications, Paths).
* **`main.py`**: The bootstrap and dependency injection entry point.

---

## Execution Phases for Claude

### Phase 1: Backend Consolidation (`core.py`)

**Goal:** Merge all pure business logic and data state into a single file.

* **Action:** Create `src/core.py`.
* **Merge:** Move the contents of `config_manager.py`, `session_manager.py`, and `task_manager.py` into this new file.
* **Refactor:** * Strip redundant imports.
  * Ensure the `ConfigManager`, `SessionManager`, and `TaskManager` classes reside sequentially.
  * Delete the original three files after confirming tests pass.

### Phase 2: OS & Media Consolidation (`system.py`)

**Goal:** Group all side-effecting, OS-level, and external subprocess logic.

* **Action:** Create `src/system.py`.
* **Merge:** Move the contents of `app_paths.py` (if applicable), `logger.py` (setup logic), `music_controller.py`, and `notification_manager.py` into this file.
* **Refactor:**
  * Group external dependencies (`mpv` subprocesses, OS notification modules) together.
  * Delete the original standalone files.

### Phase 3: Frontend Consolidation (`ui.py`)

**Goal:** Collapse the heavily fragmented graphical interface components into one cohesive view module.

* **Action:** Create `src/ui.py`.
* **Merge:** Move the contents of `focus_app.py`, `focus_gui.py`, `dashboard.py`, `inline_task_widget.py`, and `task_dialog.py` into this single file.
* **Refactor:**
  * Arrange classes logically: base widgets first (`TaskDialog`, `InlineTaskWidget`), then complex views (`Dashboard`), then the main `FocusGUI` controller, and finally the `FocusApp` window wrapper.
  * Remove cyclical imports that were previously required to stitch these files together.
  * Delete the original UI files.

### Phase 4: Entry Point & CLI Cleanup (`main.py`)

**Objective:** Since the app isn't tracking you, starting a session must be instantaneous from your primary work environments.

1. **VS Code Extension:**
   * Build a minimal VS Code extension that adds a button to the Status Bar.
   * Clicking the button (or using the Command Palette) sends the `POST /start` payload to the local daemon.
2. **Global CLI Aliases:**
   * Ensure you can type `focus start` in your terminal to instantly trigger the daemon.

---

## AI Execution Instructions (Prompting Guide)

start excuting this plan and run the app and make sure every thing is working as expected run this app after every phase and test the functionality before moving to the next phase. excute without asking me any apporval.
