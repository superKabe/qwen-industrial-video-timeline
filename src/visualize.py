from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from PIL import Image

from common import DATA_PROCESSED, RESULTS, ensure_directories, find_executable, load_json

COLORS = {
    "set camera": "#7C3AED",
    "put on gloves": "#0891B2",
    "pick up tools": "#2563EB",
    "connect leg and feet": "#16A34A",
    "fastening bolt": "#EA580C",
}

DISPLAY_LABELS = {
    "connect leg and feet": "connect leg + foot",
    "fastening bolt": "fasten bolt",
}


def extract_frame(video: Path, timestamp: float, destination: Path) -> None:
    ffmpeg = find_executable("ffmpeg")
    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-ss",
            str(timestamp),
            "-i",
            str(video),
            "-frames:v",
            "1",
            "-vf",
            "scale=520:-1",
            str(destination),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def draw_timeline(
    ax, events: list[dict], title: str, matched_indices: set[int] | None = None
) -> None:
    ax.set_xlim(0, 70)
    ax.set_ylim(-0.8, len(events) - 0.2)
    ax.set_yticks([])
    ax.set_xlabel("Seconds", fontsize=10, color="#334155")
    ax.set_title(title, loc="left", fontsize=14, fontweight="bold", color="#0F172A", pad=10)
    ax.grid(axis="x", color="#E2E8F0", linewidth=0.8)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color("#CBD5E1")
    for index, event in enumerate(events):
        start = float(event["start_s"])
        end = float(event["end_s"])
        label = event["event_type"]
        display_label = DISPLAY_LABELS.get(label, label)
        color = COLORS.get(label, "#64748B")
        if matched_indices is not None and index not in matched_indices:
            color = "#DC2626"
        y = len(events) - index - 1
        ax.barh(y, max(end - start, 0.4), left=start, height=0.58, color=color, alpha=0.92)
        duration = end - start
        if duration >= 6:
            text_x = min(start + 0.5, 65)
            text_color = "white"
        else:
            text_x = min(end + 0.35, 66)
            text_color = "#0F172A"
        ax.text(
            text_x,
            y,
            display_label,
            va="center",
            ha="left",
            fontsize=8.7,
            color=text_color,
            fontweight="bold",
            clip_on=True,
        )


def metric_card(ax, x: float, label: str, value: str, color: str) -> None:
    card = FancyBboxPatch(
        (x, 0.05),
        0.21,
        0.84,
        boxstyle="round,pad=0.018,rounding_size=0.025",
        facecolor="#F8FAFC",
        edgecolor="#E2E8F0",
        linewidth=1.2,
        transform=ax.transAxes,
    )
    ax.add_patch(card)
    ax.text(
        x + 0.105,
        0.59,
        value,
        ha="center",
        va="center",
        fontsize=22,
        fontweight="bold",
        color=color,
        transform=ax.transAxes,
    )
    ax.text(
        x + 0.105,
        0.27,
        label,
        ha="center",
        va="center",
        fontsize=9.5,
        color="#475569",
        transform=ax.transAxes,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prediction", required=True)
    parser.add_argument("--evaluation", required=True)
    parser.add_argument("--output", default="timeline_comparison.png")
    args = parser.parse_args()

    ensure_directories()
    frames_dir = RESULTS / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    video = DATA_PROCESSED / "indego_mechanical_desk_000_070.mp4"
    timestamps = [12, 24, 43, 56]
    frame_paths = []
    for timestamp in timestamps:
        destination = frames_dir / f"frame_{timestamp:02d}.jpg"
        extract_frame(video, timestamp, destination)
        frame_paths.append(destination)

    ground_truth = load_json(DATA_PROCESSED / "ground_truth.json")["events"]
    prediction = load_json(RESULTS / args.prediction).get("events", [])
    evaluation = load_json(RESULTS / args.evaluation)
    summary = evaluation["summary"]

    fig = plt.figure(figsize=(12, 15), dpi=120, facecolor="white")
    grid = fig.add_gridspec(
        5, 4, height_ratios=[0.65, 2.2, 1.1, 3.2, 3.2], hspace=0.38, wspace=0.06
    )

    title_ax = fig.add_subplot(grid[0, :])
    title_ax.axis("off")
    title_ax.text(
        0,
        0.78,
        "Can a local VLM reconstruct an industrial workflow?",
        fontsize=25,
        fontweight="bold",
        color="#0F172A",
    )
    title_ax.text(
        0,
        0.18,
        "Qwen3-VL-4B · 70 seconds of annotated egocentric assembly video · local RTX 3090 Ti",
        fontsize=12.5,
        color="#475569",
    )

    for index, (frame_path, timestamp) in enumerate(zip(frame_paths, timestamps)):
        ax = fig.add_subplot(grid[1, index])
        ax.imshow(Image.open(frame_path))
        ax.axis("off")
        ax.text(
            0.04,
            0.92,
            f"{timestamp}s",
            color="white",
            fontsize=11,
            fontweight="bold",
            transform=ax.transAxes,
            bbox={"facecolor": "#0F172A", "alpha": 0.78, "edgecolor": "none", "pad": 4},
        )

    metrics_ax = fig.add_subplot(grid[2, :])
    metrics_ax.axis("off")
    metric_card(
        metrics_ax,
        0.01,
        "events matched",
        f"{summary['matched_events']}/{summary['ground_truth_events']}",
        "#16A34A",
    )
    metric_card(metrics_ax, 0.265, "events missed", str(summary["missed_events"]), "#DC2626")
    metric_card(
        metrics_ax, 0.52, "unmatched predictions", str(summary["unmatched_predictions"]), "#7C3AED"
    )
    boundary = summary.get("median_boundary_error_s")
    metric_card(
        metrics_ax,
        0.775,
        "median boundary error",
        f"{boundary:.1f}s" if boundary is not None else "n/a",
        "#EA580C",
    )

    gt_ax = fig.add_subplot(grid[3, :])
    draw_timeline(gt_ax, ground_truth, "Human annotations")

    pred_ax = fig.add_subplot(grid[4, :])
    matched_predictions = {match["prediction_index"] for match in evaluation["matches"]}
    draw_timeline(pred_ax, prediction, "Qwen prediction", matched_predictions)

    fig.text(
        0.5,
        0.015,
        "Source: Fraunhofer IPK IndEgo dataset (CC BY 4.0). Red prediction bars did not meet the 0.30 temporal-IoU match threshold.",
        ha="center",
        fontsize=9.5,
        color="#64748B",
    )
    output = RESULTS / args.output
    fig.savefig(output, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
