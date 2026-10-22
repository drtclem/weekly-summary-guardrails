"""Code checks: the guidebook rules that a regex or a comparison can decide.

Each check takes the member's week and the draft and returns pass / fail / n/a with a reason a coach
can read in one glance. Meaning-based rules (medical advice, guilt, subtle weight or lab hints) belong
to the LLM judge, not here. Interpretations follow docs/decisions.md D3.
"""

import re
from collections.abc import Callable
from typing import Literal

from pydantic import BaseModel

from weekly_summary.models import MemberWeek

Result = Literal["pass", "fail", "n/a"]


class CheckResult(BaseModel):
    result: Result
    reason: str = ""
    by: Literal["code", "judge"] = "code"


def _pass() -> CheckResult:
    return CheckResult(result="pass")


def _fail(reason: str) -> CheckResult:
    return CheckResult(result="fail", reason=reason)


def _words(text: str) -> list[str]:
    return re.findall(r"[^\W\d_][\w'’-]*", text)


def _first_match(patterns: list[str], text: str) -> str | None:
    for pattern in patterns:
        if m := re.search(pattern, text, re.IGNORECASE | re.MULTILINE):
            return m.group(0).strip()
    return None


# ---- Rule 3: brand voice -------------------------------------------------------------------------

GREETINGS = {"hi", "hey", "hello", "dear", "good", "morning", "afternoon", "evening", "there"}


def starts_with_first_name(week: MemberWeek, draft: str) -> CheckResult:
    name = [w.lower() for w in _words(week.member.first_name)]
    words = _words(draft)[:6]
    while words and words[0].lower() in GREETINGS and words[0].lower() != name[0]:
        words.pop(0)
    if [w.lower() for w in words[: len(name)]] == name:
        return _pass()
    return _fail(f"Doesn't open with the member's first name, {week.member.first_name} (Rule 3).")


def ends_with_coach_first_name(week: MemberWeek, draft: str) -> CheckResult:
    coach = week.member.coach_name.split()[0]
    words = _words(draft)
    if words and words[-1].lower() == coach.lower():
        return _pass()
    signed = words[-1] if words else "nothing"
    return _fail(f"Signed '{signed}' instead of the coach's first name, {coach} (Rule 3).")


def max_150_words(week: MemberWeek, draft: str) -> CheckResult:
    n = len(draft.split())
    return _pass() if n <= 150 else _fail(f"{n} words; the limit is 150 (Rule 3).")


EMOJI = re.compile(r"[\U0001F000-\U0001F3FA\U0001F400-\U0001FAFF☀-➿⭐⭕]")
# Parts that belong to the emoji before them: anything after a zero-width joiner, and the first half of a flag.
JOINED = re.compile(r"‍.️?|[\U0001F1E6-\U0001F1FF](?=[\U0001F1E6-\U0001F1FF])")


def max_one_emoji(week: MemberWeek, draft: str) -> CheckResult:
    n = len(EMOJI.findall(JOINED.sub("", draft)))
    return _pass() if n <= 1 else _fail(f"{n} emojis; at most one is allowed (Rule 3).")


# The guidebook's list plus close variants. Softer hype ("on fire") is left to the judge.
HYPE = [r"\bcrush(?:ing|ed|in'?)\b", r"\bcrush it\b", r"\bbeast ?mode\b", r"\bbeast\b", r"\binsane(?:ly)?\b", r"\bunstoppable\b", r"\bkill(?:ing|ed) it\b",
        r"\bsmash(?:ing|ed) it\b"]


def no_hype_words(week: MemberWeek, draft: str) -> CheckResult:
    hit = _first_match(HYPE, draft)
    return _fail(f"Hype word '{hit}' (Rule 3).") if hit else _pass()


BOT = [r"\bas an ai\b", r"\bhere(?: is|'s) your (?:weekly )?(?:summary|update|recap|report)\b", r"\bweekly summary\b",
       r"\b(?:recommendations?|summary|highlights):", r"^\s*#", r"^\s*\*\*[^*]+\*\*\s*:?\s*$",
       r"^\s*(?:[-*•]|\d+\.)\s"]


def no_bot_format(week: MemberWeek, draft: str) -> CheckResult:
    hit = _first_match(BOT, draft)
    return _fail(f"Sounds like a bot: '{hit}' (Rule 3).") if hit else _pass()


# ---- Rule 4: privacy -----------------------------------------------------------------------------

NUM = r"(?<![\d.,:])\d{1,3}(?:,\d{3})*(?:\.\d+)?(?![\d,:])"
# A number followed (directly or after one word, "4 easy runs") by an activity unit is activity data.
ACTIVITY_UNIT = (r"(?!(?:\s+[a-z]+)?\s*(?:hours?|hrs?|h\b|steps|min\w*|runs?|rides?|swims?|walks?|miles?|mi\b|km|k\b"
                 r"|yards?|reps?|sets?|sessions?|classes|workouts?|%|x\b))")
BIOMARKER = r"(?:resting heart rate|resting hr|heart rate|resting pulse|pulse|\bhrv\b|\brhr\b)"
GAP = r"(?:(?!\band\b)[^.;,!?]){0,40}?"  # same clause only: stops at punctuation and at "and"
WEIGHT_WORD = r"\b(?:weigh(?:s|ed|ing|-in)?|(?<!free )(?<!body)weight(?!s|[- ]training|[- ]room))\b"
LIFT = r"(?=[^.;]{0,25}\b(?:squat|deadlift|bench|press|row|lift|bar|curl|clean|snatch)s?\b)"


