"""FR-1: download monthly CAA files and store them unchanged.

Downloads every URL listed in ``data/sources.json`` to ``data/raw/`` without
transformation. Re-runnable: already-downloaded files are left untouched
unless ``force`` is set.
"""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path

import requests

from heathrow.config import PROJECT_ROOT, RAW_DIR

log = logging.getLogger(__name__)

SOURCES_PATH = PROJECT_ROOT / "data" / "sources.json"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_sources(path: Path = SOURCES_PATH) -> dict:
    """Return the source manifest dict, or a no-op manifest if absent."""
    if not path.exists():
        return {"base_url": "", "files": []}
    return json.loads(path.read_text(encoding="utf-8"))


def download(
    sources_path: Path = SOURCES_PATH, raw_dir: Path = RAW_DIR, force: bool = False
) -> list[Path]:
    """Download all manifest files. Returns the list of local paths written."""
    raw_dir.mkdir(parents=True, exist_ok=True)
    manifest = load_sources(sources_path)
    base = manifest.get("base_url", "").rstrip("/")
    files = manifest.get("files", [])

    written: list[Path] = []
    for item in files:
        name = item["name"] if isinstance(item, dict) else item
        url = item["url"] if isinstance(item, dict) else f"{base}/{name}"
        if base and not url.startswith("http"):
            url = f"{base}/{url.lstrip('/')}"

        dest = raw_dir / name
        if dest.exists() and not force:
            log.info("skip (exists): %s", name)
            written.append(dest)
            continue

        log.info("download: %s -> %s", url, name)
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        dest.write_bytes(resp.content)
        log.info("  bytes=%d sha256=%s", len(resp.content), _sha256(resp.content))
        written.append(dest)

    if not files:
        log.warning("sources.json has no files listed — nothing to download.")
    return written


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    download()
