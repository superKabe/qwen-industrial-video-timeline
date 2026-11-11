A vision-language model can describe a video. That doesn’t mean it can produce a timeline you should trust.

I tested Qwen3-VL-4B locally on 70 seconds of annotated industrial assembly footage from Fraunhofer IPK’s IndEgo dataset.

The model received one frame per second and a fixed action vocabulary. Its task was to return a structured event log with start and end timestamps. I then compared that output with the existing human annotations.

At a 0.30 temporal-overlap threshold, Qwen matched 2 of 7 annotated events.

It recognized the worker putting on gloves and fastening a bolt. But it also:

- collapsed two fastening events into one long interval;
- missed the leg-and-foot connection;
- misplaced a tool pickup;
- returned one invalid zero-length event.

The completed run took 25 seconds and used 18.5 GB of VRAM on an RTX 3090 Ti.

I also tried denser sampling and the 8B model. Both nearly filled the 24 GB card and were still running after eight minutes, so I stopped them. “Fits locally” and “is practical locally” are very different claims.

My main takeaways:

1. Frame sampling and visual-token budgets are part of model performance, not implementation details.
2. Structured output makes failures easier to detect than a convincing prose summary.
3. Recognizing the workflow is easier than producing an auditable record of when each step happened.

For field engineering, inspection, and quality workflows, the most promising role I see today is not autonomous enforcement. It’s turning long, messy video into structured evidence that an engineer or operator can review faster.

The interesting engineering is between the capable model and the trustworthy field system: observability, validation, deployment constraints, and failure handling.

I put the code, prompt, raw prediction, evaluation, and visualization in a public repository: https://github.com/superKabe/qwen-industrial-video-timeline
