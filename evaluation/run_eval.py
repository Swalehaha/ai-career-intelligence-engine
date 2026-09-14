"""Run skill-pair and profile evaluation; write JSON results under data/evaluation/out."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from evaluation.metrics import paired_errors, summarize
from evaluation.predictors import (
    pair_similarity,
    predict_baseline_pair,
    predict_profile_scores,
    predict_semantic_system_pair,
)

ROOT = Path(__file__).resolve().parent.parent
PAIRS_PATH = ROOT / "data" / "evaluation" / "skill_pairs.json"
PROFILES_PATH = ROOT / "data" / "evaluation" / "score_profiles.json"
OUT_DIR = ROOT / "data" / "evaluation" / "out"

DEFAULT_MATCH = 0.60
DEFAULT_PARTIAL = 0.45


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def evaluate_skill_pairs(
    match_threshold: float = DEFAULT_MATCH,
    partial_threshold: float = DEFAULT_PARTIAL,
) -> dict:
    data = load_json(PAIRS_PATH)
    examples = data["examples"]

    y_true = [ex["expected"] for ex in examples]

    baseline_preds: list[str] = []
    baseline_sims: list[float | None] = []
    full_preds: list[str] = []
    full_sims: list[float | None] = []

    for ex in examples:
        b_pred, b_sim = predict_baseline_pair(ex["resume_skill"], ex["jd_skill"])
        f_pred, f_sim = predict_semantic_system_pair(
            ex["resume_skill"],
            ex["jd_skill"],
            match_threshold=match_threshold,
            partial_threshold=partial_threshold,
        )
        baseline_preds.append(b_pred)
        baseline_sims.append(b_sim)
        full_preds.append(f_pred)
        full_sims.append(f_sim)

    baseline_summary = summarize(y_true, baseline_preds)
    full_summary = summarize(y_true, full_preds)

    return {
        "dataset": data["dataset_name"],
        "synthetic": data.get("synthetic", True),
        "thresholds": {
            "match_threshold": match_threshold,
            "partial_threshold": partial_threshold,
        },
        "label_mapping_note": (
            "System buckets semantic_matched and partial both map to gold label "
            "'partial' (related). Baseline never predicts partial."
        ),
        "baseline": baseline_summary,
        "exact_plus_semantic": full_summary,
        "baseline_errors": paired_errors(
            examples, y_true, baseline_preds, baseline_sims
        ),
        "semantic_errors": paired_errors(examples, y_true, full_preds, full_sims),
        "predictions": [
            {
                "id": ex["id"],
                "resume_skill": ex["resume_skill"],
                "jd_skill": ex["jd_skill"],
                "expected": ex["expected"],
                "baseline_pred": b,
                "full_pred": f,
                "full_similarity": s,
                "category": ex.get("category"),
            }
            for ex, b, f, s in zip(
                examples, baseline_preds, full_preds, full_sims, strict=True
            )
        ],
    }


def evaluate_score_profiles(
    match_threshold: float = DEFAULT_MATCH,
    partial_threshold: float = DEFAULT_PARTIAL,
) -> dict:
    data = load_json(PROFILES_PATH)
    rows = []
    for profile in data["profiles"]:
        result = predict_profile_scores(
            profile["resume_skills"],
            profile["jd_skills"],
            match_threshold=match_threshold,
            partial_threshold=partial_threshold,
        )
        rows.append(
            {
                "id": profile["id"],
                "tier": profile["tier"],
                "notes": profile.get("notes"),
                "n_resume_skills": len(profile["resume_skills"]),
                "n_jd_skills": len(profile["jd_skills"]),
                **result,
            }
        )

    # Sanity: mean full score by declared tier (heuristic check, not accuracy)
    by_tier: dict[str, list[float]] = {}
    for row in rows:
        by_tier.setdefault(row["tier"], []).append(row["full_score"])
    tier_means = {
        tier: round(sum(vals) / len(vals), 2) for tier, vals in sorted(by_tier.items())
    }

    return {
        "dataset": data["dataset_name"],
        "synthetic": True,
        "score_is_heuristic": True,
        "thresholds": {
            "match_threshold": match_threshold,
            "partial_threshold": partial_threshold,
        },
        "tier_mean_full_scores": tier_means,
        "profiles": rows,
    }


def threshold_sweep(
    match_grid: list[float] | None = None,
    partial_grid: list[float] | None = None,
) -> dict:
    """Sweep thresholds; does not modify production defaults."""
    match_grid = match_grid or [0.50, 0.55, 0.60, 0.65, 0.70]
    partial_grid = partial_grid or [0.35, 0.40, 0.45, 0.50, 0.55]

    data = load_json(PAIRS_PATH)
    examples = data["examples"]
    y_true = [ex["expected"] for ex in examples]

    # Precompute similarities for non-exact pairs
    sims: dict[str, float] = {}
    for ex in examples:
        if ex["expected"] == "exact" and ex["resume_skill"] == ex["jd_skill"]:
            sims[ex["id"]] = 1.0
        else:
            sims[ex["id"]] = pair_similarity(ex["resume_skill"], ex["jd_skill"])

    rows = []
    for match_t in match_grid:
        for partial_t in partial_grid:
            if partial_t >= match_t:
                continue
            preds = []
            for ex in examples:
                pred, _ = predict_semantic_system_pair(
                    ex["resume_skill"],
                    ex["jd_skill"],
                    match_threshold=match_t,
                    partial_threshold=partial_t,
                )
                preds.append(pred)
            summary = summarize(y_true, preds)
            partial_stats = summary["per_class"]["partial"]
            missing_stats = summary["per_class"]["missing"]
            rows.append(
                {
                    "match_threshold": match_t,
                    "partial_threshold": partial_t,
                    "label_accuracy": summary["label_accuracy"],
                    "macro_f1": summary["macro_f1"],
                    "partial_precision": partial_stats["precision"],
                    "partial_recall": partial_stats["recall"],
                    "partial_f1": partial_stats["f1"],
                    "missing_precision": missing_stats["precision"],
                    "missing_recall": missing_stats["recall"],
                    "missing_f1": missing_stats["f1"],
                    "partial_fp": partial_stats["fp"],
                    "partial_fn": partial_stats["fn"],
                }
            )

    rows.sort(key=lambda r: (r["macro_f1"], r["partial_f1"], r["label_accuracy"]), reverse=True)
    return {
        "production_defaults": {
            "match_threshold": DEFAULT_MATCH,
            "partial_threshold": DEFAULT_PARTIAL,
        },
        "n_configs_evaluated": len(rows),
        "ranked_configs": rows,
        "pair_similarities": [
            {
                "id": ex["id"],
                "resume_skill": ex["resume_skill"],
                "jd_skill": ex["jd_skill"],
                "expected": ex["expected"],
                "similarity": round(sims[ex["id"]], 4),
            }
            for ex in examples
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run P0.5 evaluation")
    parser.add_argument("--match-threshold", type=float, default=DEFAULT_MATCH)
    parser.add_argument("--partial-threshold", type=float, default=DEFAULT_PARTIAL)
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Evaluating skill pairs...")
    pairs = evaluate_skill_pairs(args.match_threshold, args.partial_threshold)
    pairs_path = OUT_DIR / "skill_pair_results.json"
    pairs_path.write_text(json.dumps(pairs, indent=2), encoding="utf-8")
    print(f"Wrote {pairs_path}")

    print("Evaluating score profiles...")
    profiles = evaluate_score_profiles(args.match_threshold, args.partial_threshold)
    profiles_path = OUT_DIR / "score_profile_results.json"
    profiles_path.write_text(json.dumps(profiles, indent=2), encoding="utf-8")
    print(f"Wrote {profiles_path}")

    print("Running threshold sweep...")
    sweep = threshold_sweep()
    sweep_path = OUT_DIR / "threshold_sweep.json"
    sweep_path.write_text(json.dumps(sweep, indent=2), encoding="utf-8")
    print(f"Wrote {sweep_path}")

    b = pairs["baseline"]
    s = pairs["exact_plus_semantic"]
    print("\n=== Baseline (exact only) ===")
    print(
        f"n={b['n_examples']} label_accuracy={b['label_accuracy']} "
        f"macro_f1={b['macro_f1']}"
    )
    print("per_class:", json.dumps(b["per_class"], indent=2))
    print("\n=== Exact + semantic ===")
    print(
        f"n={s['n_examples']} label_accuracy={s['label_accuracy']} "
        f"macro_f1={s['macro_f1']}"
    )
    print("per_class:", json.dumps(s["per_class"], indent=2))
    print("\n=== Profile tier mean full scores ===")
    print(profiles["tier_mean_full_scores"])
    print("\n=== Top threshold configs by macro_f1 ===")
    for row in sweep["ranked_configs"][:5]:
        print(row)


if __name__ == "__main__":
    main()
