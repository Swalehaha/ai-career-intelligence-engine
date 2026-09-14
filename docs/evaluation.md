# Evaluation & Error Analysis (P0.5)

**Scope:** Make skill matching measurable and interview-defensible.  
**Dataset:** Synthetic / constructed for development (`data/evaluation/`).  
**Rule:** Metrics below were computed *after* labels were frozen. Numbers are not invented and are **not** claimed as production ATS accuracy.

Production scoring formula was **not** changed during this phase:

```text
100 * (exact + 0.85 * semantic + 0.40 * partial) / jd_skills
```

This formula is a **heuristic**, not ground truth and not a probability.

---

## 1. Evaluation dataset and labelling method

### Files

| Path | Role |
|------|------|
| `data/evaluation/LABELS.md` | Labelling criteria |
| `data/evaluation/skill_pairs.json` | 30 skill-pair examples |
| `data/evaluation/score_profiles.json` | 6 multi-skill score sanity profiles |
| `data/evaluation/out/*.json` | Machine-written results from `python -m evaluation.run_eval` |

### Primary unit: skill pairs (n=30)

Each example has:

- `resume_skill`, `jd_skill` (canonical vocabulary names)
- `expected` ∈ `{exact, partial, missing}`
- `category`, `notes`

**Label distribution (gold):** exact=6, partial=15, missing=9

### Labelling summary

- `exact` — same canonical skill  
- `partial` — related substitute / library↔concept / adjacent tools (conservative: when unsure, prefer `missing`)  
- `missing` — no meaningful match credit  

Full rules: `data/evaluation/LABELS.md`.

### What this dataset does *not* evaluate

- PDF extraction quality  
- Free-text skill extraction from messy resumes  
- Hiring outcomes or recruiter judgments at scale  

Matching is evaluated on **already-canonical skill strings** to isolate the matcher from the extractor.

---

## 2. Baseline methodology

**System A — Exact matching baseline**

1. Compare canonical skill names with set intersection (`ml.matching.exact.exact_match`).  
2. If equal → predict `exact`.  
3. Otherwise → predict `missing`.  
4. Baseline **never** predicts `partial`.

This is deterministic string/canonical equality after vocabulary normalization (aliases are upstream of this eval).

---

## 3. Semantic methodology

**System B — Exact + embedding semantic matching**

1. Exact match first (same as baseline).  
2. For unmatched JD skills, embed short skill **descriptions** (`ml.skills.descriptions`) with `sentence-transformers/all-MiniLM-L6-v2`.  
3. Cosine similarity to the best resume skill:  
   - ≥ `0.60` → production bucket `semantic_matched`  
   - ≥ `0.45` → production bucket `partial`  
   - else → `missing`  

### Label mapping used for metrics

Gold has 3 classes. Production has an extra `semantic_matched` bucket.

For classification metrics:

| Production status | Mapped eval label |
|-------------------|-------------------|
| exact | `exact` |
| semantic_matched | `partial` |
| partial | `partial` |
| missing | `missing` |

Rationale: both non-exact similarity buckets mean “related, not identical.”

**Distinction of system parts**

| Layer | Type |
|-------|------|
| Vocabulary / aliases / exact match | Deterministic rules |
| MiniLM embeddings + thresholds | Embedding-based ML |
| Overall 0–100 score | Heuristic (not trained) |
| Future resume rewrite / interview Qs | Generative AI (not in P0 matching) |

---

## 4. Metrics

### Appropriate for skill-pair classification

- Per-class precision / recall / F1  
- Macro-F1  
- Confusion matrix  
- Label accuracy (share of examples with exact label match) — **not** called “model accuracy” of an ATS score  

### Not used as claims of score quality

- Calling the heuristic overall score “accuracy”  
- ROC/AUC (no probabilistic calibrated score for class membership)  
- Resume-level ranking metrics (too few profiles; no ranked candidate list)

### How to reproduce

```bash
python -m evaluation.run_eval
pytest
```

---

## 5. Results (computed)

Source: `data/evaluation/out/skill_pair_results.json`  
Thresholds: match=`0.60`, partial=`0.45` (production defaults)

### Baseline (exact only)

| Metric | Value |
|--------|-------|
| n | 30 |
| Label accuracy | 0.5000 |
| Macro-F1 | 0.5152 |

| Class | Precision | Recall | F1 | Support |
|-------|-----------|--------|-----|---------|
| exact | 1.0000 | 1.0000 | 1.0000 | 6 |
| partial | 0.0000 | 0.0000 | 0.0000 | 15 |
| missing | 0.3750 | 1.0000 | 0.5455 | 9 |

Confusion (rows=actual, cols=predicted):

