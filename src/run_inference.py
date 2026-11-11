from __future__ import annotations

import argparse
import json
import platform
import re
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

import torch
from qwen_vl_utils import process_vision_info
from transformers import AutoModelForImageTextToText, AutoProcessor, BitsAndBytesConfig

from common import (
    DATA_PROCESSED,
    RESULTS,
    ROOT,
    ensure_directories,
    find_executable,
    load_json,
    write_json,
)


def extract_json(text: str) -> dict:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start >= 0 and end > start:
            return json.loads(cleaned[start : end + 1])
        raise


def validate_prediction(prediction: dict, allowed_labels: set[str], duration_s: float) -> list[str]:
    errors: list[str] = []
    events = prediction.get("events")
    if not isinstance(events, list):
        return ["`events` must be a list"]
    for index, event in enumerate(events):
        if not isinstance(event, dict):
            errors.append(f"events[{index}] must be an object")
            continue
        label = event.get("event_type")
        if label not in allowed_labels:
            errors.append(f"events[{index}].event_type is not in the allowed vocabulary: {label!r}")
        start = event.get("start_s")
        end = event.get("end_s")
        if not isinstance(start, (int, float)) or not isinstance(end, (int, float)):
            errors.append(f"events[{index}] timestamps must be numeric")
            continue
        if start < 0 or end > duration_s or start >= end:
            errors.append(
                f"events[{index}] has invalid interval [{start}, {end}] for {duration_s}s clip"
            )
    return errors


