# Local VLM Timeline Extraction for Industrial Video

## Summary

I evaluated whether local Qwen3-VL models could turn egocentric industrial assembly footage into an auditable timestamped event log, then measured whether moving from 4B to 8B parameters improved temporal grounding on consumer hardware.

## Why this project

Video-language models can generate persuasive summaries, but field systems need outputs that can be checked against source evidence. Inspection, quality, and incident-review workflows care not only about what happened, but when it happened, whether repeated events stayed separate, and how failures are surfaced.

## Approach

- Selected a 70-second annotated clip from Fraunhofer IPK's IndEgo dataset.
- Sampled 70 frames at 1 FPS.
- Ran Qwen3-VL-4B in BF16 and Qwen3-VL-8B in INT8 on an RTX 3090 Ti.
- Supplied a fixed action vocabulary and required structured JSON intervals.
- Matched predictions one-to-one against human annotations using temporal IoU.
- Preserved raw output, environment metadata, and source hashes for auditability.
- Built an interactive video audit interface with synchronized human/model tracks, clickable events, and a 4B/8B selector.

## Result

The 4B model matched 2 of 7 annotated events at a 0.30 temporal-IoU threshold; the 8B model matched 3 of 7. F1 improved from 0.36 to 0.55, and median boundary error fell from 4.26 to 2.27 seconds. The larger model still merged repeated fastening actions and missed the assembly connection. The 8B INT8 inference took 55.1 seconds and peaked at 19.7 GB of VRAM.

## Takeaway

The experiment showed a meaningful gap between understanding the overall workflow and producing an event log suitable for audit. Doubling model capacity improved localization but did not solve repeated-event separation. Local VLMs look useful as indexing and review-assistance layers, but deployment quality depends on sampling, precision, token budgets, structured validation, and human review—not model weights alone.

## Stack

Python, PyTorch, Transformers, Qwen3-VL, FFmpeg, Matplotlib, vanilla JavaScript, IndEgo
