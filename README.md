# Weekly Summary

This app writes a weekly progress summary for a Future member. One LLM call writes the draft, and a coach approves it before the member reads it.

Read the assessment prompt for your task. Read `GUIDEBOOK.md` for the rules that the drafts must follow.

## Setup

You need [uv](https://docs.astral.sh/uv/). It installs Python 3.14 for you.

```
uv sync
```

Set a provider and an API key:

```
export LLM_PROVIDER=anthropic   # or openai
export ANTHROPIC_API_KEY=...    # or OPENAI_API_KEY
export LLM_MODEL=...            # optional
```

Set `LLM_PROVIDER=replay` to use the recorded drafts in the traces file. The replay client makes no API call. It ignores the system prompt, so a prompt change has no effect in replay mode.

## The hardened feature (one command)

```
uv run weekly-summary --traces data/traces.jsonl guard                 # write, check, repair, rewrite once, decide
uv run weekly-summary --traces data/traces.jsonl guard --no-generate   # evals + guardrail on the drafts in the file
```

Each writes `results/decisions_<name>.jsonl` with one line per trace, `{"trace_id", "decision", "reasons"}`, plus `_details.jsonl` (final drafts, every check) and a summary `.md`. Decisions: `pass`, `flag` (a reason the coach reads in one glance), or `block` (the coach writes this one). Policy: `docs/decisions.md` D7.

Models are settings: `LLM_PROVIDER` / `LLM_MODEL` write the drafts (default `claude-sonnet-5-5`); `JUDGE_PROVIDER` / `JUDGE_MODEL` judge them (default `claude-haiku-5-5`). Options and costs: `docs/judge_model_options.md`.

## Evals

```
uv run weekly-summary eval --name run1_original          # code checks + judge on the drafts in a traces file
uv run weekly-summary eval --no-judge                    # code checks only, no API calls
uv run weekly-summary compare-judges                     # score judge models against the owner's labels
uv run weekly-summary prep-labels | label | label-sheet | import-sheet   # owner labeling (docs/decisions.md D2)
```

## Commands

```
uv run weekly-summary show t_001        # print the input and the recorded draft for one trace
uv run weekly-summary generate t_001    # write a new draft for the input of one trace
uv run weekly-summary run               # write new drafts for all traces into runs/
uv run weekly-summary --traces other.jsonl run
uv run pytest
uv run ruff check .
uv run pyright
```

## Layout

| Path | What it does |
|---|---|
| `weekly_summary/models.py` | The data shapes: `MemberWeek` is the input, `Trace` is one logged call. |
| `weekly_summary/prompt.py` | The system prompt and the input format. |
| `weekly_summary/generate.py` | The feature. It sends one `MemberWeek` to the model and returns the draft. |
| `weekly_summary/llm.py` | The client wrapper for Anthropic, OpenAI, and replay. |
| `weekly_summary/data.py` | Loads traces from JSONL. |
| `data/traces.jsonl` | 60 recent production traces, with no labels. |
