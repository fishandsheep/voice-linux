import platform

import gradio as gr

from src.config import UserConfig
from src.i18n.i18n import I18nAuto

from app.gradio_gulliver import GradioGulliver
from app.gradio_voice_celeb import GradioCelebVoice
from app.tts_help import render_helped_control

i18n = I18nAuto()


def gulliver_tab(user_config: UserConfig):
    gulliver = GradioGulliver(user_config)
    f5_reference_voice = GradioCelebVoice(user_config)
    voxcpm_reference_voice = GradioCelebVoice(user_config)
    index_reference_voice = GradioCelebVoice(user_config)
    system = platform.system()

    with gr.Row():
        with gr.Column(scale=3):
            with gr.Group():
                gr.HTML(f'<center><h4>{i18n("Upload media")}</h4></center>')
                media_file = gr.File(label=i18n("Upload File"), type="filepath", file_count="single", file_types=["audio", "video"])
                mic_audio = gr.Audio(label=i18n("Microphone Input"), sources=["microphone"], type="filepath", visible=system == "Windows")
                with gr.Group():
                    url_text = gr.Textbox(label=i18n("YouTube URL"), placeholder="https://youtu.be/abcdefgh...")
                    youtube_quality_radio = gr.Radio(label=i18n("YouTube Video Quality"), choices=["low", "good", "best"], value=user_config.get("video_quality", "good"))
                audio_format_radio = gr.Radio(label=i18n("Audio Format"), choices=["wav", "mp3"], value=user_config.get("upload_audio_format", "wav"))

            with gr.Row():
                clear_button = gr.ClearButton(value=i18n("Clear"))
                submit_button = gr.Button(value=i18n("Submit"), variant="primary")

            with gr.Group():
                gr.HTML(f'<center><h4>{i18n("Whisper subtitles")}</h4></center>')
                whisper_model_dropdown = gr.Dropdown(
                    label=i18n("Whisper Model"),
                    choices=gulliver.get_whisper_models(),
                    value=user_config.get("whisper_timestamped_model", "large-v3-turbo"),
                )
                whisper_language_dropdown = gr.Dropdown(
                    label=i18n("Media Language"),
                    choices=gulliver.get_whisper_languages(),
                    value=user_config.get("whisper_language", "english"),
                )
                denoise_level = gr.Slider(minimum=0, maximum=2, step=1, value=user_config.get("denoise_level", 0), label=i18n("Denoise Level"))
            with gr.Row():
                whisper_default_button = gr.ClearButton(value=i18n("Load Defaults"))
                whisper_button = gr.Button(value=i18n("Transcribe"), variant="primary")

        with gr.Column(scale=8):
            with gr.Row():
                with gr.Column():
                    with gr.Group():
                        gr.HTML(f'<center><h4>{i18n("Input Video")}</h4></center>')
                        input_video = gr.Video(label=i18n("Video"), interactive=False)
                        input_audio = gr.Audio(label=i18n("Audio"), type="filepath", interactive=False)
                        transcription_textbox = gr.Textbox(label=i18n("Subtitles"), interactive=True, show_label=True, max_lines=24, show_copy_button=True, placeholder=i18n("Placeholder for Source SRT"), lines=15)
                with gr.Column():
                    with gr.Group():
                        gr.HTML(f'<center><h4>{i18n("Output Video")}</h4></center>')
                        dubbing_progress = gr.HTML(visible=False)
                        dubbing_video = gr.Video(label=i18n("Video"), interactive=False)
                        dubbing_audio = gr.Audio(label=i18n("Audio"), type="filepath", interactive=False)
                        translation_textbox = gr.Textbox(label=i18n("Translated captions"), interactive=True, show_label=True, max_lines=24, show_copy_button=True, placeholder=i18n("Placeholder for Translated Text"), lines=15)
            dubbing_files = gr.File(label=i18n("Files"), type="filepath", file_count="multiple", interactive=False)
            with gr.Row():
                workspace_button = gr.Button(value=i18n("🗂️ Open workspace folder"), variant="secondary")
                temp_button = gr.Button(value=i18n("🗀 Open Temp folder"), variant="secondary")

        with gr.Column(scale=3):
            with gr.Group():
                gr.HTML(f'<center><h4>{i18n("Translation")}</h4></center>')
                source_language_dropdown = gr.Dropdown(label=i18n("Source Language"), choices=gulliver.gradio_translate_languages(), value=user_config.get("translate_source_language", "English"))
                translate_language_dropdown = gr.Dropdown(label=i18n("Translated Language"), choices=gulliver.gradio_translate_languages(), value=user_config.get("translate_target_language", "English"))
            with gr.Row():
                language_detection_button = gr.Button(value=i18n("Language Detection"))
                translate_button = gr.Button(value=i18n("Translate"), variant="primary")

            with gr.Group():
                gr.HTML(f'<center><h4>{i18n("Speech Generation")}</h4></center>')

            with gr.Tab(i18n("F5-TTS (Single)")):
                with gr.Group():
                    f5_language_radio = gr.Radio(choices=f5_reference_voice.gradio_f5_languages(), label=i18n("Language"), value="English")
                    f5_voice_dropdown = gr.Dropdown(label=i18n("Voice"), choices=f5_reference_voice.gradio_voices(), value=None)
                    f5_reference_audio = gr.Audio(label="Reference Audio", sources=["upload", "microphone"], type="filepath", interactive=True)
                    f5_reference_transcript = gr.Textbox(label=i18n("Transcript"), interactive=True, max_lines=12, lines=6, placeholder=i18n("Optional"))
                    f5_reference_image = gr.Image(label="Photo", type="filepath", interactive=False, show_download_button=False)
                    f5_model_choice = render_helped_control("f5", "Choose Model", lambda: gr.Dropdown(choices=gulliver.gradio_f5_available_models(), label="Choose Model", value="SWivid/F5-TTS_v1"))
                    f5_tts_speed = render_helped_control("f5", "Speech rate", lambda: gr.Slider(0.3, 2.0, value=1.0, step=0.1, label=i18n("Speech rate"), info="0.3 ~ 2.0"))
                    f5_audio_format = render_helped_control("f5", "Audio Format", lambda: gr.Radio(label=i18n("Audio Format"), choices=["wav", "flac", "mp3"], value=user_config.get("tts_audio_format", "mp3")))
                with gr.Row():
                    f5_default_button = gr.ClearButton(value=i18n("Load Defaults"))
                    f5_dubbing_button = gr.Button(value=i18n("Synthesis"), variant="primary")

            with gr.Tab("VoxCPM"):
                with gr.Group():
                    voxcpm_language_radio = gr.Radio(choices=voxcpm_reference_voice.gradio_languages(), label=i18n("Language"), value="English")
                    voxcpm_voice_dropdown = gr.Dropdown(label=i18n("Voice"), choices=voxcpm_reference_voice.gradio_voices(), value=None)
                    voxcpm_reference_audio = gr.Audio(label="Reference Audio", sources=["upload", "microphone"], type="filepath", interactive=True)
                    voxcpm_reference_transcript = gr.Textbox(label=i18n("Transcript"), interactive=True, max_lines=12, lines=6, placeholder=i18n("Optional"))
                    voxcpm_reference_image = gr.Image(label="Photo", type="filepath", interactive=False, show_download_button=False)
                    voxcpm_mode_choice = render_helped_control("voxcpm", "Mode", lambda: gr.Dropdown(choices=gulliver.gradio_voxcpm_modes(), label="Mode", value=user_config.get("voxcpm_mode", "Voice Clone")))
                    voxcpm_voice_description = render_helped_control("voxcpm", "Voice Description", lambda: gr.Textbox(label="Voice Description", interactive=True, max_lines=6, lines=4, placeholder=i18n("Optional")))
                    voxcpm_cfg_value = render_helped_control("voxcpm", "CFG Value", lambda: gr.Slider(0.5, 4.0, value=user_config.get("voxcpm_cfg_value", 2.0), step=0.1, label="CFG Value", info="0.5 ~ 4.0"))
                    voxcpm_inference_timesteps = render_helped_control("voxcpm", "Inference Steps", lambda: gr.Slider(4, 20, value=user_config.get("voxcpm_inference_timesteps", 10), step=1, label="Inference Steps", info="4 ~ 20"))
                    voxcpm_normalize_text = render_helped_control("voxcpm", "Normalize Text", lambda: gr.Checkbox(label="Normalize Text", value=user_config.get("voxcpm_normalize_text", False)))
                    voxcpm_denoise_reference = render_helped_control("voxcpm", "Denoise Reference", lambda: gr.Checkbox(label="Denoise Reference", value=user_config.get("voxcpm_denoise_reference", False)))
                    voxcpm_audio_format = render_helped_control("voxcpm", "Audio Format", lambda: gr.Radio(label=i18n("Audio Format"), choices=["wav", "flac", "mp3"], value=user_config.get("tts_audio_format", "mp3")))
                with gr.Row():
                    voxcpm_default_button = gr.ClearButton(value=i18n("Load Defaults"))
                    voxcpm_dubbing_button = gr.Button(value=i18n("Synthesis"), variant="primary")

            with gr.Tab("IndexTTS"):
                with gr.Group():
                    index_language_radio = gr.Radio(choices=index_reference_voice.gradio_languages(), label=i18n("Language"), value="English")
                    index_voice_dropdown = gr.Dropdown(label=i18n("Voice"), choices=index_reference_voice.gradio_voices(), value=None)
                    index_reference_audio = gr.Audio(label="Reference Audio", sources=["upload", "microphone"], type="filepath", interactive=True)
                    index_reference_transcript = gr.Textbox(label=i18n("Transcript"), interactive=True, max_lines=12, lines=6, placeholder=i18n("Optional"))
                    index_reference_image = gr.Image(label="Photo", type="filepath", interactive=False, show_download_button=False)
                    index_emo_audio_prompt = render_helped_control("index_tts", "Emotion Reference Audio", lambda: gr.Audio(label="Emotion Reference Audio", sources=["upload", "microphone"], type="filepath", interactive=True))
                    index_enable_emo_audio = render_helped_control("index_tts", "Enable Emotion Audio", lambda: gr.Checkbox(label="Enable Emotion Audio", value=user_config.get("index_tts_enable_emo_audio", False)))
                    index_emo_alpha = render_helped_control("index_tts", "Emotion Strength", lambda: gr.Slider(0.0, 1.0, value=user_config.get("index_tts_emo_alpha", 1.0), step=0.05, label="Emotion Strength", info="0.0 ~ 1.0"))
                    index_audio_format = render_helped_control("index_tts", "Audio Format", lambda: gr.Radio(label=i18n("Audio Format"), choices=["wav", "flac", "mp3"], value=user_config.get("tts_audio_format", "mp3")))
                with gr.Row():
                    index_default_button = gr.ClearButton(value=i18n("Load Defaults"))
                    index_dubbing_button = gr.Button(value=i18n("Synthesis"), variant="primary")

    submit_button.click(gulliver.gradio_upload_source, inputs=[media_file, mic_audio, url_text, youtube_quality_radio, audio_format_radio], outputs=[input_video, input_audio, dubbing_files])
    clear_button.add([input_video, input_audio, transcription_textbox, dubbing_video, dubbing_audio, translation_textbox, dubbing_progress])

    whisper_default_button.click(gulliver.gradio_whisper_default, outputs=[whisper_model_dropdown, whisper_language_dropdown, denoise_level])
    whisper_button.click(gulliver.gradio_whisper, inputs=[whisper_model_dropdown, whisper_language_dropdown, denoise_level], outputs=[input_video, input_audio, transcription_textbox, dubbing_files])

    workspace_button.click(gulliver.gradio_workspace_folder)
    temp_button.click(gulliver.gradio_temp_folder)

    language_detection_button.click(gulliver.gradio_language_detection, inputs=[transcription_textbox], outputs=[source_language_dropdown])
    translate_button.click(gulliver.gradio_translate, inputs=[source_language_dropdown, transcription_textbox, translate_language_dropdown], outputs=[dubbing_video, dubbing_audio, translation_textbox, dubbing_files, dubbing_progress])

    f5_language_radio.change(f5_reference_voice.gradio_change_language, inputs=[f5_language_radio], outputs=[f5_voice_dropdown])
    f5_voice_dropdown.change(f5_reference_voice.gradio_change_voice, inputs=[f5_voice_dropdown], outputs=[f5_reference_audio, f5_reference_transcript, f5_reference_image])
    f5_reference_audio.clear(f5_reference_voice.gradio_clear_voice, inputs=None, outputs=[f5_reference_transcript, f5_reference_image])
    f5_default_button.click(gulliver.gradio_f5_default, outputs=[f5_model_choice, f5_tts_speed, f5_audio_format])
    f5_dubbing_button.click(gulliver.gradio_f5_dubbing_single, inputs=[translation_textbox, f5_voice_dropdown, f5_reference_audio, f5_reference_transcript, f5_model_choice, f5_tts_speed, f5_audio_format], outputs=[dubbing_video, dubbing_audio, dubbing_files, dubbing_progress])

    voxcpm_language_radio.change(voxcpm_reference_voice.gradio_change_language, inputs=[voxcpm_language_radio], outputs=[voxcpm_voice_dropdown])
    voxcpm_voice_dropdown.change(voxcpm_reference_voice.gradio_change_voice, inputs=[voxcpm_voice_dropdown], outputs=[voxcpm_reference_audio, voxcpm_reference_transcript, voxcpm_reference_image])
    voxcpm_reference_audio.clear(voxcpm_reference_voice.gradio_clear_voice, inputs=None, outputs=[voxcpm_reference_transcript, voxcpm_reference_image])
    voxcpm_default_button.click(gulliver.gradio_voxcpm_default, outputs=[voxcpm_mode_choice, voxcpm_voice_description, voxcpm_cfg_value, voxcpm_inference_timesteps, voxcpm_normalize_text, voxcpm_denoise_reference, voxcpm_audio_format])
    voxcpm_dubbing_button.click(gulliver.gradio_voxcpm_dubbing, inputs=[translation_textbox, voxcpm_voice_dropdown, voxcpm_reference_audio, voxcpm_reference_transcript, voxcpm_mode_choice, voxcpm_voice_description, voxcpm_cfg_value, voxcpm_inference_timesteps, voxcpm_normalize_text, voxcpm_denoise_reference, voxcpm_audio_format], outputs=[dubbing_video, dubbing_audio, dubbing_files, dubbing_progress])

    index_language_radio.change(index_reference_voice.gradio_change_language, inputs=[index_language_radio], outputs=[index_voice_dropdown])
    index_voice_dropdown.change(index_reference_voice.gradio_change_voice, inputs=[index_voice_dropdown], outputs=[index_reference_audio, index_reference_transcript, index_reference_image])
    index_reference_audio.clear(index_reference_voice.gradio_clear_voice, inputs=None, outputs=[index_reference_transcript, index_reference_image])
    index_default_button.click(gulliver.gradio_index_default, outputs=[index_enable_emo_audio, index_emo_alpha, index_audio_format])
    index_dubbing_button.click(gulliver.gradio_index_dubbing, inputs=[translation_textbox, index_voice_dropdown, index_reference_audio, index_reference_transcript, index_emo_audio_prompt, index_enable_emo_audio, index_emo_alpha, index_audio_format], outputs=[dubbing_video, dubbing_audio, dubbing_files, dubbing_progress])
