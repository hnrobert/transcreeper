# TransCreeper

<div align="center">

![TransCreeper Logo](resources/icon.png)

**A Local High Performance Real-Time Transcription & Translation Subtitle Generator**

[![Build](https://github.com/hnrobert/transcreeper/workflows/Build%20and%20Package/badge.svg)](https://github.com/hnrobert/transcreeper/actions)
[![Release](https://github.com/hnrobert/transcreeper/workflows/Release/badge.svg)](https://github.com/hnrobert/transcreeper/releases)
[![License](https://img.shields.io/github/license/hnrobert/transcreeper)](LICENSE)

[Features](#features) • [Installation](#installation) • [Usage](#usage) • [Development](#development) • [Contributing](#contributing)

</div>

---

## Features

TransCreeper is a powerful desktop application that provides real-time transcription and translation of audio using the state-of-the-art **faster-whisper-large-v3** model.

### Core Features

- 🎤 **Real-Time Transcription**: Ultra-low latency speech-to-text conversion (~200-500ms)
- 🌍 **Multi-Language Support**: Support for 99 languages with adaptive language detection
- 🔄 **Real-Time Translation**: Simultaneous translation to multiple target languages
- 🎨 **Customizable UI**: Fully customizable subtitle display with fonts, colors, and opacity
- 🎧 **Multiple Audio Sources**:
  - System default microphone
  - Multiple microphone inputs
  - System audio output capture
  - Per-application audio capture
- ⚡ **High Performance**:
  - GPU acceleration (CUDA support)
  - Optimized with faster-whisper (CTranslate2)
  - Low-latency optimized transcription engine
  - FP16/INT8 quantization support
  - Adaptive multi-language processing
  - VAD (Voice Activity Detection) for better efficiency
- 🖥️ **Cross-Platform**: Windows, macOS, and Linux support

### User Interface

- **Subtitle Window**: Frameless, transparent window with customizable appearance
- **Settings Window**: Comprehensive configuration interface
- **System Tray**: Background operation support

---

## System Requirements

### Minimum Requirements

- **OS**: Windows 10/11, macOS 10.15+, or Linux (Ubuntu 20.04+)
- **CPU**: Modern multi-core processor (Intel Core i5 or equivalent)
- **RAM**: 8GB
- **Disk**: 5GB free space (for models and application)

### Recommended Requirements

- **GPU**: NVIDIA GPU with CUDA support (RTX 2060 or better)
- **RAM**: 16GB or more
- **Internet**: For initial model download

---

## Installation

### Windows

1. Download the latest release from [Releases](https://github.com/hnrobert/transcreeper/releases)
2. Run `TransCreeper-Windows-vX.X.X.exe`
3. Follow the installation wizard

### macOS

1. Download `TransCreeper-macOS-vX.X.X.dmg` from [Releases](https://github.com/hnrobert/transcreeper/releases)
2. Open the DMG file
3. Drag TransCreeper to your Applications folder
4. First time: Right-click → Open (to bypass Gatekeeper)

### Linux

1. Download `TransCreeper-Linux-vX.X.X.AppImage` from [Releases](https://github.com/hnrobert/transcreeper/releases)
2. Make it executable:

   ```bash
   chmod +x TransCreeper-Linux-vX.X.X.AppImage
   ```

3. Run:

   ```bash
   ./TransCreeper-Linux-vX.X.X.AppImage
   ```

### From Source

```bash
# Clone the repository
git clone https://github.com/hnrobert/transcreeper.git
cd transcreeper

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python src/main.py
```

---

## Usage

### First Launch

1. **Select Audio Input**: Choose your microphone or enable system audio capture
2. **Configure Languages**:
   - Set the speaker's language
   - Add target languages for translation
3. **Customize Appearance**: Adjust colors, fonts, and transparency
4. **Start Transcribing**: The subtitle window will display real-time transcriptions

### Settings

#### General

- **Auto-start**: Launch TransCreeper on system startup
- **Auto-update**: Automatically check for updates
- **Exit on close**: Exit application when subtitle window is closed
- **Hide menu bar icon** (macOS only): Hide the menu bar icon

#### Appearance

- **Window Opacity**: Adjust subtitle window transparency (10-100%)
- **Background Color**: Choose subtitle window background color
- **Text Color**: Choose subtitle text color

#### Input

- **Microphone**: Select default or specific microphones
- **System Audio**: Capture system audio output
- **Application Audio**: Capture audio from specific applications

#### Transcription & Translation

- **Speaker's Language**: The language being spoken
- **Show Transcription**: Display original transcription
- **Target Languages**: Add/remove/reorder translation languages

#### Layout

- **Font Settings**: Configure font family and size per language
- **Display Lines**: Set number of lines to display per language

### Keyboard Shortcuts

- `Cmd/Ctrl + ,`: Open Settings
- `Cmd/Ctrl + Q`: Quit Application
- `Cmd/Ctrl + H`: Hide/Show Subtitle Window

---

## Development

### Project Structure

```text
transcreeper/
├── .github/
│   └── workflows/          # GitHub Actions workflows
│       ├── build.yml       # Build and package
│       └── release.yml     # Release automation
├── config/
│   └── production.yaml     # Production configuration
├── resources/              # Icons and assets
├── src/
│   ├── core/              # Core functionality
│   │   ├── audio_input.py # Audio capture
│   │   └── transcription_engine.py # Transcription engine
│   ├── gui/               # GUI components
│   │   ├── subtitle_window.py # Subtitle display
│   │   └── settings_window.py # Settings dialog
│   ├── utils/             # Utilities
│   │   └── config.py      # Configuration manager
│   └── main.py           # Application entry point
├── requirements.txt      # Python dependencies
├── setup.py             # Setup script
└── README.md           # This file
```

### Building from Source

#### Prerequisites

```bash
pip install pyinstaller
```

#### Building from Source - Windows

```bash
pyinstaller --name="TransCreeper" ^
            --windowed ^
            --onefile ^
            --icon=resources/icon.ico ^
            --add-data="resources;resources" ^
            src/main.py
```

#### Building from Source - macOS

```bash
pyinstaller --name="TransCreeper" \
            --windowed \
            --onefile \
            --icon=resources/icon.icns \
            --add-data="resources:resources" \
            --osx-bundle-identifier=com.transcreeper.app \
            src/main.py
```

#### Building from Source - Linux

```bash
pyinstaller --name="TransCreeper" \
            --windowed \
            --onefile \
            --add-data="resources:resources" \
            src/main.py
```

### Running Tests

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Run with coverage
pytest --cov=src tests/
```

### Code Style

```bash
# Format code
black src/

# Check style
flake8 src/

# Type checking
mypy src/
```

---

## 🔧 Technical Details

### Architecture

TransCreeper is built on several key technologies:

1. **faster-whisper-large-v3**: State-of-the-art speech recognition model

   - Based on OpenAI Whisper large-v3
   - Optimized with CTranslate2 for 4x faster inference
   - FP16 quantization for reduced memory usage

2. **PyQt6**: Modern Qt6 bindings for Python

   - Cross-platform GUI framework
   - Hardware-accelerated rendering
   - Native look and feel on each platform

3. **sounddevice**: Low-latency audio I/O
   - Real-time audio capture
   - Multiple device support
   - Cross-platform audio backend

### Performance Optimization

- **Model Quantization**: FP16/INT8 for reduced memory footprint
- **Batch Processing**: Dynamic batching for throughput optimization
- **VAD Filtering**: Voice Activity Detection to skip silence
- **Streaming Architecture**: Continuous audio processing pipeline
- **GPU Acceleration**: CUDA support for NVIDIA GPUs

### Supported Languages

TransCreeper supports 99 languages including:

Afrikaans, Arabic, Armenian, Azerbaijani, Belarusian, Bosnian, Bulgarian, Catalan, Chinese, Croatian, Czech, Danish, Dutch, English, Estonian, Finnish, French, Galician, German, Greek, Hebrew, Hindi, Hungarian, Icelandic, Indonesian, Italian, Japanese, Kannada, Kazakh, Korean, Latvian, Lithuanian, Macedonian, Malay, Marathi, Maori, Nepali, Norwegian, Persian, Polish, Portuguese, Romanian, Russian, Serbian, Slovak, Slovenian, Spanish, Swahili, Swedish, Tagalog, Tamil, Thai, Turkish, Ukrainian, Urdu, Vietnamese, Welsh, and many more...

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Guidelines

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Development Setup

```bash
# Clone your fork
git clone https://github.com/hnrobert/transcreeper.git
cd transcreeper

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install in development mode
pip install -e ".[dev]"

# Create a branch
git checkout -b feature/my-feature

# Make your changes and commit
git add .
git commit -m "Description of changes"

# Push and create PR
git push origin feature/my-feature
```

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [OpenAI Whisper](https://github.com/openai/whisper) - Original Whisper model
- [faster-whisper](https://github.com/guillaumekln/faster-whisper) - Optimized Whisper implementation
- [CTranslate2](https://github.com/OpenNMT/CTranslate2) - Fast inference engine
- [PyQt](https://www.riverbankcomputing.com/software/pyqt/) - GUI framework

---

## 📧 Contact

- **Issues**: [GitHub Issues](https://github.com/hnrobert/transcreeper/issues)
- **Discussions**: [GitHub Discussions](https://github.com/hnrobert/transcreeper/discussions)

---

## 🗺️ Roadmap

- [ ] Speaker diarization (identify different speakers)
- [ ] Custom vocabulary support
- [ ] Export subtitles to SRT/VTT format
- [ ] Cloud synchronization of settings
- [ ] Mobile companion app
- [ ] WebSocket API for third-party integrations
- [ ] Plugin system for extensibility
- [ ] AI-powered punctuation and formatting
- [ ] Emotion and tone detection
- [ ] Multi-channel audio processing

---

<div align="center">

**Made with ❤️ by the TransCreeper Team**

⭐ Star us on GitHub if you find this project useful!

</div>

A Local High performance Real-Time Transcription & Translation Subtitle Generator
