# Prompt for the portfolio website chat

Integrate the Qwen industrial-video timeline project into this portfolio website as a polished, interactive case study.

Start with a read-only discovery pass. Inspect this website repository's framework, routes, design system, component conventions, asset pipeline, responsive breakpoints, tests, and deployment limits. Then read the Qwen source project's files in this order:

1. `handoff/README.md`
2. `handoff/project-context.md`
3. `handoff/asset-manifest.json`
4. `demo/README.md`
5. `demo/index.html`, `demo/style.css`, and `demo/app.js`
6. `post/website_project.md`

Use the source repository at https://github.com/superKabe/qwen-industrial-video-timeline if it is not already available locally.

Preserve these behaviors:

- synchronized video playback, custom scrubber, and timeline playhead;
- stacked human-reference and Qwen prediction tracks;
- clickable events that seek the video;
- the 4B BF16 / 8B INT8 selector;
- event evidence, status, timing, and temporal-IoU details;
- the aggregate metrics for both runs;
- visible Fraunhofer IPK / IndEgo attribution;
- responsive and accessible interactions.

Adapt the demo to this site's existing framework and design language. Do not introduce a second frontend framework. Treat the JSON result artifacts as the data source of truth, and preserve the caveat that the 4B-versus-8B comparison also changes weight precision.

Before implementation, report:

1. the website architecture you found;
2. the proposed route and component boundaries;
3. the exact files you will copy, adapt, or create;
4. the source-video hosting recommendation and licensing implications;
5. the verification plan;
6. any decision that genuinely requires my input.

Then implement the approved integration, validate it responsively in the browser, and leave deployment as a separate explicit step unless I have already asked you to publish.

