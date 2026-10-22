"""Run the evals over a traces file, summarise them, and compare judge models against the owner's labels."""

import json
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from weekly_summary.evals.checks import CHECKS, CheckResult, run_code_checks
from weekly_summary.evals.judge import JUDGE_CHECKS, JudgeRun, judge
from weekly_summary.llm import LLMClient
from weekly_summary.models import MemberWeek, Trace

RULES = (1, 2, 3, 4)
RULE_OF = {name: rule for name, (rule, _) in CHECKS.items()} | {name: rule for name, (rule, _) in JUDGE_CHECKS.items()}

# $ per million tokens (input, output), list prices as of 2026-10-21 (docs/decisions.md D1).
PRICES = {
    "claude-haiku-5-5": (0.10, 0.50), "claude-sonnet-5-5": (2.0, 10.0), "claude-opus-5-5": (4.0, 20.0),
    "gpt-6-luna": (0.10, 0.50), "gpt-6.1-sol": (2.0, 10.0), "gpt-6-astra": (10.0, 50.0),
}
JUDGE_MODELS = [
    ("anthropic", "claude-haiku-5-5"), ("anthropic", "claude-sonnet-5-5"), ("anthropic", "claude-opus-5-5"),
    ("openai", "gpt-6-luna"), ("openai", "gpt-6.1-sol"), ("openai", "gpt-6-astra"),
]


def cost(model: str, input_tokens: int, output_tokens: int) -> float | None:
    if model not in PRICES:
        return None
    price_in, price_out = PRICES[model]
    return (input_tokens * price_in + output_tokens * price_out) / 1e6


def evaluate(week: MemberWeek, draft: str, client: LLMClient | None) -> dict:
    """Code checks, then (if a judge client is given) the judge. Returns checks, rule verdicts and judge usage."""
    checks: dict[str, CheckResult] = run_code_checks(week, draft)
    run: JudgeRun | None = judge(week, draft, client) if client else None
    if run:
        checks |= run.checks
    rules = {f"rule_{r}": "fail" if any(c.result == "fail" for n, c in checks.items() if RULE_OF[n] == r) else "pass"
             for r in RULES}
    return {
        "checks": {name: c.model_dump() for name, c in checks.items()},
        "rules": rules,
        "judge": run.model_dump(exclude={"checks"}) if run else None,
    }


def evaluate_traces(traces: list[Trace], client: LLMClient | None, workers: int = 8) -> list[dict]:
    def one(trace: Trace) -> dict:
        return {"trace_id": trace.trace_id, "model": trace.model, **evaluate(trace.input, trace.output, client)}

    with ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(one, traces))


def write_jsonl(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))


def _pct(n: int, d: int) -> str:
    return f"{100 * n / d:.0f}% ({n}/{d})" if d else "–"


def summarize(rows: list[dict], title: str) -> str:
    """Markdown summary: violation rate per rule and per check, split by generating model, plus judge cost."""
    n = len(rows)
    if not rows:
        return f"# {title}\n\nNo drafts.\n"
    lines = [f"# {title}", "", f"{n} drafts.", ""]
    lines += ["| | All drafts | " + " | ".join(sorted({r["model"] for r in rows})) + " |"]
    models = sorted({r["model"] for r in rows})
    lines += ["|---|---|" + "---|" * len(models)]

    def row(label: str, failed: Callable[[dict], bool], applies: Callable[[dict], bool] = lambda r: True) -> str:
        cells = [_pct(sum(failed(r) for r in rs if applies(r)), sum(applies(r) for r in rs))
                 for rs in [rows] + [[r for r in rows if r["model"] == m] for m in models]]
        return f"| {label} | " + " | ".join(cells) + " |"

    lines.append(row("**Any rule broken**", lambda r: "fail" in r["rules"].values()))
    for rule in RULES:
        lines.append(row(f"**Rule {rule}**", lambda r, k=f"rule_{rule}": r["rules"][k] == "fail"))
        for name in [c for c in rows[0]["checks"] if RULE_OF[c] == rule]:
            lines.append(row(f"&nbsp;&nbsp;{name}", lambda r, c=name: r["checks"][c]["result"] == "fail",
                             lambda r, c=name: r["checks"][c]["result"] != "n/a"))
    judged = [r["judge"] for r in rows if r["judge"]]
    if judged:
        model = judged[0]["model"]
        tokens_in = sum(j["input_tokens"] for j in judged)
        tokens_out = sum(j["output_tokens"] for j in judged)
        spend = cost(model, tokens_in, tokens_out)
        lines += ["", f"Judge: {model}. {sum(j['calls'] for j in judged)} calls, "
                  f"{tokens_in:,} input and {tokens_out:,} output tokens, "
                  + (f"${spend:.4f} total (${spend / len(judged):.5f} per draft), " if spend is not None else "")
                  + f"{sum(j['seconds'] for j in judged) / len(judged):.1f}s per draft. "
                  f"Flakes: {sum(len(j['flakes']) for j in judged)}. Judge errors: {sum(j['errors'] for j in judged)}."]
    return "\n".join(lines) + "\n"


