import glob
import os

import gradio as gr
import pysubs2
import soundfile as sf
from pydub import AudioSegment
from huggingface_hub import snapshot_download

from app.abus_download_progress import LoggingTqdm
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


class VoxCPMTTS:
    MODE_VOICE_CLONE = "Voice Clone"
    MODE_ULTIMATE_CLONE = "Ultimate Clone"
    MODE_VOICE_DESIGN = "Voice Design"
    MODE_CHOICES = [MODE_VOICE_CLONE, MODE_ULTIMATE_CLONE, MODE_VOICE_DESIGN]

    def __init__(self):
        self.default_model_dir = os.path.join(path_model_folder(), "voxcpm", "VoxCPM2")
        self.snapshot_cache_dir = os.path.join(path_model_folder(), "voxcpm", "hf-cache")
        self.repo_id = "openbmb/VoxCPM2"
        self._runtime = None
        self._runtime_model_dir = None
        self._sample_rate = 48000

    def available_modes(self):
        return self.MODE_CHOICES.copy()

    @staticmethod
    def default_values():
        return [
            VoxCPMTTS.MODE_VOICE_CLONE,
            "",
            2.0,
            10,
            False,
            False,
            "mp3",
        ]

    @property
    def sample_rate(self):
        return self._sample_rate

    def _candidate_model_dirs(self):
        candidates = [self.default_model_dir]
        snapshot_glob = os.path.join(
            self.snapshot_cache_dir,
            "models--openbmb--VoxCPM2",
            "snapshots",
            "*",
        )
        candidates.extend(sorted(glob.glob(snapshot_glob)))
        return [path for path in candidates if path and os.path.isdir(path)]

    def resolve_model_dir(self) -> str:
        weight_files = ("model.safetensors", "model.safetensors.index.json", "pytorch_model.bin")
        partial_candidates = []

        for candidate in self._candidate_model_dirs():
            missing = []
            if not os.path.exists(os.path.join(candidate, "config.json")):
                missing.append("config.json")
            if not any(os.path.exists(os.path.join(candidate, name)) for name in weight_files):
                missing.append("model weights")
            if not missing:
                return candidate
            partial_candidates.append((candidate, missing))

        if partial_candidates:
            details = "; ".join(f"{path} missing {', '.join(missing)}" for path, missing in partial_candidates)
            raise RuntimeError(
                "VoxCPM model files are incomplete. Expected a full local snapshot with "
                f"`config.json` and model weights. Checked: {details}"
            )

        raise RuntimeError(
            "VoxCPM model directory not found. Expected `model/voxcpm/VoxCPM2` or a snapshot under "
            "`model/voxcpm/hf-cache/models--openbmb--VoxCPM2/snapshots/`."
        )

    def ensure_model_available(self) -> str:
        try:
            return self.resolve_model_dir()
        except RuntimeError as exc:
            logger.warning("[abus_tts_voxcpm.py] local model incomplete, downloading %s: %s", self.repo_id, exc)

        os.makedirs(self.default_model_dir, exist_ok=True)
        os.makedirs(self.snapshot_cache_dir, exist_ok=True)
        snapshot_download(
            repo_id=self.repo_id,
            local_dir=self.default_model_dir,
            cache_dir=self.snapshot_cache_dir,
            local_files_only=False,
            local_dir_use_symlinks=False,
            resume_download=True,
            tqdm_class=LoggingTqdm,
        )
        return self.resolve_model_dir()

    def _get_runtime(self):
        model_dir = self.ensure_model_available()
        if self._runtime is not None and self._runtime_model_dir == model_dir:
            return self._runtime

        try:
            from voxcpm import VoxCPM
        except ImportError as exc:
            raise RuntimeError("`voxcpm` is not installed in current environment.") from exc

        logger.info("[abus_tts_voxcpm.py] loading runtime: model_dir=%s", model_dir)
        runtime = VoxCPM.from_pretrained(
            model_dir,
            local_files_only=True,
            load_denoiser=False,
            optimize=False,
        )
        self._runtime = runtime
        self._runtime_model_dir = model_dir
        self._sample_rate = getattr(runtime.tts_model, "sample_rate", 48000)
        return runtime

    @staticmethod
    def update_progress(progress, current: int, total: int, desc: str):
        if progress is None or total <= 0:
            return

        try:
            progress(current / total, desc=desc)
        except Exception:
            pass

    @staticmethod
    def validate_inputs(mode, prompt_audio, prompt_text, voice_description):
        if mode == VoxCPMTTS.MODE_VOICE_CLONE:
            if not prompt_audio:
                raise ValueError("Voice Clone requires reference audio.")
            return

        if mode == VoxCPMTTS.MODE_ULTIMATE_CLONE:
            if not prompt_audio:
                raise ValueError("Ultimate Clone requires reference audio.")
            if not (prompt_text and prompt_text.strip()):
                raise ValueError("Ultimate Clone requires transcript.")
            return

        if mode == VoxCPMTTS.MODE_VOICE_DESIGN:
            if not (voice_description and voice_description.strip()):
                raise ValueError("Voice Design requires voice description.")
            return

        raise ValueError(f"Unsupported VoxCPM mode: {mode}")

    @staticmethod
    def build_text(target_text: str, voice_description: str | None):
        clean_text = target_text.strip()
        clean_desc = (voice_description or "").strip()
        if clean_desc:
            return f"({clean_desc}){clean_text}"
        return clean_text

    def generate_audio(
        self,
        text: str,
        output_file: str,
        mode: str,
        prompt_audio: str | None,
        prompt_text: str | None,
        voice_description: str | None,
        cfg_value: float,
        inference_timesteps: int,
        normalize_text: bool,
        denoise_reference: bool,
    ):
        self.validate_inputs(mode, prompt_audio, prompt_text, voice_description)

        runtime = self._get_runtime()
        synthesis_text = self.build_text(text, voice_description)
        kwargs = {
            "text": synthesis_text,
            "cfg_value": float(cfg_value),
            "inference_timesteps": int(inference_timesteps),
            "normalize": bool(normalize_text),
            "denoise": bool(denoise_reference),
        }

        if mode == self.MODE_VOICE_CLONE:
            kwargs["reference_wav_path"] = prompt_audio
        elif mode == self.MODE_ULTIMATE_CLONE:
            kwargs["prompt_wav_path"] = prompt_audio
            kwargs["prompt_text"] = prompt_text.strip()

        temp_wav = path_add_postfix(output_file, "_voxcpm_raw", ".wav")
        wav = runtime.generate(**kwargs)
        sf.write(temp_wav, wav, self.sample_rate)
        return temp_wav

    def request_tts(
        self,
        line: str,
        output_file: str,
        mode: str,
        prompt_audio,
        prompt_text,
        voice_description,
        cfg_value,
        inference_timesteps,
        normalize_text,
        denoise_reference,
        audio_format,
    ):
        line = AbusText.normalize_text(line)
        if len(line) < 1:
            logger.warning("[abus_tts_voxcpm.py] request_tts - error: no line")
            return False

        logger.info("[abus_tts_voxcpm.py] request_tts - mode=%s line=%s", mode, line)
        temp_wav = self.generate_audio(
            line,
            output_file,
            mode,
            prompt_audio,
            prompt_text,
            voice_description,
            cfg_value,
            inference_timesteps,
            normalize_text,
            denoise_reference,
        )
        ffmpeg_convert_audio(temp_wav, output_file, audio_format)
        cmd_delete_file(temp_wav)
        return True

    def srt_to_voice(
        self,
        subtitle_file: str,
        output_file: str,
        mode: str,
        prompt_audio,
        prompt_text,
        voice_description,
        cfg_value,
        inference_timesteps,
        normalize_text,
        denoise_reference,
        audio_format,
        progress=gr.Progress(),
    ):
        tts_subtitle_file = path_add_postfix(subtitle_file, "-voxcpm", ".srt")
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
                mode,
                prompt_audio,
                prompt_text,
                voice_description,
                cfg_value,
                inference_timesteps,
                normalize_text,
                denoise_reference,
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
        mode: str,
        prompt_audio,
        prompt_text,
        voice_description,
        cfg_value,
        inference_timesteps,
        normalize_text,
        denoise_reference,
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
                mode,
                prompt_audio,
                prompt_text,
                voice_description,
                cfg_value,
                inference_timesteps,
                normalize_text,
                denoise_reference,
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
        mode: str,
        voice_description: str,
        cfg_value,
        inference_timesteps,
        normalize_text,
        denoise_reference,
        audio_format: str,
        progress=gr.Progress(),
    ):
        self.validate_inputs(mode, prompt_audio, prompt_text, voice_description)

        subtitle_file = None
        if AbusText.is_subtitle_format(dubbing_text):
            subs = pysubs2.SSAFile.from_string(dubbing_text)
            subtitle_file = os.path.join(path_dubbing_folder(), path_new_filename(f".{subs.format}"))
            subs.save(subtitle_file)

        if subtitle_file:
            self.srt_to_voice(
                subtitle_file,
                output_file,
                mode,
                prompt_audio,
                prompt_text,
                voice_description,
                cfg_value,
                inference_timesteps,
                normalize_text,
                denoise_reference,
                audio_format,
                progress,
            )
            cmd_delete_file(subtitle_file)
            return

        self.text_to_voice(
            dubbing_text.strip(),
            output_file,
            mode,
            prompt_audio,
            prompt_text,
            voice_description,
            cfg_value,
            inference_timesteps,
            normalize_text,
            denoise_reference,
            audio_format,
            progress,
        )
