"""The hardened feature (docs/decisions.md D5–D7): write, check, repair in code, rewrite once, decide.

    write (v4 prompt, facts input) -> code checks -> repair in code -> judge
        -> if anything fails: one rewrite with the reasons -> repair -> checks -> decide

Evaluate-only mode (the drafts already in a traces file) skips writing, repair and rewrite, and applies the same
checks and decision to the draft as written.
"""

import re
import time

from pydantic import BaseModel

from weekly_summary.evals.checks import (
    EMOJI,
    JOINED,
    CheckResult,
    no_biomarker_values,
    no_lab_mention,
    run_code_checks,
)
from weekly_summary.evals.judge import JudgeRun, judge
from weekly_summary.evals.labeling import member_reports_pain
from weekly_summary.evals.run import RULE_OF, cost
from weekly_summary.llm import Completion, LLMClient
from weekly_summary.models import MemberWeek
from weekly_summary.prompt import SYSTEM_PROMPT, mentions_labs, render_user_message

MAX_REASONS = 2


class Outcome(BaseModel):
    trace_id: str
    decision: str
    reasons: list[str]
    draft: str
    first_draft: str = ""
    removed: list[str] = []
    rewritten: bool = False
    checks: dict[str, CheckResult] = {}
    rules: dict[str, str] = {}
    generator_tokens: tuple[int, int] = (0, 0)
    judge_runs: list[JudgeRun] = []
    seconds: float = 0.0


# ---- Repair in code (D6): remove what must never be sent, deterministically --------------------------------


def _drop_extra_emoji(draft: str) -> str:
    seen = 0
    out = []
    for ch in JOINED.sub("", draft):
        if EMOJI.match(ch):
            seen += 1
            if seen > 1:
                continue
        out.append(ch)
    return "".join(out)


def repair(week: MemberWeek, draft: str) -> tuple[str, list[str]]:
    """Delete each sentence that quotes a biomarker value or mentions labs; keep only the first emoji.

    Text between sentences (paragraph breaks) is kept as it was.
    """
    removed = [s for s in re.split(r"(?<=[.!?])\s+", draft.strip())
               if no_biomarker_values(week, s).result == "fail" or no_lab_mention(week, s).result == "fail"]
    for sentence in removed:
        draft = re.sub(re.escape(sentence) + r"[ \t]*", "", draft, count=1)
    return _drop_extra_emoji(draft.strip()), removed


# ---- Checks and decision (D7) ------------------------------------------------------------------------------


def _blocking(week: MemberWeek, name: str, result: CheckResult) -> bool:
    if result.result != "fail":
        return False
    rule = RULE_OF[name]
    return (
        rule == 4
        or name == "no_medical_advice"
        or (rule == 2 and week.member.avoid_weight_talk)
        or result.reason.startswith("Judge error")
    )


def check(week: MemberWeek, draft: str, judge_client: LLMClient | None) -> tuple[dict[str, CheckResult], JudgeRun | None]:
    """Code checks; then the judge, unless code already decided a block (D1: don't pay to confirm a block)."""
    checks = run_code_checks(week, draft)
    if judge_client is None or any(_blocking(week, n, r) for n, r in checks.items()):
        return checks, None
    run = judge(week, draft, judge_client)
    return checks | run.checks, run


def coach_todos(week: MemberWeek, checks: dict[str, CheckResult]) -> list[str]:
    todos = []
    pain = checks.get("pain_handled")
    if pain and pain.result != "n/a":
        todos.append("Coach to-do: the member reported pain, injury or illness this week. Contact them about it.")
    elif pain is None and member_reports_pain(week):  # judge skipped: fall back to the member's own words
        todos.append("Coach to-do: the member may have reported pain, injury or illness this week. Check their notes.")
    if any(mentions_labs(m.text) for m in week.messages if m.sender == "member"):
        todos.append("Coach to-do: the member asked about lab results. Handle it with them directly, not in this message.")
    return todos


def decide(week: MemberWeek, checks: dict[str, CheckResult], removed: bool = False) -> tuple[str, list[str]]:
    blocks = [r.reason for n, r in checks.items() if _blocking(week, n, r)]
    flags = [r.reason for n, r in checks.items() if r.result == "fail" and not _blocking(week, n, r)]
    if removed:  # health data had to be cut from the final draft: a hint may survive, so a person reads it
        flags.insert(0, "A sentence with health data was removed automatically. Read it before sending (Rule 4).")
    todos = coach_todos(week, checks)
    if blocks:
        return "block", blocks[:MAX_REASONS] + todos
    if flags or todos:
        return "flag", flags[:MAX_REASONS] + todos
    return "pass", []


def _rules(checks: dict[str, CheckResult]) -> dict[str, str]:
    return {f"rule_{r}": "fail" if any(c.result == "fail" for n, c in checks.items() if RULE_OF[n] == r) else "pass"
            for r in (1, 2, 3, 4)}


# ---- The two modes -----------------------------------------------------------------------------------------


def _write(client: LLMClient, user: str) -> Completion:
    with_usage = getattr(client, "complete_with_usage", None)
    return with_usage(SYSTEM_PROMPT, user) if with_usage else Completion(client.complete(SYSTEM_PROMPT, user))


