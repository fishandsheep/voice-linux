import os
import sys
from contextlib import suppress
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent


def _package_dir(module) -> str | None:
    file_path = getattr(module, "__file__", None)
    if file_path:
        return os.path.dirname(file_path)

    package_paths = getattr(module, "__path__", None)
    if package_paths:
        for package_path in package_paths:
            if package_path:
                return os.fspath(package_path)

    return None


def configure_nvidia_library_path() -> None:
    lib_dirs: list[str] = []

    try:
        import nvidia.cublas.lib

        lib_dir = _package_dir(nvidia.cublas.lib)
        if lib_dir:
            lib_dirs.append(lib_dir)
    except ImportError:
        pass

    try:
        import nvidia.cudnn.lib

        lib_dir = _package_dir(nvidia.cudnn.lib)
        if lib_dir:
            lib_dirs.append(lib_dir)
    except ImportError:
        pass

    if not lib_dirs:
        return

    current = os.environ.get("LD_LIBRARY_PATH", "")
    path_parts = [part for part in current.split(os.pathsep) if part]

    for lib_dir in reversed(lib_dirs):
        if lib_dir not in path_parts:
            path_parts.insert(0, lib_dir)

    os.environ["LD_LIBRARY_PATH"] = os.pathsep.join(path_parts)


def _ensure_demucs_yaml_configs() -> None:
    import shutil
    demucs_remote_dir = PROJECT_ROOT / "src" / "demucs" / "remote"
    demucs_model_dir = PROJECT_ROOT / "model" / "demucs"

    if not demucs_remote_dir.exists():
        return

    demucs_model_dir.mkdir(parents=True, exist_ok=True)

    for yaml_file in demucs_remote_dir.glob("*.yaml"):
        target = demucs_model_dir / yaml_file.name
        if not target.exists():
            shutil.copy(yaml_file, target)


def ensure_ctranslate2_cudnn_compat() -> None:
    with suppress(ImportError):
        import ctranslate2

        libs_dir = Path(ctranslate2.__file__).resolve().parent / "../ctranslate2.libs"
        libs_dir = libs_dir.resolve()
        bundled = next(libs_dir.glob("libcudnn-*.so.8.*"), None)
        if bundled is None:
            return

        expected_names = [
            "libcudnn.so.8",
            "libcudnn_ops_infer.so.8",
            "libcudnn_ops_train.so.8",
            "libcudnn_cnn_infer.so.8",
            "libcudnn_cnn_train.so.8",
            "libcudnn_adv_infer.so.8",
            "libcudnn_adv_train.so.8",
        ]

        for name in expected_names:
            target = libs_dir / name
            if target.exists():
                continue
            try:
                target.symlink_to(bundled.name)
            except FileExistsError:
                continue
            except OSError:
                continue


def main() -> None:
    os.chdir(PROJECT_ROOT)

    project_root = str(PROJECT_ROOT)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    configure_nvidia_library_path()
    ensure_ctranslate2_cudnn_compat()

    from src.config import UserConfig
    from app.abus_genuine import genuine_init
    from app.abus_hf import AbusHuggingFace
    from app.abus_app_voice import create_ui
    from app.abus_path import path_workspace_folder, path_gradio_folder

    genuine_init()
    AbusHuggingFace.initialize(app_name="voice")
    AbusHuggingFace.hf_download_models(file_type="demucs", level=0)
    _ensure_demucs_yaml_configs()
    AbusHuggingFace.hf_download_models(file_type="edge-tts", level=0)
    AbusHuggingFace.hf_download_models(file_type="kokoro", level=0)
    AbusHuggingFace.hf_download_models(file_type="cosyvoice", level=0)

    path_workspace_folder()
    path_gradio_folder()

    user_config_path = PROJECT_ROOT / "app" / "config-user.json5"
    user_config = UserConfig(str(user_config_path))
    create_ui(user_config=user_config)


if __name__ == "__main__":
    main()
