# Eval: run1_original

60 drafts.

| | All drafts | claude-sonnet-4-5 | gpt-4.1 |
|---|---|---|---|
| **Any rule broken** | 60% (36/60) | 57% (28/49) | 73% (8/11) |
| **Rule 1** | 15% (9/60) | 14% (7/49) | 18% (2/11) |
| &nbsp;&nbsp;no_medical_advice | 15% (9/60) | 14% (7/49) | 18% (2/11) |
| &nbsp;&nbsp;pain_handled | 56% (5/9) | 50% (3/6) | 67% (2/3) |
| **Rule 2** | 10% (6/60) | 10% (5/49) | 9% (1/11) |
| &nbsp;&nbsp;no_weight_words | 17% (3/18) | 13% (2/15) | 33% (1/3) |
| &nbsp;&nbsp;no_weight_pressure | 10% (6/60) | 10% (5/49) | 9% (1/11) |
| **Rule 3** | 45% (27/60) | 43% (21/49) | 55% (6/11) |
| &nbsp;&nbsp;starts_with_first_name | 2% (1/60) | 2% (1/49) | 0% (0/11) |
| &nbsp;&nbsp;ends_with_coach_first_name | 2% (1/60) | 2% (1/49) | 0% (0/11) |
| &nbsp;&nbsp;max_150_words | 2% (1/60) | 2% (1/49) | 0% (0/11) |
| &nbsp;&nbsp;max_one_emoji | 0% (0/60) | 0% (0/49) | 0% (0/11) |
| &nbsp;&nbsp;no_hype_words | 2% (1/60) | 2% (1/49) | 0% (0/11) |
| &nbsp;&nbsp;no_bot_format | 2% (1/60) | 2% (1/49) | 0% (0/11) |
| &nbsp;&nbsp;no_guilt | 2% (1/60) | 2% (1/49) | 0% (0/11) |
| &nbsp;&nbsp;no_hype | 5% (3/60) | 4% (2/49) | 9% (1/11) |
| &nbsp;&nbsp;specific_to_week | 2% (1/60) | 2% (1/49) | 0% (0/11) |
| &nbsp;&nbsp;facts_grounded | 35% (21/60) | 33% (16/49) | 45% (5/11) |
| **Rule 4** | 12% (7/60) | 12% (6/49) | 9% (1/11) |
| &nbsp;&nbsp;no_biomarker_values | 7% (4/60) | 6% (3/49) | 9% (1/11) |
| &nbsp;&nbsp;no_lab_mention | 5% (3/60) | 6% (3/49) | 0% (0/11) |
| &nbsp;&nbsp;no_lab_hint | 5% (3/60) | 6% (3/49) | 0% (0/11) |

Judge: claude-haiku-5-5. 96 calls, 194,018 input and 109,557 output tokens, $0.0742 total ($0.00124 per draft), 8.1s per draft. Flakes: 3. Judge errors: 6.
