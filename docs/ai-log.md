# AI log

**Split:** Claude (Opus 5.5, in the Claude app with a shell on this repo) reads, plans, writes all code, and runs offline checks. Taylor makes every decision, labels traces, runs anything that needs the API key, and reviews results. Subagents (tester, reviewer) check Claude's work so it isn't grading itself.

Entry template: what I asked / what happened / worked or didn't / what I overrode and why.

## 2026-10-20 — Reading the brief
- **Asked:** review the repo and ASSESSMENT.md, ask questions first.
- **Happened:** Claude found the v3 system prompt pushes the model to break all four guidebook rules, and that labs and biomarker values are sent to the model at all.
- **Worked:** I initially read "the prompt" as something else; Claude clarified it meant the feature's `SYSTEM_PROMPT`.

## 2026-10-20 — Live check: today's model on the old prompt (t_016, Isaac)
- **Asked:** regenerate one draft with `uv run weekly-summary generate t_016` (claude-sonnet-5-5, prompt v3).
- **Happened:** The recorded draft (sonnet-4-5) made one vague leak ("cholesterol coming back on the high side"). The new draft named LDL, triglycerides and HDL with values and "above the reference ranges", quoted resting HR 63, HRV 35 and weight 175.6, and ran 168 words. Facts checked against the input: accurate.
- **Takeaway:** a better instruction-follower obeys a bad prompt more closely. A model upgrade without a prompt fix makes things worse. This is why the before/after compares the old prompt on today's model, not just the recorded drafts.
- **Also surfaced:** a keyword scan for lab names missed "cholesterol on the high side", which is evidence that lab mentions need a judge as well as code.

## 2026-10-21 — Eval layering and cheap classifiers
- **Asked:** layer deterministic checks first, then a classifier like "JEV" or "LAYA", then an LLM; model it on the clinical co-pilot's evals.
- **Happened:** Claude didn't recognize the names and guessed Llama Guard / G-Eval. That was wrong. When I asked it to research, it found TypeSafe's Jev (hosted "System One" decision model) and Laya (free local ModernBERT stand-in), plus an independent bake-off showing Laya is easily swayed by injected text.
- **Overrode:** Claude proposed a Laya bake-off; I dropped Laya because it's a 3 GB download for graders. I kept the reason for wanting it, cheap and fast, as a new goal (G7), to be weighed at D1.
- **Lesson:** Claude should research unfamiliar names before guessing.

## 2026-10-21 — Environment
- The sandboxed shell on my Mac ran out of disk installing Python 3.14 for `uv sync`. Claude now develops and tests in its cloud workspace and copies files into the repo; I run `uv` and anything needing the API key in my own terminal.

## 2026-10-21 — Live check: six models through the starter clients
- **Asked:** list the OpenAI models my key can use, then generate t_016 once per candidate model.
- **Happened:** a third-party price page named gpt-6-luna / gpt-6.1-sol / gpt-6-astra; my key confirmed all three exist. All six models (3 Claude, 3 OpenAI) answered through the existing clients with no code change. Opus and Sonnet ran 171 and 167 words on the old prompt, over the 150 limit.
- **Worked:** checking against a real key instead of trusting the price page. Model IDs are recorded in D1.

