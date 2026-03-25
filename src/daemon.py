#!/usr/bin/env python3
"""
daemon.py - Lean FastAPI backend with Ultradian Rhythm State Machine.

Implements the 90/20 Ultradian protocol:
  RAMP_UP    (5 min)  → warm up, silence distractions
  DEEP_WORK  (85 min) → 40 Hz binaural beats, full focus
  NEURAL_REST (20 min) → audio stops, rest enforced

Usage:
  python -m src.daemon          # start daemon on default port 8765
  curl -X POST localhost:8765/start
  curl localhost:8765/status
  curl -X POST localhost:8765/stop
"""

import asyncio
import logging
import threading
import time
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

RAMP_UP_SECS = 5 * 60       # 5 minutes
DEEP_WORK_SECS = 85 * 60    # 85 minutes
NEURAL_REST_SECS = 20 * 60  # 20 minutes

DAEMON_PORT = 8765
DAEMON_HOST = "127.0.0.1"


# ── Phase Enum ────────────────────────────────────────────────────────────────


class UltradianPhase(str, Enum):
    IDLE = "IDLE"
    RAMP_UP = "RAMP_UP"
    DEEP_WORK = "DEEP_WORK"
    NEURAL_REST = "NEURAL_REST"


# ── Binaural Beat Generator ───────────────────────────────────────────────────

_audio_thread: Optional[threading.Thread] = None
_audio_stop = threading.Event()


def _generate_binaural(
    carrier_hz: float = 200.0,
    beat_hz: float = 40.0,
    volume: float = 0.15,
    sample_rate: int = 44100,
) -> None:
    """Generate 40 Hz binaural beats using numpy + sounddevice.

    Left channel: carrier_hz
    Right channel: carrier_hz + beat_hz (creates the binaural beat perception)
    """
    try:
        import numpy as np
        import sounddevice as sd

        logger.info(
            "Binaural beat started: %.0f Hz carrier + %.0f Hz beat", carrier_hz, beat_hz
        )

        block_duration = 0.5  # seconds per block
        block_samples = int(sample_rate * block_duration)

        sample_idx = 0
        while not _audio_stop.is_set():
            t = (np.arange(block_samples) + sample_idx) / sample_rate
            left = volume * np.sin(2 * np.pi * carrier_hz * t)
            right = volume * np.sin(2 * np.pi * (carrier_hz + beat_hz) * t)
            stereo = np.column_stack([left, right]).astype(np.float32)
            sd.play(stereo, samplerate=sample_rate, blocking=True)
            sample_idx += block_samples
    except ImportError:
        logger.warning("sounddevice or numpy not installed; binaural beat skipped")
    except Exception:
        logger.exception("Binaural beat generator error")


def start_binaural() -> None:
    """Start 40 Hz binaural beats in a background thread."""
    global _audio_thread
    _audio_stop.clear()
    _audio_thread = threading.Thread(target=_generate_binaural, daemon=True)
    _audio_thread.start()


def stop_binaural() -> None:
    """Stop the binaural beat generator."""
    _audio_stop.set()
    if _audio_thread and _audio_thread.is_alive():
        _audio_thread.join(timeout=2)


# ── Ultradian State Machine ───────────────────────────────────────────────────


