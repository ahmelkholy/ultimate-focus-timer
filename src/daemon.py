#!/usr/bin/env python3
"""
Ultra-Lightweight FastAPI Daemon for Ultimate Focus Timer
Implements 90/20 Ultradian rhythm without system monitoring
"""

import asyncio
from contextlib import suppress
import enum
import logging
import platform
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Import audio and Zeigarnik controllers
try:
    from .audio_controller import AudioController

    AUDIO_AVAILABLE = True
except (ImportError, OSError) as e:
    AUDIO_AVAILABLE = False
    AudioController = None  # type: ignore
    logging.getLogger(__name__).warning("Audio controller not available: %s", e)

try:
    from .zeigarnik_manager import ZeigarnikOffloadManager

    ZEIGARNIK_AVAILABLE = True
except ImportError as e:
    ZEIGARNIK_AVAILABLE = False
    ZeigarnikOffloadManager = None  # type: ignore
    logging.getLogger(__name__).warning("Zeigarnik manager not available: %s", e)

from .core import ConfigManager, TaskManager
from .google_integration import DEFAULT_TASK_LIST_ID, create_google_integration
from .system import DATA_DIR

logger = logging.getLogger(__name__)


# ============================================================================
# State Machine - 90/20 Ultradian Rhythm
# ============================================================================


class UltradianPhase(str, enum.Enum):
    """Three strict phases of the Ultradian cycle"""

    IDLE = "idle"
    RAMP_UP = "ramp_up"  # 5 minutes - gradual transition into focus
    DEEP_WORK = "deep_work"  # 85 minutes - peak cognitive performance
    NEURAL_REST = "neural_rest"  # 20 minutes - complete mental recovery


class SessionState(BaseModel):
    """Current session state"""

    phase: UltradianPhase = UltradianPhase.IDLE
    started_at: Optional[datetime] = None
    phase_started_at: Optional[datetime] = None
    phase_duration: int = 0  # minutes
    remaining_seconds: int = 0
    distraction_blocking_active: bool = False
    audio_active: bool = False


# ============================================================================
# Ultradian State Machine
# ============================================================================


