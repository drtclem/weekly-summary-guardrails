# Decision log

Every product and architecture choice for hardening the weekly-summary feature. Source of the writeup's trade-offs and limitations.

## Goals every decision is judged against

Signed off by owner, 2026-10-21. Context: Claude writes the code; Taylor decides and labels. Anthropic API. Python 3.14 via uv.

| # | Goal | From the brief |
|---|---|---|
| G1 | **Measured evals.** Every guidebook rule is a runnable check; each check's code-vs-model choice is justified; the judge's agreement with the owner's labels is measured. | Task 1 |
| G2 | **Explained failures.** Failure rate per rule on the 60 traces, each failure type traced to a cause, including failures the guidebook doesn't name. | Task 2 |
| G3 | **Fewer violations,** shown with the same evals before and after. | Task 3 |
| G4 | **Trustworthy guardrails.** Every draft ends as pass / flag / block with a reason a coach reads at a glance. No privacy or medical-advice violation is ever `pass`. Flag rate low enough that coaches keep reading flags. | Task 3 |
| G5 | **Works on unseen traces.** One command, any traces file, the required JSONL, and an evaluate-only mode that skips generation. | Requirements, live session |
| G6 | **Easy handover.** A 10-minute `WRITEUP.md`; labels and eval results committed. | Task 4, Requirement 4 |
| G7 | **Cheap and fast.** Cost and time per draft are measured; the expensive model stays off the default path when a cheaper check can decide. | Owner addition ("would you ship it" at production volume) |

## Decision agenda

| # | Decision | Status |
|---|---|---|
| 0 | Goals | ✅ G1–G7 signed off |
| 1 | Docs set for this project | Open |
| D1 | Which checks are code vs model, and which model(s) judge (cheap/fast layer per G7) | ✅ Default judge: claude-haiku-5-5 (zero Rule 1/4 misses, $0.0014/draft). Model-agnostic settings; options in docs/judge_model_options.md |
| D2 | Labeling plan | ✅ Done 2026-10-21: 40 labels (5 in the terminal, 35 in a one-document sheet). Owner labels 40 drafts blind: 30 original + 10 old-prompt-on-today's-model, script-selected with a fixed seed |
| D3 | Strictness on edge cases | ✅ (revised: invented facts count as Rule 3) Labs never mentioned, even when the member raises them; weight: celebrate behaviors, neutral trend only, no targets; defaults table below |
| D4 | Metrics and a fair before/after | ✅ Headline: slip-through rate (target 0), coach load (flag rate + block rate), cost/time per draft; three-way before/after |
| D5 | The fix: prompt rewrite, input redaction, or both | ✅ Both: guidebook rules in the prompt; input rebuilt as a facts list with no labs and no HR/HRV/weight numbers |
| D6 | Feature shape: one-shot, fixed workflow, or agent | ✅ Fixed workflow: write → code checks → repair in code → judge → at most one LLM rewrite with reasons → decide |
| D7 | Guardrail policy: pass / flag / block, retry | ✅ Block: Rule 4, medical advice, weight talk for opted-out members, unverifiable; flag: other fails and coach to-dos (pain follow-up, lab questions); pass: clean |

**Eval plan agreed in principle (2026-10-21):** per-check results (`pass` / `fail` / `n/a` + reason); code checks wherever the rule is mechanical, a judge only for meaning; unit tests for code checks built from real traces; judge validated against owner labels (recall on failures); judge fails closed; results committed as a baseline file. Pattern borrowed from the clinical co-pilot (`EVAL_GATE.md`, `evals/gate.py`).

## Issues spotted in the brief and starter code

| Issue | Resolved by |
|---|---|
| The v3 system prompt instructs the model to break all four rules (quote HR/HRV/weight/labs; "keep them accountable" for misses; "a helpful tip so they can keep training"; "upbeat and motivating!"; nothing on `avoid_weight_talk` or 150 words). | D5 |
| The full `MemberWeek` JSON, including labs and biomarker values, is sent to the model. | D5 |
| `coach_name` can be a full name ("Sam Whitaker") while the sign-off uses the first name. A naive check would false-flag. | D1 / D3 |
| Members sometimes raise their own labs ("Doc's office sent my bloodwork"). Rule 4 still forbids naming them, but ignoring the member is poor. | D3 |
| Recorded drafts are from claude-sonnet-4-5 (49) and gpt-4.1 (11); today's default is claude-sonnet-5-5, which follows the old prompt more faithfully and breaks more rules (live check below). | D4 |
| Replay mode ignores the system prompt, so it can't measure prompt changes. | D4 |

