# Local VLM Timeline Extraction for Industrial Video

## Summary

I evaluated whether Qwen3-VL-4B could turn egocentric industrial assembly footage into an auditable timestamped event log while running entirely on local hardware.

## Why this project

Video-language models can generate persuasive summaries, but field systems need outputs that can be checked against source evidence. Inspection, quality, and incident-review workflows care not only about what happened, but when it happened, whether repeated events stayed separate, and how failures are surfaced.

## Approach

- Selected a 70-second annotated clip from Fraunhofer IPK's IndEgo dataset.
- Sampled 70 frames at 1 FPS.
- Ran Qwen3-VL-4B in BF16 on an RTX 3090 Ti.
- Supplied a fixed action vocabulary and required structured JSON intervals.
- Matched predictions one-to-one against human annotations using temporal IoU.
- Preserved raw output, environment metadata, and source hashes for auditability.

## Result

Qwen matched 2 of 7 annotated events at a 0.30 temporal-IoU threshold. It recognized glove use and fastening, but merged repeated actions, missed an assembly connection, and produced one invalid interval. The completed inference took 25.2 seconds and allocated 18.5 GB of VRAM.

## Takeaway

The experiment showed a meaningful gap between understanding the overall workflow and producing an event log suitable for audit. Local VLMs look useful as indexing and review-assistance layers, but deployment quality depends on sampling, token budgets, structured validation, and human review—not model weights alone.

## Stack

Python, PyTorch, Transformers, Qwen3-VL, FFmpeg, Matplotlib, IndEgo
