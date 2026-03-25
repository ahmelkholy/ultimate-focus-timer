#!/usr/bin/env python3
"""
Zeigarnik Offload Hotkey Manager
Implements instant brain dump via global hotkey (Ctrl+Shift+Space)

Based on the Zeigarnik Effect: The brain holds unfinished tasks in working memory,
causing cognitive load. Quickly capturing thoughts frees mental resources.
"""

import logging
import tkinter as tk
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Check for keyboard library
try:
    import keyboard

    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False
    logger.warning("keyboard library not available - Zeigarnik hotkey disabled")


class ZeigarnikOffloadManager:
    """
    Manages the Zeigarnik offload hotkey system

    - Global hotkey: Ctrl+Shift+Space
    - Opens instant text input box
    - Appends to ~/brain_dump.md
    - No database, no overhead - pure text appending
    """

    def __init__(self, brain_dump_path: Optional[Path] = None):
        """
        Initialize Zeigarnik offload manager

        Args:
            brain_dump_path: Path to brain dump file (defaults to ~/brain_dump.md)
        """
        self.brain_dump_path = brain_dump_path or Path.home() / "brain_dump.md"
        self.is_active = False
        self._input_window: Optional[tk.Tk] = None

        if not KEYBOARD_AVAILABLE:
            logger.warning("Keyboard library not installed - hotkey unavailable")

    def start(self):
        """Start listening for the hotkey"""
        if not KEYBOARD_AVAILABLE:
            logger.warning("Cannot start Zeigarnik hotkey - keyboard library not available")
            return

        if self.is_active:
            logger.warning("Zeigarnik hotkey already active")
            return

        try:
            # Register global hotkey: Ctrl+Shift+Space
            keyboard.add_hotkey("ctrl+shift+space", self._on_hotkey_triggered)
            self.is_active = True
            logger.info("Zeigarnik hotkey active: Ctrl+Shift+Space")
        except Exception as e:
            logger.error("Error starting Zeigarnik hotkey: %s", e)

    def stop(self):
        """Stop listening for the hotkey"""
        if not KEYBOARD_AVAILABLE or not self.is_active:
            return

        try:
            keyboard.remove_hotkey("ctrl+shift+space")
            self.is_active = False
            logger.info("Zeigarnik hotkey deactivated")
        except Exception as e:
            logger.error("Error stopping Zeigarnik hotkey: %s", e)

    def _on_hotkey_triggered(self):
        """Handle hotkey press - show input window"""
        logger.info("Zeigarnik hotkey triggered")
        self._show_input_window()

    def _show_input_window(self):
        """Show instant-load text input box"""
        # Create a minimal, always-on-top window
        if self._input_window:
            # Window already exists, bring to front
            self._input_window.lift()
            self._input_window.focus_force()
            return

        self._input_window = tk.Tk()
        self._input_window.title("Brain Dump")
        self._input_window.geometry("400x150")
        self._input_window.resizable(False, False)

        # Make window always on top
        self._input_window.attributes("-topmost", True)

        # Center the window
        self._center_window(self._input_window)

        # Configure dark theme
        bg_color = "#2b2b2b"
        fg_color = "#00ff00"

        self._input_window.configure(bg=bg_color)

        # Instructions label
        instruction_label = tk.Label(
            self._input_window,
            text="💡 Quick thought capture:",
            font=("Arial", 10, "bold"),
            bg=bg_color,
            fg=fg_color,
        )
        instruction_label.pack(pady=(10, 5))

        # Text entry
        text_entry = tk.Text(
            self._input_window, height=4, font=("Consolas", 11), bg="#1a1a1a", fg=fg_color, insertbackground=fg_color
        )
        text_entry.pack(padx=10, pady=(0, 10), fill="both", expand=True)
        text_entry.focus_set()

        # Button frame
        button_frame = tk.Frame(self._input_window, bg=bg_color)
        button_frame.pack(pady=(0, 10))

        # Save button
        save_button = tk.Button(
            button_frame,
            text="💾 Save (Enter)",
            command=lambda: self._save_thought(text_entry),
            bg="#404040",
            fg=fg_color,
            font=("Arial", 10),
            padx=10,
        )
        save_button.pack(side="left", padx=(0, 5))

        # Cancel button
        cancel_button = tk.Button(
            button_frame,
            text="❌ Cancel (Esc)",
            command=self._close_input_window,
            bg="#404040",
            fg=fg_color,
            font=("Arial", 10),
            padx=10,
        )
        cancel_button.pack(side="left")

        # Bind keys
        self._input_window.bind("<Return>", lambda e: self._save_thought(text_entry))
        self._input_window.bind("<Escape>", lambda e: self._close_input_window())
        self._input_window.protocol("WM_DELETE_WINDOW", self._close_input_window)

    def _center_window(self, window):
        """Center the window on screen"""
        window.update_idletasks()
        width = window.winfo_width()
        height = window.winfo_height()
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry(f"{width}x{height}+{x}+{y}")

    def _save_thought(self, text_widget: tk.Text):
        """Save the thought to brain_dump.md"""
        thought = text_widget.get("1.0", "end-1c").strip()

        if not thought:
            self._close_input_window()
            return

        try:
            # Create file if it doesn't exist
            if not self.brain_dump_path.exists():
                self.brain_dump_path.parent.mkdir(parents=True, exist_ok=True)
                self.brain_dump_path.write_text("# Brain Dump\n\n", encoding="utf-8")

            # Append thought with timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            entry = f"\n## {timestamp}\n{thought}\n"

            with open(self.brain_dump_path, "a", encoding="utf-8") as f:
                f.write(entry)

            logger.info("Saved thought to brain dump: %s", self.brain_dump_path)

        except Exception as e:
            logger.error("Error saving brain dump: %s", e)

        finally:
            self._close_input_window()

    def _close_input_window(self):
        """Close the input window"""
        if self._input_window:
            self._input_window.destroy()
            self._input_window = None


# ============================================================================
# Test Runner
# ============================================================================


def test_zeigarnik_offload():
    """Test the Zeigarnik offload system"""
    if not KEYBOARD_AVAILABLE:
        print("❌ keyboard library not installed - cannot test")
        print("Install with: pip install keyboard")
        return

    print("🧠 Testing Zeigarnik Offload System")
    print("=" * 50)
    print("Press Ctrl+Shift+Space to trigger brain dump")
    print("Press Ctrl+C to exit test")
    print("")

    manager = ZeigarnikOffloadManager()
    manager.start()

    try:
        # Keep the script running to listen for hotkey
        import signal

        signal.pause()
    except KeyboardInterrupt:
        print("\n✅ Test complete!")
        manager.stop()


if __name__ == "__main__":
    test_zeigarnik_offload()
