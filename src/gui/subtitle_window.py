"""
Subtitle window - The main display window for real-time subtitles
"""
import platform
from typing import List, Optional

from PyQt6.QtCore import QPoint, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QMouseEvent
from PyQt6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QPushButton,
                             QVBoxLayout, QWidget)


class SubtitleWindow(QWidget):
    """Main subtitle display window with frameless design"""

    settings_requested = pyqtSignal()

    def __init__(self, config_manager):
        """
        Initialize subtitle window

        Args:
            config_manager: Configuration manager instance
        """
        super().__init__()
        self.config = config_manager
        self.is_macos = platform.system() == "Darwin"

        # Window drag support
        self.drag_position = QPoint()

        # Subtitle labels
        self.subtitle_labels = {}

        self._init_ui()
        self._apply_config()

    def _init_ui(self):
        """Initialize user interface"""
        # Window flags based on platform and settings
        always_on_top = self.config.get('appearance.always_on_top', True)

        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool
        if always_on_top:
            flags |= Qt.WindowType.WindowStaysOnTopHint

        self.setWindowFlags(flags)

        # Enable transparency
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Control bar - only show on non-macOS or when explicitly needed
        if not self.is_macos:
            control_bar = self._create_control_bar()
            main_layout.addWidget(control_bar)

        # Subtitle area
        self.subtitle_container = QWidget()
        self.subtitle_layout = QVBoxLayout(self.subtitle_container)
        self.subtitle_layout.setContentsMargins(10, 10, 10, 10)
        self.subtitle_layout.setSpacing(5)
        main_layout.addWidget(self.subtitle_container)

        self.setLayout(main_layout)

        # Set default size and position
        width = self.config.get('window.subtitle_window.width', 800)
        height = self.config.get('window.subtitle_window.height', 100)
        self.resize(width, height)

        x = self.config.get('window.subtitle_window.x')
        y = self.config.get('window.subtitle_window.y')

        if x is None or y is None:
            # Center on screen
            primary_screen = QApplication.primaryScreen()
            if primary_screen is not None:
                screen_geom = primary_screen.geometry()
                x = (screen_geom.width() - width) // 2
                y = screen_geom.height() - height - 100
            else:
                # Fallback to (0,0) if no screen is available
                x, y = 0, 0

        self.move(x, y)

    def _create_control_bar(self) -> QWidget:
        """Create control bar with buttons (Windows/Linux only)"""
        control_bar = QWidget()
        control_bar.setFixedHeight(30)

        layout = QHBoxLayout(control_bar)
        layout.setContentsMargins(5, 0, 5, 0)
        layout.setSpacing(5)

        # Settings button
        self.settings_btn = QPushButton("⚙ Settings")
        self.settings_btn.clicked.connect(self.settings_requested.emit)
        layout.addWidget(self.settings_btn)

        layout.addStretch()

        # Minimize button
        self.minimize_btn = QPushButton("−")
        self.minimize_btn.setFixedWidth(30)
        self.minimize_btn.clicked.connect(self.showMinimized)
        layout.addWidget(self.minimize_btn)

        # Hide button (instead of close)
        self.hide_btn = QPushButton("×")
        self.hide_btn.setFixedWidth(30)
        self.hide_btn.clicked.connect(self.hide)
        layout.addWidget(self.hide_btn)

        control_bar.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 0, 0, 0.3);
            }
            QPushButton {
                background-color: rgba(255, 255, 255, 0.2);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 3px;
                color: white;
                padding: 3px 8px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.3);
            }
        """)

        return control_bar

    def _apply_config(self):
        """Apply configuration to window appearance"""
        # Background color and opacity
        bg_color = self.config.get('appearance.background_color', '#000000')
        opacity = self.config.get('appearance.window_opacity', 0.9)

        color = QColor(bg_color)
        color.setAlphaF(opacity)

        self.subtitle_container.setStyleSheet(f"""
            QWidget {{
                background-color: {color.name(QColor.NameFormat.HexArgb)};
                border-radius: 10px;
            }}
        """)

        self.setWindowOpacity(1.0)  # Window itself is fully opaque

    def setup_subtitle_labels(self, languages: List[str]):
        """
        Setup subtitle labels for each language

        Args:
            languages: List of language codes to display
        """
        # Clear existing labels
        for label in self.subtitle_labels.values():
            self.subtitle_layout.removeWidget(label)
            label.deleteLater()
        self.subtitle_labels.clear()

        # Create new labels
        text_color = self.config.get('appearance.text_color', '#FFFFFF')

        for lang in languages:
            # Get language-specific settings
            font_family = self.config.get(f'layout.language_fonts.{lang}.family',
                                          self.config.get('appearance.font_family', 'Arial'))
            font_size = self.config.get(f'layout.language_fonts.{lang}.size',
                                        self.config.get('appearance.font_size', 24))
            num_lines = self.config.get(f'layout.language_lines.{lang}', 2)

            label = QLabel()
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setWordWrap(True)
            label.setFont(QFont(font_family, font_size))
            label.setStyleSheet(f"""
                QLabel {{
                    color: {text_color};
                    padding: 5px;
                }}
            """)
            label.setMinimumHeight(font_size * num_lines + 20)

            self.subtitle_labels[lang] = label
            self.subtitle_layout.addWidget(label)

    def update_subtitle(self, language: str, text: str):
        """
        Update subtitle text for a specific language

        Args:
            language: Language code
            text: Subtitle text
        """
        if language in self.subtitle_labels:
            self.subtitle_labels[language].setText(text)

    def clear_subtitle(self, language: Optional[str] = None):
        """
        Clear subtitle text

        Args:
            language: Language code (None to clear all)
        """
        if language is None:
            for label in self.subtitle_labels.values():
                label.setText("")
        elif language in self.subtitle_labels:
            self.subtitle_labels[language].setText("")

    # Window dragging support
    def mousePressEvent(self, a0: Optional[QMouseEvent]):
        """Handle mouse press for window dragging"""
        if a0 is not None and a0.button() == Qt.MouseButton.LeftButton:
            self.drag_position = a0.globalPosition().toPoint() - \
                self.frameGeometry().topLeft()
            a0.accept()

    def mouseMoveEvent(self, a0: Optional[QMouseEvent]):
        """Handle mouse move for window dragging"""
        if a0 is not None and a0.buttons() == Qt.MouseButton.LeftButton:
            self.move(a0.globalPosition().toPoint() - self.drag_position)
            a0.accept()

    def closeEvent(self, a0):
        """Handle window close event"""
        # Save window position
        self.config.set('window.subtitle_window.x', self.x())
        self.config.set('window.subtitle_window.y', self.y())
        self.config.set('window.subtitle_window.width', self.width())
        self.config.set('window.subtitle_window.height', self.height())
        self.config.save_config()

        # Always just hide the window, don't exit
        # Exit is controlled by the system tray
        self.hide()

        if a0 is not None:
            a0.ignore()  # Ignore the close event to prevent actual closing
