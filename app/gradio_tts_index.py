import os

import gradio as gr

from app.abus_genuine import *
from app.abus_path import *
from app.abus_tts_index import IndexTTSTTS
from src.config import UserConfig
from src.i18n.i18n import I18nAuto

i18n = I18nAuto()

import structlog

logger = structlog.get_logger()


class GradioIndexTTS:
    def __init__(self, user_config: UserConfig):
        self.user_config = user_config
        self.tts = IndexTTSTTS()

    def gradio_workspace_folder(self):
        cmd_open_explorer(path_workspace_folder())

    def gradio_temp_folder(self):
        cmd_open_explorer(path_gradio_folder())

    def gradio_upload_file(self, file_obj):
        if file_obj is not None:
            text = self._read_file(file_obj.name)
            return text
        return "No file uploaded"

    def gradio_index_default(self):
        return self.tts.default_values()

    def gradio_tts_dubbing_single(
        self,
        dubbing_text: str,
        celeb_audio,
        celeb_transcript,
        emo_audio_prompt,
        enable_emo_audio,
        emo_alpha,
        audio_format: str,
    ):
        if not (dubbing_text and dubbing_text.strip()):
            message = i18n("Input error")
            gr.Warning(message)
            return None, None

        logger.info("[gradio_tts_index.py] gradio_tts_dubbing_single")
        try:
            effective_emo_enabled = self.tts.normalize_emotion_inputs(enable_emo_audio, emo_audio_prompt)
            self.user_config.set("index_tts_enable_emo_audio", effective_emo_enabled)
            self.user_config.set("index_tts_emo_alpha", float(emo_alpha))
            self.user_config.set("audio_format", audio_format)

            dubbing_file = os.path.join(path_dubbing_folder(), path_new_filename(f".{audio_format}"))
            self.tts.infer_single(
                dubbing_text.strip(),
                dubbing_file,
                celeb_audio,
                celeb_transcript,
                emo_audio_prompt,
                effective_emo_enabled,
                emo_alpha,
                audio_format,
            )
            return dubbing_file, dubbing_file
        except Exception as e:
            logger.error(f"[gradio_tts_index.py] gradio_tts_dubbing_single - error: {e}")
            gr.Warning(f"{e}")
            return None, None

    def _read_file(self, filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as file:
                return file.read()
        except UnicodeDecodeError:
            return "Error: The file is not a valid text file or uses an unsupported encoding."
        except IOError:
            return "Error: Unable to read the file."
