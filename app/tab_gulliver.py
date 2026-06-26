import os
import sys
import platform

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)


import gradio as gr
from src.config import UserConfig

import src.ui as ui
from src.i18n.i18n import I18nAuto
i18n = I18nAuto()


from app.gradio_gulliver import *
from app.gradio_voice_celeb import *
from app.gradio_voice_ms import *
from app.gradio_voice_kokoro import *


def gulliver_tab(user_config: UserConfig):
    gulliver = GradioGulliver(user_config)
    
    ms_voice = GradioMSVoice(user_config)
    ms_voice.selected_language = user_config.get("ms_language", "English")
    
    f5_reference_voice = GradioCelebVoice(user_config)
    cosy_reference_voice = GradioCelebVoice(user_config)
    dots_reference_voice = GradioCelebVoice(user_config)
    voxcpm_reference_voice = GradioCelebVoice(user_config)
    index_reference_voice = GradioCelebVoice(user_config)
    kokoro_voice = GradioKokoroVoice(user_config)    
    
    system = platform.system()
    
    with gr.Row():
        with gr.Column(scale=3):
            with gr.Group():
                gr.HTML(f'<center><h4>{i18n("Upload media")}</h4></center>')
                media_file = gr.File(label=i18n("Upload File"), type="filepath", file_count="single", file_types=['audio', 'video']) 
                mic_audio = gr.Audio(label=i18n("Microphone Input"), sources=["microphone"], type="filepath", visible=True if system == "Windows" else False) 
                with gr.Group():
                    url_text = gr.Textbox(label=i18n("YouTube URL"), placeholder="https://youtu.be/abcdefgh...")
                    youtube_quality_radio = gr.Radio(label=i18n("YouTube Video Quality"), choices=["low", "good", "best"], value=user_config.get("video_quality", "good"))
                audio_format_radio = gr.Radio(label=i18n("Audio Format"), choices=["wav", "flac", "mp3"], value=user_config.get("audio_format", "flac"))
            
            with gr.Row():
                clear_button = gr.ClearButton(value=i18n("Clear"))
                submit_button = gr.Button(value=i18n("Submit"), variant="primary")

            with gr.Group():
                gr.HTML(f'<center><h4>{i18n("Whisper subtitles")}</h4></center>')
                supported_asr_engines = gulliver.get_asr_engines()
                asr_engine = user_config.get("asr_engine", 'whisper-timestamped')
                if asr_engine not in supported_asr_engines:
                    asr_engine = 'whisper-timestamped'
                asr_engine_radio = gr.Radio(
                    label=i18n("Whisper Engine"),
                    choices=gulliver.get_asr_engines(),
                    value=asr_engine,
                    info=gulliver.get_dubbing_asr_note(),
                )

                whisper_model_name = user_config.get(f"{asr_engine.replace('-', '_')}_model", 'large')
                whisper_model_dropdown = gr.Dropdown(label=i18n("Whisper Model"), choices=gulliver.get_whisper_models(), value=whisper_model_name, info=i18n(""))
                whisper_language_dropdown = gr.Dropdown(label=i18n("Media Language"), choices=gulliver.get_whisper_languages(), value=user_config.get("whisper_language", 'english'), info=i18n(""))
                compute_type_dropdown = gr.Dropdown(
                    label=i18n("Compute Type"),
                    choices=gulliver.get_whisper_compute_types(),
                    value=user_config.get("whisper_compute_type", 'default'),
                    visible=False,
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
                        transcription_textbox = gr.Textbox(label=i18n("Subtitles"), interactive=True, show_label=True, max_lines=24, show_copy_button=True,
                                                placeholder=i18n("Placeholder for Source SRT"), lines=15)
                with gr.Column():
                    with gr.Group():
                        gr.HTML(f'<center><h4>{i18n("Output Video")}</h4></center>')    
                        dubbing_progress = gr.HTML(visible=False)
                        dubbing_video = gr.Video(label=i18n("Video"), interactive=False)
                        dubbing_audio = gr.Audio(label=i18n("Audio"), type="filepath", interactive=False)
                        translation_textbox = gr.Textbox(label=i18n("Translated captions"), interactive=True, show_label=True, max_lines=24, show_copy_button=True,
                                                placeholder=i18n("Placeholder for Translated Text"), lines=15)
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

            tab_name = i18n('Azure-TTS') if azure_text_api_working() else i18n('Edge-TTS')
            with gr.Tab(tab_name):     
                with gr.Group():                            
                    ms_language_dropdown = gr.Dropdown(label=i18n("Language"), choices=ms_voice.gradio_languages(), value=ms_voice.selected_language)                            
                    ms_voice_dropdown = gr.Dropdown(label=i18n("Voice"), choices=ms_voice.gradio_voices(), value=user_config.get("ms_voice", "UNITED STATES-Ana-Female"))                    
                    ms_sample_audio = gr.Audio(label="Sample Audio", type="filepath", 
                                            editable=False, interactive=False, show_download_button=False)
                    edge_tts_pitch = gr.Slider(-400, 400, value=user_config.get("edge_tts_pitch", 0), step = 10, label=i18n("Pitch(Hz)"), info="-400Hz ~ +400Hz")
                    edge_tts_rate = gr.Slider(-100, 200, value=user_config.get("edge_tts_rate", 0), step = 1, label=i18n("Speech rate"), info="-100% ~ +200%")
                    edge_tts_volume = gr.Slider(-100, 100, value=user_config.get("edge_tts_volume", 0), step=1, label=i18n("Speech volume"), info="-100% ~ +100%")
                with gr.Row():
                    edge_default_button = gr.ClearButton(value=i18n("Load Defaults"))
                    edge_dubbing_button = gr.Button(value=i18n("Synthesis"), variant="primary")

            with gr.Tab(i18n('F5-TTS')):          
                with gr.Group():                            
                    f5_language_radio = gr.Radio(choices=f5_reference_voice.gradio_f5_languages(), label=i18n("Language"), value="English")
                    f5_voice_dropdown = gr.Dropdown(label=i18n("Voice"), choices=f5_reference_voice.gradio_voices(), value=None)                                                    
                    f5_reference_audio = gr.Audio(label="Reference Audio", sources=['upload', 'microphone'], type="filepath", interactive=True)
                    f5_reference_transcript = gr.Textbox(label=i18n("Transcript"), interactive=True, max_lines=12, lines=6,
                                                placeholder=i18n("Optional"))
                    f5_reference_image = gr.Image(label="Photo", type="filepath", interactive=False, show_download_button=False)       
                    f5_model_choice = gr.Dropdown(choices=gulliver.gradio_f5_available_models(), label="Choose Model", value="SWivid/F5-TTS_v1")
                    f5_tts_speed = gr.Slider(0.3, 2.0, value=1.0, step = 0.1, label=i18n("Speech rate"), info="0.3 ~ 2.0")
                with gr.Row():
                    f5_default_button = gr.ClearButton(value=i18n("Load Defaults")) 
                    f5_dubbing_button = gr.Button(value=i18n("Synthesis"), variant="primary")  
                                    
                    
            with gr.Tab(i18n('CosyVoice')):          
                with gr.Group():                            
                    cosy_language_radio = gr.Radio(choices=cosy_reference_voice.gradio_languages(), label=i18n("Language"), value="English")
                    cosy_voice_dropdown = gr.Dropdown(label=i18n("Voice"), choices=cosy_reference_voice.gradio_voices(), value=None)                                                    
                    cosy_reference_audio = gr.Audio(label="Reference Audio", sources=['upload', 'microphone'], type="filepath", interactive=True)
                    cosy_reference_transcript = gr.Textbox(label=i18n("Transcript"), interactive=True, max_lines=12, lines=6,
                                                placeholder=i18n("Required"))
                    cosy_reference_image = gr.Image(label="Photo", type="filepath", interactive=False, show_download_button=False)   

                    cosy_mode_choice = gr.Radio(choices=["Zero-Shot", "Cross-Lingual", "Instruct"], label="Inference Mode", value="Zero-Shot")
                    cosy_tts_speed = gr.Slider(0.3, 2.0, value=1.0, step = 0.1, label=i18n("Speech rate"), info="0.3 ~ 2.0")
                with gr.Row():
                    cosy_default_button = gr.ClearButton(value=i18n("Load Defaults")) 
                    cosy_dubbing_button = gr.Button(value=i18n("Synthesis"), variant="primary")  
                    
                    
            with gr.Tab(i18n('kokoro')):          
                with gr.Group():   
                    kokoro_language_dropdown = gr.Dropdown(label=i18n("Language"), choices=kokoro_voice.gradio_languages(), value=kokoro_voice.selected_language)
                    kokoro_voice_dropdown = gr.Dropdown(label=i18n("Voice"), choices=kokoro_voice.gradio_voices(), value=user_config.get("kokoro_voice", "🚺 Heart ❤️"))
                    kokoro_sample_audio = gr.Audio(label="Sample Audio", type="filepath", 
                                            editable=False, interactive=False, show_download_button=False)
                    kokoro_transcript = gr.Textbox(label=i18n("Transcript"), interactive=False, max_lines=6, lines=3,
                                              placeholder=i18n("Optional"))    
                    kokoro_tts_speed = gr.Slider(0.3, 2.0, value=1.0, step = 0.1, label=i18n("Speech rate"), info="0.3 ~ 2.0")                    
                with gr.Row():
                    kokoro_default_button = gr.ClearButton(value=i18n("Load Defaults")) 
                    kokoro_dubbing_button = gr.Button(value=i18n("Synthesis"), variant="primary")                          
            
            with gr.Tab("dots.tts"):
                with gr.Group():
                    dots_language_radio = gr.Radio(choices=dots_reference_voice.gradio_languages(), label=i18n("Language"), value="English")
                    dots_voice_dropdown = gr.Dropdown(label=i18n("Voice"), choices=dots_reference_voice.gradio_voices(), value=None)
                    dots_reference_audio = gr.Audio(label="Reference Audio", sources=['upload', 'microphone'], type="filepath", interactive=True)
                    dots_reference_transcript = gr.Textbox(label=i18n("Transcript"), interactive=True, max_lines=12, lines=6, placeholder=i18n("Optional"))
                    dots_reference_image = gr.Image(label="Photo", type="filepath", interactive=False, show_download_button=False)
                    dots_model_choice = gr.Dropdown(choices=gulliver.gradio_dots_available_models(), label="Model", value=user_config.get("dots_model", "rednote-hilab/dots.tts-mf"))
                    dots_language_tag = gr.Dropdown(choices=gulliver.gradio_dots_language_tags(), label="Language Tag", value=user_config.get("dots_language", "Auto Detect"))
                    dots_num_steps = gr.Slider(4, 32, value=user_config.get("dots_num_steps", 4), step=1, label="Num Steps", info="4 ~ 32")
                    dots_guidance_scale = gr.Slider(0.5, 2.5, value=user_config.get("dots_guidance_scale", 1.2), step=0.1, label="Guidance Scale", info="0.5 ~ 2.5")
                    dots_seed = gr.Number(value=user_config.get("dots_seed", 42), precision=0, label="Seed")
                    dots_normalize_text = gr.Checkbox(label="Normalize Text", value=user_config.get("dots_normalize_text", False))
                with gr.Row():
                    dots_default_button = gr.ClearButton(value=i18n("Load Defaults"))
                    dots_dubbing_button = gr.Button(value=i18n("Synthesis"), variant="primary")

            with gr.Tab("VoxCPM"):
                with gr.Group():
                    voxcpm_language_radio = gr.Radio(choices=voxcpm_reference_voice.gradio_languages(), label=i18n("Language"), value="English")
                    voxcpm_voice_dropdown = gr.Dropdown(label=i18n("Voice"), choices=voxcpm_reference_voice.gradio_voices(), value=None)
                    voxcpm_reference_audio = gr.Audio(label="Reference Audio", sources=['upload', 'microphone'], type="filepath", interactive=True)
                    voxcpm_reference_transcript = gr.Textbox(label=i18n("Transcript"), interactive=True, max_lines=12, lines=6, placeholder=i18n("Optional"))
                    voxcpm_reference_image = gr.Image(label="Photo", type="filepath", interactive=False, show_download_button=False)
                    voxcpm_mode_choice = gr.Dropdown(choices=gulliver.gradio_voxcpm_modes(), label="Mode", value=user_config.get("voxcpm_mode", "Voice Clone"))
                    voxcpm_voice_description = gr.Textbox(label="Voice Description", interactive=True, max_lines=6, lines=4, placeholder=i18n("Optional"))
                    voxcpm_cfg_value = gr.Slider(0.5, 4.0, value=user_config.get("voxcpm_cfg_value", 2.0), step=0.1, label="CFG Value", info="0.5 ~ 4.0")
                    voxcpm_inference_timesteps = gr.Slider(4, 20, value=user_config.get("voxcpm_inference_timesteps", 10), step=1, label="Inference Steps", info="4 ~ 20")
                    voxcpm_normalize_text = gr.Checkbox(label="Normalize Text", value=user_config.get("voxcpm_normalize_text", False))
                    voxcpm_denoise_reference = gr.Checkbox(label="Denoise Reference", value=user_config.get("voxcpm_denoise_reference", False))
                with gr.Row():
                    voxcpm_default_button = gr.ClearButton(value=i18n("Load Defaults"))
                    voxcpm_dubbing_button = gr.Button(value=i18n("Synthesis"), variant="primary")

            with gr.Tab("IndexTTS"):
                with gr.Group():
                    index_language_radio = gr.Radio(choices=index_reference_voice.gradio_languages(), label=i18n("Language"), value="English")
                    index_voice_dropdown = gr.Dropdown(label=i18n("Voice"), choices=index_reference_voice.gradio_voices(), value=None)
                    index_reference_audio = gr.Audio(label="Reference Audio", sources=['upload', 'microphone'], type="filepath", interactive=True)
                    index_reference_transcript = gr.Textbox(label=i18n("Transcript"), interactive=True, max_lines=12, lines=6, placeholder=i18n("Optional"))
                    index_reference_image = gr.Image(label="Photo", type="filepath", interactive=False, show_download_button=False)
                    index_emo_audio_prompt = gr.Audio(label="Emotion Reference Audio", sources=['upload', 'microphone'], type="filepath", interactive=True)
                    index_enable_emo_audio = gr.Checkbox(label="Enable Emotion Audio", value=user_config.get("index_tts_enable_emo_audio", False))
                    index_emo_alpha = gr.Slider(0.0, 1.0, value=user_config.get("index_tts_emo_alpha", 1.0), step=0.05, label="Emotion Strength", info="0.0 ~ 1.0")
                with gr.Row():
                    index_default_button = gr.ClearButton(value=i18n("Load Defaults"))
                    index_dubbing_button = gr.Button(value=i18n("Synthesis"), variant="primary")
                
    # Media Upload                        
    submit_button.click(gulliver.gradio_upload_source,
                        inputs=[media_file, mic_audio, url_text, youtube_quality_radio, audio_format_radio],
                        outputs=[input_video, input_audio, dubbing_files])
    clear_button.add([input_video, input_audio, transcription_textbox, dubbing_video, dubbing_audio, translation_textbox, dubbing_progress])

    
    # Whisper Subtitle
    asr_engine_radio.change(gulliver.update_whisper_models,
                            inputs=[asr_engine_radio],
                            outputs=[whisper_model_dropdown])    
    whisper_default_button.click(gulliver.gradio_whisper_default,
                    outputs=[whisper_model_dropdown, whisper_language_dropdown, compute_type_dropdown, denoise_level])
    whisper_button.click(gulliver.gradio_whisper, 
                            inputs=[asr_engine_radio, whisper_model_dropdown, whisper_language_dropdown, compute_type_dropdown, denoise_level], 
                            outputs=[input_video, input_audio, transcription_textbox, dubbing_files])
    
    # Folder
    workspace_button.click(gulliver.gradio_workspace_folder)
    temp_button.click(gulliver.gradio_temp_folder)


    # Translate
    language_detection_button.click(gulliver.gradio_language_detection,
                             inputs=[transcription_textbox],
                             outputs=[source_language_dropdown])
    translate_button.click(gulliver.gradio_translate,
                              inputs=[source_language_dropdown, transcription_textbox, translate_language_dropdown],
                              outputs=[dubbing_video, dubbing_audio, translation_textbox, dubbing_files, dubbing_progress])

   
    # Edge-TTS or Azure-TTS   
    ms_language_dropdown.change(ms_voice.gradio_change_language,
                                inputs=[ms_language_dropdown],
                                outputs=[ms_voice_dropdown])   
    
    ms_voice_dropdown.change(ms_voice.gradio_change_voice,
                            inputs=[ms_voice_dropdown],
                            outputs=[ms_sample_audio])       
    
    edge_default_button.click(gulliver.gradio_edge_default,
                    outputs=[edge_tts_pitch, edge_tts_rate, edge_tts_volume])   
      
    edge_dubbing_button.click(gulliver.gradio_edge_dubbing, 
                inputs=[
                        translation_textbox, 
                        ms_voice_dropdown, 
                        edge_tts_pitch, edge_tts_rate, edge_tts_volume, audio_format_radio], 
                outputs=[dubbing_video, dubbing_audio, dubbing_files, dubbing_progress]) 
                  
    # F5-TTS
    f5_language_radio.change(f5_reference_voice.gradio_change_language,
                                inputs=[f5_language_radio],
                                outputs=[f5_voice_dropdown])        
    
    f5_voice_dropdown.change(f5_reference_voice.gradio_change_voice,
                        inputs=[f5_voice_dropdown],
                        outputs=[f5_reference_audio, f5_reference_transcript, f5_reference_image])
    f5_reference_audio.clear(f5_reference_voice.gradio_clear_voice,
                      inputs=None,
                      outputs=[f5_reference_transcript, f5_reference_image])    
    
    f5_default_button.click(gulliver.gradio_f5_default,
                    outputs=[f5_model_choice, f5_tts_speed])     
        
    f5_dubbing_button.click(gulliver.gradio_f5_dubbing_single, 
            inputs=[
                    translation_textbox, 
                    f5_voice_dropdown, f5_reference_audio, f5_reference_transcript,
                    f5_model_choice, f5_tts_speed, audio_format_radio], 
            outputs=[dubbing_video, dubbing_audio, dubbing_files, dubbing_progress])     
    

    # CosyVoice     
    cosy_language_radio.change(cosy_reference_voice.gradio_change_language,
                                inputs=[cosy_language_radio],
                                outputs=[cosy_voice_dropdown])        
    
    cosy_voice_dropdown.change(cosy_reference_voice.gradio_change_voice,
                        inputs=[cosy_voice_dropdown],
                        outputs=[cosy_reference_audio, cosy_reference_transcript, cosy_reference_image])
    cosy_reference_audio.clear(cosy_reference_voice.gradio_clear_voice,
                      inputs=None,
                      outputs=[cosy_reference_transcript, cosy_reference_image])    
    
    cosy_default_button.click(gulliver.gradio_cosy_default,
                    outputs=[cosy_mode_choice, cosy_tts_speed])         
    
    cosy_dubbing_button.click(gulliver.gradio_cosy_dubbing, 
                inputs=[
                        translation_textbox, 
                        cosy_voice_dropdown, cosy_reference_audio, cosy_reference_transcript, 
                        cosy_mode_choice, cosy_tts_speed, audio_format_radio], 
                outputs=[dubbing_video, dubbing_audio, dubbing_files, dubbing_progress])     
    
    
    # kokoro
    kokoro_language_dropdown.change(kokoro_voice.gradio_change_language,
                            inputs=[kokoro_language_dropdown],
                            outputs=[kokoro_voice_dropdown])
    
    kokoro_voice_dropdown.change(kokoro_voice.gradio_change_voice,
                            inputs=[kokoro_voice_dropdown],
                            outputs=[kokoro_sample_audio, kokoro_transcript])   
    
    kokoro_default_button.click(gulliver.gradio_kokoro_default,
                    outputs=[kokoro_tts_speed, audio_format_radio])

    kokoro_dubbing_button.click(gulliver.gradio_kokoro_dubbing, 
                inputs=[translation_textbox, kokoro_language_dropdown, kokoro_voice_dropdown, kokoro_tts_speed, audio_format_radio], 
                outputs=[dubbing_video, dubbing_audio, dubbing_files, dubbing_progress])

    # dots.tts
    dots_language_radio.change(dots_reference_voice.gradio_change_language, inputs=[dots_language_radio], outputs=[dots_voice_dropdown])
    dots_voice_dropdown.change(dots_reference_voice.gradio_change_voice, inputs=[dots_voice_dropdown], outputs=[dots_reference_audio, dots_reference_transcript, dots_reference_image])
    dots_reference_audio.clear(dots_reference_voice.gradio_clear_voice, inputs=None, outputs=[dots_reference_transcript, dots_reference_image])
    dots_model_choice.change(gulliver.gradio_dots_recommended_steps, inputs=[dots_model_choice], outputs=[dots_num_steps])
    dots_default_button.click(
        gulliver.gradio_dots_default,
        outputs=[dots_model_choice, dots_language_tag, dots_num_steps, dots_guidance_scale, dots_seed, dots_normalize_text],
    )
    dots_dubbing_button.click(
        gulliver.gradio_dots_dubbing,
        inputs=[
            translation_textbox,
            dots_voice_dropdown,
            dots_reference_audio,
            dots_reference_transcript,
            dots_model_choice,
            dots_language_tag,
            dots_num_steps,
            dots_guidance_scale,
            dots_seed,
            dots_normalize_text,
            audio_format_radio,
        ],
        outputs=[dubbing_video, dubbing_audio, dubbing_files, dubbing_progress],
    )

    # VoxCPM
    voxcpm_language_radio.change(voxcpm_reference_voice.gradio_change_language, inputs=[voxcpm_language_radio], outputs=[voxcpm_voice_dropdown])
    voxcpm_voice_dropdown.change(voxcpm_reference_voice.gradio_change_voice, inputs=[voxcpm_voice_dropdown], outputs=[voxcpm_reference_audio, voxcpm_reference_transcript, voxcpm_reference_image])
    voxcpm_reference_audio.clear(voxcpm_reference_voice.gradio_clear_voice, inputs=None, outputs=[voxcpm_reference_transcript, voxcpm_reference_image])
    voxcpm_default_button.click(
        gulliver.gradio_voxcpm_default,
        outputs=[voxcpm_mode_choice, voxcpm_voice_description, voxcpm_cfg_value, voxcpm_inference_timesteps, voxcpm_normalize_text, voxcpm_denoise_reference],
    )
    voxcpm_dubbing_button.click(
        gulliver.gradio_voxcpm_dubbing,
        inputs=[
            translation_textbox,
            voxcpm_voice_dropdown,
            voxcpm_reference_audio,
            voxcpm_reference_transcript,
            voxcpm_mode_choice,
            voxcpm_voice_description,
            voxcpm_cfg_value,
            voxcpm_inference_timesteps,
            voxcpm_normalize_text,
            voxcpm_denoise_reference,
            audio_format_radio,
        ],
        outputs=[dubbing_video, dubbing_audio, dubbing_files, dubbing_progress],
    )

    # IndexTTS
    index_language_radio.change(index_reference_voice.gradio_change_language, inputs=[index_language_radio], outputs=[index_voice_dropdown])
    index_voice_dropdown.change(index_reference_voice.gradio_change_voice, inputs=[index_voice_dropdown], outputs=[index_reference_audio, index_reference_transcript, index_reference_image])
    index_reference_audio.clear(index_reference_voice.gradio_clear_voice, inputs=None, outputs=[index_reference_transcript, index_reference_image])
    index_default_button.click(
        gulliver.gradio_index_default,
        outputs=[index_enable_emo_audio, index_emo_alpha],
    )
    index_dubbing_button.click(
        gulliver.gradio_index_dubbing,
        inputs=[
            translation_textbox,
            index_voice_dropdown,
            index_reference_audio,
            index_reference_transcript,
            index_emo_audio_prompt,
            index_enable_emo_audio,
            index_emo_alpha,
            audio_format_radio,
        ],
        outputs=[dubbing_video, dubbing_audio, dubbing_files, dubbing_progress],
    )