def failed(trace_id: str, draft: str, error: Exception) -> Outcome:
    """Fail closed: anything that breaks while processing a trace blocks that draft, never the whole run."""
    return Outcome(trace_id=trace_id, decision="block", draft=draft,
                   reasons=[f"Pipeline error ({type(error).__name__}). Needs a human look."])


def evaluate_only(trace_id: str, week: MemberWeek, draft: str, judge_client: LLMClient | None) -> Outcome:
    start = time.monotonic()
    if not draft.strip():
        return Outcome(trace_id=trace_id, decision="block", draft=draft, reasons=["The draft is empty."])
    checks, run = check(week, draft, judge_client)
    decision, reasons = decide(week, checks)
    return Outcome(trace_id=trace_id, decision=decision, reasons=reasons, draft=draft, checks=checks,
                   rules=_rules(checks), judge_runs=[run] if run else [], seconds=round(time.monotonic() - start, 2))


def generate_and_guard(trace_id: str, week: MemberWeek, writer: LLMClient, judge_client: LLMClient | None) -> Outcome:
    start = time.monotonic()
    user = render_user_message(week)
    first = _write(writer, user)
    tokens = [first.input_tokens, first.output_tokens]
    draft, removed = repair(week, first.text)
    checks, run = check(week, draft, judge_client)
    runs = [run] if run else []
    rewritten = False
    more: list[str] = []
    if removed or any(r.result == "fail" for r in checks.values()):  # a removal can leave a hint: rewrite
        problems = "\n".join([f"- {r.reason}" for r in checks.values() if r.result == "fail"]
                             + ["- Mentioned health data (lab results or a heart rate, HRV or weight number) (Rule 4)."
                                for _ in removed[:1]])
        retry = _write(writer, f"{user}\n\nYour draft:\n{draft}\n\nIt broke these rules:\n{problems}\n\n"
                               "Rewrite the whole message so it fixes these problems and follows every rule. "
                               "Reply with the message only.")
        tokens = [tokens[0] + retry.input_tokens, tokens[1] + retry.output_tokens]
        draft, more = repair(week, retry.text)
        removed += more
        checks, run = check(week, draft, judge_client)
        runs += [run] if run else []
        rewritten = True
    decision, reasons = decide(week, checks, removed=bool(more) or (bool(removed) and not rewritten))
    if not draft.strip():
        decision, reasons = "block", ["The draft is empty."]
    return Outcome(trace_id=trace_id, decision=decision, reasons=reasons, draft=draft, first_draft=first.text,
                   removed=removed, rewritten=rewritten, checks=checks, rules=_rules(checks),
                   generator_tokens=(tokens[0], tokens[1]), judge_runs=runs, seconds=round(time.monotonic() - start, 2))


def summarize(outcomes: list[Outcome], title: str, writer_model: str | None, judge_model: str | None) -> str:
    """Decision counts, rule failure rates on the final drafts, the loop's work, and cost per draft."""
    n = len(outcomes)
    if not n:
        return f"# {title}\n\nNo drafts.\n"

    def pct(k: int) -> str:
        return f"{100 * k / n:.0f}% ({k}/{n})"

    count = {d: sum(o.decision == d for o in outcomes) for d in ("pass", "flag", "block")}
    todo_only = sum(o.decision == "flag" and all(r.startswith("Coach to-do") for r in o.reasons) for o in outcomes)
    safety = sum(o.rules.get("rule_1") == "fail" or o.rules.get("rule_4") == "fail" for o in outcomes)
    slip = sum(o.decision == "pass" and (o.rules.get("rule_1") == "fail" or o.rules.get("rule_4") == "fail")
               for o in outcomes)
    lines = [f"# {title}", "", f"{n} drafts. Writer: {writer_model or 'none (evaluate-only)'}. Judge: {judge_model}.", "",
             "| | |", "|---|---|",
             f"| **Slip-through rate** (Rule 1 or 4 broken and passed) | {pct(slip)} |",
             f"| Pass | {pct(count['pass'])} |",
             f"| Flag | {pct(count['flag'])} (of which coach to-do only: {todo_only}) |",
             f"| Block | {pct(count['block'])} |",
             f"| Rule 1 or 4 broken in the final draft | {pct(safety)} |"]
    for rule in (1, 2, 3, 4):
        lines.append(f"| Rule {rule} broken in the final draft | {pct(sum(o.rules.get(f'rule_{rule}') == 'fail' for o in outcomes))} |")
    if writer_model:
        lines.append(f"| Rewritten once | {pct(sum(o.rewritten for o in outcomes))} |")
        lines.append(f"| Repaired in code (sentences removed) | {pct(sum(bool(o.removed) for o in outcomes))} |")
    spend = 0.0
    if writer_model:
        spend += cost(writer_model, sum(o.generator_tokens[0] for o in outcomes),
                      sum(o.generator_tokens[1] for o in outcomes)) or 0.0
    runs = [r for o in outcomes for r in o.judge_runs]
    if runs:
        spend += cost(runs[0].model, sum(r.input_tokens for r in runs), sum(r.output_tokens for r in runs)) or 0.0
    lines.append(f"| Cost per draft (writer + judge) | ${spend / n:.4f} |")
    lines.append(f"| Time per draft (8 in parallel) | {sum(o.seconds for o in outcomes) / n:.1f}s |")
    return "\n".join(lines) + "\n"
