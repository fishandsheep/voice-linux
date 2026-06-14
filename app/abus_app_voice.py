import os
import sys
import platform

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)


import torch
import gradio as gr
from src.config import UserConfig

import src.ui as ui
from src.i18n.i18n import I18nAuto, SUPPORTED_UI_LANGUAGES, normalize_language, set_active_language
i18n = I18nAuto()

import structlog
import logging

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("fairseq").setLevel(logging.WARNING)
logging.getLogger("azure.core").setLevel(logging.WARNING)
logging.getLogger("faster_whisper").setLevel(logging.WARNING)
logging.getLogger('matplotlib').setLevel(logging.WARNING)


level = os.environ.get("LOG_LEVEL", "INFO").upper()
LOG_LEVEL = getattr(logging, level)
structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(logging.WARNING)
)
logger = structlog.get_logger()


from app.abus_genuine import *
from app.tab_gulliver import gulliver_tab
from app.tab_subtitle import subtitle_tab
from app.tab_tts_edge import tts_edge_tab
from app.tab_tts_f5_single import tts_f5_single_tab
from app.tab_tts_f5_multi import tts_f5_multi_tab
from app.tab_tts_cosyvoice import tts_cosyvoice_tab
from app.tab_tts_kokoro import tts_kokoro_tab
from app.tab_tts_dots import tts_dots_tab
from app.tab_translate import translate_tab


##############################################################################################
# Gradio
##############################################################################################    


def create_ui(user_config: UserConfig):
    # css/js strings
    css = ui.css
    js = ui.js
    
    system = platform.system()    
    initial_language = normalize_language(user_config.get("gradio_language", "English"))
    set_active_language(initial_language)

    with gr.Blocks(title='voice-simple', css=css, theme=ui.theme) as gradio_interface:
        language_dropdown = gr.Dropdown(
            label="UI Language",
            choices=list(SUPPORTED_UI_LANGUAGES.keys()),
            value=initial_language,
            interactive=True,
        )

        @gr.render(inputs=[language_dropdown])
        def render_app(selected_language):
            selected_language = normalize_language(selected_language)
            set_active_language(selected_language)
            if user_config.get("gradio_language") != selected_language:
                user_config.set("gradio_language", selected_language)

            gr.HTML(f'<center><h6>{i18n("")}</h6></center>')

            with gr.Tab(i18n("Dubbing Studio")):
                gulliver_tab(user_config)

            with gr.Tab(i18n("Whisper subtitles")):
                subtitle_tab(user_config)

            with gr.Tab(i18n("Translation")):
                translate_tab(user_config)

            with gr.Tab(i18n("Speech Generation")):
                tab_name = i18n('Azure-TTS') if azure_text_api_working() else i18n('Edge-TTS')
                with gr.Tab(tab_name):
                    tts_edge_tab(user_config)
                with gr.Tab(i18n("F5-TTS (Single)")):
                    tts_f5_single_tab(user_config)
                with gr.Tab(i18n("F5-TTS (Multi)")):
                    tts_f5_multi_tab(user_config)
                with gr.Tab(i18n("CosyVoice")):
                    tts_cosyvoice_tab(user_config)
                with gr.Tab(i18n("kokoro")):
                    tts_kokoro_tab(user_config)
                with gr.Tab("dots.tts"):
                    tts_dots_tab(user_config)

            create_app_footer()
        
        
        gradio_interface.load(None, None, None, js="() => document.getElementsByTagName('body')[0].classList.add('dark')")
        gradio_interface.load(None, None, None, js=f"() => {{{js}}}")
                    

    if system == "Windows":
        gradio_interface.launch(
            share=False,
            server_name=None, 
            server_port=7870,
            inbrowser=True
        )
    elif system == "Linux" or system == "Darwin":
        gradio_interface.launch()
    else:
        print(f"Unsupported systems: {system}")



def create_app_footer():
    gradio_version = gr.__version__
    python_version = platform.python_version()
    torch_version = torch.__version__

    footer_items = ["🔊 [voice-simple](https://github.com/fishandsheep/voice-linux)"]
    footer_items.append(f"python: `{python_version}`")
    footer_items.append(f"torch: `{torch_version}`")
    footer_items.append(f"gradio: `{gradio_version}`")
    
    genuine = "activated version"
    footer_items.append(f"{genuine}")    

    gr.Markdown(
        " | ".join(footer_items),
        elem_classes=["no-translate"],
    )