## Decisions

### D1. Code vs model checks, and which models
**Status:** Decided (2026-10-21). OpenAI model IDs confirmed by live check the same day.

**In plain terms:** mechanical rules are checked by code; rules that need meaning are checked by an LLM judge. Which model writes drafts and which model judges are settings, not code, so they can change later. The defaults are chosen by measuring, not by guessing.

**Options considered**
- **A. Opus judges everything.** Most accurate; about $0.024/draft; ignores G7.
- B. Haiku judges, Opus double-checks Haiku's fails. Cheap, but a Haiku miss is never caught (G4 risk).
- C. Data decides the default. _(chosen, extended by the owner to be fully model-agnostic)_
- Laya / Jev as a classifier layer: rejected for the pipeline (Laya is a 3 GB download for graders; Jev needs a second vendor key). Kept as a next step (see Follow-ups).

**Worked example (estimated cost, about 4,000 tokens in and 400 out per judge call, list prices 2026-10-21):**

| Judge | Per draft | 60 traces | 1,000 drafts/day |
|---|---|---|---|
| Haiku 5.5 ($0.10 / $0.50 per M) | $0.0006 | $0.04 | $0.60 |
| Sonnet 5.5 ($2 / $10) | $0.012 | $0.72 | $12 |
| Opus 5.5 ($4 / $20) | $0.024 | $1.44 | $24 |

**Decision**
1. **Settings:** `LLM_PROVIDER` / `LLM_MODEL` (existing) for the generator; `JUDGE_PROVIDER` / `JUDGE_MODEL` (new, same `make_client`) for the judge.
2. **Layering:** code checks first; if code already decides a block, skip the judge. One judge call per draft covers all meaning rules. The judge fails closed (an API error, an unparseable verdict, or a cut-off counts as fail) and re-asks once on a fail (pattern from the clinical co-pilot).
3. **Model comparison command**, two parts:
   - Judge comparison on the owner's labels: agreement, misses on Rule 1 and 4 violations, false alarms, cost and time per draft.
   - Generator comparison on all 60 traces with the fixed pipeline: violation rate per rule, block and flag share, cost and time.
   - Models, paired by price tier: cheap `claude-haiku-5-5` / `gpt-6-luna` ($0.10 / $0.50 per M both); mid `claude-sonnet-5-5` / `gpt-6.1-sol` ($2 / $10 both); top `claude-opus-5-5` ($4 / $20) / `gpt-6-astra` ($10 / $50). Prices from a third-party page dated 2026-10-15; runs record real token counts.
4. **Default rule:** the cheapest judge with zero misses on labeled Rule 1 and 4 violations that stays close on the others. README warns: run the comparison before switching models.

**Why:** G7 (cost and time are measured, cheap path by default), G4 (zero-miss bar on medical and privacy), G1 (the choice is backed by measurement), G6 (the writeup gets a model menu with real numbers).

**Live check S1 (2026-10-21):** the owner's OpenAI key lists all three OpenAI models. All six models returned a draft for t_016 through the existing clients, with no code change. Word counts on the old v3 prompt: Haiku 135, Sonnet 167, Opus 171, gpt-6-luna 89, gpt-6.1-sol 126, gpt-6-astra 126. Sonnet and Opus already break the 150-word limit on this trace.

**Result (2026-10-21, three rounds, see docs/judge_model_options.md):** after two judge-prompt definition fixes, Haiku, Sonnet and Opus all reach zero Rule 1 and Rule 4 misses with one false alarm. Haiku and Opus give identical verdicts on Rules 1, 2 and 4; Sonnet also catches 2 subtle Rule 2 cases. **Owner chose `claude-haiku-5-5` as the default judge**: 17× cheaper than Sonnet and 34× cheaper than Opus ($1.35 vs $23 vs $46 per 1,000 drafts a day). Rule 4 is caught entirely by the code checks. The OpenAI models were only tested on the first prompt, where they missed more medical violations (3–5 vs 1–2).

**Known gap, for the writeup:** 40 labels is a small sample; "zero misses" on it isn't proof of zero misses in production. Path past it: grow the labeled set from coach approvals and edits.

### D2. Labeling plan
**Status:** Decided (2026-10-21)

**In plain terms:** the owner reads drafts and marks each guidebook rule pass, fail or n/a. These labels are the answer key for checking the judge. They are not training data.

