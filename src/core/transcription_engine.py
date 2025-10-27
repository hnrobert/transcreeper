"""
Real-time transcription engine based on faster-whisper-large-v3
"""
import queue
import threading
import time
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

import numpy as np
import torch
import torchaudio
from faster_whisper import WhisperModel


@dataclass
class TranscriptionSegment:
    """Transcription segment data structure"""
    text: str
    language: str
    timestamp: float
    confidence: float
    start_time: float
    end_time: float


class RealTimeTranscriptionEngine:
    """Real-time transcription engine using faster-whisper-large-v3"""

    def __init__(
        self,
        model_size: str = "large-v3",
        device: str = "cuda",
        compute_type: str = "float16",
        languages: Optional[List[str]] = None,
        callback: Optional[Callable[[TranscriptionSegment], None]] = None,
        download_root: Optional[str] = None
    ):
        """
        Initialize real-time transcription engine

        Args:
            model_size: Model size (large-v3, medium, small, etc.)
            device: Computing device (cuda, cpu)
            compute_type: Computation precision (float16, int8, float32)
            languages: List of languages to transcribe
            callback: Callback function for transcription results
            download_root: Directory to cache downloaded models
        """
        # Check device availability
        if device == "cuda" and not torch.cuda.is_available():
            print("CUDA not available, falling back to CPU")
            device = "cpu"
            compute_type = "int8"

        self.device = device
        self.compute_type = compute_type

        # Load model with optional download_root
        self.model = WhisperModel(
            model_size,
            device=device,
            compute_type=compute_type,
            download_root=download_root
        )
        self.languages = languages or ["auto"]
        self.callback = callback
        # Audio processing
        # Increase queue size to reduce drops under bursty input
        self.audio_queue = queue.Queue(maxsize=300)
        self.result_queue = queue.Queue()
        self.is_running = False
        self.sample_rate = 16000

        # Buffer settings
        self.buffer = np.array([], dtype=np.float32)
        # Keep buffer small to reduce latency and memory usage
        self.buffer_duration = 1.0  # 1 second buffer
        self.chunk_size = int(self.sample_rate * 0.5)  # 500ms chunks

        # Processing thread
        self.processing_thread = None

        # Performance metrics
        self.metrics = {
            "processing_latency": [],
            "segments_processed": 0,
            "errors": 0
        }

        # Warmup model
        self._warmup_model()

    def _warmup_model(self):
        """Warmup model for faster first inference"""
        try:
            warmup_audio = np.random.randn(
                self.sample_rate).astype(np.float32) * 0.01
            list(self.model.transcribe(warmup_audio, language="en"))
            print(f"Model warmed up successfully on {self.device}")
        except Exception as e:
            print(f"Warning: Model warmup failed: {e}")

    def resample_audio(self, audio: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
        """
        Resample audio to target sample rate

        Args:
            audio: Input audio data
            orig_sr: Original sample rate
            target_sr: Target sample rate

        Returns:
            Resampled audio data
        """
        if orig_sr == target_sr:
            return audio

        # Use torchaudio for high-quality resampling
        tensor = torch.from_numpy(audio).float()
        if len(tensor.shape) == 1:
            tensor = tensor.unsqueeze(0)

        resampler = torchaudio.transforms.Resample(orig_sr, target_sr)
        resampled = resampler(tensor)
        return resampled.squeeze().numpy()

    def add_audio_data(self, audio_data: np.ndarray, sample_rate: int = 16000):
        """
        Add audio data to processing queue

        Args:
            audio_data: Audio data as numpy array
            sample_rate: Sample rate of the audio data
        """
        if not self.is_running:
            return

        # Resample if necessary
        if sample_rate != self.sample_rate:
            audio_data = self.resample_audio(
                audio_data, sample_rate, self.sample_rate)

        try:
            self.audio_queue.put_nowait(audio_data)
        except queue.Full:
            # If queue is full, drop the oldest frame to make room for the newest
            try:
                _ = self.audio_queue.get_nowait()
                self.audio_queue.put_nowait(audio_data)
            except Exception:
                # If we still can't enqueue, drop the incoming frame
                print("Warning: Audio queue is full, dropping frame")

    def _process_audio_stream(self):
        """Internal method to process audio stream"""
        while self.is_running:
            try:
                # Get audio data from queue with timeout
                audio_chunk = self.audio_queue.get(timeout=0.1)
                self.buffer = np.concatenate([self.buffer, audio_chunk])

                # Process when buffer reaches sufficient length
                if len(self.buffer) >= self.sample_rate * self.buffer_duration:
                    processing_chunk = self.buffer[:self.chunk_size]
                    self.buffer = self.buffer[self.chunk_size:]

                    # Transcribe
                    self._transcribe_chunk(processing_chunk)

            except queue.Empty:
                continue
            except Exception as e:
                print(f"Processing error: {e}")
                self.metrics["errors"] += 1
                continue

    def _transcribe_chunk(self, audio_chunk: np.ndarray):
        """
        Transcribe audio chunk

        Args:
            audio_chunk: Audio chunk to transcribe
        """
        start_time = time.time()

        try:
            for language in self.languages:
                segments, info = self.model.transcribe(
                    audio_chunk,
                    language=None if language == "auto" else language,
                    beam_size=5,
                    vad_filter=True,
                    vad_parameters=dict(
                        min_silence_duration_ms=500,
                        threshold=0.5
                    ),
                    condition_on_previous_text=False
                )

                for segment in segments:
                    result = TranscriptionSegment(
                        text=segment.text.strip(),
                        language=info.language if language == "auto" else language,
                        timestamp=time.time(),
                        confidence=segment.avg_logprob,
                        start_time=segment.start,
                        end_time=segment.end
                    )

                    # Add to result queue
                    self.result_queue.put(result)

                    # Call callback if provided
                    if self.callback:
                        self.callback(result)

                    self.metrics["segments_processed"] += 1

            # Record processing latency
            latency = (time.time() - start_time) * 1000
            self.metrics["processing_latency"].append(latency)
            if len(self.metrics["processing_latency"]) > 1000:
                self.metrics["processing_latency"].pop(0)

        except Exception as e:
            print(f"Transcription error: {e}")
            self.metrics["errors"] += 1

    def start(self):
        """Start the transcription engine"""
        if self.is_running:
            print("Engine already running")
            return

        self.is_running = True
        self.processing_thread = threading.Thread(
            target=self._process_audio_stream, daemon=True)
        self.processing_thread.start()
        print("Transcription engine started")

    def stop(self):
        """Stop the transcription engine"""
        if not self.is_running:
            return

        self.is_running = False
        if self.processing_thread:
            self.processing_thread.join(timeout=2.0)

        # Clear queues
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break

        print("Transcription engine stopped")

    def get_result(self, timeout: float = 0.1) -> Optional[TranscriptionSegment]:
        """
        Get transcription result from queue

        Args:
            timeout: Timeout in seconds

        Returns:
            TranscriptionSegment or None
        """
        try:
            return self.result_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def get_metrics(self) -> Dict:
        """Get performance metrics"""
        latencies = self.metrics["processing_latency"]
        return {
            "avg_latency_ms": np.mean(latencies) if latencies else 0,
            "max_latency_ms": max(latencies) if latencies else 0,
            "segments_processed": self.metrics["segments_processed"],
            "errors": self.metrics["errors"]
        }


class MultiLanguageTranscriptionEngine(RealTimeTranscriptionEngine):
    """
    Optimized multi-language transcription engine with adaptive language detection
    Integrates best practices for low-latency, high-quality real-time transcription
    """

    def __init__(
        self,
        source_language: str = "auto",
        target_languages: Optional[List[str]] = None,
        use_optimized: bool = True,
        **kwargs
    ):
        """
        Initialize multi-language transcription engine

        Args:
            source_language: Source language (language being spoken)
            target_languages: List of target languages for display
            use_optimized: Use optimized settings for lower latency
            **kwargs: Additional arguments for parent class
        """
        self.source_language = source_language
        self.target_languages = target_languages or []
        self.use_optimized = use_optimized

        # Setup languages list for processing
        languages = []
        if source_language != "auto":
            languages.append(source_language)
        if target_languages:
            languages.extend(target_languages)

        super().__init__(languages=languages, **kwargs)

        self.language_detection_threshold = 0.8
        self.detected_language = None
        self.current_language = source_language

    def detect_language(self, audio_chunk: np.ndarray) -> str:
        """
        Detect language from audio chunk

        Args:
            audio_chunk: Audio chunk for language detection

        Returns:
            Detected language code
        """
        try:
            segments, info = self.model.transcribe(
                audio_chunk, task="transcribe")
            if info.language_probability > self.language_detection_threshold:
                return info.language
        except Exception as e:
            print(f"Language detection error: {e}")

        return self.detected_language or self.source_language

    def _transcribe_chunk(self, audio_chunk: np.ndarray):
        """
        Optimized transcription with adaptive settings

        Args:
            audio_chunk: Audio chunk to transcribe
        """
        start_time = time.time()

        try:
            # Optimized transcription options for low latency
            if self.use_optimized:
                options = {
                    "beam_size": 3,
                    "best_of": 1,
                    "patience": 1.0,
                    "length_penalty": 0.8,
                    "temperature": 0.0,
                    "compression_ratio_threshold": 2.4,
                    "log_prob_threshold": -0.5,
                    "no_speech_threshold": 0.3,
                    "condition_on_previous_text": False,
                    "vad_filter": True,
                    "vad_parameters": dict(
                        min_silence_duration_ms=500,
                        threshold=0.5
                    )
                }
            else:
                # Standard quality settings
                options = {
                    "beam_size": 5,
                    "vad_filter": True,
                    "vad_parameters": dict(
                        min_silence_duration_ms=500,
                        threshold=0.5
                    ),
                    "condition_on_previous_text": False
                }

            for language in self.languages:
                segments, info = self.model.transcribe(
                    audio_chunk,
                    language=None if language == "auto" else language,
                    **options
                )

                # Adaptive language detection for auto mode
                if language == "auto" and info.language != self.current_language:
                    self.current_language = info.language
                    print(f"Language switch detected: {info.language}")

                for segment in segments:
                    text = segment.text.strip()
                    if not text:
                        continue

                    result = TranscriptionSegment(
                        text=text,
                        language=info.language if language == "auto" else language,
                        timestamp=time.time(),
                        confidence=segment.avg_logprob,
                        start_time=segment.start,
                        end_time=segment.end
                    )

                    # Add to result queue
                    self.result_queue.put(result)

                    # Call callback if provided
                    if self.callback:
                        self.callback(result)

                    self.metrics["segments_processed"] += 1

            # Record processing latency
            latency = (time.time() - start_time) * 1000
            self.metrics["processing_latency"].append(latency)
            if len(self.metrics["processing_latency"]) > 1000:
                self.metrics["processing_latency"].pop(0)

        except Exception as e:
            print(f"Transcription error: {e}")
            self.metrics["errors"] += 1


# Alias for backward compatibility
OptimizedTranscriptionEngine = MultiLanguageTranscriptionEngine
