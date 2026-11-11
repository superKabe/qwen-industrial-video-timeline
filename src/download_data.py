from __future__ import annotations

import hashlib
import urllib.request
from pathlib import Path

from common import DATA_RAW, ensure_directories, write_json

HF_BASE = "https://huggingface.co/datasets/FraunhoferIPK/IndEgo/resolve/main"
ASSET_PATHS = {
    "source_video.mp4": (
        "1_Assembly/03_Mechanical_Desk/mp4_480/User_16_414_2101_2_480.mp4?download=true"
    ),
    "source_annotations.json": (
        "1_Assembly/03_Mechanical_Desk/annotations/A_User_16_414_2101_2.json?download=true"
    ),
    "procedure_keysteps.txt": (
        "1_Assembly/03_Mechanical_Desk/keysteps_03_assembly.txt?download=true"
    ),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def download(url: str, destination: Path) -> None:
    if destination.exists() and destination.stat().st_size > 0:
        print(
            f"Using existing {destination.name} ({destination.stat().st_size / 1_048_576:.1f} MB)"
        )
        return

    partial = destination.with_suffix(destination.suffix + ".partial")
    request = urllib.request.Request(url, headers={"User-Agent": "qwen-industrial-timeline/0.1"})
    print(f"Downloading {destination.name}...")
    with urllib.request.urlopen(request) as response, partial.open("wb") as output:
        total = int(response.headers.get("Content-Length", "0"))
        downloaded = 0
        while chunk := response.read(1024 * 1024):
            output.write(chunk)
            downloaded += len(chunk)
            if total:
                print(f"  {downloaded / total:6.1%}", end="\r")
    partial.replace(destination)
    print(f"  saved {destination.stat().st_size / 1_048_576:.1f} MB")


def main() -> None:
    ensure_directories()
    manifest = {
        "dataset": "IndEgo",
        "publisher": "Fraunhofer IPK",
        "license": "CC BY 4.0",
        "dataset_url": "https://huggingface.co/datasets/FraunhoferIPK/IndEgo",
        "assets": {},
    }

    for filename, remote_path in ASSET_PATHS.items():
        destination = DATA_RAW / filename
        url = f"{HF_BASE}/{remote_path}"
        download(url, destination)
        manifest["assets"][filename] = {
            "source_url": url,
            "bytes": destination.stat().st_size,
            "sha256": sha256(destination),
        }

    manifest_path = DATA_RAW.parent / "manifest.json"
    write_json(manifest_path, manifest)
    print(f"Wrote {manifest_path}")


if __name__ == "__main__":
    main()
