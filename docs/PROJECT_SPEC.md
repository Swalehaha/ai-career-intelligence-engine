# AI Career Intelligence Engine — Project Specification

Read this document before making project changes.

## Goal
Build and deploy an ML/NLP-powered career decision-support system that compares a resume with job descriptions, extracts/matches skills, identifies skill gaps, ranks priorities, and produces actionable recommendations.

## V1 MUST BUILD
- Resume PDF extraction
- JD text input
- Preprocessing and section handling
- Skill extraction
- Exact skill matching baseline
- Embedding-based semantic matching
- Interpretable match scoring
- Matched/partial/missing skill analysis
- Skill-gap priority ranking
- Small labelled evaluation set
- Metrics + error analysis
- FastAPI backend
- Simple polished web UI
- Public deployment
- README + architecture diagram + screenshots + tests + demo

## NICE TO HAVE
- Multiple JDs
- Resume suggestions
- Interview questions
- Learning recommendations
- Downloadable report
- Skill taxonomy

## NON-GOALS
- Generic chatbot
- Black-box LLM-only scoring
- Claims of being an official ATS
- Over-engineered auth/infrastructure

## Architecture
Resume PDF -> Extraction -> Preprocessing -> Structuring
JD -> Preprocessing -> Structuring
Resume/JD -> Skill Extraction -> Exact Matching + Embedding Similarity -> Scoring -> Skill Gap Analysis -> Recommendations -> FastAPI -> UI -> Deployment

## ML Principles
- Build an exact-match baseline first.
- Add semantic matching as the improvement.
- Evaluate on held-out labelled examples.
- Do not fabricate metrics.
- Error analysis is mandatory.
- Separate deterministic logic, ML/embedding logic, and generative AI.

## Git Structure
ai-career-intelligence-engine/
- app/
- ml/
- data/
- notebooks/
- tests/
- frontend/
- docs/
- scripts/
- requirements.txt
- Dockerfile
- README.md

## AI-Agent Rules
- Read this file first.
- Inspect the repository before changing it.
- Plan before large edits.
- Make small, testable changes.
- Run verification after meaningful changes.
- Never commit secrets.
- Never invent evaluation results.
- Do not add unnecessary dependencies.
- Ask the mentor before material ML/business-logic decisions.

## Human Understanding
🟢 Must understand: architecture, data flow, scoring, semantic similarity, evaluation, metrics, major errors, deployment.
🟡 Learn later: transformer internals, embedding mathematics, advanced ranking, vector DB internals.
🔵 AI can handle: boilerplate, frontend scaffolding, Docker, configuration, test scaffolding, CI, formatting.

## First Agent Task
Read this document. Inspect the repository. Do NOT build the entire application. Report current state, Day 1 architecture/files, proposed stack/dependencies, risks/ambiguities, and a concrete Day 1 plan. Wait for approval before large implementation.
