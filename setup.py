#!/usr/bin/env python3
"""
Setup script for TransCreeper
"""
from pathlib import Path

from setuptools import find_packages, setup

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(
    encoding="utf-8") if readme_file.exists() else ""

setup(
    name="transcreeper",
    version="1.0.0",
    description="A Local High Performance Real-Time Transcription & Translation Subtitle Generator",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="TransCreeper Team",
    author_email="",
    url="https://github.com/hnrobert/transcreeper",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.9",
    install_requires=[
        "faster-whisper>=1.0.0",
        "PyQt6>=6.6.0",
        "PyQt6-WebEngine>=6.6.0",
        "torch>=2.0.0",
        "torchaudio>=2.0.0",
        "numpy>=1.24.0",
        "pydub>=0.25.0",
        "sounddevice>=0.4.6",
        "psutil>=5.9.0",
        "pyyaml>=6.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "transcreeper=main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Multimedia :: Sound/Audio :: Speech",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    keywords="transcription translation subtitle speech-to-text whisper real-time",
    project_urls={
        "Bug Reports": "https://github.com/hnrobert/transcreeper/issues",
        "Source": "https://github.com/hnrobert/transcreeper",
    },
)