class UltradianStateMachine:
    """Deterministic Ultradian Rhythm state machine.

    Transitions:  IDLE → RAMP_UP → DEEP_WORK → NEURAL_REST → IDLE
    """

    def __init__(self) -> None:
        self.phase = UltradianPhase.IDLE
        self.phase_start: Optional[datetime] = None
        self.session_start: Optional[datetime] = None
        self._timer_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

        # Optional notification callback (injected at runtime)
        self._on_phase_change = None

    # ── Public controls ───────────────────────────────────────────────────────

    def start(self) -> bool:
        with self._lock:
            if self.phase != UltradianPhase.IDLE:
                return False
            self._stop_event.clear()
            self.session_start = datetime.now()
            self._enter_phase(UltradianPhase.RAMP_UP)
            self._timer_thread = threading.Thread(
                target=self._run, daemon=True
            )
            self._timer_thread.start()
            return True

    def stop(self) -> bool:
        with self._lock:
            if self.phase == UltradianPhase.IDLE:
                return False
            self._stop_event.set()
        stop_binaural()
        if self._timer_thread and self._timer_thread.is_alive():
            self._timer_thread.join(timeout=2)
        self.phase = UltradianPhase.IDLE
        logger.info("Session stopped manually")
        return True

    # ── State ─────────────────────────────────────────────────────────────────

    def get_status(self) -> Dict[str, Any]:
        elapsed = self._phase_elapsed()
        remaining = self._phase_remaining()
        return {
            "phase": self.phase.value,
            "phase_elapsed_secs": elapsed,
            "phase_remaining_secs": remaining,
            "session_started_at": (
                self.session_start.isoformat() if self.session_start else None
            ),
            "phase_started_at": (
                self.phase_start.isoformat() if self.phase_start else None
            ),
        }

    # ── Internal ──────────────────────────────────────────────────────────────

    def _run(self) -> None:
        """Main loop: wait for phase duration, then advance."""
        schedule = [
            (UltradianPhase.RAMP_UP, RAMP_UP_SECS),
            (UltradianPhase.DEEP_WORK, DEEP_WORK_SECS),
            (UltradianPhase.NEURAL_REST, NEURAL_REST_SECS),
        ]
        for phase, duration in schedule:
            if self._stop_event.wait(timeout=duration):
                break  # stopped early
            if self._stop_event.is_set():
                break
            # Advance to next phase
            if phase == UltradianPhase.RAMP_UP:
                self._enter_phase(UltradianPhase.DEEP_WORK)
            elif phase == UltradianPhase.DEEP_WORK:
                self._enter_phase(UltradianPhase.NEURAL_REST)
            elif phase == UltradianPhase.NEURAL_REST:
                stop_binaural()
                self.phase = UltradianPhase.IDLE
                logger.info("Ultradian cycle complete — returning to IDLE")
                break

    def _enter_phase(self, new_phase: UltradianPhase) -> None:
        self.phase = new_phase
        self.phase_start = datetime.now()
        logger.info("→ Phase: %s", new_phase.value)

        if new_phase == UltradianPhase.DEEP_WORK:
            start_binaural()
        elif new_phase == UltradianPhase.NEURAL_REST:
            stop_binaural()

        if self._on_phase_change:
            try:
                self._on_phase_change(new_phase)
            except Exception:
                logger.exception("Phase-change callback raised")

    def _phase_elapsed(self) -> float:
        if self.phase_start is None:
            return 0.0
        return (datetime.now() - self.phase_start).total_seconds()

    def _phase_remaining(self) -> float:
        duration_map = {
            UltradianPhase.RAMP_UP: RAMP_UP_SECS,
            UltradianPhase.DEEP_WORK: DEEP_WORK_SECS,
            UltradianPhase.NEURAL_REST: NEURAL_REST_SECS,
        }
        duration = duration_map.get(self.phase, 0)
        return max(0.0, duration - self._phase_elapsed())


# ── FastAPI App ───────────────────────────────────────────────────────────────

_state_machine = UltradianStateMachine()

app = FastAPI(
    title="Ultimate Focus Timer Daemon",
    description="Lean Ultradian Rhythm daemon — POST /start to begin a session.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class StartRequest(BaseModel):
    """Optional overrides for session timing (seconds)."""
    ramp_up_secs: Optional[int] = None
    deep_work_secs: Optional[int] = None
    neural_rest_secs: Optional[int] = None


@app.post("/start")
async def start_session(req: StartRequest = StartRequest()) -> Dict[str, Any]:
    """Begin a new Ultradian focus session."""
    global RAMP_UP_SECS, DEEP_WORK_SECS, NEURAL_REST_SECS
    # Reject timing overrides when a session is already active to avoid races
    if _state_machine.phase != UltradianPhase.IDLE and any(
        [req.ramp_up_secs, req.deep_work_secs, req.neural_rest_secs]
    ):
        return {
            "started": False,
            "message": "Cannot change timing while a session is running",
            "status": _state_machine.get_status(),
        }
    if req.ramp_up_secs is not None:
        RAMP_UP_SECS = req.ramp_up_secs
    if req.deep_work_secs is not None:
        DEEP_WORK_SECS = req.deep_work_secs
    if req.neural_rest_secs is not None:
        NEURAL_REST_SECS = req.neural_rest_secs

    started = _state_machine.start()
    return {
        "started": started,
        "message": "Session started" if started else "Session already running",
        "status": _state_machine.get_status(),
    }


@app.post("/stop")
async def stop_session() -> Dict[str, Any]:
    """Stop the current session immediately."""
    stopped = _state_machine.stop()
    return {
        "stopped": stopped,
        "message": "Session stopped" if stopped else "No active session",
    }


@app.get("/status")
async def get_status() -> Dict[str, Any]:
    """Return current phase and timing information."""
    return _state_machine.get_status()


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}


# ── Entry point ───────────────────────────────────────────────────────────────


def run_daemon(host: str = DAEMON_HOST, port: int = DAEMON_PORT) -> None:
    """Start the daemon server (blocking)."""
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting Focus Daemon on http://%s:%d", host, port)
    uvicorn.run(app, host=host, port=port, log_level="warning")


if __name__ == "__main__":
    run_daemon()
