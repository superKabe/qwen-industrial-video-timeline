"use strict";

const DURATION = 70;
const DATA_URLS = {
  groundTruth: "../data/processed/ground_truth.json",
  models: [
    {
      id: "qwen-4b-bf16",
      shortLabel: "4B · BF16",
      trackLabel: "Qwen 4B",
      title: "Qwen3-VL 4B",
      precision: "BF16",
      prediction: "../results/timeline_qwen3-vl-4b-instruct_1fps_prediction.json",
      evaluation: "../results/qwen3_vl_4b_1fps_evaluation.json",
    },
    {
      id: "qwen-8b-int8",
      shortLabel: "8B · INT8",
      trackLabel: "Qwen 8B",
      title: "Qwen3-VL 8B",
      precision: "INT8",
      prediction: "../results/timeline_qwen3-vl-8b-instruct_1fps_int8_prediction.json",
      evaluation: "../results/qwen3_vl_8b_1fps_int8_evaluation.json",
      optional: true,
    },
  ],
};

const state = {
  groundTruth: [],
  models: [],
  activeModelId: null,
  selectedKey: null,
};

const ui = {
  video: document.querySelector("#source-video"),
  videoFallback: document.querySelector("#video-fallback"),
  videoFile: document.querySelector("#video-file"),
  hudTime: document.querySelector("#hud-time"),
  scrubber: document.querySelector("#scrubber"),
  currentTime: document.querySelector("#current-time"),
  durationTime: document.querySelector("#duration-time"),
  nowHuman: document.querySelector("#now-human"),
  nowModel: document.querySelector("#now-model"),
  modelSwitcher: document.querySelector("#model-switcher"),
  activeModelTitle: document.querySelector("#active-model-title"),
  precisionBadge: document.querySelector("#precision-badge"),
  modelTrackLabel: document.querySelector("#model-track-label"),
  metrics: document.querySelector("#metrics"),
  findingCopy: document.querySelector("#finding-copy"),
  ruler: document.querySelector("#ruler"),
  humanTrack: document.querySelector("#human-track"),
  modelTrack: document.querySelector("#model-track"),
  playhead: document.querySelector("#playhead"),
  eventDetail: document.querySelector("#event-detail"),
};

function formatTime(seconds) {
  const safe = Number.isFinite(seconds) ? Math.max(0, seconds) : 0;
  const minutes = Math.floor(safe / 60);
  const remainder = safe - minutes * 60;
  return `${String(minutes).padStart(2, "0")}:${remainder.toFixed(1).padStart(4, "0")}`;
}

function percent(value) {
  return `${Math.max(0, Math.min(100, (value / DURATION) * 100))}%`;
}

function activeModel() {
  return state.models.find((model) => model.id === state.activeModelId) ?? state.models[0];
}

async function fetchJson(url) {
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
  return response.json();
}

function normalizeRun(config, prediction, evaluation) {
  const matchedPredictions = new Map(
    evaluation.matches.map((match) => [match.prediction_index, match]),
  );
  const unmatchedPredictions = new Map(
    evaluation.unmatched_predictions.map((item) => [item.prediction_index, item]),
  );
  const matchedGroundTruth = new Map(
    evaluation.matches.map((match) => [match.ground_truth_index, match]),
  );

  return {
    ...config,
    available: true,
    evaluation,
    events: prediction.events.map((event, index) => {
      const match = matchedPredictions.get(index);
      const unmatched = unmatchedPredictions.get(index);
      const invalid = Number(event.start_s) >= Number(event.end_s);
      return {
        ...event,
        index,
        key: `${config.id}-prediction-${index}`,
        source: "model",
        status: invalid ? "invalid" : match ? "matched" : unmatched?.category ?? "unmatched",
        match,
        unmatched,
      };
    }),
    groundTruthStatus: state.groundTruth.map((event, index) => ({
      ...event,
      index,
      key: `human-${index}`,
      source: "human",
      status: matchedGroundTruth.has(index) ? "matched" : "missed",
      match: matchedGroundTruth.get(index),
    })),
  };
}

async function loadData() {
  const groundTruthPayload = await fetchJson(DATA_URLS.groundTruth);
  state.groundTruth = groundTruthPayload.events;

  const runs = await Promise.all(
    DATA_URLS.models.map(async (config) => {
      try {
        const [prediction, evaluation] = await Promise.all([
          fetchJson(config.prediction),
          fetchJson(config.evaluation),
        ]);
        return normalizeRun(config, prediction, evaluation);
      } catch (error) {
        if (!config.optional) throw error;
        return { ...config, available: false, loadError: error.message };
      }
    }),
  );

  state.models = runs;
  state.activeModelId = runs.find((run) => run.available)?.id ?? null;
}

