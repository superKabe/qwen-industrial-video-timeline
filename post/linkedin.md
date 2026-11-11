A vision-language model can describe a video. That doesn’t mean it can produce a timeline you should trust.

I tested Qwen3-VL-4B and 8B locally on 70 seconds of annotated industrial assembly footage from Fraunhofer IPK’s IndEgo dataset.

The model received one frame per second and a fixed action vocabulary. Its task was to return a structured event log with start and end timestamps. I then compared that output with the existing human annotations.

At a 0.30 temporal-overlap threshold:

- Qwen3-VL-4B in BF16 matched 2 of 7 events (F1: 0.36).
- Qwen3-VL-8B in INT8 matched 3 of 7 events (F1: 0.55).

The larger model also reduced median boundary error from 4.3 to 2.3 seconds.

It recognized the worker putting on gloves and fastening a bolt. But it also:

- collapsed two fastening events into one long interval;
- missed the leg-and-foot connection;
- misplaced a tool pickup;
- returned one invalid zero-length event.

The 4B run took 25 seconds and peaked at 18.5 GB of VRAM. The 8B INT8 run took 55 seconds and peaked at 19.7 GB on the same RTX 3090 Ti.

The 8B BF16 configuration nearly filled the 24 GB card and became impractically slow under CPU offload. Quantization made it operational, but it also means this is a practical deployment comparison—not a clean model-size benchmark.

I also built a synchronized review interface that lets you scrub through the video, switch between the 4B and 8B runs, and click directly into matched, missed, and mislocalized events. That made the failures much easier to understand than the aggregate metrics alone.

My main takeaways:

1. Frame sampling and visual-token budgets are part of model performance, not implementation details.
2. Structured output makes failures easier to detect than a convincing prose summary.
3. Recognizing the workflow is easier than producing an auditable record of when each step happened.
4. A larger model helped, but the surrounding system still mattered more than the parameter count alone.

For field engineering, inspection, and quality workflows, the most promising role I see today is not autonomous enforcement. It’s turning long, messy video into structured evidence that an engineer or operator can review faster.

The interesting engineering is between the capable model and the trustworthy field system: observability, validation, deployment constraints, and failure handling.

I put the code, prompt, raw prediction, evaluation, and visualization in a public repository: https://github.com/superKabe/qwen-industrial-video-timeline