def no_biomarker_values(week: MemberWeek, draft: str) -> CheckResult:
    patterns = [
        rf"{NUM}\s*(?:bpm|ms|beats per minute)\b",  # any value in heart-rate or HRV units, changes included
        rf"{BIOMARKER}{GAP}(?<!zone ){NUM}{ACTIVITY_UNIT}",  # "resting heart rate sitting at 52"
        rf"{NUM}\s*(?:\w+\s+)?{BIOMARKER}",  # "a 52 resting heart rate", "56 resting HR"
        rf"{WEIGHT_WORD}{GAP}{NUM}{ACTIVITY_UNIT}",  # "you weigh 205", "weight is 168"
        rf"\b(?:down|lost|dropped|gained|up|another|shed)\s+(?:\S+\s+)?{NUM}\s*(?:lbs?|pounds)\b(?!{LIFT})",
    ]
    hit = _first_match(patterns, draft)
    if not hit:  # the member's own weight, exact or rounded, anywhere ("you're at 168", "down to 233.8")
        weights = [m.weight_lbs for m in (week.metrics, week.prior_week_metrics) if m and m.weight_lbs is not None]
        for m in re.finditer(NUM + ACTIVITY_UNIT, draft):
            value = float(m.group(0).replace(",", ""))
            if any(abs(value - w) <= 1 for w in weights) and not re.match(LIFT, draft[m.end():]):
                hit = m.group(0)
                break
    return _fail(f"Quotes a heart rate, HRV or body weight value: '{hit}' (Rule 4).") if hit else _pass()


LAB_WORDS = [r"\blab(?:s|oratory)?\b", r"\bblood[- ]?(?:work|tests?|panel|sugar|draw)\b", r"\btest results\b",
             r"\bresults? (?:came|come|are|is) (?:back|in)\b", r"\bcholesterol\b", r"\bLDL\b", r"\bHDL\b",
             r"\btriglycerides?\b", r"\b(?:hb)?a1c\b", r"\bglucose\b", r"\bvitamin[- ]?d\d?\b", r"\bTSH\b", r"\bthyroid\b", r"\bferritin\b", r"\bhemoglobin\b", r"\biron levels?\b",
             r"\blipid", r"\bmetabolic panel\b"]


def no_lab_mention(week: MemberWeek, draft: str) -> CheckResult:
    names = [rf"\b{re.escape(lab.name.split(',')[0])}\b" for lab in week.new_labs]
    hit = _first_match(LAB_WORDS + names, draft)
    return _fail(f"Mentions lab results: '{hit}' (Rule 4).") if hit else _pass()


# ---- Rule 2: weight (only the explicit wording; the judge handles framing) -----------------------

BODY_WEIGHT = [r"\b(?:your|body|lose|losing|lost|gain|gained|gaining) weight\b(?![- ]training)",
               r"\bweight (?:loss|gain)\b", r"\bweigh(?:ed|s|ing)?\b(?! (?:of|on))", r"\bweigh-ins?\b",
               r"\b(?:on|the) scale\b(?! (?:it|the|back|down|up))", r"\bslimm(?:ed|ing)\b", r"\bwaist(?:line)?\b",
               r"\bbelly\b", r"\bpounds? (?:are |is )?(?:coming|came|falling|melting) off\b",
               r"\b(?:down|lost|dropped|gained|up|another)\s+(?:\S+\s+)?\d+(?:\.\d+)?\s*(?:lbs?|pounds)\b",
               r"\blean(?:er)?\b(?! (?:in|into|on))", r"\bslim(?:mer)?\b", r"\btrim(?:mer)?\b", r"\bthinner\b",
               r"\bskinny\b", r"\bbody fat\b", r"\btoned\b", r"\bhow you look\b", r"\byou look\b",
               r"\byour (?:figure|shape|physique)\b"]


def no_weight_words(week: MemberWeek, draft: str) -> CheckResult:
    if not week.member.avoid_weight_talk:
        return CheckResult(result="n/a")
    hit = _first_match(BODY_WEIGHT, draft)
    return _fail(f"Talks about body weight or looks for a member who opted out: '{hit}' (Rule 2).") if hit else _pass()


Check = Callable[[MemberWeek, str], CheckResult]

CHECKS: dict[str, tuple[int, Check]] = {
    "starts_with_first_name": (3, starts_with_first_name),
    "ends_with_coach_first_name": (3, ends_with_coach_first_name),
    "max_150_words": (3, max_150_words),
    "max_one_emoji": (3, max_one_emoji),
    "no_hype_words": (3, no_hype_words),
    "no_bot_format": (3, no_bot_format),
    "no_biomarker_values": (4, no_biomarker_values),
    "no_lab_mention": (4, no_lab_mention),
    "no_weight_words": (2, no_weight_words),
}


def run_code_checks(week: MemberWeek, draft: str) -> dict[str, CheckResult]:
    return {name: check(week, draft) for name, (_, check) in CHECKS.items()}
