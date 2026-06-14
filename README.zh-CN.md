# Voice-Pro

Voice-Pro 语音识别、翻译、配音 Web UI。当前安装路径只支持 `uv`。当前支持目标：`Linux x86_64 + NVIDIA GPU`。

## 项目链接

- Fork 自 [abus-aikorea/voice-pro](https://github.com/abus-aikorea/voice-pro)
- English README: [README.md](README.md)

## 支持范围

- 当前支持：Linux x86_64，NVIDIA 驱动正常，兼容 CUDA 12.8 的 PyTorch wheels。
- 当前 `uv` 首版不支持：Windows、macOS、纯 CPU。
- 旧 conda / Miniconda / `installer_files/env` 流程已从推荐路径移除。

## 前置条件

- `uv`
- `git`
- `ffmpeg`
- `build-essential` 这类构建工具
- `espeak-ng`，供 phonemizer 相关 TTS 路径使用
- 可用 NVIDIA 驱动，`nvidia-smi` 应可正常执行

Debian/Ubuntu 示例：

```bash
sudo apt update
sudo apt install -y git ffmpeg build-essential espeak-ng
```

安装 `uv`：

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## 安装

在仓库根目录执行：

```bash
uv sync
```

这里 `uv sync` 会做这些事：

- 通过 `.python-version` 固定 Python `3.10.15`
- 创建项目虚拟环境
- 默认安装 CUDA 12.8 PyTorch wheels
- 安装 GPU 运行时依赖，如 `onnxruntime-gpu`、`whisperx`、`kokoro`、`f5-tts`、`dots.tts`
- `dots.tts` 直接安装在主项目环境里，不再需要单独 `.venv-dots-tts`

## 运行

直接运行：

```bash
uv run python start-voice.py
```

控制台脚本：

```bash
uv run voice-pro
```

Linux 后台辅助脚本：

```bash
./start-linux.sh
```

## 验证环境

检查 CUDA / torch：

```bash
uv run python -c "import torch; print(torch.__version__); print(torch.cuda.is_available())"
```

检查核心导入：

```bash
uv run python -c "import gradio, onnxruntime, whisperx, kokoro, f5_tts, dots_tts.runtime"
```

同步完成后，核心版本大致应为：

- `torch 2.8.0+cu128`
- `torchaudio 2.8.0+cu128`
- `torchvision 0.23.0+cu128`
- `transformers 4.57.4`
- `numpy 2.2.6`

## 运行说明

- 启动器会把 NVIDIA `cublas` 与 `cudnn` wheel 库路径自动加入 `LD_LIBRARY_PATH`
- 首次运行会下载所需 Hugging Face 模型，可能较慢
- 首次使用 `dots.tts` 合成时，也会下载官方 `rednote-hilab/dots.tts-*` 权重
- 工作目录仍在 `./workspace`
- 模型资源仍在 `./model`
- Gradio 工作文件现在放在 `./workspace/gradio`
- `Dubbing Studio` 和 `Speech Generation` 均已接入 `dots.tts`

## 故障排查

### `torch.cuda.is_available()` 为 `False`

- 确认虚拟环境外 `nvidia-smi` 正常
- 确认驱动支持 CUDA 12.8 wheels
- 重新执行 `uv sync`

### cuDNN / cuBLAS 相关导入或共享库错误

- 通过启动器命令运行，不要直接裸导模块
- 启动器会在应用启动前注入 wheel 提供的 NVIDIA 库目录
- `whisperX` 仍需要 cuDNN 8 兼容名字；启动器会从内置 `ctranslate2` 库自动创建这些软链接
- 新版 `nvidia.cudnn.lib` 可能是 namespace package；启动器已同时兼容 `__file__` 和 `__path__`

### `dots.tts` 首次使用很慢

- 首次调用会从 Hugging Face 下载模型权重
- `rednote-hilab/dots.tts-mf` 适合作为优先尝试的更快模型
- 字幕配音仍是逐句执行，长字幕文件依然较重

### `uv sync` 解析或构建失败

- 确保 `uv` 能安装 Python 3.10
- 更新 `uv`
- 删除 `.venv` 后重试

```bash
rm -rf .venv
uv sync
```

### 首次启动很慢或看起来卡住

- 启动期间会下载模型
- 使用 `./start-linux.sh` 时，可查看终端输出或 `/tmp/voice-pro.log`

## 旧脚本状态

以下文件只保留兼容提示或废弃提示：

- `start.sh`
- `start-abus.py`
- `configure.sh`
- `update.sh`
- `start.bat`
- `configure.bat`
- `update.bat`
- `one_click.py`

这些文件不再负责安装或管理 conda 环境。
