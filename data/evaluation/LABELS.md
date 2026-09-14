# Evaluation Dataset — Labelling Guide

**Status:** Synthetic / constructed for development evaluation.  
**Not** a production ATS benchmark. Labels were defined *before* running system metrics.

## Unit of evaluation

Primary unit: a **skill pair**

- `resume_skill`: one canonical skill assumed present on the resume
- `jd_skill`: one canonical skill required by the JD
- `expected`: gold label in `{exact, partial, missing}`

Secondary unit: a **profile** (multi-skill resume vs multi-skill JD) used only to check whether the heuristic overall score ranks strong > medium > weak. Profiles do **not** have gold numeric scores.

## Label definitions

| Label | Meaning |
|-------|---------|
| `exact` | Same canonical skill (after alias normalization). Example: resume `Python`, JD `Python`. |
| `partial` | Different canonical names, but a reasonable recruiter/engineer would treat them as related substitutes or close family (framework↔framework, DB↔DB, library↔concept it implements). Example: `Flask`↔`FastAPI`, `MySQL`↔`PostgreSQL`, `spaCy`↔`Natural Language Processing`. |
| `missing` | No meaningful skill relationship for matching credit. Example: `Docker`↔`Tableau`, `React`↔`Kubernetes`. |

## Labelling rules (applied before measurement)

1. Identical canonical skill → `exact`.
2. Alias of the same skill (e.g. `JS` / `JavaScript`) would be `exact` after normalization; pairs here use canonical forms already.
3. Same family / near-substitute tools → `partial` (web frameworks, SQL RDBMS, closely related cloud/container tools only when clearly adjacent).
4. Concept ↔ library that primarily implements that concept → `partial` (e.g. NLP↔spaCy, ML↔scikit-learn) when the library is a standard way to demonstrate the concept.
5. Unrelated domains, or only weakly associated buzzwords → `missing`.
6. When uncertain between `partial` and `missing`, prefer `missing` (conservative gold).

## What this dataset does *not* claim

- It does not measure PDF extraction quality.
- It does not measure end-to-end resume parsing.
- It does not define a “correct” overall match percentage for hiring.
- It is small and synthetic; metrics are indicative, not publishable SOTA claims.
