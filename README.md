# Voice-Pro

`voice-pro` 是 [abus-aikorea/voice-pro](https://github.com/abus-aikorea/voice-pro) 分支仓库，当前只保留真实可用主线：`Linux x86_64 + NVIDIA + uv`。仓库现在只覆盖 4 类核心页面与流程：

- `Dubbing Studio`
- `Whisper subtitles`
- `Translation`
- `Speech Generation`

不再把 Windows、macOS、conda、one-click、旧站点页面、AI Cover、Karaoke、RVC、VSR、Live Translation、Demixing、Batch TTS 当作当前支持范围。

## 支持范围

- 操作系统：`Linux x86_64`
- GPU：`NVIDIA`
- Python：`3.10.15`
- PyTorch：`2.8.0+cu128`
- CUDA 轮子基线：`cu128`
- 包管理与启动：`uv`

不支持：

- Windows 主流程
- macOS
- CPU-only
- conda / `installer_files` / `one_click.py`

## 环境要求

系统需要先装好：

- `uv`
- `git`
- `ffmpeg`
- `espeak-ng`
- 可工作的 NVIDIA 驱动

Debian / Ubuntu 可直接执行：

```bash
sudo apt update
sudo apt install -y git ffmpeg build-essential espeak-ng
curl -LsSf https://astral.sh/uv/install.sh | sh
```

建议先确认：

```bash
nvidia-smi
uv --version
ffmpeg -version
espeak-ng --version
```

## 安装

仓库根目录执行：

```bash
uv sync
```

`uv sync` 会做这些事：

- 解析 `.python-version`，安装 `Python 3.10.15`
- 创建项目虚拟环境
- 安装 CUDA 12.8 对应 PyTorch 轮子
- 安装 `whisperx`、`kokoro`、`f5-tts`、`dots-tts`、`onnxruntime-gpu` 等运行依赖
- 保持 `dots.tts` 在主环境内运行，不再依赖独立环境

## 启动

推荐命令：

```bash
uv run voice-pro
```

等价命令：

```bash
uv run python start-voice.py
```

后台启动辅助脚本：

```bash
./start-linux.sh
```

默认会拉起本地 Gradio 服务，常见地址：

```text
http://127.0.0.1:7860
```

## 环境验证

先验证 CUDA：

```bash
uv run python -c "import torch; print(torch.__version__); print(torch.cuda.is_available())"
```

再验证核心依赖导入：

```bash
uv run python -c "import gradio, onnxruntime, whisperx, kokoro, f5_tts, dots_tts.runtime"
```

如果要验证启动链本身，可执行：

```bash
uv run voice-pro
```

## 首次运行与模型下载

首次启动会自动准备部分运行模型与素材，速度可能较慢。当前启动链会预取：

- `demucs` 去噪模型
- `Edge-TTS` 示例音色素材
- `kokoro` 示例音色与 `eSpeak NG` 资源
- `CosyVoice` 示例音色与模型包

另外：

- `F5-TTS` / `E2-TTS` 首次推理会按所选模型拉取权重
- `dots.tts` 首次推理会从 Hugging Face 下载所选权重
- `whisper` / `faster-whisper` / `whisper-timestamped` / `whisperX` 首次使用对应模型时也会下载

工作目录约定：

- 工作区：`./workspace`
- Gradio 临时目录：`./workspace/gradio`
- 模型目录：`./model`

## 功能使用

### 1. 语音识别

页面：

- `Dubbing Studio`
- `Whisper subtitles`

基本流程：

1. 上传音频或视频，或填写 YouTube URL。
2. 选择 ASR 引擎。
3. 选择模型、语言、`Compute Type`、去噪等级。
4. 执行转写，生成字幕文本与字幕文件。

说明：

- `Whisper subtitles` 页面支持 `faster-whisper`、`whisper`、`whisper-timestamped`、`whisperX`
- `Dubbing Studio` 当前默认且推荐 `whisper-timestamped`
- `Dubbing Studio` 页面会把 `faster-whisper` / `whisperX` 归一到 `whisper-timestamped`
- `Compute Type` 仅对 `faster-whisper` 生效
- `Denoise Level` 会调用 `demucs` 做人声分离后再转写，因此首次运行可能更慢

输出：

- `.srt` 等字幕文件
- 工作区中的中间音频 / 视频文件

### 2. 翻译

页面：

- `Translation`
- `Dubbing Studio` 内置翻译区

基本流程：

1. 导入字幕文件或直接粘贴文本。
2. 选择源语言与目标语言。
3. 执行翻译。
4. 导出翻译后文本或字幕文件。

说明：

- 普通文本会按句切分再翻译
- 字幕会逐条翻译，并按 TTS 需要做轻量预处理
- 若配置可用，会优先使用 `Azure Translator`
- 未配置 Azure 时，默认走 `deep-translator`

### 3. 配音

页面：

- `Speech Generation`
- `Dubbing Studio` 内置配音区

基本流程：

1. 输入翻译后的文本，或导入字幕文件。
2. 选择 TTS 引擎与模型。
3. 根据引擎填写参考音频、参考文本、语言、步数、语速等参数。
4. 执行合成，生成音频文件。

说明：

- 文本输入会按句切分后逐句合成
- 字幕输入会按时间轴逐句合成并拼接
- 长字幕文件会明显更慢，尤其 `F5-TTS`、`CosyVoice`、`dots.tts`

### 4. Dubbing Studio 端到端流程

推荐顺序：

1. 上传媒体
2. 转字幕
3. 检查字幕文本
4. 选择源语言与目标语言并翻译
5. 选择 TTS 引擎与参数
6. 合成配音音频或视频

这个页面适合单文件端到端流程；如果只做某一段功能，分别去 `Whisper subtitles`、`Translation`、`Speech Generation` 更直接。

## 支持引擎与模型

### 语音识别

- `faster-whisper`
  - 页面：`Whisper subtitles`
  - 参考音频：不需要
  - 特点：支持 `Compute Type`
- `openai-whisper`
  - 页面：`Whisper subtitles`
  - 参考音频：不需要
- `whisper-timestamped`
  - 页面：`Whisper subtitles`、`Dubbing Studio`
  - 参考音频：不需要
  - 说明：`Dubbing Studio` 默认与推荐选项
- `whisperX`
  - 页面：`Whisper subtitles`
  - 参考音频：不需要
  - 说明：首次初始化通常较慢，对 CUDA / cuDNN 更敏感

### 翻译

- `deep-translator`
  - 页面：`Translation`、`Dubbing Studio`
  - 配置：默认可用
- `Azure Translator`
  - 页面：`Translation`、`Dubbing Studio`
  - 配置：需要 `.env`
  - 必填变量：`AZURE_TRANSLATOR_KEY`、`AZURE_TRANSLATOR_ENDPOINT`、`AZURE_TRANSLATOR_REGION`

### 配音

- `Edge-TTS`
  - 页面：`Speech Generation`、`Dubbing Studio`
  - 参考音频：不需要
  - 特点：启动快，适合标准配音
- `Azure TTS`
  - 页面：`Speech Generation`、`Dubbing Studio`
  - 参考音频：不需要
  - 配置：需要 `.env`
  - 必填变量：`AZURE_SPEECH_KEY`、`AZURE_SPEECH_REGION`
- `F5-TTS`
  - 页面：`Speech Generation`、`Dubbing Studio`
  - 参考音频：需要
  - 参考文本：建议提供
  - 特点：适合克隆式配音，首次加载较慢
  - 当前模型族：`SWivid/F5-TTS_v1` 及 `abus_tts_f5_models.json` 中列出的 F5 模型
- `E2-TTS`
  - 页面：`Speech Generation`、`Dubbing Studio`
  - 从属：作为 `F5-TTS` 体系中的可选模型 `SWivid/E2-TTS`
  - 参考音频：需要
  - 特点：首次拉权重较慢
- `CosyVoice`
  - 页面：`Speech Generation`、`Dubbing Studio`
  - 参考音频：需要
  - 参考文本：`Zero-Shot` 模式建议提供，界面中也标注为必填
  - 特点：模型体积大，初始化明显较慢
- `kokoro`
  - 页面：`Speech Generation`、`Dubbing Studio`
  - 参考音频：不需要
  - 限制：依赖 `espeak-ng`
- `dots.tts`
  - 页面：`Speech Generation`、`Dubbing Studio`
  - 参考音频：可选
  - 参考文本：可选
  - 当前模型：`rednote-hilab/dots.tts-mf`、`rednote-hilab/dots.tts-soar`、`rednote-hilab/dots.tts-base`
  - 特点：首次下载权重较慢；长字幕逐句合成时耗时明显

## Azure 配置

如需启用 Azure 翻译或 Azure TTS，先复制配置模板：

```bash
cp .env.example .env
```

然后填写：

```dotenv
AZURE_SPEECH_KEY=...
AZURE_SPEECH_REGION=eastus
AZURE_TRANSLATOR_KEY=...
AZURE_TRANSLATOR_ENDPOINT=https://your-translator-resource.cognitiveservices.azure.com/
AZURE_TRANSLATOR_REGION=eastus
```

未配置 Azure 时：

- 翻译自动回退到 `deep-translator`
- 语音页自动显示 `Edge-TTS`

## 常见问题

### `torch.cuda.is_available()` 是 `False`

- 先确认 `nvidia-smi` 正常
- 确认驱动能支持 CUDA 12.8 轮子
- 删除 `.venv` 后重新执行 `uv sync`

```bash
rm -rf .venv
uv sync
```

### `uv sync` 失败

- 升级 `uv`
- 确认系统能安装 Python 3.10
- 网络较差时重试
- 旧虚拟环境损坏时删除 `.venv` 后重建

### 首次启动很慢

- 启动时会下载模型与示例资源
- `CosyVoice`、`F5-TTS`、`E2-TTS`、`dots.tts` 首次初始化都偏慢
- `./start-linux.sh` 模式下可看 `/tmp/voice-pro.log`

### CUDA / cuDNN / `whisperX` 相关报错

- 用 `uv run voice-pro` 或 `uv run python start-voice.py` 启动，不要绕过启动器
- 启动器会补 `LD_LIBRARY_PATH`
- 启动器也会给 `ctranslate2` 补 `cuDNN 8` 兼容软链接

### 模型下载很慢

- 首次下载属于正常现象
- `dots.tts`、`CosyVoice` 权重体积较大
- 网络环境差时可多次重试，已下载文件会复用

### `espeak-ng` 缺失导致 `kokoro` 不工作

- 安装系统包 `espeak-ng`
- 确认命令 `espeak-ng --version` 可执行

## 当前仓库主命令

当前公开入口只保留：

```bash
uv sync
uv run voice-pro
uv run python start-voice.py
```

如果需要历史功能或旧平台支持，请回原始上游仓库或后续单独归档分支，不在当前主线维护范围内。
