# Error analysis log

A running log, not a one-time document (pattern from the clinical co-pilot). After any real eval run, add an entry for anything unexpected, whether or not it was a failure.

Format per entry: **date — what was observed — root cause — fix or status.**

---

## 2026-10-21 — Code checks on the 60 recorded drafts (first pass, before owner labels)
- **Observed:** 15 code-check failures across 13 traces. Rule 4: biomarker values in 4 (t_002 weight 233.8, t_010 resting HR 52, t_025 weight 168.4, t_044 HRV 71 ms); lab mentions in 3 (t_016 "cholesterol", t_027 "labs", t_053 "lab results"). Rule 2 (opted-out members): 3 (t_023 "trimmer", t_025 "scale", t_049 "how you look"). Rule 3: t_011 bot opener and no first name, t_033 153 words, t_038 "crushing", t_039 signed by the wrong coach.
- **Root cause (hypothesis, to confirm in T6):** the v3 prompt asks for "heart rate, HRV, weight, and any new lab results" and says nothing about `avoid_weight_talk`.
- **Outside the guidebook:** t_039 is signed "Priya" while the member's coach is Jordan Reyes. That's a wrong-identity error, not just a style slip.
- **Status:** code checks only. Meaning-based rules (medical advice, guilt, subtle framing) wait for the judge, which runs after the owner's labels.

## 2026-10-21 — Baseline: run 1 (60 recorded drafts) and run 2 (old v3 prompt on today's model)
Judge: claude-haiku-5-5 plus code checks. Full tables: `results/run1_original.md`, `results/run2_v3_today.md`.

| | Run 1: recorded drafts (sonnet-4-5, gpt-4.1) | Run 2: v3 prompt on claude-sonnet-5-5 |
|---|---|---|
| Any rule broken | 60% (36/60) | **100% (60/60)** |
| Rule 1 or 4 (medical or privacy) | 23% (14/60) | **100% (60/60)** |
| Rule 1 medical | 15% | 42% |
| — pain weeks handled correctly | 4 of 9 | **0 of 9** |
| Rule 2 weight | 10% | 18% |
| Rule 3 voice and facts | 45% | 73% |
| — over 150 words | 2% | 43% |
| — hype (judge) | 5% | 47% |
| — facts not grounded | 35% | 13% |
| Rule 4 privacy | 12% | **100%** |
| — biomarker numbers quoted | 7% | **100%** |
| — lab mention | 5% | 12% |

**Root causes (each traced to a line of the v3 prompt):**
- **"Reference their actual numbers (sleep, steps, heart rate, HRV, weight, and any new lab results)"** → Rule 4. Today's model quotes resting HR / HRV / weight in all 60 drafts and names labs in 7 (every week with new labs). The older models obeyed this line less, so run 1 leaked in 12%.
- **"If they mention pain or soreness, give them a helpful tip so they can keep training"** → Rule 1. Run 2 handled none of the 9 pain weeks correctly (icing, stretches, "work around it"); run 1 got 4 of 9 right, because the older models often ignored the instruction.
- **"Be upbeat and motivating!"** → Rule 3 hype: 47% of run 2 drafts ("You've got this!", "what a week!").
- **"Keep it to one short paragraph"** with no word limit → 43% of run 2 drafts are over 150 words.
- **Nothing about `avoid_weight_talk`, and "weight" listed among numbers to quote** → Rule 2: weight framed as progress (11 of 60 in run 2), body/appearance talk for opted-out members in run 1 (t_023 "trimmer", t_049 "how you look").
- **"Keep them accountable for any workouts they missed"** → guilt in run 1 (t_008 "no excuses"). Today's model softens this; 0 in run 2.

**The model upgrade made it worse.** Run 2 is today's default model on the unchanged prompt: it follows the bad instructions more faithfully. Upgrading the model without fixing the prompt took medical/privacy violations from 23% to 100%.

**Failures outside the guidebook (Rule 3 by the owner's D3 revision, `facts_grounded`):**
- Wrong facts: t_060 "over 7.5 hours of sleep" (it was 6.4); t_032 "Saturday's 60-mile ride was your longest yet" (that ride was rained out); t_026 "all four sessions done" (one was missed); t_046 "got back over the step goal" (last week was under it).
- Wrong identity: t_039 signed by Priya; the member's coach is Jordan.
- Invented coach context: "that's exactly why we set them up" (t_003), "the travel week" (t_048).
- **Judge over-flags here:** about half of run 1's `facts_grounded` fails are forward-looking plans ("next week we add a little distance") or mild inferences, not wrong facts. `facts_grounded` is the noisiest check; it should flag for the coach, never block.

**Judge reliability:** about 1 in 10 first calls from Haiku returned broken JSON (6 in run 1, 5 in run 2). The re-ask fixed every one; no verdict was decided by an error. Cost about $0.0012–0.0016 per draft including re-asks.

## 2026-10-21 — Run 3 (fixed pipeline), evaluate-only, independent judge, six writers
- **Run 3 (v4 prompt + facts input + repair + one rewrite, Sonnet writer, Haiku judge):** 0 medical or privacy violations, pain handled correctly 9 of 9, 0 over-length, 0 hype. Guard: 75% pass, 25% flag (9 pain follow-ups, 6 lab questions, no quality flags), 0% block, 0% slip-through. 4 drafts rewritten, none repaired.
- **Independent judge (Sonnet re-judging run 3's drafts):** 0 medical/privacy. Found one real Rule 2 miss: t_048 "Enjoy your pizza night. You've earned a good evening" (food earned through exercise). Haiku passed it, consistent with Haiku missing subtle Rule 2 framing in the judge comparison.
- **Haiku judge false alarm:** t_020 `facts_grounded` said 2026-08-31 is a Tuesday, so the draft's weekdays were "wrong". It's a Monday; the draft was right. LLM judges are unreliable at date arithmetic; next step: give the judge weekday names from code, as the writer's input already does.
- **Evaluate-only on the original 60 drafts:** 35% pass, 40% flag, 25% block, 0% slip-through. Rule 1 shows 10% here vs 15% in the run 1 eval because the judge is skipped when code already blocks a draft (D1), so Rule 1 isn't evaluated on drafts blocked for privacy. The decision is the same.
- **Six writers through the fixed pipeline:** all 0% slip-through and 0% medical/privacy in final drafts. Cost per draft from $0.0010 (gpt-6-luna) to $0.0200 (Opus). gpt-6.1-sol needed no rewrites; Haiku needed the most (12%).
