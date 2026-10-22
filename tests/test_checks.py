"""Code checks, tested against real production traces (data/traces.jsonl) and the D3 edge cases."""

import pytest

from weekly_summary.data import load_traces
from weekly_summary.evals.checks import CHECKS, run_code_checks

TRACES = {t.trace_id: t for t in load_traces()}

# t_016 regenerated on claude-sonnet-5-5 with the v3 prompt (live check, 2026-10-20).
ISAAC_V3_TODAY = (
    "Hi Isaac! Great week: you completed all 4 workouts, including that 30-second one-foot stand in balance "
    "class, which is a real win for your balance goal, and the hour-long walk with your neighborhood group. "
    "Your average steps rose to 7,300 (up from 6,800), you averaged 7.7 hours of sleep, your resting heart rate "
    "held steady at 63 bpm, your HRV edged up to 35 ms, and your weight eased to 175.6 lbs. I saw the bloodwork "
    "you mentioned, and I know it's a lot of numbers. Your LDL (162 mg/dL) and triglycerides (180 mg/dL) are "
    "above the reference ranges, and your HDL (41 mg/dL) is right at the edge of the healthy range. That's worth "
    "talking through with your doctor, who can tell you what it means for you. The consistent walking and "
    "movement you're already doing is a great foundation, so let's keep it going next week, and maybe push toward "
    "a third balance session or a few more steps each day. You're doing great! - Sam"
)


def results(trace_id: str, draft: str | None = None) -> dict[str, str]:
    trace = TRACES[trace_id]
    return {name: r.result for name, r in run_code_checks(trace.input, draft or trace.output).items()}


def test_clean_draft_passes_every_code_check():
    assert set(results("t_001").values()) == {"pass", "n/a"}  # n/a: Maya allows weight talk
    assert set(results("t_009").values()) == {"pass"}  # Lena opted out of weight talk; nothing to flag


def test_isaac_v3_today_fails_lab_biomarker_and_length_but_greeting_and_signoff_pass():
    r = results("t_016", ISAAC_V3_TODAY)
    assert r["no_lab_mention"] == "fail"
    assert r["no_biomarker_values"] == "fail"
    assert r["max_150_words"] == "fail"
    assert r["starts_with_first_name"] == "pass"  # "Hi Isaac!" passes (D3)
    assert r["ends_with_coach_first_name"] == "pass"  # coach is "Sam Whitaker", signs "- Sam"


@pytest.mark.parametrize(
    ("trace_id", "check"),
    [
        ("t_011", "starts_with_first_name"),  # "Here is your weekly summary..."
        ("t_011", "no_bot_format"),
        ("t_039", "ends_with_coach_first_name"),  # signed by Priya, coach is Jordan
        ("t_033", "max_150_words"),  # 153 words
        ("t_038", "no_hype_words"),  # "beast mode", "crushing"
        ("t_010", "no_biomarker_values"),  # resting heart rate "sitting at 52"
        ("t_044", "no_biomarker_values"),  # "HRV jumping to 71 ms"
        ("t_002", "no_biomarker_values"),  # "down to 233.8 lb"
        ("t_025", "no_biomarker_values"),  # "down another 1.4 lb to 168.4"
        ("t_016", "no_lab_mention"),  # "cholesterol coming back on the high side"
        ("t_027", "no_lab_mention"),  # "A1C is at 6.1%"
        ("t_053", "no_lab_mention"),  # "your lab results came in" (D3 Fork 1: never mention)
        ("t_023", "no_weight_words"),  # "how much trimmer you've gotten", avoid_weight_talk
        ("t_025", "no_weight_words"),  # "on the scale", avoid_weight_talk
        ("t_049", "no_weight_words"),  # "proud of how you look", avoid_weight_talk
    ],
)
def test_real_violations_are_caught(trace_id: str, check: str):
    assert results(trace_id)[check] == "fail"


@pytest.mark.parametrize(
    ("trace_id", "check"),
    [
        ("t_024", "no_biomarker_values"),  # "resting heart rate came down" (trend, no number)
        ("t_030", "no_biomarker_values"),  # "resting heart rate and HRV both trended the right way"
        ("t_052", "no_biomarker_values"),  # "your recovery numbers improved"
        ("t_042", "no_lab_mention"),  # has new labs; draft doesn't mention them
        ("t_029", "no_weight_words"),  # "free weights intro" is equipment, not body weight
        ("t_009", "no_weight_words"),
        ("t_012", "max_one_emoji"),  # exactly one emoji
        ("t_057", "ends_with_coach_first_name"),  # "Talk soon, Tasha"
        ("t_017", "ends_with_coach_first_name"),  # "🏊 Tasha"
        ("t_031", "no_biomarker_values"),  # "added 10 lb to your squat" is a lift load
    ],
)
def test_allowed_drafts_are_not_flagged(trace_id: str, check: str):
    assert results(trace_id)[check] == "pass"


def test_weight_words_not_applicable_when_weight_talk_allowed():
    assert results("t_002")["no_weight_words"] == "n/a"


def test_two_emojis_fail():
    assert results("t_001", "Maya, great week 🎉🔥 Jordan")["max_one_emoji"] == "fail"


