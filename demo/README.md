# Interactive timeline demo

A buildless, local-first audit interface for comparing reference annotations with Qwen3-VL video event predictions. It is deliberately framework-free so the component can be previewed here and later ported into a portfolio site without inheriting a second toolchain.

## Preview locally

Run the server from the **repository root** so the demo can read the ignored video and tracked JSON results:

```powershell
.\.venv\Scripts\python.exe -m http.server 8000
```

On systems where Python is already on `PATH`, `python -m http.server 8000` is equivalent.

Open `http://localhost:8000/demo/`.

The page first looks for `data/processed/indego_mechanical_desk_000_070.mp4`. Because the video is intentionally excluded from Git, a file picker appears if that path is unavailable. A selected file stays in the browser; it is not uploaded.

## What is portable

- `index.html` contains the semantic UI and source attribution.
- `style.css` is self-contained and has no font, icon, or CDN dependencies.
- `app.js` adapts the pipeline JSON into interactive tracks, metrics, event details, and video seeking.
- The UI works with native browser APIs only. No build step or backend is required.

The current adapter reads:

- `data/processed/ground_truth.json`
- `results/timeline_qwen3-vl-4b-instruct_1fps_prediction.json`
- `results/qwen3_vl_4b_1fps_evaluation.json`

An event must contain `event_type`, `start_s`, and `end_s`. Model events may also contain `evidence` and `confidence`. Evaluation files use the schema emitted by `src/evaluate.py`.

## Add the 8B result

The disabled `8B · INT8` selector automatically activates when both of these files exist:

- `results/timeline_qwen3-vl-8b-instruct_1fps_int8_prediction.json`
- `results/qwen3_vl_8b_1fps_int8_evaluation.json`

If the final evaluation filename changes, update only the second model entry in `DATA_URLS.models` at the top of `app.js`.

## Move this into the portfolio site

For the cleanest handoff, copy `demo/` into the portfolio repository and copy the small, publishable JSON artifacts into a public data directory. Then:

1. Replace the relative URLs in `DATA_URLS` with the site’s asset URLs.
2. Host the source clip only if its size and the IndEgo CC BY 4.0 terms fit the portfolio deployment. Otherwise retain the local file picker or use an externally hosted licensed asset.
3. Preserve the visible Fraunhofer IPK / IndEgo attribution.
4. Port the markup and state functions into the site’s component system only if that improves consistency; the vanilla version can also be embedded as-is.

The component has no dependency on Codex or the Python environment at runtime. The durable handoff is the code, JSON artifacts, source/license note, and this README—not the original chat transcript.
