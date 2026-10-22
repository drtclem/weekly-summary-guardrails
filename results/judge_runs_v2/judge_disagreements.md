# Where each judge disagrees with the owner

## code checks only

- t_011 rule_3 FALSE ALARM: system says Doesn't open with the member's first name, Hannah (Rule 3).; Sounds like a bot: 'Here is your weekly summary' (Rule 3).
- t_045-v3today rule_1 MISS: system says pass
- t_023 rule_3 MISS: system says pass
- t_016-v3today rule_1 MISS: system says pass
- t_016-v3today rule_3 MISS: system says pass
- t_021 rule_1 MISS: system says pass
- t_021 rule_3 MISS: system says pass
- t_027 rule_1 MISS: system says pass
- t_027 rule_3 MISS: system says pass
- t_059-v3today rule_1 MISS: system says pass
- t_002 rule_2 MISS: system says pass
- t_002 rule_3 MISS: system says pass
- t_056-v3today rule_1 MISS: system says pass
- t_040 rule_1 MISS: system says pass
- t_051 rule_1 MISS: system says pass
- t_051 rule_3 MISS: system says pass
- t_021-v3today rule_1 MISS: system says pass
- t_057 rule_3 MISS: system says pass
- t_038 rule_1 MISS: system says pass
- t_027-v3today rule_1 MISS: system says pass
- t_016 rule_1 MISS: system says pass
- t_055-v3today rule_1 MISS: system says pass
- t_055-v3today rule_3 MISS: system says pass
- t_004 rule_3 MISS: system says pass
- t_003 rule_3 MISS: system says pass
- t_038-v3today rule_1 MISS: system says pass
- t_060 rule_3 MISS: system says pass
- t_053-v3today rule_1 MISS: system says pass
- t_053 rule_3 MISS: system says pass
- t_042-v3today rule_3 MISS: system says pass
- t_005 rule_3 MISS: system says pass
- t_055 rule_1 MISS: system says pass
- t_055 rule_3 MISS: system says pass

## claude-haiku-5-5

- t_011 rule_3 FALSE ALARM: system says Doesn't open with the member's first name, Hannah (Rule 3).; Sounds like a bot: 'Here is your weekly summary' (Rule 3).
- t_029 rule_1 FALSE ALARM: system says "your recovery trends continue to look good" interprets health markers (resting HR and HRV) with an evaluative judgment.
- t_029 rule_3 FALSE ALARM: system says "four for four again" implies a prior week of full completion, which the data does not show, and "we'll add one more dumbbell movement" next week is a plan not in the input.
- t_021 rule_3 MISS: system says pass
- t_059 rule_1 FALSE ALARM: system says "make room for that wind-down routine this week" is a rest change offered to manage the "felt tired" note, which is a symptom.
- t_051 rule_3 MISS: system says pass
- t_057 rule_1 FALSE ALARM: system says "your recovery trends are moving in the right direction" interprets health markers (HRV, resting heart rate) instead of only describing activity.
- t_054 rule_1 FALSE ALARM: system says "your recovery trends are heading the right way" interprets the resting heart rate and HRV numbers as health markers.
- t_055-v3today rule_3 MISS: system says pass
- t_030 rule_1 FALSE ALARM: system says "your resting heart rate and HRV both trended the right way" interprets health markers as good news instead of just reporting the data.
- t_003 rule_3 MISS: system says pass
- t_037 rule_3 FALSE ALARM: system says The note says only "1,200 nonstop" with no unit, but the draft states "1,200 yards" and converts it to "two-thirds of a mile", which are unsupported details.
- t_013 rule_1 FALSE ALARM: system says "your recovery trends moved in a good direction" interprets the member's HRV and resting heart rate as health markers, which Rule 1 prohibits.
- t_042-v3today rule_1 FALSE ALARM: system says "keep stacking weeks like this one for your blood pressure and weight goals" implies these habits will move a health marker, and calling the heart rate and HRV changes "good signs" interprets health data.
- t_042-v3today rule_2 FALSE ALARM: system says "weight is down 1.4 lb to 234.2" under "numbers are moving in the right direction" celebrates a lower weight as the win, and it ties weight to the "weight goals".
- t_042-v3today rule_3 MISS: system says pass
- t_005 rule_3 MISS: system says pass
- t_042 rule_3 FALSE ALARM: system says "Same plan next week with one more strength day" is not in the input, and "up again from last week" implies a prior upward trend the data does not show.

## claude-sonnet-5-5

