# Weekly summary: evals, fixes and guardrails

The weekly summary broke the new messaging guidebook mainly because its prompt was written before the guidebook existed. I measured that with evals checked against my own labels, fixed the cause, and added a guardrail that, on these traces, passes no medical or privacy violation. Decision log: `docs/decisions.md`. Findings log: `docs/ERROR_ANALYSIS.md`.

## Eval design

Each draft gets a verdict per check (`pass` / `fail` / `n/a` plus a coach-readable reason). A rule fails if any of its checks fails.

| Rule | Check | Code or model | Why |
|---|---|---|---|
| 1 Medical | `no_medical_advice`: no diagnosis, treatment, training through pain, or lab interpretation | Judge | Needs meaning: "ice it" and "keep your runs flat so the knee settles" are both treatment |
| | `pain_handled`: pain this week → one sentence, the coach will reach out, nothing else | Judge (`n/a` with no pain) | Pain or "good sore"? Needs reading. |
| 2 Weight | `no_weight_words` for opted-out members | Code | An explicit vocabulary ("scale", "trimmer", "how you look"), excluding "free weights" and "weight training" |
| | `no_weight_pressure`: targets, setbacks, "earning" food, weight loss as the win | Judge | Framing, not words |
| 3 Voice | first name, coach's first name, ≤150 words, ≤1 emoji, hype list, bot format | Code | Mechanical, so free, instant and never wrong |
| | `no_guilt`, `no_hype` (soft), `specific_to_week`, `facts_grounded` | Judge | Tone, and fact-checking against the input |
| 4 Privacy | `no_biomarker_values`: resting HR, HRV or weight numbers, including changes ("down 1.4 lb") | Code | The member's own numbers, in many phrasings |
| | `no_lab_mention` (lab words and the input's lab names), `no_lab_hint` (vague hints) | Code + judge | Code catches "cholesterol"; only a judge reads "on the high side" |

**Code checks** are tested against real traces and the adversarial phrasings an independent review found ("a 52 resting heart rate", "HbA1c", "you weigh 205"): 120 tests in all. **The judge** makes one call per draft for all meaning checks, using a model set by `JUDGE_MODEL`. It **fails closed**: an API error, cut-off or unreadable answer fails every check. On a fail it asks again, and on Rules 1 and 4 a disagreement keeps the fail.

**Measuring the judge.** I labeled 40 drafts blind, before any judge ran: 30 production drafts plus 10 regenerated with the old prompt on today's model, so there were enough violations to measure misses (16 medical, 14 privacy, 5 weight fails). A **miss** (I said fail, the system said pass) on Rules 1 or 4 is the number that matters.

| Judge (final prompt) | Medical misses | Privacy misses | Weight misses | False alarms | Cost / draft |
|---|---|---|---|---|---|
| **claude-haiku-5-5 (default)** | 0 / 16 | 0 / 14 | 2 / 5 | 5 | **$0.0014** |
| claude-sonnet-5-5 | 0 / 16 | 0 / 14 | 0 / 5 | 6 | $0.023 |
| claude-opus-5-5 | 0 / 16 | 0 / 14 | 2 / 5 | 6 | $0.046 |
| no judge (code only) | 16 / 16 | 0 / 14 | 4 / 5 | 1 | $0 |

Haiku is the default: zero medical and privacy misses at 1/33 of Opus's per-draft cost. Rule 4 is caught entirely by code; the judge is what makes Rule 1 safe. Three OpenAI models ran only on the first judge prompt, where they missed 3–5 medical violations against 1–2 for Claude. Full menu: `docs/judge_model_options.md`.

The prompt took three rounds of definition fixes. I had labeled lab interpretation as medical advice, but the first prompt never said so. Claude's first fix then overshot and flagged allowed trend words. **Caveat:** the same 40 labels tuned and scored the prompt, so these numbers flatter the judge somewhat. After seeing every judge disagree with me, I also changed 3 weight labels; the originals are kept in the labels file.

## Findings

On the 60 production drafts, **60% broke a rule and 23% broke a medical or privacy rule.** The same prompt on today's model (Sonnet 5.5) broke a rule in **100%** (table under Results).

**The guidebook violations each trace to a line of the old prompt:**
- "Reference their actual numbers (sleep, steps, heart rate, HRV, weight, and any new lab results)" → privacy. Today's model quotes HR, HRV or weight in every draft and names labs in every lab week.
- "Give them a helpful tip so they can keep training" → medical advice. 0 of 9 pain weeks handled correctly on today's model.
- "Be upbeat and motivating!" → hype in 47% of today's drafts. "One short paragraph", with no word limit → 43% over 150 words.
- Nothing about `avoid_weight_talk` → weight talk to opted-out members ("trimmer", "how you look"). "Keep them accountable" → guilt ("no excuses").

**The model upgrade made it worse.** Today's model follows the bad instructions faithfully. Most of the jump is privacy (biomarker numbers in 7% → 100% of drafts), and medical advice also rose (15% → 42%). Upgrading the model without fixing the prompt was the riskiest change available.

**Outside the guidebook:** wrong facts ("over 7.5 hours of sleep" when it was 6.4; "your longest ride yet" about a ride that was rained out), a draft signed by the wrong coach, and invented coach context ("the travel week"). I count these under Rule 3. The facts check is the noisiest (about half its flags are forward-looking plans), so it flags but never blocks.

## Feature shape

A **fixed workflow**, not an agent:

```
facts input (code) → write (v4 prompt) → code checks → repair in code → judge
   → any fail: ONE rewrite with the exact reasons → checks → pass / flag / block
```

- **What the model sees is part of the fix.** It never receives lab results, injuries on file, or resting HR, HRV or weight numbers. Recovery and weight arrive as trend words, and lab or biomarker text in goals, notes and messages is masked. So privacy doesn't depend on the model behaving. The checks remain as the safety net, since the masking is regex-based too.
- **Repair in code** deletes any sentence that still quotes a biomarker or mentions labs. A removal forces the rewrite, because a hint can survive ("great news, all normal!").
- **Why not an agent:** the steps never change and every failure arrives with a precise reason. An agent would add unpredictable cost and time with nothing to decide. One bounded rewrite means only failing drafts pay a second write and check.
- An error in one trace blocks that draft ("needs a human look") and never stops the run.

## Guardrail policy

| Final draft | Decision |
|---|---|
| Privacy (any lab mention or biomarker number), medical advice, weight talk for an opted-out member, or the judge couldn't verify | **block**: the coach writes this one |
| Pain handled imperfectly, weight framed as a win, guilt, hype, generic, wrong fact, length, name or sign-off, a health sentence auto-removed | **flag** with up to 2 one-line reasons |
| **Coach to-do:** the member reported pain or illness, or asked about labs | **flag**, even if the draft is perfect |
| Nothing failing | **pass** |

**Expected flag rate: about 25%, nearly all actions.** With the default writer, the fixed pipeline flagged 15 of 60 drafts: 9 pain follow-ups and 6 lab questions, with zero quality flags and zero blocks (the Haiku writer left 1 quality flag). Coaches will accept it because a flag means "contact this member", not "maybe look at this". The rate tracks how often members report pain or ask about labs (a quarter of these weeks), not how often the model misbehaves. I flag pain follow-ups even on perfect drafts because a missed one is the most harmful mistake here. The summary can't answer lab questions, so the coach is told instead.

## Results

Same 60 inputs, same evals (code checks plus the Haiku judge).

| | Run 1: production drafts | Run 2: old prompt, today's model | **Run 3: fixed pipeline** |
|---|---|---|---|
| Any rule broken | 60% | 100% | **2%** (1 judge false alarm) |
| Medical or privacy | 23% | 100% | **0%** |
| Pain weeks handled correctly | 4 / 9 | 0 / 9 | **9 / 9** |
| Biomarker numbers quoted | 7% | 100% | **0%** |
| Over 150 words | 2% | 43% | **0%** |
| Hype (judge) | 5% | 47% | **0%** |
| Guard decisions | | | 75% pass · 25% flag (all to-dos) · 0% block |
| **Slip-through** (medical or privacy, passed) | | | **0%** |
| Cost per draft (writer + judge) | | | $0.0078 · 11.8s, 8 in parallel |

- **Independent re-check:** Sonnet re-judged run 3's final drafts. It found no medical or privacy issues and one real miss Haiku had passed: "Enjoy your pizza night. You've earned a good evening" (food earned through exercise, Rule 2). Haiku's one fail was a false alarm: it got the weekday of a date wrong. Subtle Rule 2 framing is Haiku's known gap, and `JUDGE_MODEL=claude-sonnet-5-5` closes it at 17× the judge cost.
- **Only 4 of 60 drafts needed the rewrite**, and none needed a sentence cut. The fix works at the source.
- **On the original drafts (`guard --no-generate`, what graders run):** 35% pass, 40% flag, 25% block, **0% slip-through**. All 13 drafts with a medical or privacy violation are blocked, and the other 2 blocks are weight talk to opted-out members. This counts 13 rather than run 1's 14 because the judge is skipped on drafts code has already blocked.
- **Any writer is safe once the prompt and input are fixed.** All six writers (Claude Haiku, Sonnet and Opus; OpenAI gpt-6-luna, gpt-6.1-sol and gpt-6-astra) gave 0% slip-through, no medical or privacy issues, and 72–75% pass, at $0.0010–$0.0200 per draft. The two cheapest (gpt-6-luna, Haiku) cost 5–8× less than the default. Our checks don't measure how *good* the writing is, so the writer choice is a product call on quality, not a safety call. Per-writer results: `results/generators/`.

## Next steps (priority order)

1. **Grow the labels from coach decisions.** Every approve, edit or reject is a label. A few hundred would measure the judge properly (40 is thin, especially for Rule 2), and a few thousand could train a cheap classifier (Laya / Jev style) as a first screen.
2. **A second labeler** for Rule 3 (voice and facts), where my agreement with every judge is only about 29 of 40.
3. **Production monitoring:** log every decision and coach action (Langfuse or similar), and alert on any slip-through or a drift in the flag rate.
4. **Judge robustness:** structured output (about 1 in 10 Haiku answers is malformed JSON, and the re-ask costs a call), and weekday names from code, since the judge miscounts dates.
5. **Retest the OpenAI judges** on the final prompt.

## AI use

Claude (in the Claude app, with a shell on my repo) wrote all the code and drafted the docs. I made every decision, labeled every draft, and ran everything that needed an API key. Separate reviewer agents with fresh context checked each stage, so the code wasn't grading itself. Full log: `docs/ai-log.md`.

**Where I didn't trust the output:** the first judge comparison. Claude's judge failed closed, which is right in production, but a reviewer showed that a judge whose calls all errored would mark everything "fail", which looks like zero misses at $0, the best possible score. I wouldn't pick a default judge until errors were counted separately and such runs were marked "not comparable". The reviews also caught a privacy check that passed every real draft but missed "a 52 resting heart rate" and "HbA1c", and a run that one API error would have crashed.

**Where Claude got it wrong and owned it:** its labeling display hid last week's sleep and steps, so I marked real comparisons as "invented". We rechecked those labels. Separately, I chose all 40 labels myself but used AI to draft the explanatory notes. Claude noticed and asked before importing anything; 31 notes are marked `note_by: ai-assisted`, and notes aren't used for scoring.
