# Judge model options

The judge is the LLM that checks drafts for the guidebook rules code can't decide (medical advice, pain handling, weight framing, guilt, hype, specificity, invented facts, lab hints). Its model is a setting:

```bash
export JUDGE_PROVIDER=anthropic          # or openai
export JUDGE_MODEL=claude-sonnet-5-5     # default: claude-haiku-5-5
```

**Default: `claude-haiku-5-5`.** It's the cheapest model with zero misses on medical (Rule 1) and privacy (Rule 4) violations against the owner's 40 labels (docs/decisions.md D1).

**Before switching to a model not listed here,** run the comparison for it and check that it has zero Rule 1 and Rule 4 misses and zero judge errors:

```bash
uv run weekly-summary compare-judges --models anthropic:<model>
```

## Final comparison (round 3 judge prompt, 40 owner labels, 2026-10-21)

Each rule cell: agreement · misses of the owner's fails · false alarms. A miss means the owner said fail and the system said pass. Rule 4 is decided by the code checks for every model, so it's the same for all.

| Judge | Rule 1 medical | Rule 2 weight | Rule 3 voice and facts | Rule 4 privacy | Cost per draft | Per 1,000 drafts a day | Wall time, 40 drafts | Errors |
|---|---|---|---|---|---|---|---|---|
| **claude-haiku-5-5 (default)** | 39/40 · 0 of 16 · 1 | 38/40 · 2 of 5 · 0 | 29/40 · 7 of 23 · 4 | 40/40 · 0 of 14 · 0 | **$0.0014** | **$1.35** | **49s** | 0 |
| claude-sonnet-5-5 | 39/40 · 0 of 16 · 1 | **40/40 · 0 of 5 · 0** | 29/40 · 6 of 23 · 5 | 40/40 · 0 of 14 · 0 | $0.0233 | $23 | 64s | 0 |
| claude-opus-5-5 | 39/40 · 0 of 16 · 1 | 38/40 · 2 of 5 · 0 | 29/40 · 6 of 23 · 5 | 40/40 · 0 of 14 · 0 | $0.0460 | $46 | 86s | 0 |
| Code checks only (no judge) | 24/40 · 16 of 16 · 0 | 36/40 · 4 of 5 · 0 | 24/40 · 15 of 23 · 1 | 40/40 · 0 of 14 · 0 | $0 | $0 | <1s | – |

## What you get for the money

- **Haiku → Opus (34× the cost):** the same verdicts on Rules 1, 2 and 4. Nothing gained on the safety rules.
- **Haiku → Sonnet (17× the cost):** Sonnet also catches the two subtle weight-praise drafts Haiku misses ("your weight trended down a little this week as well", and a half-pound loss listed among wins). Worth it if coaches care most about Rule 2 subtlety. One of the two drafts is blocked for privacy anyway.
- **No judge at all:** free, and still catches every privacy violation (Rule 4 is all code), but misses every medical violation (16 of 16). The judge is what makes Rule 1 safe.
- **Rule 3 (voice and invented facts)** is the most subjective rule. Every model agrees with the owner on about 29 of 40, with misses and false alarms in both directions. It's a "flag for the coach" rule, not a safety rule.

## OpenAI models (round 1 judge prompt only)

These ran only on the first version of the judge prompt, before the lab-interpretation definition was added, so they aren't directly comparable with the table above. On the same prompt, they missed more medical violations than the Claude models (Claude 1–2 misses, OpenAI 3–5).

| Judge (round 1) | Rule 1 misses of 16 | Cost per draft | Errors |
|---|---|---|---|
| gpt-6-luna | 3 | $0.0009 | 1 |
| gpt-6.1-sol | 5 | $0.0122 | 0 |
| gpt-6-astra | 5 | $0.0594 | 0 |

To retest them on the current prompt: `uv run weekly-summary compare-judges --models openai:gpt-6-luna,openai:gpt-6.1-sol,openai:gpt-6-astra`.

## How the judge prompt got here (three rounds)

| Round | Change | Result | Files |
|---|---|---|---|
| 1 | First prompt, six models | Most Rule 1 misses were drafts interpreting lab results, which the owner labels as medical advice and the prompt never mentioned | `results/judge_runs_v1/` |
| 2 | Added "lab results or health markers" | Zero Rule 1 misses, but Haiku and Sonnet flagged allowed trend words ("recovery trends heading the right way"). Haiku produced broken JSON 3 times (double quotes inside reasons). | `results/judge_runs_v2/` |
| 3 | Narrowed to clinical markers (blood pressure, cholesterol, blood sugar); trend words explicitly allowed; single quotes in reasons | Zero Rule 1/4 misses, one false alarm, zero errors for all three | `results/judge_runs_v3/` |

**Caveat:** the same 40 labels tuned the prompt and score it, so these numbers flatter the judge somewhat. Each change was a shared definition, not a fix for one draft. Three Rule 2 labels were also changed by the owner after reviewing the judges' disagreement (kept as `rule_2_before_review`).

Prices: list prices per million tokens as of 2026-10-21 (Haiku $0.10 / $0.50, Sonnet $2 / $10, Opus $4 / $20, gpt-6-luna $0.10 / $0.50, gpt-6.1-sol $2 / $10, gpt-6-astra $10 / $50). Costs use measured token counts. "Per 1,000 drafts a day" is cost per draft × 1,000. Wall time is with 8 drafts judged in parallel.
