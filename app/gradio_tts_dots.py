import os

import gradio as gr

from app.abus_genuine import *
from app.abus_path import *
from app.abus_tts_dots import DotsTTS
from src.config import UserConfig

from src.i18n.i18n import I18nAuto

i18n = I18nAuto()

import structlog

logger = structlog.get_logger()


class GradioDotsTTS:
    def __init__(self, user_config: UserConfig):
        self.user_config = user_config
        self.tts = DotsTTS()

    def gradio_workspace_folder(self):
        cmd_open_explorer(path_workspace_folder())

    def gradio_temp_folder(self):
        cmd_open_explorer(path_gradio_folder())

    def gradio_upload_file(self, file_obj):
        if file_obj is not None:
            text = self._read_file(file_obj.name)
            return text
        return "No file uploaded"

    def gradio_available_models(self):
        return self.tts.available_models()

    def gradio_language_tags(self):
        return self.tts.available_language_tags()

    def gradio_recommended_steps(self, model_choice):
        return self.tts.recommended_num_steps(model_choice)

    def gradio_dots_default(self):
        return [
            "rednote-hilab/dots.tts-mf",
            "Auto Detect",
            4,
            1.2,
            42,
            False,
            "mp3",
        ]

    def gradio_tts_dubbing_single(
        self,
        dubbing_text: str,
        celeb_audio,
        celeb_transcript,
        model_choice,
        language_tag,
        num_steps,
        guidance_scale,
        seed,
        normalize_text,
        audio_format: str,
    ):
        if not (dubbing_text and dubbing_text.strip()):
            message = i18n("Input error")
            gr.Warning(message)
            return None, None

        logger.info("[gradio_tts_dots.py] gradio_tts_dubbing_single - model=%s", model_choice)
        try:
            dubbing_file = os.path.join(path_dubbing_folder(), path_new_filename(f".{audio_format}"))
            self.tts.infer_single(
                dubbing_text.strip(),
                dubbing_file,
                celeb_audio,
                celeb_transcript,
                model_choice,
                language_tag,
                num_steps,
                guidance_scale,
                seed,
                normalize_text,
                audio_format,
            )
            return dubbing_file, dubbing_file
        except Exception as e:
            logger.error(f"[gradio_tts_dots.py] gradio_tts_dubbing_single - error: {e}")
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