|  | exact | partial | missing |
|--|------:|--------:|--------:|
| exact | 6 | 0 | 0 |
| partial | 0 | 0 | 15 |
| missing | 0 | 0 | 9 |

**Interpretation:** Baseline is perfect on identical skills and correctly keeps unrelated pairs as missing, but cannot recover any related/partial pairs (by design).

### Exact + semantic

| Metric | Value |
|--------|-------|
| n | 30 |
| Label accuracy | 0.9333 |
| Macro-F1 | 0.9429 |

| Class | Precision | Recall | F1 | Support |
|-------|-----------|--------|-----|---------|
| exact | 1.0000 | 1.0000 | 1.0000 | 6 |
| partial | 1.0000 | 0.8667 | 0.9286 | 15 |
| missing | 0.8182 | 1.0000 | 0.9000 | 9 |

Confusion:

|  | exact | partial | missing |
|--|------:|--------:|--------:|
| exact | 6 | 0 | 0 |
| partial | 0 | 13 | 2 |
| missing | 0 | 0 | 9 |

**Interpretation on this synthetic set:** Semantic matching recovered 13/15 related pairs with **zero false partials** among the 9 gold-missing pairs. Two related pairs remained missing.  

**Caveat:** High scores on n=30 synthetic pairs do **not** generalize to messy real resumes. Treat as a development smoke evaluation.

### Score heuristic sanity (profiles)

Source: `data/evaluation/out/score_profile_results.json`

Mean **full-system** heuristic scores by declared tier:

| Tier | Mean full score | Notes |
|------|----------------:|-------|
| strong | 100.00 | Near-complete exact overlap |
| medium | 66.53 | Mix of exact / semantic / gaps |
| weak | 0.00 | Unrelated or false-friend risks |

Ordering **strong > medium > weak** holds on these constructed profiles. That supports *sensibility*, not correctness of the numeric score.

Selected profile contrasts:

| Profile | Baseline score | Full score | Comment |
|---------|---------------:|-----------:|---------|
| prof_strong | 100.00 | 100.00 | Exact coverage complete |
| prof_medium | 16.67 | 65.83 | Semantic lift from Flask/MySQL/spaCy |
| prof_semantic_heavy | 0.00 | 73.75 | No exact overlap; related pairs dominate |
| prof_weak | 0.00 | 0.00 | Stays weak |
| prof_false_friend_risk | 0.00 | 0.00 | Java did not match JavaScript |

---

## 6. Error analysis

### Semantic-system failures on the frozen set (2)

| Example | Resume | JD | Expected | Predicted | Similarity | Error category | Why | Proposed improvement |
|---------|--------|-----|----------|-----------|------------|----------------|-----|----------------------|
| sp29 | CI/CD | GitHub Actions | partial | missing | 0.2259 | concept↔tool / weak description overlap | Descriptions do not place them near each other in embedding space | Enrich description (“GitHub Actions CI/CD automation”) or curated related-skill edges |
| sp30 | REST APIs | GraphQL | partial | missing | 0.3236 | API-style family under-similar | Embeddings treat API styles as fairly distinct | Add shared phrasing (“web API interface style”) carefully, or curated family map |

### Additional representative failure / risk cases (≥5 including baseline contrast)

| Example | Resume | JD | Expected | Predicted (system) | Similarity | Error category | Why | Proposed improvement |
|---------|--------|-----|----------|-------------------|------------|----------------|-----|----------------------|
| sp07 (baseline) | Flask | FastAPI | partial | missing (baseline) | n/a | baseline cannot model relatedness | Exact-only system | Keep semantic layer (already fixed in System B) |
| sp13 (borderline) | scikit-learn | Machine Learning | partial | partial | 0.4611 | library↔concept near threshold | Only 0.011 above partial=0.45; fragile | Monitor; improve description; avoid raising partial threshold blindly |
| sp18 | React | Next.js | partial | partial | 0.5389 | framework family mid-band | Works today but sits in partial band only | Stronger React-ecosystem descriptions |
| Java↔JavaScript (profile risk) | Java | JavaScript | missing (desired) | missing | 0.4079 | abbreviation / naming false friend | Below partial threshold — currently safe | **Do not** lower partial threshold to ≤0.40 without new negative examples |
| sp16 | Docker | Kubernetes | partial | partial | 0.5903 | tool adjacency | Correct related match; not identity | Keep as partial credit (already weighted 0.40 in score) |

**Major error patterns observed**

