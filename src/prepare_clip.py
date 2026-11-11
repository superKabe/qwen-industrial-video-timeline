from __future__ import annotations

import subprocess

from common import (
    DATA_PROCESSED,
    DATA_RAW,
    ensure_directories,
    find_executable,
    load_json,
    write_json,
)


def run(command: list[str]) -> None:
    print(" ".join(command))
    subprocess.run(command, check=True)


def extract_ground_truth(source: dict, clip_start: float, clip_duration: float) -> dict:
    clip_end = clip_start + clip_duration
    events = []
    for item in source.get("metadata", {}).values():
        times = item.get("z", [])
        label = item.get("av", {}).get("1")
        if len(times) != 2 or not label:
            continue
        source_start, source_end = map(float, times)
        if source_end <= clip_start or source_start >= clip_end:
            continue
        visible_start = max(source_start, clip_start)
        visible_end = min(source_end, clip_end)
        visible_duration = visible_end - visible_start
        source_duration = source_end - source_start
        # Do not score actions that are only visible as a sliver at a clip boundary.
        if visible_duration < 1.0 or visible_duration / source_duration < 0.5:
            continue
        events.append(
            {
                "event_type": label.strip().lower(),
                "start_s": round(visible_start - clip_start, 3),
                "end_s": round(visible_end - clip_start, 3),
                "source_start_s": round(source_start, 3),
                "source_end_s": round(source_end, 3),
            }
        )
    events.sort(key=lambda event: event["start_s"])
    return {
        "clip": {
            "filename": "indego_mechanical_desk_000_070.mp4",
            "source_filename": "User_16_414_2101_2_480.mp4",
            "source_start_s": clip_start,
            "duration_s": clip_duration,
        },
        "events": events,
        "action_vocabulary": sorted({event["event_type"] for event in events}),
        "annotation_note": (
            "Human temporal segments from IndEgo, clipped and shifted to the extracted video."
        ),
    }


def main() -> None:
    clip_start = 0.0
    clip_duration = 70.0

    ensure_directories()
    ffmpeg = find_executable("ffmpeg")
    source_video = DATA_RAW / "source_video.mp4"
    source_annotations = DATA_RAW / "source_annotations.json"
    output_video = DATA_PROCESSED / "indego_mechanical_desk_000_070.mp4"
    contact_sheet = DATA_PROCESSED / "contact_sheet.png"
    ground_truth_path = DATA_PROCESSED / "ground_truth.json"

    if not source_video.exists() or not source_annotations.exists():
        raise FileNotFoundError("Run src/download_data.py first.")

    run(
        [
            ffmpeg,
            "-y",
            "-ss",
            str(clip_start),
            "-t",
            str(clip_duration),
            "-i",
            str(source_video),
            "-an",
            "-vf",
            "fps=10,scale=-2:480",
            "-c:v",
            "libx264",
            "-crf",
            "20",
            "-preset",
            "medium",
            "-movflags",
            "+faststart",
            str(output_video),
        ]
    )

    run(
        [
            ffmpeg,
            "-y",
            "-i",
            str(output_video),
            "-vf",
            "fps=1/10,scale=360:-1,tile=4x2:padding=8:margin=8",
            "-frames:v",
            "1",
            "-update",
            "1",
            str(contact_sheet),
        ]
    )

    ground_truth = extract_ground_truth(load_json(source_annotations), clip_start, clip_duration)
    write_json(ground_truth_path, ground_truth)
    print(f"Wrote {output_video}")
    print(f"Wrote {contact_sheet}")
    print(f"Wrote {ground_truth_path} with {len(ground_truth['events'])} events")


if __name__ == "__main__":
    main()