def sample_frames(clip_path: Path, fps: float) -> list[Path]:
    """Use FFmpeg to create the exact ordered visual evidence sent to Qwen."""
    fps_label = f"{fps:g}".replace(".", "p")
    frame_dir = DATA_PROCESSED / f"frames_{fps_label}fps"
    frame_dir.mkdir(parents=True, exist_ok=True)
    pattern = frame_dir / "frame_%04d.jpg"
    existing = sorted(frame_dir.glob("frame_*.jpg"))
    if existing:
        return existing
    subprocess.run(
        [
            find_executable("ffmpeg"),
            "-y",
            "-i",
            str(clip_path),
            "-vf",
            f"fps={fps:g}",
            "-q:v",
            "2",
            str(pattern),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    frames = sorted(frame_dir.glob("frame_*.jpg"))
    if not frames:
        raise RuntimeError("FFmpeg did not produce sampled frames")
    return frames


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="Qwen/Qwen3-VL-4B-Instruct")
    parser.add_argument("--fps", type=float, default=1.0)
    parser.add_argument("--max-new-tokens", type=int, default=512)
    parser.add_argument("--prompt", choices=("timeline", "generic"), default="timeline")
    parser.add_argument(
        "--quantization",
        choices=("bf16", "int8", "nf4"),
        default="bf16",
        help="Weight precision. int8 is the preferred 8B mode on a 24 GB GPU.",
    )
    parser.add_argument("--max-pixels", type=int, default=128 * 32 * 32)
    parser.add_argument("--total-pixels", type=int, default=6_000 * 32 * 32)
    args = parser.parse_args()

    ensure_directories()
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is not available. This project requires the NVIDIA GPU.")

    clip_path = DATA_PROCESSED / "indego_mechanical_desk_000_070.mp4"
    ground_truth = load_json(DATA_PROCESSED / "ground_truth.json")
    prompt_template = (ROOT / "prompts" / f"{args.prompt}.txt").read_text(encoding="utf-8")
    prompt = prompt_template.format(
        action_labels="\n".join(f"- {label}" for label in ground_truth["action_vocabulary"])
    )
    sampled_frames = sample_frames(clip_path, args.fps)
    print(f"Prepared {len(sampled_frames)} sampled frames at {args.fps:g} FPS")

    print(f"Loading {args.model}...")
    torch.cuda.reset_peak_memory_stats()
    load_started = time.perf_counter()
    quantization_config = None
    model_dtype = torch.bfloat16
    if args.quantization == "int8":
        quantization_config = BitsAndBytesConfig(load_in_8bit=True)
        # bitsandbytes' INT8 matmul kernel computes in FP16. Loading the remaining
        # modules in FP16 avoids a BF16-to-FP16 cast (and warning) on every layer.
        model_dtype = torch.float16
    elif args.quantization == "nf4":
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=torch.bfloat16,
        )
    model = AutoModelForImageTextToText.from_pretrained(
        args.model,
        dtype=model_dtype,
        device_map="auto",
        attn_implementation="sdpa",
        quantization_config=quantization_config,
    )
    processor = AutoProcessor.from_pretrained(args.model)
    load_seconds = time.perf_counter() - load_started

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "video",
                    # Raw paths are intentional: qwen-vl-utils does not URL-decode
                    # percent-escaped spaces in Windows file:// URIs.
                    "video": [str(frame.resolve()) for frame in sampled_frames],
                    "sample_fps": args.fps,
                    "raw_fps": args.fps,
                    "max_pixels": args.max_pixels,
                    "total_pixels": args.total_pixels,
                },
                {"type": "text", "text": prompt},
            ],
        }
    ]

    chat_text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    images, videos, video_kwargs = process_vision_info(
        messages,
        image_patch_size=16,
        return_video_kwargs=True,
        return_video_metadata=True,
    )
    if videos is not None:
        videos, video_metadatas = zip(*videos)
        videos, video_metadatas = list(videos), list(video_metadatas)
    else:
        video_metadatas = None

    inputs = processor(
        text=chat_text,
        images=images,
        videos=videos,
        video_metadata=video_metadatas,
        return_tensors="pt",
        do_resize=False,
        cap_pixels_per_frame=True,
        **video_kwargs,
    )
    inputs = inputs.to(model.device)

    print("Running inference...")
    inference_started = time.perf_counter()
    with torch.inference_mode():
        generated_ids = model.generate(
            **inputs,
            max_new_tokens=args.max_new_tokens,
            do_sample=False,
        )
    torch.cuda.synchronize()
    inference_seconds = time.perf_counter() - inference_started
    generated_trimmed = [
        output[len(input_ids) :] for input_ids, output in zip(inputs.input_ids, generated_ids)
    ]
    raw_text = processor.batch_decode(
        generated_trimmed,
        skip_special_tokens=True,
        clean_up_tokenization_spaces=False,
    )[0]

    precision_suffix = "" if args.quantization == "bf16" else f"_{args.quantization}"
    run_name = (
        f"{args.prompt}_{args.model.split('/')[-1].lower()}_{args.fps:g}fps{precision_suffix}"
    )
    raw_path = RESULTS / f"{run_name}_raw.txt"
    prediction_path = RESULTS / f"{run_name}_prediction.json"
    metadata_path = RESULTS / f"{run_name}_run.json"
    raw_path.write_text(raw_text + "\n", encoding="utf-8")

    parse_error = None
    validation_errors: list[str] = []
    try:
        prediction = extract_json(raw_text)
        validation_errors = validate_prediction(
            prediction,
            set(ground_truth["action_vocabulary"]),
            float(ground_truth["clip"]["duration_s"]),
        )
        write_json(prediction_path, prediction)
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        parse_error = f"{type(exc).__name__}: {exc}"
        print(f"JSON parse failed: {parse_error}")

    run_metadata = {
        "created_at": datetime.now(UTC).isoformat(),
        "model": args.model,
        "quantization": args.quantization,
        "compute_dtype": str(model_dtype).removeprefix("torch."),
        "model_memory_footprint_gb": round(model.get_memory_footprint() / 1024**3, 3),
        "prompt": args.prompt,
        "video": str(clip_path.relative_to(ROOT)),
        "fps": args.fps,
        "max_pixels_per_frame": args.max_pixels,
        "total_pixels": args.total_pixels,
        "max_new_tokens": args.max_new_tokens,
        "load_seconds": round(load_seconds, 3),
        "inference_seconds": round(inference_seconds, 3),
        "peak_vram_gb": round(torch.cuda.max_memory_allocated() / 1024**3, 3),
        "input_tokens": int(inputs.input_ids.shape[-1]),
        "output_tokens": int(generated_ids.shape[-1] - inputs.input_ids.shape[-1]),
        "gpu": torch.cuda.get_device_name(0),
        "torch_version": torch.__version__,
        "python_version": platform.python_version(),
        "parse_error": parse_error,
        "validation_errors": validation_errors,
    }
    write_json(metadata_path, run_metadata)
    print(raw_text)
    print(f"Saved run as {run_name}")


if __name__ == "__main__":
    main()
