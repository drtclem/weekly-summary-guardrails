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
- t_029 rule_3 FALSE ALARM: system says "four for four again" claims a prior-week streak that is not in the input, and "Next week, we'll add one more dumbbell movement" is a plan not found in the data.
- t_021 rule_3 MISS: system says pass
- t_002 rule_3 MISS: system says pass
- t_059 rule_1 FALSE ALARM: system says "Friday felt like a tired day by your note, so make room for that wind-down routine this week" recommends rest to manage a symptom (tiredness).
- t_051 rule_3 MISS: system says pass
- t_055-v3today rule_3 MISS: system says pass
- t_003 rule_3 MISS: system says pass
- t_037 rule_3 FALSE ALARM: system says "Sleep held at 7 hours" is inaccurate: average sleep fell from 7.3 to 7.0 hours, so it did not hold steady.
- t_053-v3today rule_1 MISS: system says pass
- t_042-v3today rule_2 FALSE ALARM: system says The draft celebrates weight loss as a win: 'Your numbers are moving in the right direction too: weight is down 1.4 lb' and 'good signs', and it ties weight to the goal with 'keep stacking weeks like this one for your blood pressure and weight goals'.
- t_042-v3today rule_3 MISS: system says pass
- t_005 rule_3 MISS: system says pass
- t_042 rule_3 FALSE ALARM: system says "Same plan next week with one more strength day" is not in the input; the plan for next week is invented.

## claude-sonnet-5-5

- t_011 rule_3 FALSE ALARM: system says Doesn't open with the member's first name, Hannah (Rule 3).; Sounds like a bot: 'Here is your weekly summary' (Rule 3).
- t_029 rule_3 FALSE ALARM: system says "four for four again" implies a perfect prior week, but no prior-week workout data supports that.
- t_027 rule_1 MISS: system says pass
- t_059 rule_3 FALSE ALARM: system says 'the kind of strength that builds fast once it starts' is an unsupported promise about results.; 'that wind-down routine' refers to a routine that appears nowhere in the member's data; the other facts check out.
- t_054 rule_2 FALSE ALARM: system says "Your weight trended down a little this week as well" presents lower weight as another win, which Rule 2 doesn't allow.
- t_027-v3today rule_1 MISS: system says pass
- t_055-v3today rule_3 MISS: system says pass
- t_003 rule_3 MISS: system says pass
- t_037 rule_3 FALSE ALARM: system says The member's note says only '1,200 nonstop', but the draft states '1,200 yards' and 'two-thirds of a mile', inventing a unit and a distance.
- t_053 rule_3 MISS: system says pass
- t_042-v3today rule_2 FALSE ALARM: system says It celebrates lower weight as progress: "moving in the right direction too: weight is down 1.4 lb to 234.2", and it refers to "your blood pressure and weight goals".
- t_042-v3today rule_3 MISS: system says pass
- t_055 rule_3 MISS: system says pass
- t_042 rule_3 FALSE ALARM: system says 'both up again from last week' implies an earlier increase that the data doesn't show; only this week's rise over last week is supported (sleep 6.9 to 7.1, steps 8,900 to 9,300).

## claude-opus-5-5

- t_011 rule_3 FALSE ALARM: system says Doesn't open with the member's first name, Hannah (Rule 3).; Sounds like a bot: 'Here is your weekly summary' (Rule 3).
- t_029 rule_3 FALSE ALARM: system says 'four for four again' implies a full week last time, but the input has no prior-week workout data.
- t_059 rule_3 FALSE ALARM: system says Unsupported promise about results: 'it's the kind of strength that builds fast once it starts.'; 'that wind-down routine' implies an existing routine that appears nowhere in the member data.
- t_027-v3today rule_2 FALSE ALARM: system says "your weight is down a half pound to 181.0 lbs" is listed among the week's wins, so a lower weight is celebrated.
- t_055-v3today rule_3 MISS: system says pass
- t_003 rule_3 MISS: system says pass
- t_037 rule_3 FALSE ALARM: system says "Sleep held at 7 hours" is wrong because sleep dropped from 7.3, and "yards" is invented since her note just says "1,200 nonstop."
- t_053-v3today rule_1 MISS: system says pass
- t_042-v3today rule_2 FALSE ALARM: system says It celebrates weight loss as a win: 'numbers are moving in the right direction too: weight is down 1.4 lb to 234.2' and 'your... weight goals.'
- t_042-v3today rule_3 MISS: system says pass
- t_005 rule_3 MISS: system says pass
- t_055 rule_3 MISS: system says pass
- t_042 rule_3 FALSE ALARM: system says 'both up again from last week' implies a prior rise the data cannot confirm; only this week vs last week (6.9→7.1 h, 8,900→9,300 steps) is given.

## gpt-6-luna

