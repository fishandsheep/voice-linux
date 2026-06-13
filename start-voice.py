import argparse
import os
import sys
from pathlib import Path

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)


def configure_nvidia_library_path():
    lib_dirs = []

    try:
        import nvidia.cublas.lib

        lib_dirs.append(os.path.dirname(nvidia.cublas.lib.__file__))
    except ImportError:
        pass

    try:
        import nvidia.cudnn.lib

        lib_dirs.append(os.path.dirname(nvidia.cudnn.lib.__file__))
    except ImportError:
        pass

    if not lib_dirs:
        return

    current = os.environ.get("LD_LIBRARY_PATH", "")
    path_parts = [part for part in current.split(os.pathsep) if part]

    for lib_dir in lib_dirs:
        if lib_dir not in path_parts:
            path_parts.insert(0, lib_dir)

    os.environ["LD_LIBRARY_PATH"] = os.pathsep.join(path_parts)


configure_nvidia_library_path()


from src.config import UserConfig
from app.abus_hf import AbusHuggingFace
from app.abus_genuine import genuine_init
from app.abus_app_voice import create_ui
from app.abus_path import path_workspace_folder, path_gradio_folder

# ABUS - start voice
genuine_init()
AbusHuggingFace.initialize(app_name="voice")

# AbusHuggingFace.hf_download_models(file_type='mdxnet-model', level=0)
AbusHuggingFace.hf_download_models(file_type='demucs', level=0)
# AbusHuggingFace.hf_download_models(file_type='f5-tts', level=0)
# AbusHuggingFace.hf_download_models(file_type='vocos-mel-24khz', level=0)
# AbusHuggingFace.hf_download_models(file_type='rvc-model', level=0)
# AbusHuggingFace.hf_download_models(file_type='rvc-voice', level=0)
AbusHuggingFace.hf_download_models(file_type='edge-tts', level=0)
AbusHuggingFace.hf_download_models(file_type='kokoro', level=0)
AbusHuggingFace.hf_download_models(file_type='cosyvoice', level=0)

path_workspace_folder()
path_gradio_folder()


user_config_path = os.path.join(Path(__file__).resolve().parent, "app", "config-user.json5")
user_config = UserConfig(user_config_path)

create_ui(user_config=user_config)
