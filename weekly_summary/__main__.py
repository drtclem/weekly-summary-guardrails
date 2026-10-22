import argparse
import json
import os
import sys
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

from weekly_summary import pipeline
from weekly_summary.data import DEFAULT_TRACES, load_traces
from weekly_summary.evals import labeling
from weekly_summary.evals import run as evals
from weekly_summary.evals.judge import judge, judge_client
from weekly_summary.generate import generate_summary
from weekly_summary.llm import LLMClient, make_client
from weekly_summary.models import Trace
from weekly_summary.prompt import PROMPT_VERSION


def _client_for(traces: list[Trace]) -> Callable[[Trace], LLMClient]:
    provider = os.environ.get("LLM_PROVIDER", "anthropic")
    model = os.environ.get("LLM_MODEL")
    if provider == "replay":
        # Traces can share an input, so replay each trace from itself, not from an input lookup.
        return lambda trace: make_client(provider, model, [trace])
    try:
        client = make_client(provider, model, traces)
    except ValueError as e:
        sys.exit(str(e))
    return lambda trace: client


def _find(traces: list[Trace], trace_id: str) -> Trace:
    for trace in traces:
        if trace.trace_id == trace_id:
            return trace
    sys.exit(f"No trace with id {trace_id!r}.")


def _run(traces: list[Trace], client_for: Callable[[Trace], LLMClient], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w") as f:
        for trace in traces:
            client = client_for(trace)
            result = Trace(
                trace_id=trace.trace_id,
                created_at=datetime.now(UTC),
                prompt_version=PROMPT_VERSION,
                model=client.model,
                input=trace.input,
                output=generate_summary(trace.input, client),
            )
            f.write(result.model_dump_json() + "\n")
            f.flush()


def _guard(traces: list[Trace], name: str, no_generate: bool, out: Path | None) -> None:
    if not traces:
        sys.exit("The traces file has no traces.")
    try:
        judge_ = judge_client()
        writer = None if no_generate else _client_for(traces)(traces[0])
    except Exception as e:
        sys.exit(f"Can't set up the models: {e}")
    if writer is not None and writer.model == "replay":
        sys.exit("Replay can't write new drafts. Use --no-generate to check the drafts in the traces file.")

    def one(trace: Trace) -> pipeline.Outcome:
        try:
            if writer is None:
                return pipeline.evaluate_only(trace.trace_id, trace.input, trace.output, judge_)
            return pipeline.generate_and_guard(trace.trace_id, trace.input, writer, judge_)
        except Exception as e:  # fail closed per trace: one bad trace or API error never stops the run
            return pipeline.failed(trace.trace_id, trace.output, e)

    with ThreadPoolExecutor(max_workers=8) as pool:
        outcomes = list(pool.map(one, traces))
    label = f"{name}{'_evaluate_only' if no_generate else ''}"
    out = out or Path("results") / f"decisions_{label}.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("".join(json.dumps({"trace_id": o.trace_id, "decision": o.decision, "reasons": o.reasons}) + "\n"
                           for o in outcomes))
    details = out.with_name(out.stem + "_details.jsonl")
    details.write_text("".join(o.model_dump_json() + "\n" for o in outcomes))
    summary = pipeline.summarize(outcomes, f"Guard: {label}", writer.model if writer else None, judge_.model)
    out.with_name(out.stem + ".md").write_text(summary)
    print(summary + f"\nWrote {out} (decisions), {details} (drafts and checks), {out.with_name(out.stem + '.md')}")