1. **Missed related skills** when concept↔specific tool wording differs a lot (CI/CD↔GitHub Actions).  
2. **Borderline similarities** for library↔concept pairs (scikit-learn↔ML).  
3. **False-friend risk** (Java↔JavaScript ~0.41) — currently avoided by threshold, but leaves little margin.  
4. **Baseline systematic miss** of all partial relations (expected).  
5. **No false semantic matches** on this particular missing set — good, but the set is small; do not over-claim robustness.

---

## 7. Threshold analysis

Sweep results: `data/evaluation/out/threshold_sweep.json` (22 valid configs where `partial < match`).

Production defaults: **match=0.60, partial=0.45** → macro-F1 **0.9429**, partial FP **0**, partial FN **2**.

### What changes thresholds do on this set

| Change | Effect on this dataset |
|--------|-------------------------|
| Lower partial toward 0.35–0.40 | Same macro-F1 here, but **Java↔JavaScript (0.4079)** becomes a false-partial risk if partial ≤ ~0.40 |
| Raise partial to 0.50 | Macro-F1 drops to **0.9153**; loses borderline related pairs (e.g. scikit-learn↔ML at 0.4611) |
| Raise partial to 0.55 | Macro-F1 drops to **0.8881**; more related FN |
| match ∈ [0.50, 0.70] with partial=0.45 | Macro-F1 unchanged on this set (failures are far below 0.45) |

### Recommendation

**Keep production thresholds at match=`0.60`, partial=`0.45` for now.**

Reasons:

1. They sit in the best macro-F1 band on the frozen set.  
2. Raising partial hurts related-skill recall without reducing FP (FP already 0 here).  
3. Lowering partial risks the Java/JavaScript false friend before it recovers the two hard FN pairs (similarities 0.23 and 0.32 — far below safe partial values).  
4. Recovering sp29/sp30 is better done via **description enrichment or curated relations**, not aggressive threshold cuts.

No production threshold change was applied in this phase.

---

## 8. Known limitations

- Small synthetic n=30; class balance favors partial examples.  
- Skill descriptions are hand-written and influence embedding geometry (a form of knowledge engineering).  
- Pair eval ignores multi-skill competition (best-of-many resume skills can create different errors).  
- PDF/extraction errors are out of scope here.  
- Heuristic score is not calibrated to hiring decisions.  
- High F1 on this set can look “too good” — report with caveats in interviews.

---

## 9. Future improvements

1. Expand labelled pairs with more intentional hard negatives (Java/JavaScript, C/C++, AWS service name collisions).  
2. Multi-skill resume↔JD labelled sets with extraction included.  
3. Description quality review + frozen description versioning.  
4. Optional curated related-skill graph for concept↔tool pairs embeddings miss.  
5. Human-labelled real (anonymized) resumes when available — replace synthetic reliance.  
6. Revisit score weights only after larger labelled coverage studies — **not** because the heuristic “failed” the sanity ordering.

---

## Scoring formula decision

**Keep the current scoring formula unchanged.**

Evidence from profiles: strong/medium/weak ordering is sensible; semantic credit visibly lifts related-but-not-exact profiles (`prof_semantic_heavy`: 0 → 73.75) without inflating weak/false-friend profiles. Changing weights now would be premature relative to the matching-label evidence.

---

## 10. Follow-up: description enrichment (post P0.5)

After the initial error analysis, skill **descriptions** (not thresholds, not labels, not the score formula) were enriched for:

- `CI/CD` / `GitHub Actions`
- `REST APIs` / `GraphQL`
- clearer `Java` vs `JavaScript` wording
- slightly clearer `scikit-learn` phrasing

**Re-run results on the same frozen labels** (`python -m evaluation.run_eval`):

| System | Label accuracy | Macro-F1 | Semantic errors |
|--------|----------------|----------|-----------------|
| Baseline | 0.5000 | 0.5152 | n/a (15 partial→missing) |
| Exact + semantic (after enrichment) | **1.0000** | **1.0000** | **0** |

Key similarities after enrichment:

| Pair | Similarity | Notes |
|------|------------|-------|
| CI/CD ↔ GitHub Actions | 0.7574 | previously 0.2259 (FN) |
| REST APIs ↔ GraphQL | 0.5940 | previously 0.3236 (FN) |
| Java ↔ JavaScript | 0.4356 | previously ~0.4079; still &lt; 0.45 partial threshold |
| scikit-learn ↔ Machine Learning | 0.5271 | more stable above partial threshold |

### Honest limitation

This 1.0 result is **not** an independent holdout score. Descriptions were adjusted using knowledge of the failure cases on this same 30-pair set. Treat it as confirmation that description quality matters, **not** as proof the matcher is solved for real resumes.

**Thresholds and scoring formula remain unchanged** (`0.60` / `0.45`; same heuristic score).
