import os

import gradio as gr
import pysubs2
from pydub import AudioSegment
import soundfile as sf

from app.abus_ffmpeg import ffmpeg_convert_audio
from app.abus_nlp_spacy import AbusSpacy
from app.abus_path import (
    cmd_delete_file,
    path_add_postfix,
    path_dubbing_folder,
    path_model_folder,
    path_new_filename,
    path_tts_segments_folder,
)
from app.abus_text import AbusText

import structlog

logger = structlog.get_logger()


class DotsTTS:
    MODEL_CHOICES = [
        "rednote-hilab/dots.tts-mf",
        "rednote-hilab/dots.tts-soar",
        "rednote-hilab/dots.tts-base",
    ]
    LANGUAGE_CHOICES = ["Auto Detect", "None", "English", "Chinese", "Japanese", "Korean"]
    LANGUAGE_TAGS = {
        "Auto Detect": "auto_detect",
        "None": "none",
        "English": "EN",
        "Chinese": "ZH",
        "Japanese": "JA",
        "Korean": "KO",
        "Chinese (simplified)": "ZH",
        "Chinese (traditional)": "ZH",
        "Japanese (Japan)": "JA",
        "Korean (South Korea)": "KO",
    }

    def __init__(self):
        self.cache_dir = os.path.join(path_model_folder(), "dots-tts", "hf-cache")
        self._runtime = None
        self._runtime_model = None

    def available_models(self):
        return self.MODEL_CHOICES.copy()

    def available_language_tags(self):
        return self.LANGUAGE_CHOICES.copy()

    @staticmethod
    def recommended_num_steps(model_choice: str) -> int:
        return 4 if model_choice == "rednote-hilab/dots.tts-mf" else 10

    def resolve_language_tag(self, language_name: str | None) -> str:
        if not language_name:
            return "auto_detect"

        return self.LANGUAGE_TAGS.get(language_name, self.LANGUAGE_TAGS.get(language_name.split(" (", 1)[0], "auto_detect"))

    def _get_runtime(self, model_choice: str):
        if self._runtime is not None and self._runtime_model == model_choice:
            return self._runtime

        try:
            from dots_tts.runtime import DotsTtsRuntime
        except ImportError as exc:
            raise RuntimeError("`dots-tts` is not installed in main uv environment. Run `uv sync` again.") from exc

        logger.info("[abus_tts_dots.py] loading runtime: model=%s", model_choice)
        runtime = DotsTtsRuntime.from_pretrained(
            model_choice,
            cache_dir=self.cache_dir,
            precision="bfloat16",
            optimize=False,
        )
        self._runtime = runtime
        self._runtime_model = model_choice
        return runtime

    @staticmethod
    def update_progress(progress, current: int, total: int, desc: str):
        if progress is None or total <= 0:
            return

        try:
            progress(current / total, desc=desc)
        except Exception:
            pass

    def generate_audio(
        self,
        text: str,
        output_file: str,
        prompt_audio: str | None,
        prompt_text: str | None,
        model_choice: str,
        language_tag: str,
        num_steps: int,
        guidance_scale: float,
        seed: int,
        normalize_text: bool,
    ):
        temp_wav = path_add_postfix(output_file, "_dots_raw", ".wav")
        runtime = self._get_runtime(model_choice)
        result = runtime.generate(
            text=text,
            prompt_audio_path=prompt_audio,
            prompt_text=prompt_text.strip() if prompt_text and prompt_text.strip() else None,
            language=self.resolve_language_tag(language_tag),
            num_steps=int(num_steps),
            guidance_scale=float(guidance_scale),
            normalize_text=bool(normalize_text),
        )
        sf.write(
            temp_wav,
            result["audio"].float().cpu().squeeze().numpy(),
            result["sample_rate"],
        )
        return temp_wav

    def request_tts(
        self,
        line: str,
        output_file: str,
        prompt_audio,
        prompt_text,
        model_choice,
        language_tag,
        num_steps,
        guidance_scale,
        seed,
        normalize_text,
        audio_format,
    ):
        line = AbusText.normalize_text(line)
        if len(line) < 1:
            logger.warning("[abus_tts_dots.py] request_tts - error: no line")
            return False

        logger.info("[abus_tts_dots.py] request_tts - line=%s", line)
        temp_wav = self.generate_audio(
            line,
            output_file,
            prompt_audio,
            prompt_text,
            model_choice,
            language_tag,
            num_steps,
            guidance_scale,
            seed,
            normalize_text,
        )
        ffmpeg_convert_audio(temp_wav, output_file, audio_format)
        cmd_delete_file(temp_wav)
        return True

    def srt_to_voice(
        self,
        subtitle_file: str,
        output_file: str,
        prompt_audio,
        prompt_text,
        model_choice,
        language_tag,
        num_steps,
        guidance_scale,
        seed,
        normalize_text,
        audio_format,
        progress=gr.Progress(),
    ):
        tts_subtitle_file = path_add_postfix(subtitle_file, "-dots-tts", ".srt")
        AbusSpacy.process_subtitle_for_tts(subtitle_file, tts_subtitle_file)

        segments_folder = path_tts_segments_folder(subtitle_file)
        full_subs = pysubs2.load(tts_subtitle_file, encoding="utf-8")
        total = len(full_subs)
        combined_audio = AudioSegment.empty()

        for i in range(total):
            self.update_progress(progress, i, total, "Generating...")
            line = full_subs[i]
            next_line = full_subs[i + 1] if i < total - 1 else None

            if i == 0:
                combined_audio += AudioSegment.silent(duration=line.start)

            tts_segment_file = os.path.join(segments_folder, f"tts_{i + 1}.{audio_format}")
            tts_result = self.request_tts(
                line.text,
                tts_segment_file,
                prompt_audio,
                prompt_text,
                model_choice,
                language_tag,
                num_steps,
                guidance_scale,
                seed,
                normalize_text,
                audio_format,
            )

            if tts_result is False:
                if next_line:
                    combined_audio += AudioSegment.silent(duration=next_line.start - line.start)
                continue

            combined_audio += AudioSegment.from_file(tts_segment_file)

            if next_line and len(combined_audio) < next_line.start:
                combined_audio += AudioSegment.silent(duration=next_line.start - len(combined_audio))
            elif next_line:
                next_line.start = len(combined_audio)
                next_line.end = next_line.start + (next_line.end - next_line.start)

        self.update_progress(progress, total, total, "Generating...")
        combined_audio.export(output_file, format=audio_format)
        cmd_delete_file(tts_subtitle_file)

    def text_to_voice(
        self,
        dubbing_text: str,
        output_file: str,
        prompt_audio,
        prompt_text,
        model_choice,
        language_tag,
        num_steps,
        guidance_scale,
        seed,
        normalize_text,
        audio_format,
        progress=gr.Progress(),
    ):
        segments_folder = path_tts_segments_folder(output_file)
        use_punctuation = AbusText.has_punctuation_marks(dubbing_text)
        lines = AbusText.split_into_sentences(dubbing_text, use_punctuation)

        total = len(lines)
        combined_audio = AudioSegment.empty()
        for i, line in enumerate(lines):
            self.update_progress(progress, i, total, "Generating...")
            tts_segment_file = os.path.join(segments_folder, f"tts_{i + 1:06}.{audio_format}")
            tts_result = self.request_tts(
                line,
                tts_segment_file,
                prompt_audio,
                prompt_text,
                model_choice,
                language_tag,
                num_steps,
                guidance_scale,
                seed,
                normalize_text,
                audio_format,
            )
            if tts_result is False:
                continue
            combined_audio += AudioSegment.from_file(tts_segment_file)

        self.update_progress(progress, total, total, "Generating...")
        combined_audio.export(output_file, format=audio_format)

    def infer_single(
        self,
        dubbing_text: str,
        output_file: str,
        prompt_audio,
        prompt_text,
        model_choice,
        language_tag,
        num_steps,
        guidance_scale,
        seed,
        normalize_text,
        audio_format: str,
        progress=gr.Progress(),
    ):
        subtitle_file = None
        if AbusText.is_subtitle_format(dubbing_text):
            subs = pysubs2.SSAFile.from_string(dubbing_text)
            subtitle_file = os.path.join(path_dubbing_folder(), path_new_filename(f".{subs.format}"))
            subs.save(subtitle_file)

        if subtitle_file:
            self.srt_to_voice(
                subtitle_file,
                output_file,
                prompt_audio,
                prompt_text,
                model_choice,
                language_tag,
                num_steps,
                guidance_scale,
                seed,
                normalize_text,
                audio_format,
                progress,
            )
            cmd_delete_file(subtitle_file)
            return

        self.text_to_voice(
            dubbing_text.strip(),
            output_file,
            prompt_audio,
            prompt_text,
            model_choice,
            language_tag,
            num_steps,
            guidance_scale,
            seed,
            normalize_text,
            audio_format,
            progress,
        )