def test_biomarker_change_as_a_number_fails():  # D3: a change is still a number
    draft = "Maya, nice week. Your resting heart rate dropped 3 bpm. Jordan"
    assert results("t_001", draft)["no_biomarker_values"] == "fail"


def test_zone_two_is_not_a_biomarker_value():
    draft = "Maya, your heart rate stayed in zone 2 on the easy run. Jordan"
    assert results("t_001", draft)["no_biomarker_values"] == "pass"


def test_lab_words_fail_even_without_labs_in_input():
    assert results("t_001", "Maya, your bloodwork looks great. Jordan")["no_lab_mention"] == "fail"


def test_every_failure_has_a_reason_naming_the_rule():
    for result in run_code_checks(TRACES["t_016"].input, ISAAC_V3_TODAY).values():
        if result.result == "fail":
            assert "(Rule " in result.reason


def test_every_check_has_a_rule():
    assert all(rule in {1, 2, 3, 4} for rule, _ in CHECKS.values())


# ---- Cases from the independent review (2026-10-21) ----------------------------------------------


@pytest.mark.parametrize(
    "sentence",
    [
        "Your resting heart rate was 52 this week.",
        "That's a 52 resting heart rate.",
        "You're at 56 resting HR.",
        "Your heart sat at 52 beats per minute.",
        "A resting pulse of 56 is great.",
        "RHR: 52 and steady.",
        "HRV of 71 is a big jump.",
        "Your weight is 168 now.",
        "You weigh 168 this week.",
        "You're at 168 this week.",  # t_025's own weight, rounded, no unit
        "You're down 1.5 lb this week.",  # a rounded change
    ],
)
def test_biomarker_values_in_any_phrasing_fail(sentence: str):
    assert results("t_025", f"Aisha, {sentence} Elena")["no_biomarker_values"] == "fail"


@pytest.mark.parametrize(
    "sentence",
    [
        "Your HRV improved and sleep averaged 7.4 hours.",  # trend word + activity number (guidebook example)
        "Your heart rate stayed low on all 4 easy runs.",
        "Your heart rate stayed in Zone 2 for 45 min.",
        "Your resting heart rate came down, and your parkrun was 26:12.",
        "You averaged 7,300 steps and 7.7 hours of sleep.",
        "You added 10 lb to your squat.",
        "You went up 10 lb on your deadlift.",
        "135 for five on the squat.",
        "Your weight training block starts Monday.",
    ],
)
def test_activity_numbers_and_trend_words_pass(sentence: str):
    assert results("t_025", f"Aisha, {sentence} Elena")["no_biomarker_values"] == "pass"


@pytest.mark.parametrize(
    "sentence",
    ["Your HbA1c came back.", "Your blood-work is in.", "The laboratory results are in.", "Your Vitamin-D is fine.",
     "Your vitamin D3 looks good.", "Results from your blood draw are in.", "Your results came back normal."],
)
def test_lab_phrasings_fail(sentence: str):
    assert results("t_001", f"Maya, {sentence} Jordan")["no_lab_mention"] == "fail"


@pytest.mark.parametrize(("draft", "first"), [("Good morning, Maya! Great week. Jordan", "Maya"),
                                              ("Hi there Maya, great week. Jordan", "Maya")])
def test_greeting_variants_pass(draft: str, first: str):
    assert results("t_001", draft)["starts_with_first_name"] == "pass"


def test_non_ascii_names():
    week = TRACES["t_001"].input
    member = week.member.model_copy(update={"first_name": "Zoë", "coach_name": "Renée Diaz"})
    week = week.model_copy(update={"member": member})
    found = {n: r.result for n, r in run_code_checks(week, "Zoë, great week. Renée").items()}
    assert found["starts_with_first_name"] == found["ends_with_coach_first_name"] == "pass"


def test_one_zwj_emoji_counts_once():
    assert results("t_001", "Maya, great lift 🏋️‍♀️ Jordan")["max_one_emoji"] == "pass"


@pytest.mark.parametrize("sentence", ["You've slimmed down.", "Your waistline is shrinking.", "Belly fat is going.",
                                      "The pounds are coming off."])
def test_more_body_weight_words_fail_when_opted_out(sentence: str):
    assert results("t_009", f"Lena, {sentence} Elena")["no_weight_words"] == "fail"


@pytest.mark.parametrize("sentence", ["Your weight training is paying off.", "Let's scale the workout down a bit."])
def test_training_words_are_not_body_weight(sentence: str):
    assert results("t_009", f"Lena, {sentence} Elena")["no_weight_words"] == "pass"


def test_crush_as_a_noun_is_not_hype():
    assert results("t_001", "Maya, despite the crush of work you ran. Jordan")["no_hype_words"] == "pass"
    assert results("t_001", "Maya, beastmode this week. Jordan")["no_hype_words"] == "fail"


def test_plan_for_next_week_is_not_bot_talk():
    assert results("t_001", "Maya, here's your plan for next week: rest. Jordan")["no_bot_format"] == "pass"
    assert results("t_001", "Maya,\n**Highlights**\nYou ran. Jordan")["no_bot_format"] == "fail"
