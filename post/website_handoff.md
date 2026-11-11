# Portfolio website handoff

## What to bring into the website repository

- `demo/index.html`: semantic structure and copy
- `demo/style.css`: self-contained visual system
- `demo/app.js`: video synchronization, timeline rendering, and data adapter
- `demo/README.md`: preview instructions, data contract, licensing, and integration notes
- `data/processed/ground_truth.json`: publishable reference timeline
- `results/*_prediction.json`: publishable model timelines
- `results/*_evaluation.json`: publishable metrics and match details
- `post/website_project.md`: condensed case-study copy

Do not assume the source video is publishable merely because it exists locally. It is excluded from Git. Preserve the visible Fraunhofer IPK / IndEgo attribution and verify the final hosting approach against the CC BY 4.0 terms and the portfolio host's file-size limits.

## Recommended Codex workflow

1. Open a new Codex chat in the portfolio website workspace.
2. Give that chat access to this repository as a sibling folder, clone the public repository beside the website, or copy the files listed above into a temporary import directory.
3. Ask Codex to read this file and `demo/README.md` before changing the website.
4. Have it map the vanilla component into the site's existing framework and design system rather than importing a second framework.
5. Keep the JSON data contract stable so future model runs can be added without rewriting the UI.

## Copy-paste prompt for the website chat

> Integrate the Qwen industrial-video timeline demo into this portfolio site as a project case study. First inspect this site's framework, visual system, routing, asset conventions, and deployment limits. Then read the source project's `post/website_handoff.md`, `demo/README.md`, and the files under `demo/`. Preserve the synchronized video, scrubber, clickable human/model tracks, 4B/8B selector, event-detail panel, and IndEgo attribution. Adapt the component to the site's existing framework and styles; do not introduce a second frontend framework. Copy only publishable JSON artifacts, keep the source video strategy explicit, and validate the integrated page responsively before deployment.

## Context model

Codex chat history is thread-scoped. A fork can inherit this conversation, but durable cross-project context should live in repository files and version control. The website chat should treat the current files and measured JSON results as the source of truth rather than relying on a pasted conversation summary.
