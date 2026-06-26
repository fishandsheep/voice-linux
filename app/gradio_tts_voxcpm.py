import os

import gradio as gr

from app.abus_genuine import *
from app.abus_path import *
from app.abus_tts_voxcpm import VoxCPMTTS
from src.config import UserConfig
from src.i18n.i18n import I18nAuto

i18n = I18nAuto()

import structlog

logger = structlog.get_logger()


class GradioVoxCPM:
    def __init__(self, user_config: UserConfig):
        self.user_config = user_config
        self.tts = VoxCPMTTS()

    def gradio_workspace_folder(self):
        cmd_open_explorer(path_workspace_folder())

    def gradio_temp_folder(self):
        cmd_open_explorer(path_gradio_folder())

    def gradio_upload_file(self, file_obj):
        if file_obj is not None:
            text = self._read_file(file_obj.name)
            return text
        return "No file uploaded"

    def gradio_modes(self):
        return self.tts.available_modes()

    def gradio_voxcpm_default(self):
        return self.tts.default_values()

    def gradio_tts_dubbing_single(
        self,
        dubbing_text: str,
        celeb_audio,
        celeb_transcript,
        mode,
        voice_description,
        cfg_value,
        inference_timesteps,
        normalize_text,
        denoise_reference,
        audio_format: str,
    ):
        if not (dubbing_text and dubbing_text.strip()):
            message = i18n("Input error")
            gr.Warning(message)
            return None, None

        logger.info("[gradio_tts_voxcpm.py] gradio_tts_dubbing_single - mode=%s", mode)
        try:
            self.user_config.set("voxcpm_mode", mode)
            self.user_config.set("voxcpm_cfg_value", float(cfg_value))
            self.user_config.set("voxcpm_inference_timesteps", int(inference_timesteps))
            self.user_config.set("voxcpm_normalize_text", bool(normalize_text))
            self.user_config.set("voxcpm_denoise_reference", bool(denoise_reference))
            self.user_config.set("audio_format", audio_format)

            dubbing_file = os.path.join(path_dubbing_folder(), path_new_filename(f".{audio_format}"))
            self.tts.infer_single(
                dubbing_text.strip(),
                dubbing_file,
                celeb_audio,
                celeb_transcript,
                mode,
                voice_description,
                cfg_value,
                inference_timesteps,
                normalize_text,
                denoise_reference,
                audio_format,
            )
            return dubbing_file, dubbing_file
        except Exception as e:
            logger.error(f"[gradio_tts_voxcpm.py] gradio_tts_dubbing_single - error: {e}")
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
