# Qwen industrial timeline — project context

## Objective

Turn a local VLM experiment into a portfolio case study relevant to physical AI, field engineering, industrial computer vision, construction, safety, and quality workflows. The case study should demonstrate engineering judgment rather than imply production readiness.

## Experiment

- Source: a 70-second egocentric mechanical-desk assembly clip from Fraunhofer IPK's IndEgo dataset.
- License: source data is CC BY 4.0; preserve visible Fraunhofer IPK / IndEgo attribution.
- Evidence: 70 frames sampled at 1 FPS.
- Task: select from a fixed action vocabulary and return structured event intervals.
- Evaluation: exact one-to-one matching by label at temporal IoU >= 0.30.
- Hardware: NVIDIA GeForce RTX 3090 Ti with 24 GB VRAM.

## Verified results

### Qwen3-VL-4B-Instruct, BF16

- Matched events: 2 of 7
- Precision: 0.50
- Recall: 0.2857
- F1: 0.3636
- Mean temporal IoU: 0.4124
- Median boundary error: 4.258 seconds
- Inference: 25.198 seconds
- Peak allocated VRAM: 18.498 GB

### Qwen3-VL-8B-Instruct, INT8 weights / FP16 compute

- Matched events: 3 of 7
- Precision: 0.75
- Recall: 0.4286
- F1: 0.5455
- Mean temporal IoU: 0.5118
- Median boundary error: 2.27 seconds
- Inference: 55.066 seconds
- Peak allocated VRAM: 19.741 GB

The 8B model improved localization but did not solve repeated-event separation. It still merged two fastening events and missed the leg-and-foot connection. Because model size and precision both changed, this is an operational comparison, not a precision-controlled benchmark.

## Interface already built

The buildless implementation in `demo/` provides:

- synchronized video, native controls, custom scrubber, and playhead;
- human-reference and model-prediction tracks;
- clickable events that seek the source video;
- a 4B BF16 / 8B INT8 selector;
- event evidence, status, timing, and temporal-IoU details;
- aggregate evaluation metrics;
- local-file fallback when the source clip is not hosted;
- responsive styling and basic keyboard/accessibility support.

## Narrative to preserve

The core claim is: a VLM can understand the workflow without producing a timeline trustworthy enough for audit. Larger-model capacity helped, but sampling, precision, structured validation, failure handling, and the review interface remain part of the system.

Do not claim that this one clip is a benchmark, that the reference annotations are perfect ground truth, that confidence scores are calibrated, or that the model is ready for autonomous safety or quality enforcement.

## Website decisions still open

- Whether to host the 5.4 MB processed clip on the portfolio site or retain the local file picker.
- Whether to port the vanilla implementation into the site's component framework or embed it with minimal adaptation.
- Whether the page should include the full LinkedIn narrative, a shorter case study, or both.
- Whether to publish a screen recording in addition to the interactive page.

## Verification already completed

- Python lint and formatting checks passed.
- Three evaluation unit tests passed.
- JavaScript syntax validation passed.
- Browser QA passed for video synchronization, model switching, metrics, and event selection.
- The demo page, styles, script, source video, and all referenced JSON artifacts returned HTTP 200 locally.

