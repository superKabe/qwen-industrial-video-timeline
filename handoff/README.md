# Website integration handoff

This directory is the entry point for continuing the Qwen timeline project in the portfolio website repository.

## Read in this order

1. [`project-context.md`](project-context.md) — verified results, decisions, constraints, and open website choices.
2. [`asset-manifest.json`](asset-manifest.json) — source files to copy or adapt and whether they are safe to publish.
3. [`website-integration-prompt.md`](website-integration-prompt.md) — the ready-to-paste prompt for the website-project Codex chat.
4. [`../demo/README.md`](../demo/README.md) — runtime data contract and local preview instructions.

The live implementation is under [`../demo/`](../demo/). The public source repository is:

https://github.com/superKabe/qwen-industrial-video-timeline

## Recommended transfer

Open a new Codex chat with the portfolio website repository as its workspace. Give that workspace access to this repository by cloning it as a sibling checkout or copying this `handoff/` directory plus the files listed in `asset-manifest.json` into a temporary import directory. Then paste the contents of `website-integration-prompt.md`.

Use `/fork` only if you want a new primary chat that inherits this conversation and can still access the correct workspace. Repository files are the durable source of truth for a cross-project handoff.

