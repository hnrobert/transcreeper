"""
Main application entry point
"""
import platform
import sys
from pathlib import Path

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from core.audio_input import AudioInputManager
from core.transcription_engine import (
    MultiLanguageTranscriptionEngine,
    TranscriptionSegment,
)
from gui.settings_window import SettingsWindow
from gui.subtitle_window import SubtitleWindow
from utils.config import ConfigManager

# Add src directory to path
src_path = Path(__file__).parent
sys.path.insert(0, str(src_path))


class TransCreeperApp:
    """Main application class"""

    def __init__(self):
        """Initialize application"""
        self.app = QApplication(sys.argv)
        # Keep the application running even if all windows are closed
        # this is important for macOS where the menu bar/tray icon should keep the app alive
        try:
            # PyQt6: use setQuitOnLastWindowClosed
            self.app.setQuitOnLastWindowClosed(False)
        except Exception:
            pass
        self.app.setApplicationName("TransCreeper")
        self.app.setOrganizationName("TransCreeper")

        # Configuration
        self.config = ConfigManager()

        # Audio input manager
        self.audio_manager = AudioInputManager(
            sample_rate=16000,
            channels=1,
            callback=self._audio_callback
        )

        # Transcription engine
        self.transcription_engine = None
        self._setup_transcription_engine()

        # GUI windows
        self.subtitle_window = SubtitleWindow(self.config)
        self.subtitle_window.settings_requested.connect(self._show_settings)

        self.settings_window = SettingsWindow(self.config, self.audio_manager)
        self.settings_window.settings_changed.connect(self._apply_settings)

        # System tray
        self._setup_system_tray()

        # Subtitle buffer for each language (initialize before setup)
        self.subtitle_buffers = {}

        # Setup subtitle labels based on config
        self._setup_subtitle_labels()

        # Start transcription engine
        if self.transcription_engine:
            self.transcription_engine.start()

        # Start audio recording
        self._start_audio_capture()

        # Result polling timer
        self.result_timer = QTimer()
        self.result_timer.timeout.connect(self._process_transcription_results)
        self.result_timer.start(100)  # Check every 100ms

        # Show subtitle window
        self.subtitle_window.show()

    def _setup_transcription_engine(self):
        """Setup transcription engine"""
        try:
            source_lang = self.config.get(
                'transcription.source_language', 'auto')
            target_langs = self.config.get(
                'transcription.target_languages', [])
            show_transcription = self.config.get(
                'transcription.show_transcription', True)

            # Build languages list
            languages = []
            if show_transcription and source_lang != 'auto':
                languages.append(source_lang)
            languages.extend(target_langs)

            # Determine device and compute type
            device = self.config.get('transcription.device', 'auto')
            if device == 'auto':
                import torch
                device = 'cuda' if torch.cuda.is_available() else 'cpu'

            compute_type = self.config.get(
                'transcription.compute_type', 'float16')
            if device == 'cpu':
                compute_type = 'int8'

            model_size = self.config.get(
                'transcription.model_size', 'large-v3')

            # Check if optimized mode is enabled
            use_optimized = self.config.get(
                'transcription.use_optimized', True)

            # Get model cache directory
            model_cache_dir = str(self.config.get_model_cache_dir())

            # Use unified optimized engine
            self.transcription_engine = MultiLanguageTranscriptionEngine(
                source_language=source_lang,
                target_languages=target_langs,
                model_size=model_size,
                device=device,
                compute_type=compute_type,
                use_optimized=use_optimized,
                callback=self._transcription_callback,
                download_root=model_cache_dir
            )

            mode = "Optimized" if use_optimized else "Standard"
            print(
                f"Transcription engine initialized: {mode} {model_size} on {device}")
            print(f"Models cached in: {model_cache_dir}")

        except Exception as e:
            print(f"Error initializing transcription engine: {e}")
            self.transcription_engine = None

    def _setup_system_tray(self):
        """Setup system tray icon"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            print("System tray not available")
            return

        self.tray_icon = QSystemTrayIcon(self.app)

        # Try to load icon. Prefer a rasterized pixmap so the menubar
        # on macOS renders it correctly. We support SVG and PNG.
        icon_path_svg = Path(__file__).parent.parent / 'resources' / 'icon.svg'
        icon_path_png = Path(__file__).parent.parent / 'resources' / 'icon.png'
        loaded_icon = None

        if icon_path_png.exists():
            loaded_icon = QIcon(str(icon_path_png))
        elif icon_path_svg.exists():
            # Create a QIcon from SVG and rasterize to a pixmap to improve
            # compatibility on macOS.
            raw_icon = QIcon(str(icon_path_svg))
            pix = raw_icon.pixmap(64, 64)
            if not pix.isNull():
                loaded_icon = QIcon(pix)
            else:
                loaded_icon = raw_icon
        else:
            print(f"Icon not found at {icon_path_svg} or {icon_path_png}")

        if loaded_icon is not None:
            self.tray_icon.setIcon(loaded_icon)

        # Create menu
        tray_menu = QMenu()

        # Show window action
        show_action = QAction("Show Subtitle Window", self.app)
        show_action.triggered.connect(self._show_subtitle_window)
        tray_menu.addAction(show_action)

        tray_menu.addSeparator()

        # Settings action
        settings_action = QAction("Settings", self.app)
        settings_action.triggered.connect(self._show_settings)
        tray_menu.addAction(settings_action)

        tray_menu.addSeparator()

        # Quit action
        quit_action = QAction("Quit", self.app)
        quit_action.triggered.connect(self._quit_app)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._tray_activated)

        # Show tray icon based on settings
        show_tray = self.config.get('general.show_tray_icon', True)
        if show_tray and not (platform.system() == "Darwin" and
                              self.config.get('general.hide_menubar_icon', False)):
            self.tray_icon.show()

    def _show_subtitle_window(self):
        """Show and activate subtitle window"""
        self.subtitle_window.show()
        self.subtitle_window.raise_()
        self.subtitle_window.activateWindow()

    def _tray_activated(self, reason):
        """System tray icon activated"""
        # Left click - show subtitle window
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._show_subtitle_window()
        # Right click shows menu automatically

    def _setup_subtitle_labels(self):
        """Setup subtitle labels based on configuration"""
        source_lang = self.config.get('transcription.source_language', 'auto')
        target_langs = self.config.get('transcription.target_languages', [])
        show_transcription = self.config.get(
            'transcription.show_transcription', True)

        languages = []
        if show_transcription and source_lang != 'auto':
            languages.append(source_lang)
        languages.extend(target_langs)

        # Remove duplicates but preserve order. The subtitle window currently
        # creates one label per unique language code.
        seen = set()
        unique_languages = []
        for l in languages:
            if l not in seen:
                seen.add(l)
                unique_languages.append(l)

        self.subtitle_window.setup_subtitle_labels(unique_languages)

        # Initialize buffers
        for lang in languages:
            self.subtitle_buffers[lang] = []

    def _audio_callback(self, audio_data, sample_rate):
        """Audio data callback"""
        if self.transcription_engine:
            self.transcription_engine.add_audio_data(audio_data, sample_rate)

    def _transcription_callback(self, segment: TranscriptionSegment):
        """Transcription result callback"""
        # This is called from transcription thread
        # Results are also in the queue, so we handle them in _process_transcription_results
        pass

    def _process_transcription_results(self):
        """Process transcription results from queue"""
        if not self.transcription_engine:
            return

        while True:
            result = self.transcription_engine.get_result(timeout=0.01)
            if result is None:
                break

            # Update subtitle
            language = result.language
            text = result.text

            if language in self.subtitle_buffers:
                # Add to buffer
                self.subtitle_buffers[language].append(text)

                # Keep last N segments
                max_segments = self.config.get(
                    f'layout.language_lines.{language}', 2)
                if len(self.subtitle_buffers[language]) > max_segments:
                    self.subtitle_buffers[language].pop(0)

                # Update display
                display_text = '\n'.join(self.subtitle_buffers[language])
                self.subtitle_window.update_subtitle(language, display_text)

    def _start_audio_capture(self):
        """Start audio capture based on configuration"""
        # Get selected microphone
        use_default = self.config.get('input.microphone_device') is None

        if use_default:
            device_index = None
        else:
            # TODO: Map device name to index
            device_index = None

        self.audio_manager.start_recording(device_index)

    def _show_settings(self):
        """Show settings window"""
        self.settings_window.show()
        self.settings_window.raise_()
        self.settings_window.activateWindow()

    def _apply_settings(self):
        """Apply changed settings"""
        # Restart transcription engine
        if self.transcription_engine:
            self.transcription_engine.stop()

        self._setup_transcription_engine()

        if self.transcription_engine:
            self.transcription_engine.start()

        # Update subtitle labels
        self._setup_subtitle_labels()

        # Restart audio capture
        self.audio_manager.stop_recording()
        self._start_audio_capture()

        # Update subtitle window appearance
        self.subtitle_window._apply_config()

        # Update always on top setting
        always_on_top = self.config.get('appearance.always_on_top', True)
        flags = self.subtitle_window.windowFlags()
        if always_on_top:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        else:
            flags &= ~Qt.WindowType.WindowStaysOnTopHint
        self.subtitle_window.setWindowFlags(flags)
        self.subtitle_window.show()  # Need to show after changing flags

        # Update tray icon visibility
        show_tray = self.config.get('general.show_tray_icon', True)
        if show_tray:
            self.tray_icon.show()
        else:
            self.tray_icon.hide()

    def _quit_app(self):
        """Quit application"""
        # Stop audio recording
        self.audio_manager.stop_recording()

        # Stop transcription engine
        if self.transcription_engine:
            self.transcription_engine.stop()

        # Quit application
        self.app.quit()

    def run(self):
        """Run application"""
        return self.app.exec()


def main():
    """Main entry point"""
    app = TransCreeperApp()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