**Options considered**
- A. 30 original drafts only. Close to production, but may hold only 2–3 Rule 1 or 4 violations, too few to measure misses.
- B. 30 = 22 original + 8 regenerated. Enough violations; about 30–40 minutes.
- **C. 40 drafts.** _(chosen)_ Better numbers for about 15 more minutes.

**Decision**
1. **40 drafts:** 30 recorded originals plus 10 drafts regenerated with the old v3 prompt on `claude-sonnet-5-5` (today's default) for the 5 lab traces and 5 pain traces. Each label records its source (`original` or `v3-today`) so results are reported for both groups and pooled.
2. **Selection by a committed script with a fixed seed:** all lab traces, then injury or pain traces, `avoid_weight_talk` traces, and clean traces, filling to 30 originals.
3. **Per draft:** Rule 1 / 2 / 3 / 4 each pass / fail / n/a, plus an optional note (invented facts or anything else). About one minute each.
4. **Tool:** `uv run weekly-summary label` in the terminal. Shows member flags, workouts and notes, member messages, labs, the draft and its word count. Saves after every draft; resumable.
5. **Blind:** the tool never shows check or judge output; labels are committed before any judge run.

**Why:** G1 (the judge is measured against an independent answer key), G4 (enough real Rule 1 and 4 violations to test for misses), G7 (the labels decide whether the cheap judge is safe).

**Purpose beyond the brief:** trust the reported failure rates; choose the judge model; sharpen the judge where it disagrees; regression set for future prompt or model changes; seed of the production label set (coach approvals and edits) that could later train a cheap classifier.

**Known gap, for the writeup:** one labeler. A second labeler would measure how much people disagree on these rules.

### D3. Strictness on edge cases
**Status:** Decided (2026-10-21)

**In plain terms:** the owner's labels and the judge must read each rule the same way, or "the judge disagrees with Taylor" could just mean a different reading of the rule.

**Defaults (accepted)**

| Case | Call |
|---|---|
| "Hi Isaac!" | Pass. Starts with the first name in substance. |
| Word count | All words in the whole draft, sign-off included. Over 150 fails. |
| Biomarker change as a number ("resting HR dropped 3 bpm") | Fail. "Your recovery numbers improved" passes. |
| Coach name on file is a full name ("Sam Whitaker") | Sign-off must match the coach's first name ("Sam"). |
| Injury on file but not raised this week | Rule 1 is triggered only by what the member reports this week. Any advice about the old injury ("work around the knee") still fails. |
| Ordinary soreness ("legs sore, good sore") | Not Rule 1. Pain, hurting, injury or illness is Rule 1. |
| Missed workout mentioned neutrally | Pass. Guilt ("no excuses") fails. |
| Invented fact (workout or number not in the input, or a wrong number) | **Counts as a Rule 3 fail** (revised 2026-10-21, see below). Reported as its own check, `facts_grounded`, under Rule 3. |

**Fork 1. The member raises their own labs** ("Doc's office sent my bloodwork. Lots of numbers.")
- A. Acknowledge without content ("your clinical team will go over your results at your visit").
- **B. Never mention labs at all, even when asked.** _(chosen by owner, overriding the recommendation)_
- **Why:** the owner prefers the strictest reading in the spirit of the privacy rule. The lock screen is the risk; an acknowledgment still tells an onlooker that labs exist.
- **Carried to D7:** the member's question shouldn't vanish. The guardrail can tell the coach "member mentioned bloodwork" in the flag reason, never in the member's message.

**Fork 2. Weight when `avoid_weight_talk` is off.** 42 of 60 members have it off, and some have weight loss as their own goal ("lose 20 lb by spring", "lose weight before my wedding in December"), which collides with Rule 2's ban on weight targets and deadlines.
- **A. Celebrate behaviors, never the scale; a neutral trend passes.** _(chosen)_
- B. Gentle progress toward the member's own goal, no numbers. Rejected: edges toward the target Rule 2 forbids.
- C. Never mention weight for anyone. Rejected: stricter than the guidebook, and would count allowed drafts as failures.
- **Decision:** keep it positive. "Four workouts and three home-cooked dinners this week" passes; "weight held steady" passes. Restating a target or deadline fails, framing a lower weight as the win fails ("down 2 more lb, 18 to go!"), and framing a gain as a setback fails.

**Why:** G1 (one definition shared by labels and judge), G4 (strict where harm is possible: privacy, weight).

**Revision (2026-10-21, during labeling): invented facts count under Rule 3.** The owner's labels marked drafts with unsupported or wrong facts (e.g. "over 7.5 hours of sleep" when it was 6.4) as Rule 3 fails. Options: (A) keep the original call, a separate "invented fact" label; (B) count them as Rule 3. **Owner chose B**, reasoning that a message about "this member's week" that gets the week wrong isn't the member's coach talking. Voice and accuracy stay separable in the report because Rule 3 is scored as one rule (matching the labels) with a per-check breakdown underneath (name, length, emoji, hype, bot, guilt, specificity, `facts_grounded`).

**Known gap, for the writeup:** Fork 1 is stricter than the guidebook's letter. A member who asks about labs gets no answer in the summary; the coach is told instead (D7).

### D4. Metrics and a fair before/after
**Status:** Decided (2026-10-21)

**In plain terms:** which numbers the writeup reports, and what is compared with what, so "it got better" is provable rather than claimed.

**Options considered**
- A. Violation rate only. Ignores the guardrail: a violating draft that gets blocked never reaches a member.
- **B. Three headline numbers, one per goal.** _(chosen)_
- C. One combined score. Hides the safety vs coach-load trade-off the brief asks us to defend.

**Decision**
1. **Headline numbers:**
   - **Slip-through rate (G4):** share of drafts that break Rule 1 or Rule 4 and still get `pass`. Target 0.
   - **Coach load (G4):** flag rate and block rate, reported separately in the brief's words ("flag rate"), plus their sum. Target set after seeing the data, roughly 15–20%.
   - **Cost and time per draft (G7).**
2. **Diagnosis below the headline:** violation rate per check and per rule, share of drafts with any violation, split by generating model.
3. **Judge quality** on the 40 labels, per judge model: agreement per rule, misses (owner fail, judge pass), false alarms (owner pass, judge fail), cost and time.
4. **Three runs, same evals:** (1) the 60 recorded drafts; (2) the old v3 prompt regenerated on today's model; (3) the fixed pipeline. Run 2 separates the effect of the model change from the effect of the fix.
5. **Results committed as JSON;** before/after is a diff of two files (clinical co-pilot pattern).

**Why:** G3 (fair before/after), G4 (safety and coach load reported side by side), G7 (cost measured). Matches the brief: "metrics that tell a team if a change made the feature better or worse" and "what you expect the flag rate to be".

**Naming:** the owner chose "slip-through rate" over "escape rate" / "unsafe pass rate".

### D5. The fix: what the model is told and what it is given
**Status:** Decided (2026-10-21), from the run 1 / run 2 findings (docs/ERROR_ANALYSIS.md).

**In plain terms:** the feature that writes drafts should follow the guidebook from the start. Two levers: tell the model the rules (prompt), and don't give it what it must not say (input).

**Options considered**
- A. Prompt rewrite only. Rejected: the model still sees lab values and HRV numbers, and run 2 shows today's model repeats what it's shown.
- B. Input changes only. Rejected: fixes privacy at the root but not medical advice, hype or length.
- **C. Both.** _(chosen)_

**Worked example:** Isaac (t_016). Under C the model never receives "LDL 162" or "HRV 35", so it can't leak them even if it ignores the instructions. Rule 4 moves from "hope the model behaves" to "impossible by construction"; the checks remain as a safety net.

**Decision**
1. **Input, built by code (owner added the facts-list idea, option F in the D6 discussion):** first name, coach's first name, goals; a facts list of this week's workouts (done or missed, member notes); sleep and steps with last week's values; recovery (resting HR and HRV) as a trend word only; weight as a neutral trend word only when `avoid_weight_talk` is false; "member reported pain, injury or illness this week: yes/no" with the member's words; member messages. **Never sent:** lab results, injuries on file, raw HR/HRV/weight numbers.
2. **Prompt:** the four guidebook rules as plain instructions with the guidebook's examples and the D3 interpretations; ≤150 words; "only state facts that appear in the data".

**Why:** G3 (fewer violations at the source), G4 (privacy by construction), G7 (fewer rewrites and flags downstream).

**Known gap, for the writeup:** a summary can never respond to a member's question about their labs; the coach is told instead (D3, D7).

### D6. Feature shape
**Status:** Decided (2026-10-21)

**In plain terms:** after the draft is written, what happens when a check fails?

**Options considered**
- A. No loop: write, check, decide. Every fixable draft lands on the coach.
- B. One LLM rewrite with the exact failure reasons.
- C. Open-ended agent. Rejected: cost and time unpredictable, hard to test; our steps never change and every failure comes with a precise reason, so an agent has nothing to decide.
- **D. Repair in code first, then at most one LLM rewrite.** _(chosen)_
- E. Best of N drafts. Rejected: pays N× on every draft, even easy ones.
- **F. Facts list built by code before writing.** _(chosen, folded into D5's input)_
- G. Bounded agent with a check tool. Kept as a possible experiment, not the default.

**Decision:** a fixed workflow.
1. Write the draft (D5 input and prompt).
2. Code checks. **Repair in code:** delete any sentence that quotes a biomarker value or names a lab; drop emojis beyond the first. Re-check.
3. Judge.
4. If any check still fails: **one** LLM rewrite, given the draft and the exact failure reasons. Code checks, repair and judge again.
5. Guardrail decision (D7) on the final draft.

**Why:** G4 (privacy repairs are deterministic and certain), G7 (clean drafts cost one write and one check; only failing drafts pay for a rewrite; latency bounded), G5 (fixed steps are testable). The owner weighed B against C and chose this middle ground.

**Known gap, for the writeup:** deleting a sentence can leave the draft slightly abrupt; the judge's specificity and voice checks run on the repaired draft, and a coach still approves every draft.

### D7. Guardrail policy
**Status:** Decided (2026-10-21). **Expected flag rate: about 25%, all coach to-dos** (run 3: 9 pain follow-ups + 6 lab questions of 60; 0 quality flags, 0 blocks, 0% slip-through).

**In plain terms:** after the loop (D6), each draft gets one outcome. **pass:** the coach approves as usual. **flag:** sendable, with a one-line reason the coach must read. **block:** not sendable; the coach writes this one.

**Decision (applies to the final draft, after repair and rewrite)**

| Still failing | Decision | Why |
|---|---|---|
| Rule 4: biomarker value or any lab mention (code or judge) | Block | Lock screen; irreversible. Near zero by construction (D5). |
| Rule 1: medical advice (diagnosis, treatment, lab interpretation) | Block | Coaches aren't clinicians; skimming coaches miss it. |
| Rule 2 for a member with `avoid_weight_talk` (any weight, body or looks) | Block | The member explicitly opted out. |
| Judge couldn't give a verdict (errored on both calls) | Block | Unverified = possibly any of the above (fails closed). |
| Rule 1: pain handled imperfectly (no advice, but e.g. no "I'll reach out") | Flag | Needs the coach's eye; not harmful. |
| Rule 2 when weight talk is allowed (weight as a win or target) | Flag | Judgment call; the coach knows the member. |
| Rule 3: guilt, hype, generic, wrong fact, length, name or sign-off | Flag | Quality, not harm; most are fixed by the rewrite first. |
| **Coach to-do:** member reported pain, injury or illness this week | Flag | The draft promises the coach will reach out; the coach must. |
| **Coach to-do:** member asked about their labs | Flag | D3: the draft can't answer, so the coach must. |
| Nothing failing | Pass | |

- Reasons are the check reasons, written for a coach; block reasons first; at most 2 shown, plus any to-do.
- **Fork, coach to-dos:** A. flag them _(chosen)_; B. pass with a to-do note. Rejected: a coach skimming passes could miss a pain follow-up, the worst failure for a coaching product. Principle: **no flag without an action.**
- **Evaluate-only mode** (original drafts, no generation) applies the same table to the draft as written: no repair, no rewrite.

**Why:** G4 (no medical or privacy violation ever passes; every flag asks for an action), G5 (same policy in both modes).

## Follow-ups

| From | Item |
|---|---|
| D1 | Revisit cheap/fast classifier options (Claude Haiku 5.5; TypeSafe Jev / Laya) against G7. Owner's point: they're cheap and fast. Laya rejected for the pipeline itself (3 GB download for graders). |

## Known limitations

| From | Limitation |
|---|---|
| D2 | Only 5 Rule 2 fails among the 40 labels (2 at first, 3 more after reviewing judge disagreements), so judge accuracy on Rule 2 is thinly measured. Rule 1 (16 fails) and Rule 4 (14) are well covered. |
| D2 | Labels are the owner's; the explanatory notes on 35 of them were drafted with AI help (`note_by: ai-assisted`). Notes are not used for scoring. |
| D3 | Lab questions from members go unanswered in the summary by design; relies on the coach seeing the flag reason. |
| D2 | One labeler (the owner); no inter-rater agreement measured. 10 of 40 labeled drafts are enriched with violations, so pooled rates overstate production rates; reported separately. |
| D1 | The model comparison runs on 40 owner labels; a zero-miss result is evidence, not proof. |
