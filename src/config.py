from enum import Enum
import urllib

import os
from typing import List
from urllib.parse import urlparse
import json5
import torch

from tqdm import tqdm

import structlog
logger = structlog.get_logger()

class UserConfig:
    def __init__(self, user_config_path):
        self.user_config_path = user_config_path
        self.default_user_config = {
            "gradio_language": "English",
            "whisper_timestamped_model": "large-v3-turbo",
            "whisper_language": "korean",
            "video_quality": "best",
            "upload_audio_format": "wav",
            "tts_audio_format": "mp3",
            "translate_source_language": "English",
            "translate_target_language": "korean",
            "denoise_level" : 0,
            "last_folder" : ".",     
            "voxcpm_mode": "Voice Clone",
            "voxcpm_cfg_value": 2.0,
            "voxcpm_inference_timesteps": 10,
            "voxcpm_normalize_text": False,
            "voxcpm_denoise_reference": False,
            "index_tts_emo_alpha": 1.0,
            "index_tts_enable_emo_audio": False,
        }
        self.user_config = self.load_user_config()


    def load_user_config(self):
        try:
            with open(self.user_config_path, "r", encoding='utf-8') as file:
                return json5.load(file)
        except Exception as e:
            logger.error(f"[config.py] load_user_config - Error transcribing file: {e}")
            return self.default_user_config

    def save_user_config(self):
        with open(self.user_config_path, "w", encoding='utf-8') as file:
            json5.dump(self.user_config, file, indent=4)

    def get(self, key, default=None):
        if key == "upload_audio_format":
            legacy = self.user_config.get("audio_format")
            value = self.user_config.get(key, legacy if legacy is not None else default)
            if value not in {"wav", "mp3"}:
                value = self.default_user_config["upload_audio_format"]
            return value

        if key == "tts_audio_format":
            legacy = self.user_config.get("audio_format")
            value = self.user_config.get(key, legacy if legacy is not None else default)
            if value not in {"wav", "flac", "mp3"}:
                value = self.default_user_config["tts_audio_format"]
            return value

        if key == "whisper_timestamped_model":
            value = self.user_config.get(key, default)
            if value not in {"large", "large-v3-turbo", "turbo"}:
                return self.default_user_config["whisper_timestamped_model"]
            return value

        value = self.user_config.get(key, default)
        if value != None:
            return value
        else:
            return self.default_user_config.get(key, key)

    def set(self, key, value):
        self.user_config[key] = value
        self.save_user_config()
