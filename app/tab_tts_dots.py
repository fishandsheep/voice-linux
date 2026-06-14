import os
import sys
import platform

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import gradio as gr

from app.gradio_tts_dots import *
from app.gradio_voice_celeb import *
from src.config import UserConfig
from src.i18n.i18n import I18nAuto

i18n = I18nAuto()


def tts_dots_tab(user_config: UserConfig):
    tts = GradioDotsTTS(user_config)
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
                gr.HTML(f"<center><h4>dots.tts</h4></center>")
                model_choice = gr.Dropdown(choices=tts.gradio_available_models(), label="Model", value=user_config.get("dots_model", "rednote-hilab/dots.tts-mf"))
                language_tag = gr.Dropdown(choices=tts.gradio_language_tags(), label="Language Tag", value=user_config.get("dots_language", "Auto Detect"))
                num_steps = gr.Slider(4, 32, value=user_config.get("dots_num_steps", 4), step=1, label="Num Steps", info="4 ~ 32")
                guidance_scale = gr.Slider(0.5, 2.5, value=user_config.get("dots_guidance_scale", 1.2), step=0.1, label="Guidance Scale", info="0.5 ~ 2.5")
                seed = gr.Number(value=user_config.get("dots_seed", 42), precision=0, label="Seed")
                normalize_text = gr.Checkbox(label="Normalize Text", value=user_config.get("dots_normalize_text", False))
                audio_format_radio = gr.Radio(label=i18n("Audio Format"), choices=["wav", "flac", "mp3"], value=user_config.get("audio_format", "mp3"))
            with gr.Row():
                dots_default_button = gr.ClearButton(value=i18n("Load Defaults"))
                dubbing_button = gr.Button(value=i18n("Synthesis"), variant="primary")

    dubbing_file_in.upload(tts.gradio_upload_file, inputs=[dubbing_file_in], outputs=[dubbing_text_in])
    workspace_button.click(tts.gradio_workspace_folder)
    temp_button.click(tts.gradio_temp_folder)

    language_radio.change(voice.gradio_change_language, inputs=[language_radio], outputs=[celeb_voice_dropdown])
    celeb_voice_dropdown.change(voice.gradio_change_voice, inputs=[celeb_voice_dropdown], outputs=[celeb_audio, celeb_transcript, celeb_image])
    celeb_audio.clear(voice.gradio_clear_voice, inputs=None, outputs=[celeb_transcript, celeb_image])

    model_choice.change(tts.gradio_recommended_steps, inputs=[model_choice], outputs=[num_steps])
    dots_default_button.click(
        tts.gradio_dots_default,
        outputs=[model_choice, language_tag, num_steps, guidance_scale, seed, normalize_text, audio_format_radio],
    )
    dubbing_button.click(
        tts.gradio_tts_dubbing_single,
        inputs=[
            dubbing_text_in,
            celeb_audio,
            celeb_transcript,
            model_choice,
            language_tag,
            num_steps,
            guidance_scale,
            seed,
            normalize_text,
            audio_format_radio,
        ],
        outputs=[dubbing_audio, dubbing_file_out],
    )