- t_011 rule_3 FALSE ALARM: system says Doesn't open with the member's first name, Hannah (Rule 3).; Sounds like a bot: 'Here is your weekly summary' (Rule 3).
- t_029 rule_3 FALSE ALARM: system says “Again” implies four-for-four completion last week, which the data does not establish.
- t_041 rule_3 FALSE ALARM: system says “Get back into long runs” implies a return after a break, which the data does not establish.
- t_016-v3today rule_1 MISS: system says pass
- t_016-v3today rule_2 FALSE ALARM: system says “Weight eased to 175.6 lbs” frames the lower weight positively.
- t_027 rule_1 MISS: system says pass
- t_059-v3today rule_1 MISS: system says pass
- t_059 rule_3 FALSE ALARM: system says “Strength that builds fast once it starts” is an unsupported promise about results.
- t_031 rule_3 FALSE ALARM: system says “Keep the protein steady” and “recovery is lining up with the training” imply facts not supported by the member data.
- t_027-v3today rule_2 FALSE ALARM: system says “Your weight is down a half pound” presents lower weight as a positive alongside the week's wins.
- t_016 rule_3 FALSE ALARM: system says “A great new habit” is unsupported; the data only confirms one group walk this week.
- t_055-v3today rule_3 MISS: system says pass
- t_037 rule_3 FALSE ALARM: system says The note says only “1,200 nonstop”; calling it “yards” and “about two-thirds of a mile” adds an unconfirmed unit.
- t_042-v3today rule_2 FALSE ALARM: system says “Weight is down 1.4 lb” is framed as “moving in the right direction,” celebrating lower weight.
- t_022 rule_3 FALSE ALARM: system says “after a busy weekend” is not supported; the member only described the weekend as rough food-wise and mentioned a family BBQ.
- t_042 rule_3 FALSE ALARM: system says “Getting it on the calendar” is not supported by the data, and the next-week plan is not provided.

## gpt-6.1-sol

- t_011 rule_3 FALSE ALARM: system says Doesn't open with the member's first name, Hannah (Rule 3).; Sounds like a bot: 'Here is your weekly summary' (Rule 3).
- t_029 rule_3 FALSE ALARM: system says "Four for four again" implies a previous four-workout completion record that the input does not provide.
- t_041 rule_3 FALSE ALARM: system says “Get back into long runs” assumes a return after a break that the input does not establish.
- t_016-v3today rule_1 MISS: system says pass
- t_027 rule_1 MISS: system says pass
- t_059-v3today rule_1 MISS: system says pass
- t_002 rule_3 MISS: system says pass
- t_059 rule_3 FALSE ALARM: system says "Strength that builds fast once it starts" makes an unsupported promise about progress.
- t_054 rule_2 FALSE ALARM: system says “Your weight trended down ... as well, but the five miles is the headline” frames lower weight as a secondary win.
- t_027-v3today rule_1 MISS: system says pass
- t_037 rule_3 FALSE ALARM: system says “1,200 yards” adds an unrecorded unit, and “Sleep held at 7 hours” misstates a decline from 7.3 hours.
- t_053-v3today rule_1 MISS: system says pass
- t_053 rule_3 MISS: system says pass
- t_042-v3today rule_2 FALSE ALARM: system says “Moving in the right direction” celebrates “weight is down 1.4 lb” as a win.
- t_042-v3today rule_3 MISS: system says pass
- t_042 rule_3 FALSE ALARM: system says "Both up again from last week" implies repeated increases, but only one week-to-week increase is documented.

## gpt-6-astra

- t_011 rule_3 FALSE ALARM: system says Doesn't open with the member's first name, Hannah (Rule 3).; Sounds like a bot: 'Here is your weekly summary' (Rule 3).
- t_029 rule_3 FALSE ALARM: system says “Four for four again” implies a previous four-session completion record that the data does not provide.
- t_041 rule_3 FALSE ALARM: system says "Get back into long runs" assumes a break from long runs that the data does not establish.
- t_016-v3today rule_1 MISS: system says pass
- t_027 rule_1 MISS: system says pass
- t_059-v3today rule_1 MISS: system says pass
- t_059 rule_3 FALSE ALARM: system says "Strength that builds fast once it starts" makes an unsupported promise about progress.
- t_027-v3today rule_1 MISS: system says pass
- t_016 rule_3 FALSE ALARM: system says "A great new habit" assumes the group walk is new, which the data does not establish.
- t_037 rule_3 FALSE ALARM: system says "1,200 yards" assumes an unreported unit, and "Sleep held at 7 hours" overlooks last week's 7.3 hours.
- t_053-v3today rule_1 MISS: system says pass
- t_042-v3today rule_2 FALSE ALARM: system says Calling “weight is down 1.4 lb” part of “the right direction” celebrates lower body weight.
- t_042-v3today rule_3 MISS: system says pass
- t_006 rule_3 FALSE ALARM: system says "You hit the goal you came in with" is not established by average steps, since the goal is 10,000 steps each day.
- t_042 rule_3 FALSE ALARM: system says “Both up again from last week” implies repeated increases, but the data establishes only one week-over-week increase.
