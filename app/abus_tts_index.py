import json
import os
import glob
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from packaging.version import Version, InvalidVersion

import gradio as gr
import pysubs2
from pydub import AudioSegment

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


class IndexTTSTTS:
    REPO_URL = "https://github.com/index-tts/index-tts.git"
    MODEL_REPO_DIRNAME = "IndexTTS2"
    DOWNLOAD_SUPPORT_PACKAGES = [
        "huggingface_hub>=0.34,<1",
        "modelscope>=1.27,<2",
    ]

    def __init__(self):
        self.root_dir = os.path.join(path_model_folder(), "index-tts")
        self.repo_dir = os.path.join(self.root_dir, "index-tts")
        self.venv_dir = os.path.join(self.root_dir, ".venv")
        self.runtime_dir = os.path.join(self.root_dir, "runtime")
        self.default_model_dir = os.path.join(self.root_dir, self.MODEL_REPO_DIRNAME)
        self.sidecar_script = os.path.join(Path(__file__).resolve().parent, "index_tts_sidecar.py")
        self.download_script = os.path.join(Path(__file__).resolve().parent, "index_tts_download.py")

    @staticmethod
    def default_values():
        return [False, 1.0, "mp3"]

    @staticmethod
    def update_progress(progress, current: int, total: int, desc: str):
        if progress is None or total <= 0:
            return

        try:
            progress(current / total, desc=desc)
        except Exception:
            pass

    @property
    def venv_python(self):
        if os.name == "nt":
            return os.path.join(self.venv_dir, "Scripts", "python.exe")
        return os.path.join(self.venv_dir, "bin", "python")

    def _run_command(self, command, cwd=None, error_prefix="Command failed", stream_output: bool = False):
        logger.info("[abus_tts_index.py] run command: %s", " ".join(command))
        if stream_output:
            process = subprocess.Popen(
                command,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            output_lines = []
            assert process.stdout is not None
            for line in process.stdout:
                text = line.rstrip()
                output_lines.append(line)
                if text:
                    logger.info("[abus_tts_index.py] %s", text)
            return_code = process.wait()
            if return_code == 0:
                return subprocess.CompletedProcess(command, return_code, "".join(output_lines), "")

            details = "".join(output_lines).strip() or f"exit code {return_code}"
            raise RuntimeError(f"{error_prefix}: {details}")

        result = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
        if result.returncode == 0:
            return result

        details = result.stderr.strip() or result.stdout.strip() or f"exit code {result.returncode}"
        raise RuntimeError(f"{error_prefix}: {details}")

    def ensure_repo_available(self):
        if os.path.exists(os.path.join(self.repo_dir, "pyproject.toml")):
            return

        os.makedirs(self.root_dir, exist_ok=True)
        if os.path.isdir(self.repo_dir):
            shutil.rmtree(self.repo_dir)

        try:
            self._run_command(
                ["git", "clone", "--depth", "1", self.REPO_URL, self.repo_dir],
                error_prefix="clone failed",
            )
        except Exception as exc:
            raise RuntimeError(f"IndexTTS 官方代码拉取失败，请检查网络或仓库可达性。原始错误: {exc}") from exc

    def ensure_env_available(self):
        os.makedirs(self.root_dir, exist_ok=True)
        try:
            if not os.path.exists(self.venv_python):
                self._run_command(
                    [sys.executable, "-m", "venv", self.venv_dir],
                    error_prefix="venv creation failed",
                )
                self._run_command(
                    [self.venv_python, "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"],
                    error_prefix="pip bootstrap failed",
                )
                self._run_command(
                    [self.venv_python, "-m", "pip", "install", "-e", self.repo_dir],
                    error_prefix="IndexTTS dependency install failed",
                )

            self.ensure_download_support()
        except Exception as exc:
            raise RuntimeError(f"IndexTTS 独立环境创建失败。原始错误: {exc}") from exc

    def ensure_download_support(self):
        check = subprocess.run(
            [
                self.venv_python,
                "-c",
                (
                    "import huggingface_hub, modelscope; "
                    "from packaging.version import Version; "
                    "assert Version(huggingface_hub.__version__) < Version('1.0'); "
                    "assert Version(modelscope.__version__) >= Version('1.27.0')"
                ),
            ],
            capture_output=True,
            text=True,
        )
        if check.returncode == 0:
            return

        logger.warning("[abus_tts_index.py] installing missing download support packages")
        self._cleanup_package_metadata("huggingface_hub")
        self._run_command(
            [
                self.venv_python,
                "-m",
                "pip",
                "install",
                "--upgrade",
                "--force-reinstall",
                "--no-deps",
                *self.DOWNLOAD_SUPPORT_PACKAGES,
            ],
            error_prefix="IndexTTS download support install failed",
        )
        self._cleanup_package_metadata("huggingface_hub")

    def _cleanup_package_metadata(self, package_name: str):
        site_packages = os.path.join(self.venv_dir, "lib", "python3.10", "site-packages")
        if not os.path.isdir(site_packages):
            return

        pattern = os.path.join(site_packages, f"{package_name}-*.dist-info")
        matches = sorted(glob.glob(pattern))
        if len(matches) <= 1:
            return

        keep = None
        keep_version = None
        for path in matches:
            version_text = os.path.basename(path)[len(package_name) + 1 : -len(".dist-info")]
            try:
                version = Version(version_text)
            except InvalidVersion:
                version = None

            if keep is None:
                keep = path
                keep_version = version
                continue

            if version is not None and version < Version("1.0"):
                if keep_version is None or keep_version >= Version("1.0") or version > keep_version:
                    keep = path
                    keep_version = version

        for path in matches:
            if path == keep:
                continue
            logger.warning("[abus_tts_index.py] removing stale metadata: %s", path)
            shutil.rmtree(path, ignore_errors=True)

    def _is_valid_model_dir(self, candidate: str) -> bool:
        if not candidate or not os.path.isdir(candidate):
            return False

        config_path = os.path.join(candidate, "config.yaml")
        if not os.path.exists(config_path):
            return False

        weight_suffixes = (".pt", ".pth", ".bin", ".safetensors")
        for root, _, files in os.walk(candidate):
            for filename in files:
                if filename == "config.yaml":
                    continue
                if filename.endswith(weight_suffixes):
                    return True
        return False

    def _candidate_model_dirs(self):
        return [
            self.default_model_dir,
            os.path.join(self.root_dir, "checkpoints"),
            os.path.join(self.repo_dir, "checkpoints"),
            os.path.join(self.repo_dir, self.MODEL_REPO_DIRNAME),
        ]

    def resolve_model_dir(self) -> str:
        candidates = self._candidate_model_dirs()

        for candidate in candidates:
            if self._is_valid_model_dir(candidate):
                return candidate

        joined = "\n".join(candidates)
        raise RuntimeError(
            "未找到本地 IndexTTS 模型，请将已下载模型放到以下路径之一：\n"
            f"{joined}"
        )

    def ensure_model_available(self) -> str:
        try:
            return self.resolve_model_dir()
        except RuntimeError as exc:
            logger.warning("[abus_tts_index.py] local IndexTTS model missing, downloading: %s", exc)

        os.makedirs(self.default_model_dir, exist_ok=True)
        try:
            self._run_command(
                [
                    self.venv_python,
                    self.download_script,
                    "--repo-dir",
                    self.repo_dir,
                    "--model-dir",
                    self.default_model_dir,
                    "--source",
                    "auto",
                ],
                cwd=self.repo_dir,
                error_prefix="IndexTTS model download failed",
                stream_output=True,
            )
        except Exception as exc:
            raise RuntimeError(f"IndexTTS 模型自动下载失败。原始错误: {exc}") from exc

        return self.resolve_model_dir()

    @staticmethod
    def normalize_emotion_inputs(enable_emo_audio, emo_audio_prompt):
        return bool(enable_emo_audio and emo_audio_prompt and str(emo_audio_prompt).strip())

    @staticmethod
    def validate_inputs(prompt_audio, prompt_text, enable_emo_audio, emo_audio_prompt):
        if not prompt_audio:
            raise ValueError("IndexTTS requires reference audio.")

    def _build_payload(
        self,
        text: str,
        output_path: str,
        prompt_audio,
        prompt_text,
        emo_audio_prompt,
        enable_emo_audio,
        emo_alpha,
        audio_format,
    ):
        self.ensure_repo_available()
        self.ensure_env_available()
        effective_emo_enabled = self.normalize_emotion_inputs(enable_emo_audio, emo_audio_prompt)
        model_dir = self.ensure_model_available()

        return {
            "text": text,
            "prompt_audio": prompt_audio,
            "prompt_text": prompt_text.strip() if prompt_text and prompt_text.strip() else None,
            "emo_audio_prompt": emo_audio_prompt if effective_emo_enabled else None,
            "emo_alpha": float(emo_alpha),
            "audio_format": audio_format,
            "model_dir": model_dir,
            "output_path": output_path,
            "repo_dir": self.repo_dir,
        }

    def generate_audio(
        self,
        text: str,
        output_file: str,
        prompt_audio,
        prompt_text,
        emo_audio_prompt,
        enable_emo_audio,
        emo_alpha,
        audio_format,
    ):
        self.validate_inputs(prompt_audio, prompt_text, enable_emo_audio, emo_audio_prompt)

        temp_wav = path_add_postfix(output_file, "_index_tts_raw", ".wav")
        payload = self._build_payload(
            text=text,
            output_path=temp_wav,
            prompt_audio=prompt_audio,
            prompt_text=prompt_text,
            emo_audio_prompt=emo_audio_prompt,
            enable_emo_audio=enable_emo_audio,
            emo_alpha=emo_alpha,
            audio_format=audio_format,
        )

        os.makedirs(self.runtime_dir, exist_ok=True)
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", dir=self.runtime_dir, delete=False) as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            payload_path = handle.name

        try:
            result = self._run_command(
                [self.venv_python, self.sidecar_script, "--payload", payload_path],
                cwd=self.repo_dir,
                error_prefix="inference failed",
            )
        except RuntimeError as exc:
            raise RuntimeError(f"IndexTTS 推理失败: {exc}") from exc
        finally:
            cmd_delete_file(payload_path)

        output_path = None
        for line in reversed(result.stdout.splitlines()):
            line = line.strip()
            if not line:
                continue
            try:
                output_path = json.loads(line).get("output_path")
                break
            except json.JSONDecodeError:
                continue

        if not output_path or not os.path.exists(output_path):
            raise RuntimeError("IndexTTS sidecar did not return generated audio path.")
        return output_path

    def request_tts(
        self,
        line: str,
        output_file: str,
        prompt_audio,
        prompt_text,
        emo_audio_prompt,
        enable_emo_audio,
        emo_alpha,
        audio_format,
    ):
        line = AbusText.normalize_text(line)
        if len(line) < 1:
            logger.warning("[abus_tts_index.py] request_tts - error: no line")
            return False

        logger.info("[abus_tts_index.py] request_tts - line=%s", line)
        temp_wav = self.generate_audio(
            line,
            output_file,
            prompt_audio,
            prompt_text,
            emo_audio_prompt,
            enable_emo_audio,
            emo_alpha,
            audio_format,
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
        emo_audio_prompt,
        enable_emo_audio,
        emo_alpha,
        audio_format,
        progress=gr.Progress(),
    ):
        tts_subtitle_file = path_add_postfix(subtitle_file, "-index-tts", ".srt")
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
                emo_audio_prompt,
                enable_emo_audio,
                emo_alpha,
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
        emo_audio_prompt,
        enable_emo_audio,
        emo_alpha,
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
                emo_audio_prompt,
                enable_emo_audio,
                emo_alpha,
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
        emo_audio_prompt,
        enable_emo_audio,
        emo_alpha,
        audio_format: str,
        progress=gr.Progress(),
    ):
        self.validate_inputs(prompt_audio, prompt_text, enable_emo_audio, emo_audio_prompt)

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
                emo_audio_prompt,
                enable_emo_audio,
                emo_alpha,
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
            emo_audio_prompt,
            enable_emo_audio,
            emo_alpha,
            audio_format,
            progress,
        )