def _compare_judges(models: str | None) -> None:
    items = load_traces(labeling.LABEL_SET)
    labels = [json.loads(line) for line in labeling.LABELS.read_text().splitlines() if line.strip()]
    chosen = [tuple(m.split(":", 1)) for m in models.split(",")] if models else evals.JUDGE_MODELS
    results: dict[str, tuple[dict, list[dict], float]] = {}
    notes = []
    try:  # build every client first, so a missing key stops the run before any money is spent
        clients = [("code checks only", None)] + [
            (model, make_client(provider, model, [], max_tokens=4000)) for provider, model in chosen
        ]
    except Exception as e:
        sys.exit(f"Can't set up a judge client: {e}")
    for label, client in clients:
        if client:  # one call first: don't spend 40 drafts on a model that can't answer
            probe = judge(items[0].input, items[0].output, client)
            if probe.errors:
                print(f"Skipping {label}: the first judge call failed ({probe.error}).", flush=True)
                continue
        print(f"Judging {len(items)} labeled drafts with {label}...", flush=True)
        start = time.monotonic()
        rows = evals.evaluate_traces(items, client)
        wall = time.monotonic() - start
        evals.write_jsonl(rows, Path("results") / "judge_runs" / f"{label.replace(' ', '_')}.jsonl")
        results[label] = (evals.score_against_labels(rows, labels), rows, wall)
        notes += [f"\n## {label}\n"] + evals.disagreements(rows, labels)
    table = evals.comparison_table(results)
    out = Path("results") / "judge_comparison.md"
    out.write_text("# Judge comparison against the owner's labels\n\nEach rule cell: agreement / misses of owner "
                   "fails / false alarms. Misses on Rules 1 and 4 matter most.\n\n" + table)
    (Path("results") / "judge_disagreements.md").write_text("# Where each judge disagrees with the owner\n"
                                                            + "\n".join(notes) + "\n")
    print(table + f"\nWrote {out} and results/judge_disagreements.md")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="weekly-summary")
    parser.add_argument("--traces", type=Path, default=DEFAULT_TRACES, help="traces JSONL file")
    commands = parser.add_subparsers(dest="command", required=True)

    show = commands.add_parser("show", help="print a trace's input and output")
    show.add_argument("trace_id")

    generate = commands.add_parser("generate", help="regenerate the summary for one trace")
    generate.add_argument("trace_id")

    run = commands.add_parser("run", help="regenerate summaries for all traces")
    run.add_argument("--out", type=Path, help="output JSONL (default: runs/<UTC timestamp>.jsonl)")
    run.add_argument("--limit", type=int, help="only run the first N traces")

    commands.add_parser("prep-labels", help="pick the 40 drafts to label and regenerate 10 with today's model")
    commands.add_parser("label", help="label the drafts in labels/label_set.jsonl (blind, resumable)")
    commands.add_parser("label-sheet", help="write all unlabeled drafts into one sheet to fill in an editor")
    ev = commands.add_parser("eval", help="run code checks and the judge on the drafts in a traces file")
    ev.add_argument("--name", help="results/<name>.jsonl and .md (default: the traces file's name)")
    ev.add_argument("--no-judge", action="store_true", help="code checks only (no API calls)")
    guard = commands.add_parser("guard", help="the full pipeline: write, check, repair, rewrite, decide")
    guard.add_argument("--no-generate", action="store_true",
                       help="don't write new drafts: apply the evals and guardrail to the drafts in the traces file")
    guard.add_argument("--out", type=Path, help="decisions JSONL (default: results/decisions_<traces name>.jsonl)")
    cj = commands.add_parser("compare-judges", help="score each judge model against the owner's labels")
    cj.add_argument("--models", help="comma-separated provider:model list (default: all six from D1)")
    commands.add_parser("import-sheet", help="add the answered drafts from the sheet to the labels")

    args = parser.parse_args(argv)
    traces = load_traces(args.traces)

    match args.command:
        case "show":
            trace = _find(traces, args.trace_id)
            print(trace.input.model_dump_json(indent=2))
            print()
            print(trace.output)
        case "generate":
            trace = _find(traces, args.trace_id)
            print(generate_summary(trace.input, _client_for(traces)(trace)))
        case "run":
            out = args.out or Path("runs") / f"{datetime.now(UTC):%Y%m%dT%H%M%SZ}.jsonl"
            _run(traces[: args.limit], _client_for(traces), out)
            print(out)
        case "prep-labels":
            if labeling.LABELS.exists():
                sys.exit(f"{labeling.LABELS} already has labels; delete it first to rebuild the label set.")
            if os.environ.get("LLM_PROVIDER", "anthropic") == "replay":
                sys.exit("prep-labels regenerates drafts; set LLM_PROVIDER to anthropic or openai.")
            client = _client_for(traces)(traces[0])
            items = labeling.build_label_set(traces, lambda week: generate_summary(week, client), client.model)
            print(f"Wrote {len(items)} drafts to {labeling.LABEL_SET}. Next: uv run weekly-summary label")
        case "label":
            if not labeling.LABEL_SET.exists():
                sys.exit("No label set yet. Run: uv run weekly-summary prep-labels")
            labeling.label(load_traces(labeling.LABEL_SET))
        case "label-sheet":
            n = labeling.write_sheet(load_traces(labeling.LABEL_SET))
            print(f"Wrote {n} drafts to {labeling.SHEET}. Fill it in, then: uv run weekly-summary import-sheet")
        case "eval":
            name = args.name or args.traces.stem
            try:
                client = None if args.no_judge else judge_client()
            except Exception as e:
                sys.exit(f"Can't set up the judge: {e}")
            rows = evals.evaluate_traces(traces, client)
            out = Path("results") / f"{name}.jsonl"
            evals.write_jsonl(rows, out)
            summary = evals.summarize(rows, f"Eval: {name}")
            out.with_suffix(".md").write_text(summary)
            print(summary + f"\nWrote {out} and {out.with_suffix('.md')}")
        case "guard":
            _guard(traces, args.traces.stem, args.no_generate, args.out)
        case "compare-judges":
            _compare_judges(args.models)
        case "import-sheet":
            print(f"Added {labeling.read_sheet()} labels to {labeling.LABELS}.")


if __name__ == "__main__":
    main()
