"""Tests for evaluation metrics helpers (no embedding downloads required)."""

from __future__ import annotations

from evaluation.metrics import confusion_matrix, macro_f1, per_class_metrics, summarize
from evaluation.predictors import predict_baseline_pair


def test_baseline_predicts_exact_and_missing():
    assert predict_baseline_pair("Python", "Python") == ("exact", 1.0)
    pred, sim = predict_baseline_pair("Flask", "FastAPI")
    assert pred == "missing"
    assert sim is None


def test_confusion_and_f1_helpers():
    y_true = ["exact", "partial", "missing", "partial"]
    y_pred = ["exact", "missing", "missing", "partial"]
    matrix = confusion_matrix(y_true, y_pred)
    assert matrix["partial"]["missing"] == 1
    assert matrix["partial"]["partial"] == 1
    per_class = per_class_metrics(y_true, y_pred)
    assert per_class["exact"]["tp"] == 1
    assert per_class["missing"]["tp"] == 1
    summary = summarize(y_true, y_pred)
    assert summary["n_examples"] == 4
    assert summary["macro_f1"] == macro_f1(per_class)