def score_against_labels(rows: list[dict], labels: list[dict]) -> dict:
    """Agreement with the owner per rule. n/a in a label counts as pass. A miss is owner fail, system pass."""
    by_id = {r["trace_id"]: r for r in rows}
    out: dict = {}
    for rule in RULES:
        key = f"rule_{rule}"
        pairs = [(lab[key] == "fail", by_id[lab["trace_id"]]["rules"][key] == "fail") for lab in labels
                 if lab["trace_id"] in by_id]
        out[key] = {
            "agree": sum(a == b for a, b in pairs), "n": len(pairs),
            "owner_fails": sum(a for a, _ in pairs),
            "misses": sum(a and not b for a, b in pairs), "false_alarms": sum(b and not a for a, b in pairs),
        }
    return out


def comparison_table(results: dict[str, tuple[dict, list[dict], float]]) -> str:
    """results: label -> (score, rows, wall seconds). One line per judge model."""
    head = ("| Judge | Rule 1 agree / misses / false alarms | Rule 2 | Rule 3 | Rule 4 | Cost per draft | "
            "Latency per draft (s, 8 in parallel) | Wall time (s) | Flakes (Rule 1/4) | Judge errors |")
    lines = [head, "|---|---|---|---|---|---|---|---|---|---|"]
    for label, (score, rows, wall) in results.items():
        cells = [f"{s['agree']}/{s['n']} · {s['misses']} of {s['owner_fails']} · {s['false_alarms']}"
                 for s in score.values()]
        judged = [r["judge"] for r in rows if r["judge"]]
        if judged:
            spend = cost(judged[0]["model"], sum(j["input_tokens"] for j in judged),
                         sum(j["output_tokens"] for j in judged))
            per = f"${spend / len(judged):.5f}" if spend is not None else "?"
            secs = f"{sum(j['seconds'] for j in judged) / len(judged):.1f}"
            all_flakes = [f for j in judged for f in j["flakes"]]
            safety = sum(RULE_OF[f] in (1, 4) for f in all_flakes)
            flakes = f"{len(all_flakes)} ({safety})"
            errors = str(sum(j["errors"] for j in judged))
            if errors != "0":
                label = f"⚠ {label} (errors: not comparable)"
        else:
            per, secs, flakes, errors = "$0", "0.0", "–", "–"
        lines.append(f"| {label} | " + " | ".join(cells) + f" | {per} | {secs} | {wall:.0f} | {flakes} | {errors} |")
    return "\n".join(lines) + "\n"


def disagreements(rows: list[dict], labels: list[dict]) -> list[str]:
    """Readable list of where the system and the owner disagree, for sharpening the judge."""
    by_id = {r["trace_id"]: r for r in rows}
    out = []
    for lab in labels:
        row = by_id.get(lab["trace_id"])
        if not row:
            continue
        for rule in RULES:
            key = f"rule_{rule}"
            owner, system = lab[key] == "fail", row["rules"][key] == "fail"
            if owner != system:
                reasons = [c["reason"] for n, c in row["checks"].items() if RULE_OF[n] == rule and c["result"] == "fail"]
                kind = "MISS" if owner else "FALSE ALARM"
                out.append(f"- {lab['trace_id']} {key} {kind}: system says {'; '.join(reasons) or 'pass'}")
    return out