function renderRuler() {
  ui.ruler.replaceChildren();
  for (let second = 0; second <= DURATION; second += 10) {
    const tick = document.createElement("span");
    tick.className = "tick";
    tick.style.left = percent(second);
    tick.textContent = `${second}s`;
    ui.ruler.append(tick);
  }
}

function renderModelSwitcher() {
  ui.modelSwitcher.replaceChildren();
  for (const model of state.models) {
    const button = document.createElement("button");
    button.className = `model-button${model.id === state.activeModelId ? " active" : ""}`;
    button.type = "button";
    button.textContent = model.available ? model.shortLabel : `${model.shortLabel} · pending`;
    button.disabled = !model.available;
    button.setAttribute("aria-pressed", String(model.id === state.activeModelId));
    if (!model.available) button.title = "This run will appear when its result files are present.";
    button.addEventListener("click", () => {
      state.activeModelId = model.id;
      state.selectedKey = null;
      renderAllModelData();
      updatePlaybackUi(ui.video.currentTime || 0);
    });
    ui.modelSwitcher.append(button);
  }
}

function metric(label, value, suffix = "") {
  return `<div class="metric"><span class="metric-label">${label}</span><span class="metric-value">${value}${suffix ? `<small>${suffix}</small>` : ""}</span></div>`;
}

function renderMetrics(model) {
  const summary = model.evaluation.summary;
  const tiou = summary.mean_temporal_iou == null ? "—" : summary.mean_temporal_iou.toFixed(2);
  const boundary =
    summary.median_boundary_error_s == null
      ? "—"
      : summary.median_boundary_error_s.toFixed(1);
  ui.metrics.innerHTML = [
    metric("Matched events", `${summary.matched_events}/${summary.ground_truth_events}`),
    metric("Recall", `${Math.round(summary.recall * 100)}`, "%"),
    metric("Mean tIoU", tiou),
    metric("Median boundary error", boundary, " sec"),
  ].join("");
  ui.findingCopy.textContent = `${summary.matched_events} of ${summary.ground_truth_events} reference events matched at tIoU ≥ ${model.evaluation.threshold_temporal_iou.toFixed(2)}. Short and repeated actions remain the clearest failure mode.`;
}

function statusClass(status) {
  if (status === "matched") return "matched";
  if (status === "missed") return "missed";
  if (status === "invalid") return "invalid";
  return "mislocalized";
}

function makeEventBlock(event) {
  const block = document.createElement("button");
  const duration = Math.max(0, Number(event.end_s) - Number(event.start_s));
  block.type = "button";
  block.className = `event-block status-${statusClass(event.status)}`;
  block.dataset.key = event.key;
  block.dataset.start = event.start_s;
  block.dataset.end = event.end_s;
  block.style.left = percent(Number(event.start_s));
  block.style.width = duration > 0 ? percent(duration) : "7px";
  block.setAttribute(
    "aria-label",
    `${event.source === "human" ? "Human annotation" : "Model prediction"}: ${event.event_type}, ${formatTime(Number(event.start_s))} to ${formatTime(Number(event.end_s))}, ${event.status.replaceAll("_", " ")}`,
  );
  block.title = `${event.event_type} · ${Number(event.start_s).toFixed(1)}–${Number(event.end_s).toFixed(1)}s`;
  block.innerHTML = `<span class="event-name">${event.event_type}</span><span class="event-time">${Number(event.start_s).toFixed(1)}–${Number(event.end_s).toFixed(1)}s</span>`;
  block.addEventListener("click", () => selectEvent(event, true));
  return block;
}

function renderTracks(model) {
  ui.humanTrack.replaceChildren(...model.groundTruthStatus.map(makeEventBlock));
  ui.modelTrack.replaceChildren(...model.events.map(makeEventBlock));
}

function matchScore(event) {
  return event.match?.temporal_iou == null ? "—" : event.match.temporal_iou.toFixed(2);
}

function eventDescription(event) {
  if (event.source === "model" && event.evidence) return event.evidence;
  if (event.status === "matched") {
    return `Matched the ${event.source === "human" ? "model prediction" : "human reference"} at the 0.30 temporal-IoU threshold.`;
  }
  if (event.status === "missed") return "No model prediction matched this reference event.";
  if (event.status === "invalid") return "The model returned a zero-length interval, so this prediction is invalid for temporal evaluation.";
  return `The action label is plausible, but its timing did not overlap a reference interval enough to count as a match.`;
}

