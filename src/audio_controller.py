#!/usr/bin/env python3
"""
40Hz Acoustic Neuromodulation Generator
Generates 40Hz binaural beats for cognitive enhancement during deep work
"""

import logging
import threading
import time
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

# Check for sounddevice
try:
    import sounddevice as sd

    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    logger.warning("sounddevice not available - audio features disabled")


class BinauralBeatGenerator:
    """
    Generates 40Hz binaural beats for cognitive enhancement

    Science: 40Hz gamma waves are associated with:
    - Enhanced focus and attention
    - Improved memory consolidation
    - Increased cognitive performance
    """

    def __init__(self, sample_rate: int = 44100, volume: float = 0.15):
        """
        Initialize binaural beat generator

        Args:
            sample_rate: Audio sample rate (Hz)
            volume: Output volume (0.0 to 1.0)
        """
        self.sample_rate = sample_rate
        self.volume = volume
        self.is_playing = False
        self._play_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        if not AUDIO_AVAILABLE:
            logger.warning("Audio generation unavailable - sounddevice not installed")

    def start(self):
        """Start playing 40Hz binaural beat"""
        if not AUDIO_AVAILABLE:
            logger.warning("Cannot start audio - sounddevice not available")
            return

        if self.is_playing:
            logger.warning("Binaural beat already playing")
            return

        self.is_playing = True
        self._stop_event.clear()
        self._play_thread = threading.Thread(target=self._play_loop, daemon=True)
        self._play_thread.start()
        logger.info("Started 40Hz binaural beat (volume: %.1f%%)", self.volume * 100)

    def stop(self):
        """Stop playing binaural beat"""
        if not self.is_playing:
            return

        self.is_playing = False
        self._stop_event.set()

        if self._play_thread and self._play_thread.is_alive():
            self._play_thread.join(timeout=2.0)

        logger.info("Stopped 40Hz binaural beat")

    def _play_loop(self):
        """
        Generate and play continuous binaural beat

        Method:
        - Left ear: Base frequency (e.g., 200 Hz)
        - Right ear: Base frequency + 40 Hz (e.g., 240 Hz)
        - Brain perceives 40Hz difference as gamma wave
        """
        base_freq = 200  # Hz - base carrier frequency
        beat_freq = 40  # Hz - target gamma frequency

        # Generate continuous audio chunks
        chunk_duration = 1.0  # seconds
        chunk_samples = int(self.sample_rate * chunk_duration)

        try:
            # Create audio stream
            stream = sd.OutputStream(
                samplerate=self.sample_rate, channels=2, dtype="float32"
            )
            stream.start()

            t = 0  # Current time position
            while not self._stop_event.is_set():
                # Generate time array for this chunk
                t_chunk = np.linspace(
                    t, t + chunk_duration, chunk_samples, endpoint=False
                )

                # Generate sine waves
                left_channel = self.volume * np.sin(2 * np.pi * base_freq * t_chunk)
                right_channel = self.volume * np.sin(
                    2 * np.pi * (base_freq + beat_freq) * t_chunk
                )

                # Combine into stereo
                stereo_audio = np.column_stack((left_channel, right_channel))

                # Play chunk
                stream.write(stereo_audio.astype(np.float32))

                # Advance time
                t += chunk_duration

            stream.stop()
            stream.close()

        except Exception as e:
            logger.error("Error in binaural beat playback: %s", e)
            self.is_playing = False

    def set_volume(self, volume: float):
        """Set playback volume (0.0 to 1.0)"""
        self.volume = max(0.0, min(1.0, volume))
        logger.info("Set binaural beat volume to %.1f%%", self.volume * 100)


# ============================================================================
# Global Audio Controller
# ============================================================================


class AudioController:
    """
    Controls audio playback during focus sessions
    - 40Hz binaural beats during DEEP_WORK
    - Silent during RAMP_UP and NEURAL_REST
    """

    def __init__(self):
        self.binaural_generator = BinauralBeatGenerator()
        self.is_enabled = True

    def enable(self):
        """Enable audio features"""
        self.is_enabled = True

    def disable(self):
        """Disable audio features"""
        self.is_enabled = False
        self.stop()

    def start_deep_work_audio(self):
        """Start audio for deep work phase"""
        if not self.is_enabled:
            return

        self.binaural_generator.start()

    def stop(self):
        """Stop all audio"""
        self.binaural_generator.stop()

    def set_volume(self, volume: float):
        """Set audio volume"""
        self.binaural_generator.set_volume(volume)


# ============================================================================
# Test Runner
# ============================================================================


def test_binaural_beat():
    """Test the binaural beat generator"""
    if not AUDIO_AVAILABLE:
        print("❌ sounddevice not installed - cannot test audio")
        print("Install with: pip install sounddevice numpy")
        return

    print("🎵 Testing 40Hz Binaural Beat Generator")
    print("=" * 50)
    print("Starting 10-second test...")
    print("You should hear a continuous tone.")
    print("The 40Hz beat should induce a subtle 'wobbling' effect.")

    generator = BinauralBeatGenerator(volume=0.2)
    generator.start()

    try:
        time.sleep(10)
    finally:
        generator.stop()

    print("✅ Test complete!")


if __name__ == "__main__":
    test_binaural_beat()
