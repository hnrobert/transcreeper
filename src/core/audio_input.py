"""
Audio input manager for capturing system audio and microphone input
"""
import platform
import queue
from typing import Callable, Dict, List, Optional

import numpy as np
import sounddevice as sd


class AudioInputManager:
    """Manages audio input from various sources"""

    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        callback: Optional[Callable[[np.ndarray, int], None]] = None
    ):
        """
        Initialize audio input manager

        Args:
            sample_rate: Sample rate for audio capture
            channels: Number of audio channels
            callback: Callback function for audio data
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.callback = callback

        self.stream = None
        self.is_recording = False

        # Audio buffer
        self.audio_queue = queue.Queue()

    def list_audio_devices(self) -> List[Dict]:
        """
        List all available audio devices

        Returns:
            List of audio device information
        """
        devices = []
        for i, device in enumerate(sd.query_devices()):
            # sounddevice may return either a dict-like object or a sequence; handle both safely
            if isinstance(device, dict):
                name = device.get('name', f"device-{i}")
                channels = device.get('max_input_channels', 0)
                sample_rate = device.get('default_samplerate', 0.0)
                hostapi = device.get('hostapi', None)
            else:
                # assume a sequence/tuple-like fallback
                name = device[0] if len(device) > 0 else f"device-{i}"
                channels = device[1] if len(device) > 1 else 0
                sample_rate = device[2] if len(device) > 2 else 0.0
                hostapi = device[3] if len(device) > 3 else None

            devices.append({
                'index': i,
                'name': name,
                'channels': channels,
                'sample_rate': sample_rate,
                'hostapi': hostapi
            })
        return devices

    def get_default_input_device(self) -> Optional[int]:
        """
        Get default input device index

        Returns:
            Device index or None
        """
        try:
            return sd.default.device[0]
        except Exception as e:
            print(f"Error getting default input device: {e}")
            return None

    def _audio_callback(self, indata, frames, time_info, status):
        """Internal callback for audio stream"""
        if status:
            print(f"Audio stream status: {status}")

        # Convert to mono if necessary
        if indata.shape[1] > 1:
            audio_data = np.mean(indata, axis=1)
        else:
            audio_data = indata[:, 0]

        # Call user callback
        if self.callback:
            self.callback(audio_data.copy(), self.sample_rate)

    def start_recording(self, device_index: Optional[int] = None):
        """
        Start recording audio

        Args:
            device_index: Audio device index (None for default)
        """
        if self.is_recording:
            print("Already recording")
            return

        try:
            self.stream = sd.InputStream(
                device=device_index,
                channels=self.channels,
                samplerate=self.sample_rate,
                callback=self._audio_callback,
                blocksize=int(self.sample_rate * 0.1)  # 100ms blocks
            )
            self.stream.start()
            self.is_recording = True
            print(f"Started recording from device {device_index or 'default'}")
        except Exception as e:
            print(f"Error starting recording: {e}")
            self.is_recording = False

    def stop_recording(self):
        """Stop recording audio"""
        if not self.is_recording:
            return

        try:
            if self.stream:
                self.stream.stop()
                self.stream.close()
                self.stream = None
            self.is_recording = False
            print("Stopped recording")
        except Exception as e:
            print(f"Error stopping recording: {e}")

    def is_active(self) -> bool:
        """Check if recording is active"""
        return self.is_recording


class SystemAudioCapture:
    """Capture system audio output"""

    def __init__(self, callback: Optional[Callable[[np.ndarray, int], None]] = None):
        """
        Initialize system audio capture

        Args:
            callback: Callback function for audio data
        """
        self.callback = callback
        self.is_capturing = False
        self.platform = platform.system()

    def start_capture(self):
        """Start capturing system audio"""
        if self.platform == "Darwin":  # macOS
            self._start_macos_capture()
        elif self.platform == "Windows":
            self._start_windows_capture()
        elif self.platform == "Linux":
            self._start_linux_capture()
        else:
            print(f"System audio capture not supported on {self.platform}")

    def _start_macos_capture(self):
        """Start macOS system audio capture using BlackHole or similar"""
        # Note: Requires virtual audio device like BlackHole
        print("macOS system audio capture requires BlackHole virtual audio device")
        print("Install from: https://github.com/ExistentialAudio/BlackHole")
        # Implementation would use BlackHole device

    def _start_windows_capture(self):
        """Start Windows system audio capture using WASAPI"""
        # Implementation for Windows using sounddevice with WASAPI
        print("Windows system audio capture using WASAPI")

    def _start_linux_capture(self):
        """Start Linux system audio capture using PulseAudio/PipeWire"""
        # Implementation for Linux using PulseAudio monitor
        print("Linux system audio capture using PulseAudio monitor")

    def stop_capture(self):
        """Stop capturing system audio"""
        self.is_capturing = False


class ApplicationAudioCapture:
    """Capture audio from specific applications"""

    def __init__(self, callback: Optional[Callable[[np.ndarray, int], None]] = None):
        """
        Initialize application audio capture

        Args:
            callback: Callback function for audio data
        """
        self.callback = callback
        self.captured_apps = []

    def list_audio_applications(self) -> List[Dict]:
        """
        List applications with audio output

        Returns:
            List of applications with audio
        """
        # Platform-specific implementation needed
        applications = []

        system = platform.system()
        if system == "Darwin":
            # macOS: Use Audio MIDI Setup or system APIs
            pass
        elif system == "Windows":
            # Windows: Use Core Audio APIs
            pass
        elif system == "Linux":
            # Linux: Use PulseAudio/PipeWire
            pass

        return applications

    def start_capture_app(self, app_id: str):
        """
        Start capturing audio from specific application

        Args:
            app_id: Application identifier
        """
        if app_id not in self.captured_apps:
            self.captured_apps.append(app_id)
            # Platform-specific implementation

    def stop_capture_app(self, app_id: str):
        """
        Stop capturing audio from specific application

        Args:
            app_id: Application identifier
        """
        if app_id in self.captured_apps:
            self.captured_apps.remove(app_id)
