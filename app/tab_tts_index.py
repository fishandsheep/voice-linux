import os
import sys
import platform

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import gradio as gr

from app.gradio_tts_index import *
from app.gradio_voice_celeb import *
from app.tts_help import render_helped_control
from src.config import UserConfig
from src.i18n.i18n import I18nAuto

i18n = I18nAuto()


def tts_index_tab(user_config: UserConfig):
    tts = GradioIndexTTS(user_config)
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
                gr.HTML("<center><h4>IndexTTS</h4></center>")
                emo_audio_prompt = render_helped_control(
                    "index_tts",
                    "Emotion Reference Audio",
                    lambda: gr.Audio(
                        label="Emotion Reference Audio",
                        sources=["upload", "microphone"],
                        type="filepath",
                        interactive=True,
                    ),
                )
                enable_emo_audio = render_helped_control(
                    "index_tts",
                    "Enable Emotion Audio",
                    lambda: gr.Checkbox(
                        label="Enable Emotion Audio",
                        value=user_config.get("index_tts_enable_emo_audio", False),
                    ),
                )
                emo_alpha = render_helped_control(
                    "index_tts",
                    "Emotion Strength",
                    lambda: gr.Slider(
                        0.0,
                        1.0,
                        value=user_config.get("index_tts_emo_alpha", 1.0),
                        step=0.05,
                        label="Emotion Strength",
                        info="0.0 ~ 1.0",
                    ),
                )
                audio_format_radio = render_helped_control(
                    "index_tts",
                    "Audio Format",
                    lambda: gr.Radio(label=i18n("Audio Format"), choices=["wav", "flac", "mp3"], value=user_config.get("tts_audio_format", "mp3")),
                )
            with gr.Row():
                index_default_button = gr.ClearButton(value=i18n("Load Defaults"))
                dubbing_button = gr.Button(value=i18n("Synthesis"), variant="primary")

    dubbing_file_in.upload(tts.gradio_upload_file, inputs=[dubbing_file_in], outputs=[dubbing_text_in])
    workspace_button.click(tts.gradio_workspace_folder)
    temp_button.click(tts.gradio_temp_folder)

    language_radio.change(voice.gradio_change_language, inputs=[language_radio], outputs=[celeb_voice_dropdown])
    celeb_voice_dropdown.change(voice.gradio_change_voice, inputs=[celeb_voice_dropdown], outputs=[celeb_audio, celeb_transcript, celeb_image])
    celeb_audio.clear(voice.gradio_clear_voice, inputs=None, outputs=[celeb_transcript, celeb_image])

    index_default_button.click(
        tts.gradio_index_default,
        outputs=[enable_emo_audio, emo_alpha, audio_format_radio],
    )
    dubbing_button.click(
        tts.gradio_tts_dubbing_single,
        inputs=[
            dubbing_text_in,
            celeb_audio,
            celeb_transcript,
            emo_audio_prompt,
            enable_emo_audio,
            emo_alpha,
            audio_format_radio,
        ],
        outputs=[dubbing_audio, dubbing_file_out],
    )
