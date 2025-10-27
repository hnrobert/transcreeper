"""
Configuration manager for application settings
"""
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


class ConfigManager:
    """Manages application configuration"""

    DEFAULT_CONFIG = {
        'general': {
            'auto_start': False,
            'auto_update': True,
            'exit_on_close': False,
            'show_tray_icon': True,
            'hide_menubar_icon': False  # macOS only
        },
        'appearance': {
            'window_opacity': 0.9,
            'background_color': '#000000',
            'text_color': '#FFFFFF',
            'font_family': 'Arial',
            'font_size': 24,
            'always_on_top': True
        },
        'input': {
            'microphone_device': None,  # None means default
            'selected_microphones': [],
            'system_audio_enabled': False,
            'selected_applications': []
        },
        'transcription': {
            # Default to Chinese source for bilingual default (user-requested)
            'source_language': 'zh',
            'show_transcription': True,
            # By default show Chinese transcription and subtitle outputs
            # for Chinese and English (bilingual). Note: the subtitle
            # window currently creates one label per unique language code.
            'target_languages': ['zh', 'en'],  # List of language codes
            'model_size': 'large-v3',
            'device': 'auto',  # auto, cuda, cpu
            'compute_type': 'float16',
            'use_optimized': True
        },
        'layout': {
            'languages_display_order': [],
            'language_fonts': {},  # {language: {family, size}}
            'language_lines': {}  # {language: num_lines}
        },
        'window': {
            'subtitle_window': {
                'width': 800,
                'height': 100,
                'x': None,  # None means center
                'y': None
            },
            'settings_window': {
                'width': 600,
                'height': 500
            }
        }
    }

    # Supported languages by faster-whisper-large-v3
    SUPPORTED_LANGUAGES = [
        ('auto', 'Auto Detect'),
        ('af', 'Afrikaans'),
        ('am', 'Amharic'),
        ('ar', 'Arabic'),
        ('as', 'Assamese'),
        ('az', 'Azerbaijani'),
        ('ba', 'Bashkir'),
        ('be', 'Belarusian'),
        ('bg', 'Bulgarian'),
        ('bn', 'Bengali'),
        ('bo', 'Tibetan'),
        ('br', 'Breton'),
        ('bs', 'Bosnian'),
        ('ca', 'Catalan'),
        ('cs', 'Czech'),
        ('cy', 'Welsh'),
        ('da', 'Danish'),
        ('de', 'German'),
        ('el', 'Greek'),
        ('en', 'English'),
        ('es', 'Spanish'),
        ('et', 'Estonian'),
        ('eu', 'Basque'),
        ('fa', 'Persian'),
        ('fi', 'Finnish'),
        ('fo', 'Faroese'),
        ('fr', 'French'),
        ('gl', 'Galician'),
        ('gu', 'Gujarati'),
        ('ha', 'Hausa'),
        ('haw', 'Hawaiian'),
        ('he', 'Hebrew'),
        ('hi', 'Hindi'),
        ('hr', 'Croatian'),
        ('ht', 'Haitian Creole'),
        ('hu', 'Hungarian'),
        ('hy', 'Armenian'),
        ('id', 'Indonesian'),
        ('is', 'Icelandic'),
        ('it', 'Italian'),
        ('ja', 'Japanese'),
        ('jw', 'Javanese'),
        ('ka', 'Georgian'),
        ('kk', 'Kazakh'),
        ('km', 'Khmer'),
        ('kn', 'Kannada'),
        ('ko', 'Korean'),
        ('la', 'Latin'),
        ('lb', 'Luxembourgish'),
        ('ln', 'Lingala'),
        ('lo', 'Lao'),
        ('lt', 'Lithuanian'),
        ('lv', 'Latvian'),
        ('mg', 'Malagasy'),
        ('mi', 'Maori'),
        ('mk', 'Macedonian'),
        ('ml', 'Malayalam'),
        ('mn', 'Mongolian'),
        ('mr', 'Marathi'),
        ('ms', 'Malay'),
        ('mt', 'Maltese'),
        ('my', 'Myanmar'),
        ('ne', 'Nepali'),
        ('nl', 'Dutch'),
        ('nn', 'Norwegian Nynorsk'),
        ('no', 'Norwegian'),
        ('oc', 'Occitan'),
        ('pa', 'Punjabi'),
        ('pl', 'Polish'),
        ('ps', 'Pashto'),
        ('pt', 'Portuguese'),
        ('ro', 'Romanian'),
        ('ru', 'Russian'),
        ('sa', 'Sanskrit'),
        ('sd', 'Sindhi'),
        ('si', 'Sinhala'),
        ('sk', 'Slovak'),
        ('sl', 'Slovenian'),
        ('sn', 'Shona'),
        ('so', 'Somali'),
        ('sq', 'Albanian'),
        ('sr', 'Serbian'),
        ('su', 'Sundanese'),
        ('sv', 'Swedish'),
        ('sw', 'Swahili'),
        ('ta', 'Tamil'),
        ('te', 'Telugu'),
        ('tg', 'Tajik'),
        ('th', 'Thai'),
        ('tk', 'Turkmen'),
        ('tl', 'Tagalog'),
        ('tr', 'Turkish'),
        ('tt', 'Tatar'),
        ('uk', 'Ukrainian'),
        ('ur', 'Urdu'),
        ('uz', 'Uzbek'),
        ('vi', 'Vietnamese'),
        ('yi', 'Yiddish'),
        ('yo', 'Yoruba'),
        ('zh', 'Chinese'),
    ]

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager

        Args:
            config_path: Path to configuration file
        """
        if config_path is None:
            # Default config directory
            self.config_dir = Path.home() / '.transcreeper'
            self.config_dir.mkdir(exist_ok=True)
            config_path = str(self.config_dir / 'config.yaml')
        else:
            self.config_dir = Path(config_path).parent
            self.config_dir.mkdir(exist_ok=True)

        self.config_path = Path(config_path)
        self.config = self._load_config()

    def get_config_dir(self) -> Path:
        """Get configuration directory path"""
        return self.config_dir

    def get_model_cache_dir(self) -> Path:
        """Get model cache directory path"""
        model_dir = self.config_dir / 'models'
        model_dir.mkdir(exist_ok=True)
        return model_dir

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded_config = yaml.safe_load(f)
                # Merge with default config
                return self._merge_configs(self.DEFAULT_CONFIG.copy(), loaded_config)
            except Exception as e:
                print(f"Error loading config: {e}, using defaults")
                return self.DEFAULT_CONFIG.copy()
        else:
            return self.DEFAULT_CONFIG.copy()

    def _merge_configs(self, default: Dict, loaded: Dict) -> Dict:
        """Recursively merge loaded config with default config"""
        for key, value in loaded.items():
            if key in default:
                if isinstance(value, dict) and isinstance(default[key], dict):
                    default[key] = self._merge_configs(default[key], value)
                else:
                    default[key] = value
        return default

    def save_config(self):
        """Save configuration to file"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False,
                          allow_unicode=True)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value by key path

        Args:
            key_path: Dot-separated key path (e.g., 'general.auto_start')
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key_path.split('.')
        value = self.config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def set(self, key_path: str, value: Any):
        """
        Set configuration value by key path

        Args:
            key_path: Dot-separated key path (e.g., 'general.auto_start')
            value: Value to set
        """
        keys = key_path.split('.')
        config = self.config

        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]

        config[keys[-1]] = value

    def get_supported_languages(self) -> List[tuple]:
        """Get list of supported languages"""
        return self.SUPPORTED_LANGUAGES.copy()

    def get_language_name(self, code: str) -> str:
        """
        Get language name from code

        Args:
            code: Language code

        Returns:
            Language name
        """
        for lang_code, lang_name in self.SUPPORTED_LANGUAGES:
            if lang_code == code:
                return lang_name
        return code
