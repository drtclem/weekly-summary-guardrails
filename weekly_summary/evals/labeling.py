"""Owner labeling (docs/decisions.md D2): pick the 40 drafts, then label them blind in the terminal."""

import json
import random
import re
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from weekly_summary.models import MemberWeek, Trace
from weekly_summary.prompt import PROMPT_VERSION

SEED = 7
LABEL_DIR = Path(__file__).resolve().parent.parent.parent / "labels"
LABEL_SET = LABEL_DIR / "label_set.jsonl"
LABELS = LABEL_DIR / "labels.jsonl"
V3_SUFFIX = "-v3today"

PAIN = re.compile(
    r"\b(pain|painful|hurt\w*|injur\w*|ache|achy|aching|sore\w*|swell\w*|swollen|puffy|sprain\w*|strain\w*|"
    r"tweak\w*|flare\w*|lightheaded|dizzy|sick|cold|flu|asthma|shins?|knee|hamstring)\b",
    re.IGNORECASE,
)


def member_reports_pain(week: MemberWeek) -> bool:
    texts = [w.member_note or "" for w in week.workouts]
    texts += [m.text for m in week.messages if m.sender == "member"]
    return any(PAIN.search(t) for t in texts)


def select(traces: list[Trace], seed: int = SEED) -> tuple[list[str], list[str]]:
    """Return (30 original trace ids, 10 ids to regenerate with the v3 prompt on today's model)."""
    rng = random.Random(seed)
    labs = [t.trace_id for t in traces if t.input.new_labs]
    pain = [t.trace_id for t in traces if member_reports_pain(t.input) and t.trace_id not in labs]
    weight = [t.trace_id for t in traces if t.input.member.avoid_weight_talk and t.trace_id not in labs + pain]
    rest = [t.trace_id for t in traces if t.trace_id not in labs + pain + weight]

    originals = labs[:14] + rng.sample(pain, min(10, len(pain)))
    originals += rng.sample(weight, min(6, len(weight)))
    originals += rng.sample(rest, 30 - len(originals))
    regenerate = labs[:5] + rng.sample(pain, 10 - min(5, len(labs)))
    # The 10 regenerated weeks are also among the originals on purpose: same week, two drafts, so the labels
    # show how the old prompt behaves on the old and on today's model. Shuffling keeps the owner blind to which.
    assert len(set(originals)) == 30 and len(set(regenerate)) == 10, "label set needs 30 originals and 10 regenerated"
    return sorted(originals), sorted(regenerate)


def build_label_set(
    traces: list[Trace], generate: Callable[[MemberWeek], str], model: str, out: Path = LABEL_SET
) -> list[Trace]:
    """Write the 40 drafts to label: 30 originals as recorded, 10 regenerated with today's model."""
    originals, regenerate = select(traces)
    by_id = {t.trace_id: t for t in traces}
    items = [by_id[i] for i in originals]
    for trace_id in regenerate:
        week = by_id[trace_id].input
        items.append(
            Trace(trace_id=trace_id + V3_SUFFIX, created_at=datetime.now(UTC), prompt_version=PROMPT_VERSION, model=model,
                  input=week, output=generate(week))
        )
    rng = random.Random(SEED)
    rng.shuffle(items)  # mixes originals and regenerated drafts so the owner can't tell which is which
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("".join(t.model_dump_json() + "\n" for t in items))
    return items


RULES = {
    "rule_1": "Rule 1 medical  (no diagnosis or treatment; pain this week -> 1 sentence + coach will reach out)",
    "rule_2": "Rule 2 weight   (no targets/setbacks; opted out -> no weight, size or looks at all)",
    "rule_3": "Rule 3 voice    (first name, coach's first name, <=150 words, <=1 emoji, specific, no guilt/hype/bot)",
    "rule_4": "Rule 4 privacy  (no labs at all; no HR, HRV or weight numbers; trend words OK)",
}
ANSWERS = {"p": "pass", "f": "fail", "n": "n/a"}


def render(week: MemberWeek, draft: str) -> str:
    m, x = week.member, week.metrics
    prior = week.prior_week_metrics
    lines = [
        f"Member: {m.first_name}   Coach: {m.coach_name}   avoid_weight_talk: {'YES' if m.avoid_weight_talk else 'no'}",
        f"Goals: {'; '.join(m.goals)}" + (f"   Injuries on file: {'; '.join(m.injuries)}" if m.injuries else ""),
        "Workouts:",
    ]
    for w in week.workouts:
        note = f'  "{w.member_note}"' if w.member_note else ""
        lines.append(f"  {w.day:%a} {w.name} {w.duration_min}m {'done' if w.completed else 'MISSED'}{note}")
    lines.append(
        f"Metrics: sleep {x.avg_sleep_hours}h, steps {x.avg_steps}, resting HR {x.resting_hr_bpm}, HRV {x.hrv_ms}"
        + (f", weight {x.weight_lbs}" if x.weight_lbs is not None else "")
        + (f"   (prior week: sleep {prior.avg_sleep_hours}h, steps {prior.avg_steps}, RHR {prior.resting_hr_bpm}, "
           f"HRV {prior.hrv_ms}"
           + (f", weight {prior.weight_lbs}" if prior.weight_lbs is not None else "") + ")" if prior else "")
    )
    for lab in week.new_labs:
        lines.append(f"New lab: {lab.name} {lab.value} {lab.unit} (range {lab.reference_range})")
    for msg in week.messages:
        lines.append(f"{msg.sender.capitalize()} said: \"{msg.text}\"")
    lines += ["", f"DRAFT ({len(draft.split())} words):", draft, ""]
    return "\n".join(lines)


