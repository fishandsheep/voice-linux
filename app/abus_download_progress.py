import os
import shutil
from pathlib import Path

import requests
from huggingface_hub import hf_hub_url
from tqdm.auto import tqdm

import structlog

logger = structlog.get_logger()


class LoggingTqdm(tqdm):
    def __init__(self, *args, **kwargs):
        self._last_logged_percent = -1
        super().__init__(*args, **kwargs)

    def update(self, n=1):
        displayed = super().update(n)
        self._log_percent()
        return displayed

    def refresh(self, *args, **kwargs):
        value = super().refresh(*args, **kwargs)
        self._log_percent()
        return value

    def _log_percent(self):
        if not self.total or self.total <= 0:
            return

        percent = int(self.n * 100 / self.total)
        if percent <= self._last_logged_percent:
            return

        if percent - self._last_logged_percent >= 1 or percent == 100:
            desc = self.desc or "download"
            logger.info("[download] %s %s%%", desc, percent)
            self._last_logged_percent = percent


def download_hf_file_with_resume(
    repo_id: str,
    filename: str,
    local_path: str,
    subfolder: str | None = None,
    token=None,
    force_download: bool = False,
    chunk_size: int = 1024 * 1024,
):
    target_path = Path(local_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)

    if force_download and target_path.exists():
        target_path.unlink()

    part_path = target_path.with_suffix(target_path.suffix + ".part")
    if force_download and part_path.exists():
        part_path.unlink()

    resume_size = part_path.stat().st_size if part_path.exists() else 0
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if resume_size > 0:
        headers["Range"] = f"bytes={resume_size}-"

    url = hf_hub_url(repo_id=repo_id, filename=filename, subfolder=subfolder)
    with requests.get(url, headers=headers, stream=True, timeout=60, allow_redirects=True) as response:
        if response.status_code == 416 and part_path.exists():
            shutil.move(part_path, target_path)
            return str(target_path)
        response.raise_for_status()

        if response.status_code == 200 and resume_size > 0:
            # Server ignored Range. Restart cleanly.
            resume_size = 0
            if part_path.exists():
                part_path.unlink()

        total_size = _resolve_total_size(response, resume_size)
        mode = "ab" if resume_size > 0 else "wb"
        desc = f"{repo_id}/{filename}"
        with open(part_path, mode) as handle, LoggingTqdm(
            total=total_size,
            initial=resume_size,
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
            desc=desc,
        ) as progress:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if not chunk:
                    continue
                handle.write(chunk)
                progress.update(len(chunk))

    shutil.move(part_path, target_path)
    return str(target_path)


def _resolve_total_size(response, resume_size: int) -> int | None:
    content_range = response.headers.get("Content-Range")
    if content_range and "/" in content_range:
        try:
            return int(content_range.rsplit("/", 1)[1])
        except ValueError:
            pass

    content_length = response.headers.get("Content-Length")
    if content_length:
        try:
            return int(content_length) + resume_size
        except ValueError:
            pass
    return None