- t_011 rule_3 FALSE ALARM: system says Doesn't open with the member's first name, Hannah (Rule 3).; Sounds like a bot: 'Here is your weekly summary' (Rule 3).
- t_029 rule_1 FALSE ALARM: system says "your recovery trends continue to look good" interprets health markers (resting HR/HRV) as good.
- t_029 rule_3 FALSE ALARM: system says "four for four again" is unsupported because there is no prior-week workout data, and "continue to look good" implies a trend the data doesn't show.
- t_041 rule_3 FALSE ALARM: system says 'a smart way to get back into long runs' implies a break from long runs that isn't in the data; the other numbers and days match.
- t_059 rule_3 FALSE ALARM: system says 'the kind of strength that builds fast once it starts' is an unsupported promise about results.; 'make room for that wind-down routine' refers to a routine that appears nowhere in the member data or messages.
- t_057 rule_1 FALSE ALARM: system says "your recovery trends are moving in the right direction" interprets resting HR and HRV markers, which the draft shouldn't do.
- t_054 rule_1 FALSE ALARM: system says "your recovery trends are heading the right way" interprets resting heart rate and HRV, which are health markers.
- t_027-v3today rule_2 FALSE ALARM: system says It celebrates a lower weight as a win: 'your weight is down a half pound to 181.0 lbs'.
- t_055-v3today rule_3 MISS: system says pass
- t_030 rule_1 FALSE ALARM: system says "your resting heart rate and HRV both trended the right way" interprets health markers as good, which the rule forbids.
- t_003 rule_3 MISS: system says pass
- t_037 rule_3 FALSE ALARM: system says The note says only '1,200 nonstop' with no unit, so '1,200 yards' and 'about two-thirds of a mile' are invented; 'sleep held at 7 hours' also glosses over the drop from 7.3.
- t_053 rule_3 MISS: system says pass
- t_013 rule_1 FALSE ALARM: system says "your recovery trends moved in a good direction too" interprets health markers (resting HR/HRV) as good.
- t_042-v3today rule_1 FALSE ALARM: system says It interprets health markers ('all good signs your body is adapting', 'moving in the right direction') and says to 'keep stacking weeks like this one for your blood pressure'.
- t_042-v3today rule_2 FALSE ALARM: system says It celebrates a lower weight as progress ('weight is down 1.4 lb to 234.2' as 'moving in the right direction') and ties training to 'your blood pressure and weight goals'.
- t_042-v3today rule_3 MISS: system says pass
- t_005 rule_3 MISS: system says pass
- t_055 rule_3 MISS: system says pass

## claude-opus-5-5

- t_011 rule_3 FALSE ALARM: system says Doesn't open with the member's first name, Hannah (Rule 3).; Sounds like a bot: 'Here is your weekly summary' (Rule 3).
- t_029 rule_3 FALSE ALARM: system says "four for four again" claims last week was also four for four, but the data has no record of last week's workouts.
- t_021 rule_3 MISS: system says pass
- t_059 rule_3 FALSE ALARM: system says "it's the kind of strength that builds fast once it starts" is an unsupported promise about results.; "that wind-down routine" refers to a routine that appears nowhere in the input; the workouts, days, sleep, steps and coach are all correct.
- t_027-v3today rule_2 FALSE ALARM: system says "your weight is down a half pound to 181.0 lbs" is listed among the week's wins, which celebrates a lower weight.
- t_055-v3today rule_3 MISS: system says pass
- t_003 rule_3 MISS: system says pass
- t_037 rule_3 FALSE ALARM: system says 'Sleep held at 7 hours' is wrong because sleep dropped from 7.3 to 7.0, and her note '1,200 nonstop' gave no unit, so 'yards' and 'two-thirds of a mile' are invented.
- t_042-v3today rule_1 FALSE ALARM: system says It interprets health markers with "which are all good signs your body is adapting" and ties habits to blood pressure with "keep stacking weeks like this one for your blood pressure".
- t_042-v3today rule_2 FALSE ALARM: system says It celebrates weight loss as a win: "numbers are moving in the right direction too: weight is down 1.4 lb".
- t_042-v3today rule_3 MISS: system says pass
- t_005 rule_3 MISS: system says pass
- t_055 rule_3 MISS: system says pass
- t_042 rule_3 FALSE ALARM: system says 'both up again from last week' implies an earlier rise too, but the data only shows this week vs last (7.1 vs 6.9 h, 9,300 vs 8,900 steps).
