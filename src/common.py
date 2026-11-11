from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
RESULTS = ROOT / "results"


def ensure_directories() -> None:
    for path in (DATA_RAW, DATA_PROCESSED, RESULTS):
        path.mkdir(parents=True, exist_ok=True)


def find_executable(name: str) -> str:
    found = shutil.which(name)
    if found:
        return found

    if os.name == "nt":
        package_root = (
            Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Packages"
        )
        patterns = {
            "ffmpeg": "Gyan.FFmpeg*/**/ffmpeg.exe",
            "ffprobe": "Gyan.FFmpeg*/**/ffprobe.exe",
        }
        pattern = patterns.get(name.lower())
        if pattern and package_root.exists():
            matches = list(package_root.glob(pattern))
            if matches:
                return str(matches[0])

    raise FileNotFoundError(f"Could not find executable: {name}")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
