import argparse
import os
import sys

import requests
from huggingface_hub import hf_hub_url, snapshot_download as hf_snapshot_download
from tqdm.auto import tqdm


class LoggingTqdm(tqdm):
    def __init__(self, *args, **kwargs):
        self._last_logged_percent = -1
        super().__init__(*args, **kwargs)

    def update(self, n=1):
        value = super().update(n)
        self._log_percent()
        return value

    def refresh(self, *args, **kwargs):
        value = super().refresh(*args, **kwargs)
        self._log_percent()
        return value

    def _log_percent(self):
        if not self.total or self.total <= 0:
            return
        percent = int(self.n * 100 / self.total)
        if percent > self._last_logged_percent:
            if percent - self._last_logged_percent >= 1 or percent == 100:
                print(f"[download] {self.desc or 'download'} {percent}%", flush=True)
                self._last_logged_percent = percent


def download_single_file_with_resume(repo_id: str, filename: str, local_path: str):
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    part_path = local_path + ".part"
    resume_size = os.path.getsize(part_path) if os.path.exists(part_path) else 0
    headers = {"Range": f"bytes={resume_size}-"} if resume_size > 0 else {}
    url = hf_hub_url(repo_id=repo_id, filename=filename)

    with requests.get(url, headers=headers, stream=True, timeout=60, allow_redirects=True) as response:
        if response.status_code == 416 and os.path.exists(part_path):
            os.replace(part_path, local_path)
            return local_path
        response.raise_for_status()
        if response.status_code == 200 and resume_size > 0:
            resume_size = 0
            if os.path.exists(part_path):
                os.remove(part_path)

        total = resolve_total_size(response, resume_size)
        mode = "ab" if resume_size > 0 else "wb"
        with open(part_path, mode) as handle, LoggingTqdm(
            total=total,
            initial=resume_size,
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
            desc=f"{repo_id}/{filename}",
        ) as progress:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if not chunk:
                    continue
                handle.write(chunk)
                progress.update(len(chunk))

    os.replace(part_path, local_path)
    return local_path


def resolve_total_size(response, resume_size: int) -> int | None:
    content_range = response.headers.get("Content-Range")
    if content_range and "/" in content_range:
        return int(content_range.rsplit("/", 1)[1])
    content_length = response.headers.get("Content-Length")
    if content_length:
        return int(content_length) + resume_size
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-dir", required=True)
    parser.add_argument("--model-dir", required=True)
    parser.add_argument("--source", choices=("auto", "huggingface", "modelscope"), default="auto")
    args = parser.parse_args()

    sys.path.insert(0, args.repo_dir)
    model_dir = os.path.abspath(args.model_dir)
    os.makedirs(model_dir, exist_ok=True)
    model_repo_id = "IndexTeam/IndexTTS-2"

    import indextts.utils.model_download as model_download

    def snapshot_with_progress(repo_id: str, local_dir: str, revision=None, force_download=False, **kwargs):
        if model_download._get_using_modelscope():
            return model_download._snapshot_from_modelscope(repo_id, local_dir, revision)
        return hf_snapshot_download(
            repo_id=repo_id,
            local_dir=local_dir,
            revision=revision,
            force_download=force_download,
            resume_download=True,
            local_dir_use_symlinks=False,
            tqdm_class=LoggingTqdm,
            **kwargs,
        )

    model_download.snapshot_download = snapshot_with_progress
    model_download._download_single_file = download_single_file_with_resume

    if args.source == "huggingface":
        model_download._USING_MODELSCOPE = False
        snapshot_with_progress(repo_id=model_repo_id, local_dir=model_dir)
        model_download.ensure_models_available(model_dir)
        return

    if args.source == "modelscope":
        model_download._USING_MODELSCOPE = True
        model_download._snapshot_from_modelscope(model_repo_id, model_dir)
        model_download.ensure_models_available(model_dir)
        return

    snapshot_with_progress(model_repo_id, local_dir=model_dir)
    model_download.ensure_models_available(model_dir)


if __name__ == "__main__":
    main()
