import os
import sys
import platform

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import gradio as gr

from app.gradio_tts_voxcpm import *
from app.gradio_voice_celeb import *
from app.tts_help import render_helped_control
from src.config import UserConfig
from src.i18n.i18n import I18nAuto

i18n = I18nAuto()


def tts_voxcpm_tab(user_config: UserConfig):
    tts = GradioVoxCPM(user_config)
    voice = GradioCelebVoice(user_config)
    subtitle_exts = [".ass", ".ssa", ".srt", ".mpl2", ".tmp", ".vtt", ".microdvd", ".json"]
    system = platform.system()

    with gr.Row():
        with gr.Column(scale=4):
            with gr.Group():
                gr.HTML(f"<center><h4>{i18n('Voice')}</h4></center>")
                language_radio = gr.Radio(choices=voice.gradio_languages(), label=i18n("Language"), value="English")
                celeb_voice_dropdown = gr.Dropdown(label=i18n("Voice"), choices=voice.gradio_voices(), value=None)
                celeb_audio = gr.Audio(label="Reference Audio", sources=["upload", "microphone"], type="filepath", interactive=True)
                celeb_transcript = gr.Textbox(label=i18n("Transcript"), interactive=True, max_lines=12, lines=6, placeholder=i18n("Optional"))
                celeb_image = gr.Image(label="Photo", type="filepath", interactive=False, show_download_button=False)
        with gr.Column(scale=8):
            with gr.Group():
                gr.HTML(f"<center><h4>{i18n('Script')}</h4></center>")
                dubbing_file_in = gr.File(label=i18n("Subtitle File"), type="filepath", file_count="single", file_types=subtitle_exts)
                dubbing_text_in = gr.Textbox(
                    label=i18n("Source Text"),
                    interactive=True,
                    show_label=True,
                    max_lines=24,
                    show_copy_button=True,
                    placeholder=i18n("Placeholder for Source Text"),
                    lines=5,
                )
            with gr.Group():
                gr.HTML(f"<center><h4>{i18n('Synthesized voice')}</h4></center>")
                dubbing_audio = gr.Audio(label=i18n("Audio"), type="filepath", interactive=False)
                dubbing_file_out = gr.File(label=i18n("File"), type="filepath", file_count="single", interactive=False)
            with gr.Row():
                workspace_button = gr.Button(value=i18n("🗂️ Open workspace folder"), variant="secondary")
                temp_button = gr.Button(value=i18n("🗀 Open Temp folder"), variant="secondary")
        with gr.Column(scale=4):
            with gr.Group():
                gr.HTML(f"<center><h4>VoxCPM</h4></center>")
                mode_choice = render_helped_control(
                    "voxcpm",
                    "Mode",
                    lambda: gr.Dropdown(choices=tts.gradio_modes(), label="Mode", value=user_config.get("voxcpm_mode", "Voice Clone")),
                )
                voice_description = render_helped_control(
                    "voxcpm",
                    "Voice Description",
                    lambda: gr.Textbox(label="Voice Description", interactive=True, max_lines=6, lines=4, placeholder=i18n("Optional")),
                )
                cfg_value = render_helped_control(
                    "voxcpm",
                    "CFG Value",
                    lambda: gr.Slider(0.5, 4.0, value=user_config.get("voxcpm_cfg_value", 2.0), step=0.1, label="CFG Value", info="0.5 ~ 4.0"),
                )
                inference_timesteps = render_helped_control(
                    "voxcpm",
                    "Inference Steps",
                    lambda: gr.Slider(4, 20, value=user_config.get("voxcpm_inference_timesteps", 10), step=1, label="Inference Steps", info="4 ~ 20"),
                )
                normalize_text = render_helped_control(
                    "voxcpm",
                    "Normalize Text",
                    lambda: gr.Checkbox(label="Normalize Text", value=user_config.get("voxcpm_normalize_text", False)),
                )
                denoise_reference = render_helped_control(
                    "voxcpm",
                    "Denoise Reference",
                    lambda: gr.Checkbox(label="Denoise Reference", value=user_config.get("voxcpm_denoise_reference", False)),
                )
                audio_format_radio = render_helped_control(
                    "voxcpm",
                    "Audio Format",
                    lambda: gr.Radio(label=i18n("Audio Format"), choices=["wav", "flac", "mp3"], value=user_config.get("tts_audio_format", "mp3")),
                )
            with gr.Row():
                voxcpm_default_button = gr.ClearButton(value=i18n("Load Defaults"))
                dubbing_button = gr.Button(value=i18n("Synthesis"), variant="primary")

    dubbing_file_in.upload(tts.gradio_upload_file, inputs=[dubbing_file_in], outputs=[dubbing_text_in])
    workspace_button.click(tts.gradio_workspace_folder)
    temp_button.click(tts.gradio_temp_folder)

    language_radio.change(voice.gradio_change_language, inputs=[language_radio], outputs=[celeb_voice_dropdown])
    celeb_voice_dropdown.change(voice.gradio_change_voice, inputs=[celeb_voice_dropdown], outputs=[celeb_audio, celeb_transcript, celeb_image])
    celeb_audio.clear(voice.gradio_clear_voice, inputs=None, outputs=[celeb_transcript, celeb_image])

    voxcpm_default_button.click(
        tts.gradio_voxcpm_default,
        outputs=[mode_choice, voice_description, cfg_value, inference_timesteps, normalize_text, denoise_reference, audio_format_radio],
    )
    dubbing_button.click(
        tts.gradio_tts_dubbing_single,
        inputs=[
            dubbing_text_in,
            celeb_audio,
            celeb_transcript,
            mode_choice,
            voice_description,
            cfg_value,
            inference_timesteps,
            normalize_text,
            denoise_reference,
            audio_format_radio,
        ],
        outputs=[dubbing_audio, dubbing_file_out],
    )