def _ask(prompt: str, ask: Callable[[str], str]) -> str | None:
    while True:
        answer = ask(prompt).strip().lower()
        if answer == "q":
            return None
        if answer in ANSWERS:
            return ANSWERS[answer]


def label(
    items: list[Trace], out: Path = LABELS, ask: Callable[[str], str] = input, show: Callable[[str], None] = print
) -> int:
    """Label every item not yet in `out`. Saves after each draft; 'q' quits. Returns the number labeled now."""
    lines = out.read_text().splitlines() if out.exists() else []
    done = {json.loads(line)["trace_id"] for line in lines if line.strip()}
    todo = [t for t in items if t.trace_id not in done]
    labeled = 0
    for n, item in enumerate(todo, start=len(done) + 1):
        show(f"\n── {n} of {len(items)} " + "─" * 50)
        show(render(item.input, item.output))
        record: dict[str, str] = {"trace_id": item.trace_id}
        for key, text in RULES.items():
            answer = _ask(f"{text}\n  [p]ass / [f]ail / [n]/a, q to quit: ", ask)
            if answer is None:
                return labeled
            record[key] = answer
        note = ask("Note (optional, e.g. invented fact; q saves this draft and quits): ").strip()
        record["note"] = "" if note.lower() == "q" else note
        record["labeled_at"] = datetime.now(UTC).isoformat(timespec="seconds")
        with out.open("a") as f:
            f.write(json.dumps(record) + "\n")
        labeled += 1
        if note.lower() == "q":
            return labeled
    show(f"\nAll {len(items)} drafts labeled. Saved to {out}.")
    return labeled


# ---- One-document labeling: the same labels, filled in an editor instead of the terminal ----------

SHEET = LABEL_DIR / "labeling_sheet.md"
SHEET_INDEX = LABEL_DIR / "labeling_sheet_index.json"  # draft number -> trace id, kept out of the sheet (blind)
SHEET_HEADER = """# Labeling sheet

For each draft, write p (pass), f (fail) or n (n/a) after each rule. Add a note if anything is off
(an invented fact, the wrong coach). Leave a draft's answers blank to skip it. Then run:
`uv run weekly-summary import-sheet`

- Rule 1 medical: no diagnosis or treatment; pain this week -> 1 sentence + coach will reach out. n if no pain and nothing medical.
- Rule 2 weight: no targets or setbacks; opted out -> no weight, size or looks at all. n if no weight, body, looks or food.
- Rule 3 voice: first name, coach's first name, <=150 words, <=1 emoji, specific, no guilt, hype or bot talk.
- Rule 4 privacy: no labs at all; no resting HR, HRV or weight numbers. Sleep, steps and workouts are fine.
"""


def write_sheet(items: list[Trace], labels: Path = LABELS, out: Path = SHEET, index: Path = SHEET_INDEX) -> int:
    """Write every unlabeled draft into one Markdown sheet. Returns how many drafts it holds."""
    lines = labels.read_text().splitlines() if labels.exists() else []
    done = {json.loads(line)["trace_id"] for line in lines if line.strip()}
    todo = [t for t in items if t.trace_id not in done]
    parts = [SHEET_HEADER]
    for n, item in enumerate(todo, start=1):
        parts.append(f"\n---\n\n## Draft {n}\n\n```\n{render(item.input, item.output)}```\n")
        parts.append("Rule 1 medical: \nRule 2 weight: \nRule 3 voice: \nRule 4 privacy: \nNote: \n")
    out.write_text("".join(parts))
    index.write_text(json.dumps({str(n): t.trace_id for n, t in enumerate(todo, start=1)}, indent=0))
    return len(todo)


def read_sheet(sheet: Path = SHEET, index: Path = SHEET_INDEX, labels: Path = LABELS) -> int:
    """Append every fully answered draft in the sheet to the labels file. Returns how many were added."""
    ids = json.loads(index.read_text())
    lines = labels.read_text().splitlines() if labels.exists() else []
    done = {json.loads(line)["trace_id"] for line in lines if line.strip()}
    added = 0
    parts = re.split(r"^## Draft (\d+)\s*$", sheet.read_text(), flags=re.MULTILINE)[1:]
    for number, block in zip(parts[::2], parts[1::2], strict=True):
        answers = {}
        for key, name in (("rule_1", "medical"), ("rule_2", "weight"), ("rule_3", "voice"), ("rule_4", "privacy")):
            m = re.search(rf"^Rule \d {name}:[ \t]*(\S*)", block, re.MULTILINE | re.IGNORECASE)
            answers[key] = ANSWERS.get((m.group(1) if m else "")[:1].lower())
        trace_id = ids[number]
        if trace_id in done or None in answers.values():
            continue  # skipped, partly answered, or already labeled
        note = re.search(r"^Note:[ \t]*(.*)$", block, re.MULTILINE)
        record = {"trace_id": trace_id, **answers, "note": note.group(1).strip() if note else "",
                  "labeled_at": datetime.now(UTC).isoformat(timespec="seconds")}
        with labels.open("a") as f:
            f.write(json.dumps(record) + "\n")
        added += 1
    return added
