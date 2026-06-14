import json
import locale
import os
from pathlib import Path


SUPPORTED_UI_LANGUAGES = {
    "English": "en_US",
    "中文": "zh_CN",
    "日本語": "ja_JP",
    "한국어": "ko_KR",
}

LOCALE_TO_UI_LANGUAGE = {value: key for key, value in SUPPORTED_UI_LANGUAGES.items()}
ACTIVE_LANGUAGE = None

def load_language_list(language):
    json_path = os.path.join(Path(__file__).resolve().parent, f"locale/{language}.json")

    # json_path = os.path.join(Path(__file__).resolve().parent, f"locale/de_DE.json")  
    # json_path = os.path.join(Path(__file__).resolve().parent, f"locale/en_US.json")
    # json_path = os.path.join(Path(__file__).resolve().parent, f"locale/es_ES.json")                   
    # json_path = os.path.join(Path(__file__).resolve().parent, f"locale/ja_JP.json")
    # json_path = os.path.join(Path(__file__).resolve().parent, f"locale/ko_KR.json")    
    # json_path = os.path.join(Path(__file__).resolve().parent, f"locale/pt_BR.json")    
    # json_path = os.path.join(Path(__file__).resolve().parent, f"locale/zh_CN.json")
    # json_path = os.path.join(Path(__file__).resolve().parent, f"locale/zh_TW.json")    
  

    with open(json_path, "r", encoding="utf-8") as f:
        language_list = json.load(f)
    return language_list


def normalize_language(language):
    if language in SUPPORTED_UI_LANGUAGES:
        return language
    if language in LOCALE_TO_UI_LANGUAGE:
        return LOCALE_TO_UI_LANGUAGE[language]
    return "English"


def to_locale(language):
    normalized = normalize_language(language)
    return SUPPORTED_UI_LANGUAGES[normalized]


def set_active_language(language):
    global ACTIVE_LANGUAGE
    ACTIVE_LANGUAGE = normalize_language(language)


def get_active_language():
    if ACTIVE_LANGUAGE is not None:
        return ACTIVE_LANGUAGE

    system_locale = locale.getdefaultlocale()[0]
    if system_locale in LOCALE_TO_UI_LANGUAGE:
        return LOCALE_TO_UI_LANGUAGE[system_locale]
    return "English"


class I18nAuto:
    def __init__(self, language=None):
        self.language = None
        self.language_map = {}
        self.set_language(language)

    def set_language(self, language=None):
        if language in ["Auto", None]:
            language = get_active_language()
        language = normalize_language(language)
        locale_name = to_locale(language)

        json_path = os.path.join(Path(__file__).resolve().parent, f"locale/{locale_name}.json")
        if not os.path.exists(json_path):
            language = "English"
            locale_name = to_locale(language)

        self.language = locale_name
        self.language_map = load_language_list(locale_name)

    def __call__(self, key):
        active_locale = to_locale(get_active_language())
        if self.language != active_locale:
            self.set_language(get_active_language())
        return self.language_map.get(key, key)

    def __repr__(self):
        return "Use Language: " + self.language
