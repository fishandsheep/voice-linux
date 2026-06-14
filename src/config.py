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
            "asr_engine": "whisper-timestamped",
            "gradio_language": "English",
            "whisper_model": "large",
            "faster_whisper_model": "large",
            "whisper_timestamped_model": "large",
            "whisperX_model": "large",            
            "whisper_language": "korean",
            "word_timestamps": True,
            "denoise": False,
            "burn_subtitles": False,
            "video_quality": "best",
            "audio_format": "flac",
            "translate_source_language": "English",
            "translate_target_language": "korean",
            "denoise_level" : 0,
            "whisper_compute_type" : 'default',
            "whisper_highlight_words" : False,
            "last_folder" : ".",     
            "ms_language": "English",
            "ms_voice": "UNITED STATES-Ana-Female",
            "azure_tts_pitch": 0,
            "azure_tts_rate": 0,
            "azure_tts_volume": 0,
            "edge_tts_pitch": 0,
            "edge_tts_rate": 0,
            "edge_tts_volume": 0,            
            "dots_model": "rednote-hilab/dots.tts-mf",
            "dots_language": "Auto Detect",
            "dots_num_steps": 4,
            "dots_guidance_scale": 1.2,
            "dots_seed": 42,
            "dots_normalize_text": False,
            "f5_single_language": "English",
            "f5_multi_language1": "English",
            "f5_multi_language2": "English",            
            "cosy_voice_language": "English",
            "kokoro_language": "American English",
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
        value = self.user_config.get(key, default)
        if value != None:
            return value
        else:
            return self.default_user_config.get(key, key)

    def set(self, key, value):
        self.user_config[key] = value
        self.save_user_config()
