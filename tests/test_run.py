import json

from tests.test_judge import Fake, answer
from weekly_summary.data import load_traces
from weekly_summary.evals import run
from weekly_summary.llm import Completion

TRACES = load_traces()


def test_rule_fails_if_any_code_or_judge_check_under_it_fails():
    t = TRACES[0]  # clean draft
    result = run.evaluate(t.input, t.output, Fake(Completion(answer(no_guilt="no excuses"), 1000, 100),
                                                  Completion(answer(no_guilt="no excuses"), 1000, 100)))
    assert result["rules"] == {"rule_1": "pass", "rule_2": "pass", "rule_3": "fail", "rule_4": "pass"}
    assert result["checks"]["no_guilt"]["by"] == "judge" and result["judge"]["calls"] == 2


def test_code_only_run_needs_no_client():
    rows = run.evaluate_traces(TRACES, None)
    assert len(rows) == 60 and all(r["judge"] is None for r in rows)
    by_id = {r["trace_id"]: r for r in rows}
    assert by_id["t_016"]["rules"]["rule_4"] == "fail" and by_id["t_001"]["rules"]["rule_4"] == "pass"
    assert "Any rule broken" in run.summarize(rows, "x")


def test_scoring_counts_misses_and_false_alarms_with_na_as_pass():
    rows = [{"trace_id": "a", "rules": {"rule_1": "pass", "rule_2": "fail", "rule_3": "pass", "rule_4": "fail"}}]
    labels = [{"trace_id": "a", "rule_1": "fail", "rule_2": "n/a", "rule_3": "pass", "rule_4": "fail"}]
    score = run.score_against_labels(rows, labels)
    assert score["rule_1"] == {"agree": 0, "n": 1, "owner_fails": 1, "misses": 1, "false_alarms": 0}
    assert score["rule_2"]["false_alarms"] == 1 and score["rule_4"]["agree"] == 1


def test_cost_uses_list_prices():
    assert run.cost("claude-haiku-5-5", 4000, 400) == (4000 * 0.10 + 400 * 0.50) / 1e6
    assert run.cost("unknown", 1, 1) is None


def test_compare_table_has_a_row_per_judge():
    rows = run.evaluate_traces(TRACES[:2], None)
    labels = [{"trace_id": r["trace_id"], "rule_1": "pass", "rule_2": "n/a", "rule_3": "pass", "rule_4": "pass"}
              for r in rows]
    table = run.comparison_table({"code checks only": (run.score_against_labels(rows, labels), rows, 1.0)})
    assert "code checks only" in table and json.dumps(run.disagreements(rows, labels))


def test_a_judge_with_errors_is_marked_not_comparable():
    t = TRACES[0]
    broken = Fake(RuntimeError("no key"), RuntimeError("no key"))
    rows = [{"trace_id": t.trace_id, "model": t.model, **run.evaluate(t.input, t.output, broken)}]
    labels = [{"trace_id": t.trace_id, "rule_1": "fail", "rule_2": "n/a", "rule_3": "pass", "rule_4": "fail"}]
    assert rows[0]["judge"]["errors"] == 2
    table = run.comparison_table({"haiku": (run.score_against_labels(rows, labels), rows, 1.0)})
    assert "not comparable" in table