class UltradianStateMachine:
    """
    Deterministic state machine for 90/20 Ultradian rhythm
    States: IDLE -> RAMP_UP (5m) -> DEEP_WORK (85m) -> NEURAL_REST (20m) -> IDLE
    """

    # Phase durations in minutes
    PHASE_DURATIONS = {
        UltradianPhase.RAMP_UP: 5,
        UltradianPhase.DEEP_WORK: 85,
        UltradianPhase.NEURAL_REST: 20,
    }

    def __init__(self):
        self.state = SessionState()
        self._timer_task: Optional[asyncio.Task] = None
        self._phase_transition_callbacks: Dict[UltradianPhase, List[callable]] = {
            phase: [] for phase in UltradianPhase
        }

        # Initialize audio and Zeigarnik controllers
        self.audio_controller = AudioController() if AUDIO_AVAILABLE else None
        self.zeigarnik_manager = ZeigarnikOffloadManager() if ZEIGARNIK_AVAILABLE else None

    def register_phase_callback(self, phase: UltradianPhase, callback: callable):
        """Register callback for phase transitions"""
        self._phase_transition_callbacks[phase].append(callback)

    async def start_session(self) -> dict:
        """Start a new Ultradian session"""
        if self.state.phase != UltradianPhase.IDLE:
            raise ValueError("Session already in progress")

        self.state.started_at = datetime.now()
        await self._transition_to_phase(UltradianPhase.RAMP_UP)

        # Start the timer loop
        if self._timer_task and not self._timer_task.done():
            self._timer_task.cancel()
        self._timer_task = asyncio.create_task(self._timer_loop())

        return self._get_state_dict()

    async def stop_session(self) -> dict:
        """Stop the current session"""
        if self._timer_task:
            self._timer_task.cancel()

        # Clean up any active effects
        await self._cleanup_phase_effects()

        self.state = SessionState()  # Reset to IDLE
        return self._get_state_dict()

    async def _transition_to_phase(self, phase: UltradianPhase):
        """Transition to a new phase"""
        # Clean up previous phase
        await self._cleanup_phase_effects()

        # Update state
        self.state.phase = phase
        self.state.phase_started_at = datetime.now()

        if phase == UltradianPhase.IDLE:
            self.state.phase_duration = 0
            self.state.remaining_seconds = 0
        else:
            self.state.phase_duration = self.PHASE_DURATIONS[phase]
            self.state.remaining_seconds = self.state.phase_duration * 60

        logger.info("Transitioned to phase: %s (%d minutes)", phase, self.state.phase_duration)

        # Execute phase-specific actions
        await self._execute_phase_actions(phase)

        # Trigger callbacks
        for callback in self._phase_transition_callbacks[phase]:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback()
                else:
                    callback()
            except Exception as e:
                logger.error("Phase callback error: %s", e)

    async def _execute_phase_actions(self, phase: UltradianPhase):
        """Execute deterministic actions for each phase"""
        if phase == UltradianPhase.DEEP_WORK:
            # Activate distraction blocking
            await self._activate_distraction_blocking()
            self.state.distraction_blocking_active = True

            # Start 40Hz binaural beats
            if self.audio_controller:
                self.audio_controller.start_deep_work_audio()
                self.state.audio_active = True
                logger.info("Started 40Hz binaural beat audio")

        elif phase == UltradianPhase.NEURAL_REST:
            # Deactivate distraction blocking
            await self._deactivate_distraction_blocking()
            self.state.distraction_blocking_active = False

            # Stop audio
            if self.audio_controller:
                self.audio_controller.stop()
                self.state.audio_active = False
                logger.info("Stopped audio for neural rest")

    async def _cleanup_phase_effects(self):
        """Clean up all phase-specific effects"""
        if self.state.distraction_blocking_active:
            await self._deactivate_distraction_blocking()
            self.state.distraction_blocking_active = False

        if self.state.audio_active:
            if self.audio_controller:
                self.audio_controller.stop()
            self.state.audio_active = False

    async def _timer_loop(self):
        """Main timer loop - ticks every second"""
        try:
            while self.state.phase != UltradianPhase.IDLE:
                await asyncio.sleep(1)
                self.state.remaining_seconds -= 1

                # Check if phase is complete
                if self.state.remaining_seconds <= 0:
                    await self._advance_to_next_phase()

        except asyncio.CancelledError:
            logger.info("Timer loop cancelled")
            raise

    async def _advance_to_next_phase(self):
        """Automatically advance to the next phase in the cycle"""
        if self.state.phase == UltradianPhase.RAMP_UP:
            await self._transition_to_phase(UltradianPhase.DEEP_WORK)
        elif self.state.phase == UltradianPhase.DEEP_WORK:
            await self._transition_to_phase(UltradianPhase.NEURAL_REST)
        elif self.state.phase == UltradianPhase.NEURAL_REST:
            await self._transition_to_phase(UltradianPhase.IDLE)

    async def _activate_distraction_blocking(self):
        """
        Binary state execution: Block designated distractions
        - Modify OS hosts file to block domains
        - Kill specific background processes
        """
        logger.info("Activating distraction blocking")

        # Load distraction list from config
        blocked_domains = self._get_blocked_domains()

        # Modify hosts file (requires sudo/admin)
        await self._modify_hosts_file(blocked_domains, block=True)

        # Kill background processes (e.g., Slack, Discord)
        blocked_processes = self._get_blocked_processes()
        await self._kill_processes(blocked_processes)

    async def _deactivate_distraction_blocking(self):
        """
        Restore normal system state
        - Remove blocks from hosts file
        """
        logger.info("Deactivating distraction blocking")

        blocked_domains = self._get_blocked_domains()
        await self._modify_hosts_file(blocked_domains, block=False)

    def _get_blocked_domains(self) -> List[str]:
        """Get list of domains to block during deep work"""
        # TODO: Load from config.yml
        return [
            "www.reddit.com",
            "reddit.com",
            "www.twitter.com",
            "twitter.com",
            "x.com",
            "www.x.com",
            "www.facebook.com",
            "facebook.com",
            "www.youtube.com",
            "youtube.com",
            "www.instagram.com",
            "instagram.com",
            "news.ycombinator.com",
        ]

    def _get_blocked_processes(self) -> List[str]:
        """Get list of process names to kill during deep work"""
        # TODO: Load from config.yml
        return [
            "slack",
            "discord",
            "telegram",
            "teams",
        ]

    async def _modify_hosts_file(self, domains: List[str], block: bool):
        """
        Modify the OS hosts file to block/unblock domains
        Requires admin/sudo privileges
        """
        system = platform.system()

        if system == "Windows":
            hosts_path = Path(r"C:\Windows\System32\drivers\etc\hosts")
        else:  # macOS/Linux
            hosts_path = Path("/etc/hosts")

        try:
            # Read current hosts file
            if not hosts_path.exists():
                logger.warning("Hosts file not found: %s", hosts_path)
                return

            # Check if we have write permissions
            if not hosts_path.is_file():
                logger.warning("Cannot access hosts file: %s", hosts_path)
                return

            marker_start = "# >>> FOCUS TIMER BLOCKING START >>>"
            marker_end = "# <<< FOCUS TIMER BLOCKING END <<<"

            # For safety, we'll create a command that uses sudo/admin
            if block:
                # Add blocking entries
                block_lines = [marker_start]
                for domain in domains:
                    block_lines.append(f"127.0.0.1    {domain}")
                block_lines.append(marker_end)

                logger.info("Would block %d domains (requires admin/sudo)", len(domains))
                # TODO: Implement actual hosts file modification with proper permissions
                # This requires elevated privileges and should be done carefully

            else:
                # Remove blocking entries
                logger.info("Would unblock domains (requires admin/sudo)")
                # TODO: Implement hosts file cleanup

        except Exception as e:
            logger.error("Error modifying hosts file: %s", e)

    async def _kill_processes(self, process_names: List[str]):
        """Kill specified background processes"""
        for proc_name in process_names:
            try:
                logger.info("Would kill process: %s", proc_name)
                # TODO: Uncomment to actually kill processes
                # import subprocess
                # system = platform.system()
                # if system == "Windows":
                #     cmd = ["taskkill", "/F", "/IM", f"{proc_name}.exe"]
                # else:  # macOS/Linux
                #     cmd = ["pkill", "-9", proc_name]
                # subprocess.run(cmd, capture_output=True)

            except Exception as e:
                logger.error("Error killing process %s: %s", proc_name, e)

    def _get_state_dict(self) -> dict:
        """Get current state as dictionary"""
        return {
            "phase": self.state.phase,
            "started_at": self.state.started_at.isoformat() if self.state.started_at else None,
            "phase_started_at": self.state.phase_started_at.isoformat() if self.state.phase_started_at else None,
            "phase_duration_minutes": self.state.phase_duration,
            "remaining_seconds": self.state.remaining_seconds,
            "distraction_blocking_active": self.state.distraction_blocking_active,
            "audio_active": self.state.audio_active,
        }

    def get_status(self) -> dict:
        """Get current status"""
        return self._get_state_dict()


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(title="Ultimate Focus Timer Daemon", version="3.0.0")

