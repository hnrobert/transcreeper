"""
Settings window for configuring the application
"""
import platform

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (QCheckBox, QColorDialog, QComboBox, QDialog,
                             QFontComboBox, QFormLayout, QGroupBox,
                             QHBoxLayout, QLabel, QListWidget, QPushButton,
                             QScrollArea, QSlider, QSpinBox, QTabWidget,
                             QVBoxLayout, QWidget)


class SettingsWindow(QDialog):
    """Settings configuration dialog"""

    settings_changed = pyqtSignal()

    def __init__(self, config_manager, audio_manager):
        """
        Initialize settings window

        Args:
            config_manager: Configuration manager instance
            audio_manager: Audio input manager instance
        """
        super().__init__()
        self.config = config_manager
        self.audio_manager = audio_manager
        self.is_macos = platform.system() == "Darwin"

        self._init_ui()
        self._load_settings()

    def _init_ui(self):
        """Initialize user interface"""
        self.setWindowTitle("Settings - TransCreeper")

        width = self.config.get('window.settings_window.width', 600)
        height = self.config.get('window.settings_window.height', 500)
        self.resize(width, height)

        # Main layout
        layout = QVBoxLayout()

        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.addTab(self._create_general_tab(), "General")
        self.tabs.addTab(self._create_appearance_tab(), "Appearance")
        self.tabs.addTab(self._create_input_tab(), "Input")
        self.tabs.addTab(self._create_transcription_tab(),
                         "Transcription && Translation")
        self.tabs.addTab(self._create_layout_tab(), "Layout")

        layout.addWidget(self.tabs)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.apply_btn = QPushButton("Apply")
        self.apply_btn.clicked.connect(self._apply_settings)

        self.ok_btn = QPushButton("OK")
        self.ok_btn.clicked.connect(self._ok_clicked)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)

        button_layout.addWidget(self.apply_btn)
        button_layout.addWidget(self.ok_btn)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def _create_general_tab(self) -> QWidget:
        """Create general settings tab"""
        widget = QWidget()
        layout = QVBoxLayout()

        # Auto start
        self.auto_start_cb = QCheckBox("Start on system startup")
        layout.addWidget(self.auto_start_cb)

        # Auto update
        self.auto_update_cb = QCheckBox("Automatically check for updates")
        layout.addWidget(self.auto_update_cb)

        # Show tray icon
        self.show_tray_cb = QCheckBox("Show system tray icon")
        layout.addWidget(self.show_tray_cb)

        # Hide menubar icon (macOS only)
        if self.is_macos:
            self.hide_menubar_cb = QCheckBox("Hide menu bar icon")
            layout.addWidget(self.hide_menubar_cb)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def _create_appearance_tab(self) -> QWidget:
        """Create appearance settings tab"""
        widget = QWidget()
        layout = QFormLayout()

        # Always on top
        self.always_on_top_cb = QCheckBox("Keep subtitle window always on top")
        layout.addRow("", self.always_on_top_cb)

        # Window opacity
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setMinimum(10)
        self.opacity_slider.setMaximum(100)
        self.opacity_slider.setValue(90)
        self.opacity_label = QLabel("90%")
        self.opacity_slider.valueChanged.connect(
            lambda v: self.opacity_label.setText(f"{v}%")
        )

        opacity_layout = QHBoxLayout()
        opacity_layout.addWidget(self.opacity_slider)
        opacity_layout.addWidget(self.opacity_label)

        layout.addRow("Window Opacity:", opacity_layout)

        # Background color
        self.bg_color_btn = QPushButton("Choose Color")
        self.bg_color_btn.clicked.connect(self._choose_bg_color)
        self.bg_color_preview = QLabel()
        self.bg_color_preview.setFixedSize(50, 30)
        self.bg_color_preview.setStyleSheet("border: 1px solid gray;")

        color_layout = QHBoxLayout()
        color_layout.addWidget(self.bg_color_btn)
        color_layout.addWidget(self.bg_color_preview)
        color_layout.addStretch()

        layout.addRow("Background Color:", color_layout)

        # Text color
        self.text_color_btn = QPushButton("Choose Color")
        self.text_color_btn.clicked.connect(self._choose_text_color)
        self.text_color_preview = QLabel()
        self.text_color_preview.setFixedSize(50, 30)
        self.text_color_preview.setStyleSheet("border: 1px solid gray;")

        text_color_layout = QHBoxLayout()
        text_color_layout.addWidget(self.text_color_btn)
        text_color_layout.addWidget(self.text_color_preview)
        text_color_layout.addStretch()

        layout.addRow("Text Color:", text_color_layout)

        widget.setLayout(layout)
        return widget

    def _create_input_tab(self) -> QWidget:
        """Create input settings tab"""
        widget = QWidget()
        layout = QVBoxLayout()

        # Microphone selection
        mic_group = QGroupBox("Microphone Input")
        mic_layout = QVBoxLayout()

        self.default_mic_cb = QCheckBox("Use system default microphone")
        self.default_mic_cb.stateChanged.connect(self._update_mic_list_state)
        mic_layout.addWidget(self.default_mic_cb)

        mic_layout.addWidget(QLabel("Select specific microphones:"))
        self.mic_list = QListWidget()
        self.mic_list.setSelectionMode(
            QListWidget.SelectionMode.MultiSelection)
        self._populate_microphone_list()
        mic_layout.addWidget(self.mic_list)

        mic_group.setLayout(mic_layout)
        layout.addWidget(mic_group)

        # System audio
        self.system_audio_cb = QCheckBox("Capture system audio output")
        self.system_audio_cb.stateChanged.connect(self._update_app_list_state)
        layout.addWidget(self.system_audio_cb)

        # Application audio
        app_group = QGroupBox("Application Audio")
        app_layout = QVBoxLayout()

        app_layout.addWidget(QLabel("Select applications to capture:"))
        self.app_list = QListWidget()
        self.app_list.setSelectionMode(
            QListWidget.SelectionMode.MultiSelection)
        self.app_list.itemSelectionChanged.connect(
            self._update_system_audio_state)
        app_layout.addWidget(self.app_list)

        self.refresh_apps_btn = QPushButton("Refresh Application List")
        self.refresh_apps_btn.clicked.connect(self._refresh_applications)
        app_layout.addWidget(self.refresh_apps_btn)

        app_group.setLayout(app_layout)
        layout.addWidget(app_group)

        widget.setLayout(layout)
        return widget

    def _create_transcription_tab(self) -> QWidget:
        """Create transcription and translation settings tab"""
        widget = QWidget()
        layout = QFormLayout()

        # Source language
        self.source_lang_combo = QComboBox()
        for code, name in self.config.get_supported_languages():
            self.source_lang_combo.addItem(name, code)
        layout.addRow("Speaker's Language:", self.source_lang_combo)

        # Show transcription
        self.show_transcription_cb = QCheckBox("Show original transcription")
        self.show_transcription_cb.stateChanged.connect(
            self._update_target_languages)
        layout.addRow("", self.show_transcription_cb)

        # Target languages
        lang_group = QGroupBox("Target Languages")
        lang_layout = QVBoxLayout()

        lang_layout.addWidget(
            QLabel("Select languages to display (in order):"))

        # Language selector
        add_lang_layout = QHBoxLayout()
        self.target_lang_combo = QComboBox()
        for code, name in self.config.get_supported_languages():
            if code != 'auto':
                self.target_lang_combo.addItem(name, code)

        self.add_lang_btn = QPushButton("Add Language")
        self.add_lang_btn.clicked.connect(self._add_target_language)

        add_lang_layout.addWidget(self.target_lang_combo)
        add_lang_layout.addWidget(self.add_lang_btn)
        lang_layout.addLayout(add_lang_layout)

        # Selected languages list
        self.target_lang_list = QListWidget()
        lang_layout.addWidget(self.target_lang_list)

        # Move up/down buttons
        list_btn_layout = QHBoxLayout()
        self.move_up_btn = QPushButton("Move Up")
        self.move_up_btn.clicked.connect(self._move_language_up)
        self.move_down_btn = QPushButton("Move Down")
        self.move_down_btn.clicked.connect(self._move_language_down)
        self.remove_lang_btn = QPushButton("Remove")
        self.remove_lang_btn.clicked.connect(self._remove_target_language)

        list_btn_layout.addWidget(self.move_up_btn)
        list_btn_layout.addWidget(self.move_down_btn)
        list_btn_layout.addWidget(self.remove_lang_btn)
        lang_layout.addLayout(list_btn_layout)

        lang_group.setLayout(lang_layout)
        layout.addRow(lang_group)

        widget.setLayout(layout)
        return widget

    def _create_layout_tab(self) -> QWidget:
        """Create layout settings tab"""
        widget = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        content = QWidget()
        layout = QVBoxLayout()

        layout.addWidget(
            QLabel("Configure font and display settings for each language:"))
        layout.addWidget(
            QLabel("(Configure languages in Transcription & Translation tab first)"))

        self.language_settings_container = QVBoxLayout()
        layout.addLayout(self.language_settings_container)

        layout.addStretch()
        content.setLayout(layout)
        scroll.setWidget(content)

        main_layout = QVBoxLayout()
        main_layout.addWidget(scroll)
        widget.setLayout(main_layout)

        return widget

    def _populate_microphone_list(self):
        """Populate microphone device list"""
        self.mic_list.clear()
        devices = self.audio_manager.list_audio_devices()
        for device in devices:
            if device['channels'] > 0:
                self.mic_list.addItem(
                    f"{device['name']} ({device['channels']} ch)")

    def _refresh_applications(self):
        """Refresh application list"""
        # TODO: Implement application audio enumeration
        self.app_list.clear()
        self.app_list.addItem("Chrome")
        self.app_list.addItem("Zoom")
        self.app_list.addItem("Spotify")

    def _update_mic_list_state(self, state):
        """Update microphone list enable state"""
        self.mic_list.setEnabled(not self.default_mic_cb.isChecked())

    def _update_app_list_state(self, state):
        """Update application list enable state"""
        if self.system_audio_cb.isChecked():
            self.app_list.setEnabled(False)
            self.app_list.clearSelection()

    def _update_system_audio_state(self):
        """Update system audio checkbox state"""
        if self.app_list.selectedItems():
            self.system_audio_cb.setEnabled(False)
        else:
            self.system_audio_cb.setEnabled(True)

    def _update_target_languages(self):
        """Update target language combo based on show transcription"""
        source_lang = self.source_lang_combo.currentData()
        show_transcription = self.show_transcription_cb.isChecked()

        # Update combo box items
        self.target_lang_combo.clear()
        for code, name in self.config.get_supported_languages():
            if code == 'auto':
                continue
            if show_transcription and code == source_lang:
                continue
            self.target_lang_combo.addItem(name, code)

    def _add_target_language(self):
        """Add language to target list"""
        lang_code = self.target_lang_combo.currentData()
        lang_name = self.target_lang_combo.currentText()

        # Check if already exists
        for i in range(self.target_lang_list.count()):
            item = self.target_lang_list.item(i)
            if item is not None and item.data(Qt.ItemDataRole.UserRole) == lang_code:
                return

        # Add to list
        from PyQt6.QtWidgets import QListWidgetItem
        item = QListWidgetItem(lang_name)
        item.setData(Qt.ItemDataRole.UserRole, lang_code)
        self.target_lang_list.addItem(item)

        self._update_layout_settings()

    def _remove_target_language(self):
        """Remove selected language from target list"""
        current_row = self.target_lang_list.currentRow()
        if current_row >= 0:
            self.target_lang_list.takeItem(current_row)
            self._update_layout_settings()

    def _move_language_up(self):
        """Move selected language up"""
        current_row = self.target_lang_list.currentRow()
        if current_row > 0:
            item = self.target_lang_list.takeItem(current_row)
            self.target_lang_list.insertItem(current_row - 1, item)
            self.target_lang_list.setCurrentRow(current_row - 1)

    def _move_language_down(self):
        """Move selected language down"""
        current_row = self.target_lang_list.currentRow()
        if 0 <= current_row < self.target_lang_list.count() - 1:
            item = self.target_lang_list.takeItem(current_row)
            self.target_lang_list.insertItem(current_row + 1, item)
            self.target_lang_list.setCurrentRow(current_row + 1)

    def _update_layout_settings(self):
        """Update layout settings panel based on selected languages"""
        # Clear existing settings
        while self.language_settings_container.count():
            child = self.language_settings_container.takeAt(0)
            widget = child.widget() if child is not None else None
            if widget is not None:
                widget.deleteLater()

        # Create settings for each language
        for i in range(self.target_lang_list.count()):
            item = self.target_lang_list.item(i)
            if item is None:
                continue
            lang_code = item.data(Qt.ItemDataRole.UserRole)
            lang_name = item.text()

            group = QGroupBox(lang_name)
            group_layout = QFormLayout()

            # Font family
            font_combo = QFontComboBox()
            group_layout.addRow("Font:", font_combo)

            # Font size
            size_spin = QSpinBox()
            size_spin.setMinimum(8)
            size_spin.setMaximum(72)
            size_spin.setValue(24)
            group_layout.addRow("Size:", size_spin)

            # Number of lines
            lines_spin = QSpinBox()
            lines_spin.setMinimum(1)
            lines_spin.setMaximum(10)
            lines_spin.setValue(2)
            group_layout.addRow("Lines:", lines_spin)

            group.setLayout(group_layout)
            self.language_settings_container.addWidget(group)

    def _choose_bg_color(self):
        """Choose background color"""
        color = QColorDialog.getColor()
        if color.isValid():
            self.bg_color = color
            self.bg_color_preview.setStyleSheet(
                f"background-color: {color.name()}; border: 1px solid gray;"
            )

    def _choose_text_color(self):
        """Choose text color"""
        color = QColorDialog.getColor()
        if color.isValid():
            self.text_color = color
            self.text_color_preview.setStyleSheet(
                f"background-color: {color.name()}; border: 1px solid gray;"
            )

    def _load_settings(self):
        """Load settings from config"""
        # General
        self.auto_start_cb.setChecked(
            self.config.get('general.auto_start', False))
        self.auto_update_cb.setChecked(
            self.config.get('general.auto_update', True))
        self.show_tray_cb.setChecked(
            self.config.get('general.show_tray_icon', True))

        if self.is_macos:
            self.hide_menubar_cb.setChecked(
                self.config.get('general.hide_menubar_icon', False))

        # Appearance
        self.always_on_top_cb.setChecked(
            self.config.get('appearance.always_on_top', True))
        
        opacity = int(self.config.get('appearance.window_opacity', 0.9) * 100)
        self.opacity_slider.setValue(opacity)

        bg_color = QColor(self.config.get(
            'appearance.background_color', '#000000'))
        self.bg_color = bg_color
        self.bg_color_preview.setStyleSheet(
            f"background-color: {bg_color.name()}; border: 1px solid gray;"
        )

        text_color = QColor(self.config.get(
            'appearance.text_color', '#FFFFFF'))
        self.text_color = text_color
        self.text_color_preview.setStyleSheet(
            f"background-color: {text_color.name()}; border: 1px solid gray;"
        )

        # Transcription
        source_lang = self.config.get('transcription.source_language', 'auto')
        index = self.source_lang_combo.findData(source_lang)
        if index >= 0:
            self.source_lang_combo.setCurrentIndex(index)

        self.show_transcription_cb.setChecked(
            self.config.get('transcription.show_transcription', True)
        )

    def _apply_settings(self):
        """Apply settings to config"""
        # General
        self.config.set('general.auto_start', self.auto_start_cb.isChecked())
        self.config.set('general.auto_update', self.auto_update_cb.isChecked())
        self.config.set('general.show_tray_icon', self.show_tray_cb.isChecked())

        if self.is_macos:
            self.config.set('general.hide_menubar_icon',
                            self.hide_menubar_cb.isChecked())

        # Appearance
        self.config.set('appearance.always_on_top',
                        self.always_on_top_cb.isChecked())
        self.config.set('appearance.window_opacity',
                        self.opacity_slider.value() / 100.0)
        self.config.set('appearance.background_color', self.bg_color.name())
        self.config.set('appearance.text_color', self.text_color.name())

        # Transcription
        self.config.set('transcription.source_language',
                        self.source_lang_combo.currentData())
        self.config.set('transcription.show_transcription',
                        self.show_transcription_cb.isChecked())

        # Target languages
        target_languages = []
        for i in range(self.target_lang_list.count()):
            item = self.target_lang_list.item(i)
            if item is not None:
                target_languages.append(item.data(Qt.ItemDataRole.UserRole))
        self.config.set('transcription.target_languages', target_languages)

        # Save config
        self.config.save_config()

        # Emit signal
        self.settings_changed.emit()

    def _ok_clicked(self):
        """OK button clicked"""
        self._apply_settings()
        self.accept()

    def closeEvent(self, a0):
        """Handle close event - just hide the window"""
        self.hide()
        if a0 is not None:
            a0.ignore()
