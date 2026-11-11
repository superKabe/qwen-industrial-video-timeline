# Can a local VLM reconstruct an industrial workflow?

This project tests whether Qwen3-VL-4B, running locally on an RTX 3090 Ti, can convert annotated industrial assembly footage into an auditable event timeline.

![Human annotations compared with Qwen's predicted timeline](results/timeline_comparison.png)

## Result

On one 70-second egocentric assembly clip, Qwen matched **2 of 7** human-annotated events at a temporal intersection-over-union threshold of 0.30.

- Precision: **0.50**
- Recall: **0.29**
- F1: **0.36**
- Mean temporal IoU for matched events: **0.41**
- Median start/end boundary error for matched events: **4.3 seconds**
- Inference time: **25.2 seconds** after model loading
- Peak allocated VRAM: **18.5 GB**

The model recognized glove use and bolt fastening, but it merged two separate fastening events into one long interval, missed the leg-and-foot connection, misplaced a tool pickup, and emitted one invalid zero-length interval.

This is a one-clip case study, not a general benchmark. The useful result is the gap between a plausible description of the workflow and a timeline that can be checked event by event.

## Experiment design

The source is a 70-second excerpt from Fraunhofer IPK's [IndEgo dataset](https://huggingface.co/datasets/FraunhoferIPK/IndEgo). The matching human timestamp annotations contain seven complete events:

1. Set camera
2. Put on gloves
3. Pick up tools
4. Pick up tools
5. Connect leg and foot
6. Fasten bolt
7. Fasten bolt

Qwen receives:

- 70 frames sampled uniformly at 1 FPS;
- the valid action vocabulary, but not the timestamps or event count;
- a JSON schema requiring an action, start time, end time, evidence, and confidence;
- instructions to report only visibly supported actions.

Supplying the vocabulary makes this a temporal recognition and localization task. It is not open-ended action discovery.

Predictions are matched one-to-one by action label using an exact maximum-cardinality assignment. A match requires at least 0.30 temporal IoU. Unmatched predictions are separated into unsupported labels, duplicate predictions, and correct-label-but-mislocalized predictions rather than labeling every timing failure a hallucination.

## Local deployment observations

The completed configuration used Qwen3-VL-4B in BF16 with 131,072 maximum pixels per sampled frame and a 6,144,000-pixel total video budget.

Several larger configurations were deliberately stopped after bounded trials:

- Qwen3-VL-8B at 1 FPS consumed approximately 23.8–23.9 GB of VRAM and did not complete within 8–10 minutes.
- Qwen3-VL-4B at 2 FPS consumed approximately 23.9 GB and did not complete within 8 minutes.

Those stopped runs are deployment observations, not latency or accuracy measurements. They show that fitting model weights into VRAM does not make a video configuration operationally useful. See [`results/runtime_observations.json`](results/runtime_observations.json) for the recorded settings.

## Reproduce

### Requirements

- Windows with an NVIDIA GPU and current driver
- Approximately 25 GB of free disk space
- [uv](https://docs.astral.sh/uv/)
- [FFmpeg](https://ffmpeg.org/)

The `uv` configuration selects CUDA 12.8 PyTorch wheels on Windows. Other platforms may need to adjust the PyTorch package source in `pyproject.toml`.

### Run

```powershell
uv sync
uv run python src/download_data.py
uv run python src/prepare_clip.py
uv run python src/run_inference.py --prompt timeline --fps 1
uv run python src/evaluate.py `
  --prediction timeline_qwen3-vl-4b-instruct_1fps_prediction.json `
  --name qwen3_vl_4b_1fps
uv run python src/visualize.py `
  --prediction timeline_qwen3-vl-4b-instruct_1fps_prediction.json `
  --evaluation qwen3_vl_4b_1fps_evaluation.json
uv run python -m unittest discover -s tests -v
```

Model weights, source video, extracted frames, and the processed clip are excluded from Git. The downloader retrieves the required assets from the publisher and writes tracked source URLs, sizes, and SHA-256 hashes to [`data/manifest.json`](data/manifest.json).

## Files worth inspecting

- [`prompts/timeline.txt`](prompts/timeline.txt): exact structured prompt
- [`data/processed/ground_truth.json`](data/processed/ground_truth.json): clipped reference events
- [`results/timeline_qwen3-vl-4b-instruct_1fps_raw.txt`](results/timeline_qwen3-vl-4b-instruct_1fps_raw.txt): unedited model response
- [`results/qwen3_vl_4b_1fps_evaluation.json`](results/qwen3_vl_4b_1fps_evaluation.json): event-level scoring details
- [`results/timeline_qwen3-vl-4b-instruct_1fps_run.json`](results/timeline_qwen3-vl-4b-instruct_1fps_run.json): runtime and environment metadata

## Limitations

- One clip cannot establish model-wide performance.
- Human timestamps are reference annotations, not perfect ground truth.
- The model sees sampled frames, not continuous video.
- Self-reported confidence values are not calibrated probabilities.
- This is offline analysis; the model can use future frames when describing earlier events.
- The experiment does not test persistent worker tracking, audio, live alerts, or safety-rule enforcement.

A general-purpose VLM may be useful for indexing video, proposing events, and retrieving evidence. This experiment does not support using one as the sole decision-maker for safety or quality control.

## Data and code licenses

IndEgo is published by Fraunhofer IPK under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). This project downloads one source video, its matching annotations, and the procedure keysteps from the [official Hugging Face repository](https://huggingface.co/datasets/FraunhoferIPK/IndEgo). The source video is not redistributed here.

Project code is released under the [MIT License](LICENSE).