# Global state machine instance
state_machine = UltradianStateMachine()
SYNC_INTERVAL_SECONDS = 15 * 60

google_config_dir = Path.home() / ".ultimate-focus-timer"
daemon_config = ConfigManager()
daemon_google_integration = create_google_integration(google_config_dir)
daemon_task_manager = TaskManager(
    data_dir=DATA_DIR,
    google_integration=daemon_google_integration,
    google_task_list_id=daemon_config.get("google_task_list_id", DEFAULT_TASK_LIST_ID),
)
_periodic_sync_handle: Optional[asyncio.Task] = None


class StartSessionRequest(BaseModel):
    """Request to start a session"""

    enable_audio: bool = True
    enable_blocking: bool = True


class StatusResponse(BaseModel):
    """Status response"""

    phase: str
    started_at: Optional[str]
    phase_started_at: Optional[str]
    phase_duration_minutes: int
    remaining_seconds: int
    distraction_blocking_active: bool
    audio_active: bool


async def run_background_sync(reason: str = "interval") -> None:
    """Run a task sync in a background thread to avoid blocking the loop."""
    try:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, daemon_task_manager.sync_with_cloud)
        logger.info("Background sync finished (%s)", reason)
    except Exception as exc:
        logger.warning("Background sync failed (%s): %s", reason, exc)


async def periodic_sync_loop():
    """Periodic sync every SYNC_INTERVAL_SECONDS seconds."""
    while True:
        await asyncio.sleep(SYNC_INTERVAL_SECONDS)
        await run_background_sync("interval")


async def rest_phase_sync():
    """Trigger sync when entering neural rest."""
    await run_background_sync("rest_phase")


state_machine.register_phase_callback(UltradianPhase.NEURAL_REST, rest_phase_sync)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "online", "name": "Ultimate Focus Timer Daemon", "version": "3.0.0"}


@app.post("/start", response_model=StatusResponse)
async def start_session(request: StartSessionRequest):
    """Start a new Ultradian focus session"""
    try:
        result = await state_machine.start_session()
        logger.info("Session started via API")
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Error starting session")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/stop", response_model=StatusResponse)
async def stop_session():
    """Stop the current session"""
    try:
        result = await state_machine.stop_session()
        logger.info("Session stopped via API")
        return result
    except Exception as e:
        logger.exception("Error stopping session")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status", response_model=StatusResponse)
async def get_status():
    """Get current session status"""
    return state_machine.get_status()


@app.on_event("startup")
async def startup_event():
    """Initialize daemon on startup"""
    logger.info("Focus Timer Daemon starting...")
    logger.info("Ultradian rhythm: 5m RAMP_UP -> 85m DEEP_WORK -> 20m NEURAL_REST")
    global _periodic_sync_handle
    if _periodic_sync_handle is None:
        _periodic_sync_handle = asyncio.create_task(periodic_sync_loop())

    # Start Zeigarnik hotkey manager
    if state_machine.zeigarnik_manager:
        state_machine.zeigarnik_manager.start()
        logger.info("Zeigarnik offload hotkey (Ctrl+Shift+Space) active")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown"""
    logger.info("Focus Timer Daemon shutting down...")
    global _periodic_sync_handle
    if _periodic_sync_handle:
        _periodic_sync_handle.cancel()
        with suppress(asyncio.CancelledError):
            await _periodic_sync_handle
        _periodic_sync_handle = None

    # Stop Zeigarnik hotkey
    if state_machine.zeigarnik_manager:
        state_machine.zeigarnik_manager.stop()

    # Stop any active session
    await state_machine.stop_session()


# ============================================================================
# Daemon Runner
# ============================================================================


def run_daemon(host: str = "127.0.0.1", port: int = 8765):
    """Run the daemon server"""
    import uvicorn

    logger.info("Starting daemon on %s:%d", host, port)
    uvicorn.run(app, host=host, port=port, log_level="warning", access_log=False)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Ultimate Focus Timer Daemon")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8765, help="Port to bind to")
    args = parser.parse_args()

    run_daemon(args.host, args.port)
