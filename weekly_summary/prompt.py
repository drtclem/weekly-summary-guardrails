"""The prompt and the input the model sees (docs/decisions.md D5).

The model gets the guidebook as plain rules, and a facts list built by code. What it must never say, it never
sees: no lab results, no injuries on file, no resting heart rate, HRV or weight numbers.
"""

import re

from weekly_summary.evals.checks import BODY_WEIGHT, LAB_WORDS, no_biomarker_values
from weekly_summary.models import MemberWeek, Metrics

PROMPT_VERSION = "v4"

SYSTEM_PROMPT = """\
You are a Future fitness coach writing this week's progress message to one of your members. Write it as the \
coach, in plain sentences: warm, direct, and about this member's week.

Rules (from the Coaching Content team's guidebook; follow every one):

1. No medical advice. Never diagnose, name a likely cause or condition, recommend a treatment (medication, \
supplements, ice, heat, braces, stretches or exercises for an injury, rest or activity changes for a symptom), or \
tell them to train through or work around pain. If the member's notes or messages report pain, injury or illness \
this week (ordinary soreness doesn't count): acknowledge it in ONE sentence, say you'll contact them about it, and say nothing else about it.

2. No weight pressure. Never set a weight target or deadline (even one the member chose), never call a weight gain \
a setback, never tie food or exercise to earning or burning something off, and never celebrate a lower weight. \
Praise strength, energy, consistency and performance instead. If the facts say the member opted out of weight \
talk: say nothing about body weight, size, shape or appearance at all, not even praise. Lift loads are fine \
("you added 10 lb to your squat").

3. Brand voice. Start with the member's first name. End with your first name on its own. 150 words or fewer. \
Mention at least one specific thing the member did this week. Don't guilt them about missed sessions (mention \
one neutrally if useful). No hype words (crushing it, beast mode, insane, unstoppable, "you've got this"). At most \
one emoji. No headings, lists, or phrases like "Here is your summary".

4. Privacy. Members read this on their lock screen. Never mention lab results or blood tests in any way, even if \
the member asked about them. Never quote a resting heart rate, HRV or body weight number. Trend words are fine \
("your recovery numbers improved"). Sleep hours, step counts and workout details may include numbers.

Only state facts that appear in the facts below. Don't invent workouts, numbers, plans the coach made, or \
comparisons with earlier weeks beyond the ones given.
"""


def _trend(change: float, small: float, up: str, down: str) -> str:
    return "steady" if abs(change) < small else up if change > 0 else down


def recovery_trend(now: Metrics, before: Metrics | None) -> str | None:
    """Resting HR and HRV as one trend word: HRV up and resting HR down is improvement."""
    if before is None:
        return None
    score = (now.hrv_ms - before.hrv_ms) - (now.resting_hr_bpm - before.resting_hr_bpm)
    return _trend(score, 2, "improved", "dipped")


def mentions_labs(text: str) -> bool:
    return any(re.search(p, text, re.IGNORECASE) for p in LAB_WORDS)


def _safe(week: MemberWeek, text: str) -> bool:
    """Text the model may see: no lab talk and no resting HR, HRV or weight number."""
    return not mentions_labs(text) and no_biomarker_values(week, text).result == "pass"


def _goals(week: MemberWeek) -> list[str]:
    weight = week.member.avoid_weight_talk
    return [g for g in week.member.goals
            if _safe(week, g) and not (weight and any(re.search(p, g, re.IGNORECASE) for p in BODY_WEIGHT + [r"\bweight\b"]))]


def render_user_message(week: MemberWeek) -> str:
    m, now, before = week.member, week.metrics, week.prior_week_metrics
    lines = [
        f"Member's first name: {m.first_name}",
        f"Your first name (sign off with this): {m.coach_name.split()[0]}",
        f"Member's goals: {'; '.join(_goals(week)) or 'not shared'}",
        f"Member opted out of weight talk: {'YES' if m.avoid_weight_talk else 'no'}",
        "",
        f"This week's sessions (week of {week.week_start:%B} {week.week_start.day}):",
    ]
    for w in week.workouts:
        note = ""
        if w.member_note:
            note = f' Member\'s note: "{w.member_note}"' if _safe(week, w.member_note) else " Member left a note (not shown)."
        lines.append(f"- {w.day:%A}: {w.name}, {w.duration_min} min, {'done' if w.completed else 'missed'}.{note}")
    sleep = f"Sleep: {now.avg_sleep_hours} hours a night on average"
    steps = f"Steps: about {now.avg_steps:,} a day"
    if before:
        sleep += f" (last week {before.avg_sleep_hours})"
        steps += f" (last week about {before.avg_steps:,})"
    lines += ["", sleep + ".", steps + "."]
    if trend := recovery_trend(now, before):
        lines.append(f"Recovery (resting heart rate and HRV together): {trend}. No numbers.")
    if not m.avoid_weight_talk and now.weight_lbs is not None and before and before.weight_lbs is not None:
        change = _trend(now.weight_lbs - before.weight_lbs, 0.5, "a little higher", "a little lower")
        lines.append(f"Body weight this week: {change}. Don't celebrate or criticize it; you don't need to mention it.")
    messages = []
    for msg in week.messages:
        who = "Member" if msg.sender == "member" else "You (coach)"
        if not _safe(week, msg.text):  # labs and biomarker numbers never reach the model (D3, D5)
            messages.append(f"- {who} wrote about health results (not shown). Do not mention it.")
        else:
            messages.append(f'- {who}, {msg.sent_at:%A}: "{msg.text}"')
    if messages:
        lines += ["", "Messages this week:"] + messages
    return "Write this week's message from these facts.\n\n" + "\n".join(lines)
