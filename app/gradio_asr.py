import os

import gradio as gr

from src.config import UserConfig

from app.abus_asr_parameters import WhisperParameters
from app.abus_asr_whisper_timestamped import WhisperTimestampedInference
from app.abus_demucs import demucs_split_file
from app.abus_downloader import YoutubeDownloader
from app.abus_ffmpeg import ffmpeg_browser_compatible, ffmpeg_codec_type, ffmpeg_extract_audio
from app.abus_files import FileManager
from app.abus_path import (
    cmd_copy_file_to,
    cmd_open_explorer,
    path_change_ext,
    path_gradio_folder,
    path_workspace_folder,
    path_workspace_subfolder,
    path_youtube_folder,
)

import structlog

logger = structlog.get_logger()


class GradioASR:
    ALLOWED_MODELS = ["large", "large-v3-turbo", "turbo"]

    def __init__(self, user_config: UserConfig):
        self.user_config = user_config
        self.fm = FileManager()
        self.downloader = YoutubeDownloader()
        self.whisper_inf = WhisperTimestampedInference()

    def open_workspace_folder(self):
        cmd_open_explorer(path_workspace_folder())

    def open_temp_folder(self):
        cmd_open_explorer(path_gradio_folder())

    def get_whisper_models(self):
        return self.ALLOWED_MODELS.copy()

    def get_whisper_languages(self):
        return self.whisper_inf.available_langs()

    def upload_source(self, file_obj, mic_file, youtube_url: str, video_quality: str, audio_format: str):
        self.user_config.set("video_quality", video_quality)
        self.user_config.set("upload_audio_format", audio_format)

        try:
            logger.debug("upload_source: file=%s mic=%s youtube=%s", file_obj, mic_file, youtube_url)
            self.fm = FileManager()
            if not self._upload(file_obj, mic_file, youtube_url, video_quality, audio_format):
                return None, None
            return self.fm.get_split("Source.video"), self.fm.get_split("Source.audio")
        except Exception as e:
            logger.error("[gradio_asr.py] upload_source - error: %s", e)
            gr.Warning(f"{e}")
            return None, None

    def _upload(self, file_obj, mic_file, youtube_url: str, video_quality: str, audio_format: str):
        if file_obj is not None:
            uploaded_file = path_workspace_subfolder(file_obj.name)
            uploaded_file = cmd_copy_file_to(file_obj.name, uploaded_file)
        elif mic_file and mic_file.strip():
            uploaded_file = cmd_copy_file_to(mic_file, path_workspace_subfolder(mic_file))
        elif youtube_url and youtube_url.strip():
            youtube_file = self.downloader.yt_download(youtube_url, path_youtube_folder(), video_quality)
            uploaded_file = cmd_copy_file_to(youtube_file, path_workspace_subfolder(youtube_file))
        else:
            return False

        self.source_file = uploaded_file
        self.has_audio, self.has_video = ffmpeg_codec_type(self.source_file)
        if not self.has_audio:
            return False
        if not self.has_video:
            self.fm.set_split("Source.video", None)
            self.fm.set_split("Source.audio", self.source_file)
            return True

        input_audio_file = path_change_ext(self.source_file, f".{audio_format}")
        ffmpeg_extract_audio(self.source_file, input_audio_file, audio_format)
        self.fm.set_split("Source.video", self.source_file)
        self.fm.set_split("Source.audio", input_audio_file)
        return True

    def gradio_whisper_default(self):
        return ["large-v3-turbo", "english", False, 0]

    def transcribe(self, model_name, whisper_language, highlight_words, denoise_level):
        if model_name not in self.ALLOWED_MODELS:
            model_name = "large-v3-turbo"

        self.user_config.set("whisper_timestamped_model", model_name)
        self.user_config.set("whisper_language", whisper_language)
        self.user_config.set("whisper_highlight_words", highlight_words)
        self.user_config.set("denoise_level", denoise_level)

        try:
            source_audio = self.fm.get_split("Source.audio")
            denoise_inst_path, denoise_vocal_path = self._denoise(source_audio, denoise_level)
            input_path = denoise_vocal_path if os.path.exists(denoise_vocal_path) else source_audio
            params = WhisperParameters(model_size=model_name, lang=whisper_language.lower(), compute_type="default")
            subtitles = self.whisper_inf.transcribe_file(input_path, params, highlight_words, gr.Progress())
            if not subtitles:
                raise RuntimeError("Transcription did not produce subtitle files.")

            self.fm.set_subtitles(subtitles, whisper_language, source_audio)
            srt_file = self.fm.get_subtitle(".srt")
            srt_string = self._read_subtitle_file(srt_file)

            if self.has_video and ffmpeg_browser_compatible(self.source_file):
                return (self.source_file, srt_file), srt_string, self.fm.get_all_files()
            return None, srt_string, self.fm.get_all_files()
        except Exception as e:
            logger.error("[gradio_asr.py] transcribe - error: %s", e, exc_info=True)
            gr.Warning(f"{e}")
            return None, None, None

    def _denoise(self, source_audio, denoise_level=2):
        if denoise_level == 1:
            return self._demucs_split(source_audio, "htdemucs")
        if denoise_level == 2:
            return self._demucs_split(source_audio, "htdemucs_ft")
        return "", ""

    def _demucs_split(self, source_audio, model_name: str):
        _, extension = os.path.splitext(os.path.basename(source_audio))
        output_dir = os.path.dirname(source_audio)
        inst_audio_file, vocal_audio_file = demucs_split_file(source_audio, output_dir, model_name, extension[1:])
        self.fm.set_split("Instrumental.audio", inst_audio_file)
        self.fm.set_split("Vocals.audio", vocal_audio_file)
        return inst_audio_file, vocal_audio_file

    @staticmethod
    def _read_subtitle_file(file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()
