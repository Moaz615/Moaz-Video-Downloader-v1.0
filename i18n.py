import json
from pathlib import Path
import os
import sys

# Determine the correct path to the languages directory
# This handles both running from an IDE and as a PyInstaller bundle
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    # Running in a PyInstaller bundle
    LANGUAGES_DIR = Path(sys._MEIPASS) / 'languages'
else:
    # Running in a normal Python environment
    LANGUAGES_DIR = Path(__file__).parent / 'languages'

LANGUAGES = {}

def load_languages():
    """Loads all language JSON files from the 'languages' directory."""
    if not LANGUAGES_DIR.is_dir():
        print(f"Error: Languages directory not found at {LANGUAGES_DIR}")
        return

    for lang_file in LANGUAGES_DIR.glob('*.json'):
        try:
            lang_code = lang_file.stem
            with open(lang_file, 'r', encoding='utf-8') as f:
                LANGUAGES[lang_code] = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading language file {lang_file}: {e}")

# Load languages on module import
load_languages()

DEFAULT_LANG = 'en'

def get_translator(language_code: str):
    """
    Returns a function that translates a key into the given language.
    Falls back to English if the key or language is not found.
    """
    # Ensure the requested language is loaded, otherwise use default
    lang_data = LANGUAGES.get(language_code, LANGUAGES.get(DEFAULT_LANG, {}))
    
    def t(key: str) -> str:
        # Get translation, falling back to English if not found in the current language
        translation = lang_data.get(key)
        if translation is None and language_code != DEFAULT_LANG:
            # Fallback to default language
            default_lang_data = LANGUAGES.get(DEFAULT_LANG, {})
            translation = default_lang_data.get(key, key) # Fallback to key itself if not in default
        elif translation is None:
            # If still not found (even in default), just return the key
            translation = key
        return translation
        
    return t 