function selectEvent(event, startPlayback) {
  state.selectedKey = event.key;
  document.querySelectorAll(".event-block").forEach((block) => {
    block.classList.toggle("selected", block.dataset.key === event.key);
  });
  const status = event.status.replaceAll("_", " ");
  ui.eventDetail.innerHTML = `
    <div class="detail-time">${formatTime(Number(event.start_s))}<br />${formatTime(Number(event.end_s))}</div>
    <div>
      <p class="detail-type">${event.source === "human" ? "Human reference" : "Model prediction"} · ${status}</p>
      <h3>${event.event_type}</h3>
      <p>${eventDescription(event)}</p>
    </div>
    <div class="detail-score"><span>tIoU</span><strong>${matchScore(event)}</strong></div>`;

  ui.video.currentTime = Math.max(0, Number(event.start_s));
  updatePlaybackUi(ui.video.currentTime);
  if (startPlayback) ui.video.play().catch(() => {});
}

function renderAllModelData() {
  const model = activeModel();
  if (!model) return;
  ui.activeModelTitle.textContent = model.title;
  ui.precisionBadge.textContent = model.precision;
  ui.modelTrackLabel.textContent = model.trackLabel;
  renderModelSwitcher();
  renderMetrics(model);
  renderTracks(model);
}

function currentEvents(events, time) {
  return events.filter(
    (event) => Number(event.start_s) <= time && time <= Number(event.end_s),
  );
}

function setNowPill(element, prefix, events) {
  const names = [...new Set(events.map((event) => event.event_type))];
  element.textContent = `${prefix}: ${names.length ? names.join(" + ") : "—"}`;
  element.classList.toggle("active", names.length > 0);
}

function updatePlaybackUi(time) {
  const safeTime = Math.max(0, Math.min(DURATION, Number(time) || 0));
  const ratio = (safeTime / DURATION) * 100;
  const model = activeModel();
  ui.hudTime.textContent = formatTime(safeTime);
  ui.currentTime.textContent = formatTime(safeTime);
  ui.scrubber.value = safeTime;
  ui.scrubber.setAttribute("aria-valuetext", `${safeTime.toFixed(1)} seconds`);
  ui.scrubber.style.background = `linear-gradient(90deg, var(--signal) 0%, var(--signal) ${ratio}%, var(--line) ${ratio}%)`;
  ui.playhead.style.left = `${ratio}%`;

  const humanNow = currentEvents(model?.groundTruthStatus ?? [], safeTime);
  const modelNow = currentEvents(model?.events ?? [], safeTime);
  setNowPill(ui.nowHuman, "Human", humanNow);
  setNowPill(ui.nowModel, "Qwen", modelNow);

  document.querySelectorAll(".event-block").forEach((block) => {
    const start = Number(block.dataset.start);
    const end = Number(block.dataset.end);
    block.classList.toggle("active", start <= safeTime && safeTime <= end && start < end);
  });
}

function wireVideo() {
  ui.video.addEventListener("loadedmetadata", () => {
    ui.videoFallback.hidden = true;
    updatePlaybackUi(ui.video.currentTime);
  });
  ui.video.addEventListener("timeupdate", () => updatePlaybackUi(ui.video.currentTime));
  ui.video.addEventListener("seeked", () => updatePlaybackUi(ui.video.currentTime));
  ui.video.addEventListener("error", () => {
    ui.videoFallback.hidden = false;
  });
  ui.scrubber.addEventListener("input", () => {
    ui.video.currentTime = Number(ui.scrubber.value);
    updatePlaybackUi(Number(ui.scrubber.value));
  });
  ui.videoFile.addEventListener("change", () => {
    const [file] = ui.videoFile.files;
    if (!file) return;
    if (ui.video.dataset.objectUrl) URL.revokeObjectURL(ui.video.dataset.objectUrl);
    const objectUrl = URL.createObjectURL(file);
    ui.video.dataset.objectUrl = objectUrl;
    ui.video.src = objectUrl;
    ui.video.load();
  });
}

async function init() {
  renderRuler();
  wireVideo();
  ui.durationTime.textContent = formatTime(DURATION);
  try {
    await loadData();
    renderAllModelData();
    updatePlaybackUi(0);
  } catch (error) {
    ui.eventDetail.innerHTML = `<div class="detail-time">DATA<br />ERROR</div><div><p class="detail-type">Load failure</p><h3>Serve this page from the repository root.</h3><p>${error.message}. See demo/README.md for the preview command.</p></div><div class="detail-score"><span>Status</span><strong>!</strong></div>`;
    console.error(error);
  }
}

init();
