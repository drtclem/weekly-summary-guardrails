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
- t_054 rule_2 MISS: system says pass
- t_038 rule_1 MISS: system says pass
- t_027-v3today rule_1 MISS: system says pass
- t_027-v3today rule_2 MISS: system says pass
- t_016 rule_1 MISS: system says pass
- t_055-v3today rule_1 MISS: system says pass
- t_055-v3today rule_3 MISS: system says pass
- t_004 rule_3 MISS: system says pass
- t_003 rule_3 MISS: system says pass
- t_038-v3today rule_1 MISS: system says pass
- t_060 rule_3 MISS: system says pass
- t_053-v3today rule_1 MISS: system says pass
- t_053 rule_3 MISS: system says pass
- t_042-v3today rule_2 MISS: system says pass
- t_042-v3today rule_3 MISS: system says pass
- t_005 rule_3 MISS: system says pass
- t_055 rule_1 MISS: system says pass
- t_055 rule_3 MISS: system says pass

## claude-haiku-5-5

- t_011 rule_3 FALSE ALARM: system says Doesn't open with the member's first name, Hannah (Rule 3).; Sounds like a bot: 'Here is your weekly summary' (Rule 3).
- t_029 rule_3 FALSE ALARM: system says The draft says 'four for four again', but no prior-week workout data is provided to support 'again', and 'we'll add one more dumbbell movement' next week is a plan that does not appear in the input.
- t_021 rule_3 MISS: system says pass
- t_051 rule_3 MISS: system says pass
- t_054 rule_2 MISS: system says pass
- t_027-v3today rule_2 MISS: system says pass
- t_055-v3today rule_3 MISS: system says pass
- t_003 rule_3 MISS: system says pass
- t_037 rule_3 FALSE ALARM: system says The draft says 'Sleep held at 7 hours', but sleep fell from 7.3 hours last week to 7.0 this week, so it did not hold.
- t_042-v3today rule_1 FALSE ALARM: system says The draft says to 'keep stacking weeks like this one for your blood pressure and weight goals', which implies these habits will improve a clinical marker.
- t_042-v3today rule_3 MISS: system says pass
- t_005 rule_3 MISS: system says pass
- t_055 rule_3 MISS: system says pass
- t_042 rule_3 FALSE ALARM: system says 'Same plan next week with one more strength day' is not in the input; no plan or added strength day is recorded.

## claude-sonnet-5-5

- t_011 rule_3 FALSE ALARM: system says Doesn't open with the member's first name, Hannah (Rule 3).; Sounds like a bot: 'Here is your weekly summary' (Rule 3).
- t_029 rule_3 FALSE ALARM: system says 'four for four again' implies a previous perfect week and a four-session plan, but the data shows neither; 'we'll add one more dumbbell movement' is also an invented plan.
- t_059 rule_3 FALSE ALARM: system says 'the kind of strength that builds fast once it starts' is an unsupported promise about results.; 'that wind-down routine' refers to a routine that appears nowhere in the member's data; the days, sleep and step figures are correct.
- t_055-v3today rule_3 MISS: system says pass
- t_003 rule_3 MISS: system says pass
- t_037 rule_3 FALSE ALARM: system says The member's note says only '1,200 nonstop' with no unit, so '1,200 yards' and 'about two-thirds of a mile' are invented; 'Sleep held at 7 hours' also glosses over the drop from 7.3.
- t_053 rule_3 MISS: system says pass
- t_042-v3today rule_1 FALSE ALARM: system says 'keep stacking weeks like this one for your blood pressure' implies these habits will improve a clinical marker.
- t_042-v3today rule_3 MISS: system says pass
- t_005 rule_3 MISS: system says pass
- t_055 rule_3 MISS: system says pass
- t_042 rule_3 FALSE ALARM: system says 'both up again from last week' implies an earlier rise the data doesn't show, and 'Same plan next week with one more strength day' is an invented plan detail; the days, 7.1 hours, 9,300 steps and 70 minutes all match.

## claude-opus-5-5

- t_011 rule_3 FALSE ALARM: system says Doesn't open with the member's first name, Hannah (Rule 3).; Sounds like a bot: 'Here is your weekly summary' (Rule 3).
- t_029 rule_3 FALSE ALARM: system says 'four for four again' claims last week was also four for four, but the input has no record of last week's workouts.
- t_021 rule_3 MISS: system says pass
- t_059 rule_3 FALSE ALARM: system says 'the kind of strength that builds fast once it starts' is an unsupported promise about results.; 'that wind-down routine' refers to a routine that appears nowhere in the member's data; the workouts, days, sleep and steps all match.
- t_054 rule_2 MISS: system says pass
- t_027-v3today rule_2 MISS: system says pass
- t_055-v3today rule_3 MISS: system says pass
- t_003 rule_3 MISS: system says pass
- t_037 rule_3 FALSE ALARM: system says 'Sleep held at 7 hours' is wrong: sleep dropped from 7.3 to 7.0 hours, and the 'yards' unit is not in her note.
- t_042-v3today rule_1 FALSE ALARM: system says 'keep stacking weeks like this one for your blood pressure' suggests these habits will lower a clinical marker.
- t_042-v3today rule_3 MISS: system says pass
- t_005 rule_3 MISS: system says pass
- t_055 rule_3 MISS: system says pass
- t_042 rule_3 FALSE ALARM: system says Sleep and steps did rise from last week, but 'up again' claims an earlier rise that the data does not show.