## 2026-10-21 — D3: overrode the recommendation on member-raised labs
- **Asked:** Claude recommended letting the draft say "your clinical team will go over your results at your visit" when the member raises labs.
- **Overrode:** I chose never to mention labs at all, in the spirit of the privacy rule. Claude flagged the cost (the member's question goes unanswered) and moved the fix to the guardrail: tell the coach, not the member.
- **Asked Claude to explain** why `avoid_weight_talk` would ever be off. The answer surfaced a real conflict: members whose own goal is "lose 20 lb by spring" versus Rule 2's ban on targets and deadlines. Decided: celebrate behaviors, neutral trend only.

## 2026-10-21 — T0–T2 built; independent review caught Rule 4 misses
- **Happened:** Claude wrote tests from real traces first, then the code checks and the labeling tool. 46 tests passed and the checks fired on 13 of 60 recorded drafts with no false alarms.
- **Review:** a separate reviewer agent (fresh context, read-only) tried adversarial phrasings and marked the work "request changes". The privacy check missed number-first biomarkers ("a 52 resting heart rate", "you weigh 205", "you're at 168"), rounded weight changes, and lab words like "HbA1c", "blood-work" and "your results came back normal". It also found false alarms ("HRV improved and sleep averaged 7.4 hours", the guidebook's own allowed example), a ZWJ emoji counted twice, and non-ASCII names ("Zoë") failing.
- **Fixed:** all blocking and should-fix items, each added as a test (87 tests now). The 60 recorded drafts still fail on the same 13 traces, so no new false alarms.
- **Lesson:** "passes on the real data" isn't enough for a privacy check. The real drafts happened not to use the phrasings that slipped through, and an adversarial reviewer found them in minutes.
- **Known limit kept:** a weight target with no unit ("you can be at 220 by Halloween", t_002) isn't a biomarker value the code can see. It's a Rule 2 target, left to the judge.

## 2026-10-21 — Labeling: my labels, AI-drafted notes, and a display bug Claude caused
- **Asked:** after 5 drafts in the terminal I asked for all the rest in one document. Claude built `label-sheet` / `import-sheet` (blind: trace ids kept in a separate index).
- **What I did:** I chose every p/f/n myself. I used an AI to help write the explanatory notes. Claude noticed the notes read like model output and asked directly before importing anything, because model-written labels would make the judge measurement circular. We kept the labels and marked the 35 notes `note_by: ai-assisted`. Notes aren't used in scoring.
- **Claude's bug:** the labeling display showed last week's resting HR, HRV and weight, but not last week's sleep and steps. About a dozen notes called real numbers "invented" ("sleep up from 6.4"). Claude owned it, fixed the display, and showed me the 4 drafts whose Rule 3 fail rested on that; I rechecked and passed all 4.
- **Decision changed:** I chose to count invented or wrong facts as Rule 3 fails (D3 revision), overriding Claude's recommendation. It found a real one: t_060 says "over 7.5 hours of sleep" when it was 6.4.
- **Result:** 40 labels. Fails: Rule 1 16, Rule 2 2, Rule 3 23, Rule 4 14. Committed before any judge run.

## 2026-10-21 — T3–T5 built; review found that a broken judge would have won
- **Happened:** Claude built the judge (one call per draft, 8 meaning checks, fails closed, re-asks on a fail), the `eval` runner and `compare-judges`.
- **Review (fresh reviewer agent):** failing closed is right in production but backfires in a comparison. A judge whose calls all error (missing key, rate limits) marks everything "fail", so it shows **zero misses at $0** and would win under "cheapest with zero Rule 1/4 misses". Also: the judge could answer "n/a" on a privacy check and get a pass; a disagreement on a privacy check silently became a pass.
- **Fixed:** errors are counted and shown, and a judge with errors is marked "not comparable". Each model gets a one-call probe before its 40-draft run. "n/a" is only accepted where allowed. On Rules 1 and 4 a disagreement keeps the fail. SDK retries raised to 6 for rate limits. Wall time is reported next to per-draft latency. 104 tests.
- **Lesson:** a safety default (fail closed) can make a measurement lie. The comparison has to count errors separately from verdicts.

## 2026-10-21 — Judge comparison: three rounds, each fixing a judge-prompt problem (not the labels)
- **Round 1 (six models):** no judge had zero Rule 1 misses. Almost every miss was a draft interpreting lab results ("A1C a bit above range, but this kind of week moves those numbers"). I labeled that as medical advice; Claude's judge prompt never mentioned labs. Rule 4 was caught 14 of 14 by the code checks alone, so the judge adds nothing there. The OpenAI models missed 3–5 medical violations; the Claude models 1–2. Kept in `results/judge_runs_v1/`.
- **Round 2 (Claude only, prompt adds "lab results or health markers"):** zero Rule 1 misses for all three, but Haiku and Sonnet now flagged "your recovery trends are heading the right way", which the guidebook explicitly allows (6–7 false alarms). Opus read it correctly (1 false alarm). Claude's fix had overshot. Haiku's 3 errors were broken JSON, caused by the instruction to "quote the offending words" (double quotes inside JSON strings). Kept in `results/judge_runs_v2/`.
- **Round 3 prompt:** "lab results or clinical markers such as blood pressure, cholesterol or blood sugar"; trend words about recovery, HR or HRV are explicitly allowed; quotes must be single quotes.
- **Caveat for the writeup:** the same 40 labels both tuned the judge prompt and score it, so the final numbers flatter the judge a little. Each change was a definition fix shared across all drafts, not a tweak for one draft.
- **Label review:** Claude asked me to recheck 3 Rule 2 labels that all six judges disagreed with ("weight is down 1.4 lb… moving in the right direction", "your weight trended down a little this week as well", "your weight is down a half pound" in a list of wins). Under D3 Fork 2 ("a lower weight is never the win") I agreed the judges were right and changed all three to fail. The originals are kept in the labels file (`rule_2_before_review`). Rule 2 fails went from 2 to 5. The AI-drafted notes had called these "neutral trends", which likely pulled my first call.

## 2026-10-21 — T7–T8 built; review found the run could crash on one API error
- **Happened:** Claude built the v4 prompt, the facts-list input, the repair-and-rewrite loop, the D7 guardrail and the `guard` command (with `--no-generate`).
- **Review (fresh reviewer agent) found:** (1) blocking: one writer error (a 503) crashed the whole run and wrote nothing, fatal for a live session on unseen traces; (2) repair could delete "Your bloodwork came back" but keep "Great news, all normal!", a lab hint with no context left for the judge; (3) lab and biomarker text could still reach the model through goals ("lower my A1C") and member messages ("my resting HR was 48"); (4) coach to-dos were dropped when a draft was blocked; (5) repair flattened paragraph breaks; (6) a trace with `output: null` stopped the load.
- **Fixed:** a failure blocks only its own trace ("Pipeline error… Needs a human look"); any removal forces the rewrite, and a removal in the final draft flags it for a person; goals, notes and messages with lab or biomarker content are masked before the model sees them; to-dos are kept on block (pain detected from the member's words when the judge is skipped); repair keeps formatting; null outputs load as empty and an empty draft blocks. 120 tests.
