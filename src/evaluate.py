from __future__ import annotations

import argparse
import statistics
from functools import cache

from common import DATA_PROCESSED, RESULTS, load_json, write_json


def normalize_label(value: str) -> str:
    return " ".join(value.lower().replace("_", " ").replace("-", " ").split())


def temporal_iou(left: dict, right: dict) -> float:
    intersection = max(
        0.0,
        min(float(left["end_s"]), float(right["end_s"]))
        - max(float(left["start_s"]), float(right["start_s"])),
    )
    union = max(float(left["end_s"]), float(right["end_s"])) - min(
        float(left["start_s"]), float(right["start_s"])
    )
    return intersection / union if union > 0 else 0.0


def optimal_label_matches(
    ground_truth: list[dict],
    predicted: list[dict],
    gt_indices: list[int],
    pred_indices: list[int],
    threshold: float,
) -> list[tuple[int, int, float]]:
    """Maximize match count, then total temporal IoU, for one action label."""
    if len(pred_indices) > 20:
        raise ValueError("Too many same-label predictions for exact matching")

    @cache
    def solve(
        position: int, used_mask: int
    ) -> tuple[int, float, tuple[tuple[int, int, float], ...]]:
        if position >= len(gt_indices):
            return 0, 0.0, ()
        best = solve(position + 1, used_mask)
        gt_index = gt_indices[position]
        for local_pred_index, pred_index in enumerate(pred_indices):
            if used_mask & (1 << local_pred_index):
                continue
            score = temporal_iou(ground_truth[gt_index], predicted[pred_index])
            if score < threshold:
                continue
            count, total, pairs = solve(position + 1, used_mask | (1 << local_pred_index))
            candidate = (count + 1, total + score, ((gt_index, pred_index, score),) + pairs)
            if candidate[:2] > best[:2]:
                best = candidate
        return best

    return list(solve(0, 0)[2])


def evaluate(ground_truth: list[dict], predicted: list[dict], threshold: float) -> dict:
    matches = []
    used_gt: set[int] = set()
    used_pred: set[int] = set()
    labels = sorted({normalize_label(event["event_type"]) for event in ground_truth})
    for label in labels:
        gt_indices = [
            index
            for index, event in enumerate(ground_truth)
            if normalize_label(event["event_type"]) == label
        ]
        pred_indices = [
            index
            for index, event in enumerate(predicted)
            if normalize_label(event.get("event_type", "")) == label
        ]
        for gt_index, pred_index, score in optimal_label_matches(
            ground_truth, predicted, gt_indices, pred_indices, threshold
        ):
            used_gt.add(gt_index)
            used_pred.add(pred_index)
            gt_event = ground_truth[gt_index]
            pred_event = predicted[pred_index]
            matches.append(
                {
                    "ground_truth_index": gt_index,
                    "prediction_index": pred_index,
                    "ground_truth": gt_event,
                    "prediction": pred_event,
                    "temporal_iou": round(score, 4),
                    "start_error_s": round(float(pred_event["start_s"]) - gt_event["start_s"], 3),
                    "end_error_s": round(float(pred_event["end_s"]) - gt_event["end_s"], 3),
                }
            )

    missed = [event for index, event in enumerate(ground_truth) if index not in used_gt]
    ground_truth_labels = {normalize_label(event["event_type"]) for event in ground_truth}
    unmatched_predictions = []
    for index, event in enumerate(predicted):
        if index in used_pred:
            continue
        label = normalize_label(event.get("event_type", ""))
        same_label_gt = [gt for gt in ground_truth if normalize_label(gt["event_type"]) == label]
        best_iou = max((temporal_iou(gt, event) for gt in same_label_gt), default=0.0)
        if label not in ground_truth_labels:
            category = "unsupported_label"
        elif best_iou >= threshold:
            category = "duplicate_prediction"
        else:
            category = "mislocalized_prediction"
        unmatched_predictions.append(
            {
                "prediction_index": index,
                "category": category,
                "best_same_label_iou": round(best_iou, 4),
                "event": event,
            }
        )
    true_positive = len(matches)
    precision = true_positive / len(predicted) if predicted else 0.0
    recall = true_positive / len(ground_truth) if ground_truth else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    ious = [match["temporal_iou"] for match in matches]
    boundary_errors = [
        abs(value) for match in matches for value in (match["start_error_s"], match["end_error_s"])
    ]

    return {
        "threshold_temporal_iou": threshold,
        "summary": {
            "ground_truth_events": len(ground_truth),
            "predicted_events": len(predicted),
            "matched_events": true_positive,
            "missed_events": len(missed),
            "unmatched_predictions": len(unmatched_predictions),
            "unsupported_labels": sum(
                item["category"] == "unsupported_label" for item in unmatched_predictions
            ),
            "mislocalized_predictions": sum(
                item["category"] == "mislocalized_prediction" for item in unmatched_predictions
            ),
            "duplicate_predictions": sum(
                item["category"] == "duplicate_prediction" for item in unmatched_predictions
            ),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "mean_temporal_iou": round(statistics.mean(ious), 4) if ious else None,
            "median_boundary_error_s": (
                round(statistics.median(boundary_errors), 3) if boundary_errors else None
            ),
        },
        "matches": sorted(matches, key=lambda item: item["ground_truth"]["start_s"]),
        "missed": missed,
        "unmatched_predictions": unmatched_predictions,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prediction", required=True)
    parser.add_argument("--name", default="primary")
    parser.add_argument("--threshold", type=float, default=0.3)
    args = parser.parse_args()

    ground_truth = load_json(DATA_PROCESSED / "ground_truth.json")["events"]
    prediction = load_json(RESULTS / args.prediction)
    predicted_events = prediction.get("events", [])
    report = evaluate(ground_truth, predicted_events, args.threshold)
    destination = RESULTS / f"{args.name}_evaluation.json"
    write_json(destination, report)
    print(report["summary"])
    print(f"Wrote {destination}")


if __name__ == "__main__":
    main()
