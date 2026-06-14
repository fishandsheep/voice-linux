# Voice-Pro

Voice-Pro speech recognition, translation, dubbing web UI. Current install path now `uv` only. Current supported target: Linux x86_64 + NVIDIA GPU.

## Project Links

- Forked from [abus-aikorea/voice-pro](https://github.com/abus-aikorea/voice-pro)
- Chinese README: [README.zh-CN.md](README.zh-CN.md)

## Support Scope

- Supported now: Linux x86_64, NVIDIA driver working, CUDA 12.8-compatible PyTorch wheels.
- Not supported in this `uv` first release: Windows, macOS, CPU-only.
- Legacy conda / Miniconda / `installer_files/env` flow removed from recommended path.

## Prerequisites

- `uv`
- `git`
- `ffmpeg`
- build tools such as `build-essential`
- `espeak-ng` for phonemizer-backed TTS paths
- working NVIDIA driver (`nvidia-smi` should succeed)

Example Debian/Ubuntu packages:

```bash
sudo apt update
sudo apt install -y git ffmpeg build-essential espeak-ng
```

Install `uv`:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Install

Repository root:

```bash
uv sync
```

What `uv sync` does here:

- pins Python to `3.10.15` via `.python-version`
- creates project virtualenv
- installs CUDA 12.8 PyTorch wheels by default
- installs GPU runtime packages such as `onnxruntime-gpu`, `whisperx`, `kokoro`, `f5-tts`, and `dots.tts`
- keeps `dots.tts` in main project environment; no separate `.venv-dots-tts` needed

## Run

Direct:

```bash
uv run python start-voice.py
```

Console script:

```bash
uv run voice-pro
```

Background Linux helper:

```bash
./start-linux.sh
```

## Verify Environment

CUDA / torch:

```bash
uv run python -c "import torch; print(torch.__version__); print(torch.cuda.is_available())"
```

Core imports:

```bash
uv run python -c "import gradio, onnxruntime, whisperx, kokoro, f5_tts, dots_tts.runtime"
```

Main package versions after sync should look roughly like:

- `torch 2.8.0+cu128`
- `torchaudio 2.8.0+cu128`
- `torchvision 0.23.0+cu128`
- `transformers 4.57.4`
- `numpy 2.2.6`

## Runtime Notes

- launcher auto-prepends NVIDIA `cublas` and `cudnn` wheel library paths into `LD_LIBRARY_PATH`
- first run downloads required Hugging Face models; can take long time
- first `dots.tts` synthesis also downloads official `rednote-hilab/dots.tts-*` weights
- workspace still created under `./workspace`
- model assets still stored under `./model`
- Gradio working files now go under `./workspace/gradio`
- `Dubbing Studio` and `Speech Generation` both include `dots.tts`

## Troubleshooting

### `torch.cuda.is_available()` is `False`

- confirm `nvidia-smi` works outside virtualenv
- confirm driver supports CUDA 12.8 wheels
- re-run `uv sync`

### Import or shared-library failure around cuDNN / cuBLAS

- run through launcher command, not raw module import
- launcher injects wheel-provided NVIDIA library directories before app boot
- `whisperX` still needs cuDNN 8 compatibility names; launcher creates those symlinks from bundled `ctranslate2` libs automatically
- newer `nvidia.cudnn.lib` can be namespace-package style; launcher now handles both `__file__` and `__path__`

### `dots.tts` is slow on first use

- first call downloads model weights from Hugging Face
- `rednote-hilab/dots.tts-mf` is fastest recommended starting point
- subtitle dubbing still runs sentence by sentence, so long subtitle files remain heavy

### `uv sync` resolution/build failure

- make sure Python 3.10 can be installed by `uv`
- update `uv`
- clear `.venv` and retry

```bash
rm -rf .venv
uv sync
```

### First launch slow or appears stuck

- model downloads happen during startup
- check terminal output or `/tmp/voice-pro.log` when using `./start-linux.sh`

## Legacy Scripts

These files remain only as compatibility shims or deprecation notices:

- `start.sh`
- `start-abus.py`
- `configure.sh`
- `update.sh`
- `start.bat`
- `configure.bat`
- `update.bat`
- `one_click.py`

They no longer install or manage conda environments.
