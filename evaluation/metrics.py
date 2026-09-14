"""Classification metrics for skill-pair evaluation."""

from __future__ import annotations

from collections import defaultdict


LABELS = ("exact", "partial", "missing")


def confusion_matrix(
    y_true: list[str],
    y_pred: list[str],
    labels: tuple[str, ...] = LABELS,
) -> dict[str, dict[str, int]]:
    matrix = {actual: {pred: 0 for pred in labels} for actual in labels}
    for actual, pred in zip(y_true, y_pred, strict=True):
        if actual not in matrix or pred not in matrix[actual]:
            raise ValueError(f"Unexpected labels: true={actual!r}, pred={pred!r}")
        matrix[actual][pred] += 1
    return matrix


def _counts_for_label(
    y_true: list[str],
    y_pred: list[str],
    label: str,
) -> tuple[int, int, int]:
    tp = fp = fn = 0
    for actual, pred in zip(y_true, y_pred, strict=True):
        if pred == label and actual == label:
            tp += 1
        elif pred == label and actual != label:
            fp += 1
        elif pred != label and actual == label:
            fn += 1
    return tp, fp, fn


def precision_recall_f1(tp: int, fp: int, fn: int) -> dict[str, float]:
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    if precision + recall == 0:
        f1 = 0.0
    else:
        f1 = 2 * precision * recall / (precision + recall)
    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "support": tp + fn,
        "tp": tp,
        "fp": fp,
        "fn": fn,
    }


def per_class_metrics(
    y_true: list[str],
    y_pred: list[str],
    labels: tuple[str, ...] = LABELS,
) -> dict[str, dict[str, float | int]]:
    return {
        label: precision_recall_f1(*_counts_for_label(y_true, y_pred, label))
        for label in labels
    }


def macro_f1(per_class: dict[str, dict[str, float | int]]) -> float:
    scores = [float(stats["f1"]) for stats in per_class.values()]
    return round(sum(scores) / len(scores), 4) if scores else 0.0


def accuracy(y_true: list[str], y_pred: list[str]) -> float:
    if not y_true:
        return 0.0
    correct = sum(1 for a, p in zip(y_true, y_pred, strict=True) if a == p)
    return round(correct / len(y_true), 4)


def summarize(
    y_true: list[str],
    y_pred: list[str],
    labels: tuple[str, ...] = LABELS,
) -> dict:
    per_class = per_class_metrics(y_true, y_pred, labels)
    return {
        "n_examples": len(y_true),
        "label_accuracy": accuracy(y_true, y_pred),
        "macro_f1": macro_f1(per_class),
        "per_class": per_class,
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels),
        "label_distribution_true": _distribution(y_true, labels),
        "label_distribution_pred": _distribution(y_pred, labels),
    }


def _distribution(values: list[str], labels: tuple[str, ...]) -> dict[str, int]:
    counts: dict[str, int] = {label: 0 for label in labels}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return counts


def paired_errors(
    examples: list[dict],
    y_true: list[str],
    y_pred: list[str],
    similarities: list[float | None],
) -> list[dict]:
    rows = []
    for ex, actual, pred, sim in zip(
        examples, y_true, y_pred, similarities, strict=True
    ):
        if actual == pred:
            continue
        rows.append(
            {
                "id": ex["id"],
                "resume_skill": ex["resume_skill"],
                "jd_skill": ex["jd_skill"],
                "expected": actual,
                "predicted": pred,
                "similarity": sim,
                "category": ex.get("category"),
                "notes": ex.get("notes"),
            }
        )
    return rows
