import json
from datetime import UTC, datetime

from weekly_summary.data import load_traces
from weekly_summary.evals import labeling
from weekly_summary.models import Trace

TRACES = load_traces()


def test_selection_is_reproducible_and_covers_the_risky_cases():
    originals, regenerate = labeling.select(TRACES)
    assert (originals, regenerate) == labeling.select(TRACES)
    assert len(originals) == len(set(originals)) == 30
    assert len(regenerate) == 10
    labs = {t.trace_id for t in TRACES if t.input.new_labs}
    assert labs <= set(originals) and labs <= set(regenerate)


def test_build_label_set_writes_30_originals_and_10_regenerated(tmp_path):
    out = tmp_path / "label_set.jsonl"
    items = labeling.build_label_set(TRACES, lambda week: f"{week.member.first_name}, new draft. Sam", "fake", out)
    assert len(items) == 40 == len(load_traces(out))
    regenerated = [t for t in items if t.trace_id.endswith(labeling.V3_SUFFIX)]
    assert len(regenerated) == 10 and all(t.model == "fake" for t in regenerated)


def test_label_saves_each_draft_and_resumes_where_it_stopped(tmp_path):
    out = tmp_path / "labels.jsonl"
    items = TRACES[:2]
    answers = iter(["p", "x", "n", "p", "f", "invented a run"] + ["q"])  # 'x' is ignored and re-asked
    assert labeling.label(items, out, ask=lambda _: next(answers), show=lambda _: None) == 1

    first = json.loads(out.read_text())
    assert first["trace_id"] == items[0].trace_id
    assert [first[k] for k in ("rule_1", "rule_2", "rule_3", "rule_4")] == ["pass", "n/a", "pass", "fail"]
    assert first["note"] == "invented a run"

    answers = iter(["p", "p", "p", "p", ""])
    assert labeling.label(items, out, ask=lambda _: next(answers), show=lambda _: None) == 1
    assert [json.loads(line)["trace_id"] for line in out.read_text().splitlines()] == [t.trace_id for t in items]


def test_render_never_shows_source_or_model():
    trace = Trace(trace_id="t_016-v3today", created_at=datetime.now(UTC), prompt_version="v3",
                  model="claude-sonnet-5-5", input=TRACES[15].input, output="Isaac, hi. Sam")
    text = labeling.render(trace.input, trace.output)
    assert "v3" not in text and "sonnet" not in text and "LDL Cholesterol 162.0" in text
    assert "prior week: sleep 7.6h, steps 6800" in text  # drafts cite last week's sleep and steps


def test_prep_labels_refuses_to_overwrite_existing_labels(tmp_path, monkeypatch):
    import pytest

    from weekly_summary.__main__ import main

    labels = tmp_path / "labels.jsonl"
    labels.write_text('{"trace_id": "t_001"}\n')
    monkeypatch.setattr(labeling, "LABELS", labels)
    with pytest.raises(SystemExit, match="already has labels"):
        main(["prep-labels"])


def test_q_at_the_note_saves_the_draft_and_quits(tmp_path):
    out = tmp_path / "labels.jsonl"
    answers = iter(["p", "p", "p", "p", "q"])
    assert labeling.label(TRACES[:3], out, ask=lambda _: next(answers), show=lambda _: None) == 1
    assert json.loads(out.read_text())["note"] == ""


def test_sheet_round_trip_skips_done_and_unanswered_drafts(tmp_path):
    labels, sheet, index = tmp_path / "labels.jsonl", tmp_path / "sheet.md", tmp_path / "index.json"
    labels.write_text(json.dumps({"trace_id": TRACES[0].trace_id}) + "\n")
    assert labeling.write_sheet(TRACES[:3], labels, sheet, index) == 2
    text = sheet.read_text()
    assert TRACES[1].trace_id not in text  # blind: ids live only in the index

    first = "Rule 1 medical: p\nRule 2 weight: N\nRule 3 voice: f\nRule 4 privacy: fail\nNote: wrong coach\n"
    text = text.replace("Rule 1 medical: \nRule 2 weight: \nRule 3 voice: \nRule 4 privacy: \nNote: \n", first, 1)
    sheet.write_text(text)

    assert labeling.read_sheet(sheet, index, labels) == 1  # draft 2 left blank, so skipped
    record = json.loads(labels.read_text().splitlines()[1])
    assert record["trace_id"] == TRACES[1].trace_id
    assert [record[k] for k in ("rule_1", "rule_2", "rule_3", "rule_4")] == ["pass", "n/a", "fail", "fail"]
    assert record["note"] == "wrong coach"
    assert labeling.read_sheet(sheet, index, labels) == 0  # importing twice adds nothing
