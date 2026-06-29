# voice-simple

`voice-simple` for Linux NVIDIA. Focus now narrow:

- ASR: `whisper-timestamped`
- TTS: `F5-TTS (Single)`, `VoxCPM`, `IndexTTS`
- Pages: `Dubbing Studio`, `Whisper subtitles`, `Translation`, `Speech Generation`

## Requirements

- Linux x86_64
- Python `3.10`
- NVIDIA GPU + CUDA runtime usable by `torch==2.8.0+cu128`
- `ffmpeg`
- `uv`

## Install

```bash
uv sync
```

First launch:

```bash
uv run voice-simple
```

or

```bash
uv run python voice_simple_launcher.py
```

## First Download

Launcher preloads only:

- `demucs`
- celebrity/reference sample pack used by retained TTS pages

Note:

- startup log may still show `ABUS-AI/CosyVoice/celebrities30s.zip`
- this is reference sample pack source name, not old `CosyVoice` TTS page/runtime being enabled again

On demand:

- `whisper-timestamped` downloads selected ASR model
- `F5-TTS` downloads needed F5 checkpoint assets
- `VoxCPM` downloads local snapshot if missing
- `IndexTTS` bootstraps own repo/env/model if missing

## Pages

### Dubbing Studio

Pipeline in one page:

1. Upload media
2. Transcribe with `whisper-timestamped`
3. Translate
4. Generate speech with one of 3 TTS engines

Notes:

- ASR engine no longer selectable
- Whisper model choices only: `large`, `large-v3-turbo`, `turbo`
- Upload audio extraction format only: `wav`, `mp3`
- Each retained TTS parameter block has clickable `?` help, desktop and mobile both usable

### Whisper subtitles

Standalone subtitle extraction page.

- ASR fixed to `whisper-timestamped`
- Whisper model choices only: `large`, `large-v3-turbo`, `turbo`
- `Compute Type` removed
- Upload audio extraction format only: `wav`, `mp3`

### Translation

Text or subtitle translation page.

### Speech Generation

Only 3 tabs remain:

- `F5-TTS (Single)`
- `VoxCPM`
- `IndexTTS`

TTS parameter help:

- every retained parameter block has clickable `?`
- click opens fixed help popup with dim backdrop
- click backdrop or `×` closes popup

## Engine Notes

### whisper-timestamped

- Used by both `Whisper subtitles` and `Dubbing Studio`
- Default model: `large-v3-turbo`
- Old configs pointing to unsupported Whisper model auto-fallback to `large-v3-turbo`

### F5-TTS (Single)

- Single-speaker voice clone
- Available model list comes only from bundled F5 config
- `SWivid/E2-TTS` no longer exposed

### VoxCPM

- Supports `Voice Clone`, `Ultimate Clone`, `Voice Design`
- Best when reference audio clean and transcript accurate

### IndexTTS

- Optional emotion reference audio
- Maintains separate sidecar environment under `model/index-tts/`

## Config

User config file:

- [app/config-user.json5](/home/zdx/code/voice-linux/app/config-user.json5)

Active keys:

- `upload_audio_format`
- `tts_audio_format`
- `whisper_timestamped_model`
- `whisper_language`
- `denoise_level`
- `translate_source_language`
- `translate_target_language`
- `voxcpm_*`
- `index_tts_*`

Compatibility:

- old `audio_format` still read once as fallback
- old removed-engine keys can stay in existing file, but app no longer uses them

## Smoke Checks

```bash
uv run python -c "from app.abus_app_voice import create_ui"
uv run python -c "from app.gradio_asr import GradioASR; from app.gradio_gulliver import GradioGulliver"
```

## Repo Scope

Current repo keeps only active ASR/TTS paths used by app surface above.
