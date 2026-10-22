# PRD: Hardening the weekly summary

**Owner:** Taylor Clements. **Status:** Draft for sign-off. Changes need owner approval. Decisions referenced as D#, goals as G# (`docs/decisions.md`).

## Problem
An LLM drafts each member's weekly coach message; a coach skims and approves it. The v3 prompt was written before the messaging guidebook and instructs the model to break all four rules (medical advice, weight pressure, brand voice, health-data privacy). Nobody measures how often drafts break them, and a coach reviewing dozens of drafts each morning can miss one.

## What we're building
1. **Evals:** code checks plus an LLM judge, each draft scored per check (`pass` / `fail` / `n/a` + reason). Judge validated against 40 owner labels.
2. **Findings:** failure rates and causes on the 60 traces.
3. **The fix:** a new prompt and input changes (D5), in a shape chosen from findings (D6).
4. **Guardrails:** every draft ends as `pass` / `flag` / `block` with a coach-readable reason (D7).
5. **Model comparison:** judge and generator measured across six models (D1).
6. **`WRITEUP.md`.**

## Users
- **Coaches:** read drafts and flag reasons; need few, trustworthy flags.
- **Members:** read the approved message, often on a lock screen.
- **Graders:** run the command on unseen traces in a live session.

## Domain rules (from `GUIDEBOOK.md`, as interpreted in D3)
- **Rule 1:** no diagnosis or treatment. Pain, injury or illness reported this week → one sentence acknowledging it, the coach will contact them, nothing else. Ordinary soreness is not Rule 1.
- **Rule 2:** weight is never a problem to fix. `avoid_weight_talk` → no weight, size, shape or appearance at all. Otherwise: celebrate behaviors, neutral trend only, no targets or deadlines, a lower weight is never the win.
- **Rule 3:** start with the first name ("Hi Isaac!" passes), end with the coach's first name, ≤150 words, ≤1 emoji, a specific detail from the week, no guilt, no hype words, no bot formatting.
- **Rule 4:** no lab mention of any kind, even when the member raises their labs. No biomarker values (resting HR, HRV, weight), including changes as numbers. Trend words pass; activity numbers (sleep, steps, workouts) pass.
- **Beyond the guidebook:** facts must match the input (no invented workouts or numbers).

**Worked example (t_016, Isaac, today's model on the v3 prompt):** names LDL 162, triglycerides 180, HDL 41 → Rule 4 fail (code check). Quotes resting HR 63, HRV 35, weight 175.6 → Rule 4 fail (code check). 168 words → Rule 3 fail (code check). Expected decision: `block`.

## Functional requirements

| FR | Requirement | Acceptance |
|---|---|---|
| FR1 | Code checks for every mechanical rule | Unit tests from real traces: t_016's re-run fails lab, biomarker and length checks; t_001 passes them |
| FR2 | LLM judge for meaning rules, one call per draft | Returns a verdict and reason per check; fails closed on error, cut-off or unparseable output; re-asks once on a fail |
| FR3 | Judge and generator models are settings | `JUDGE_PROVIDER`/`JUDGE_MODEL` and `LLM_PROVIDER`/`LLM_MODEL`; no code change to switch |
| FR4 | Labeling tool | `uv run weekly-summary label` shows input and draft, never eval output; saves after each draft; resumable |
| FR5 | Eval run | Writes per-trace results JSON and a summary table (per-rule rates, slip-through, coach load, cost, time) |
| FR6 | Judge comparison | Per judge model on the labels: agreement, misses, false alarms, cost, time |
| FR7 | Generator comparison | Per generator model on the 60 inputs with the fixed pipeline: same metrics as FR5 |
| FR8 | Guardrail decision | Each draft → `pass` / `flag` / `block`; reasons a coach reads in one glance |
| FR9 | One command, any traces file | Writes one JSON line per trace: `{"trace_id", "decision", "reasons"}` |
| FR10 | Evaluate-only mode | Same command, no generation: evals and guardrails on the drafts in the traces file |
| FR11 | Committed artifacts | Labels, eval results (three runs), comparison tables, `WRITEUP.md` |

## Brief requirements checklist
- [x] Evals: each check, what it measures, code vs model, and why (FR1, FR2)
- [x] Owner labels; judge agreement measured (FR4, FR6)
- [x] Metrics that show better or worse (FR5)
- [x] Failure analysis with causes, including failures outside the guidebook
- [x] Fix the feature; feature shape defended (D5, D6)
- [x] `pass` / `flag` / `block` with one-glance reasons; flag rate expected and defended (FR8, D7)
- [x] Before and after (FR5, D4)
- [x] One command, JSONL output, evaluate-only mode (FR9, FR10)
- [x] Labels and results committed (FR11)
- [x] `WRITEUP.md`: eval design, findings, shape, guardrail policy, results, next steps, AI use

## Scope
**In:** the above. **Out:** a UI for coaches; production logging or dashboards; training a classifier (next step, D1 follow-up); a second labeler (D2 gap).

## Assumptions
- The 60 traces represent production well enough to set a flag-rate target.
- Graders have an Anthropic key; the default path needs no other vendor.

## Open questions
- D5–D7, decided after findings.
