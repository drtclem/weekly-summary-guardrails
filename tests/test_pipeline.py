import json

from tests.test_judge import Fake, answer
from weekly_summary import pipeline
from weekly_summary.__main__ import main
from weekly_summary.data import load_traces
from weekly_summary.evals.checks import CheckResult
from weekly_summary.llm import Completion
from weekly_summary.prompt import render_user_message

T = {t.trace_id: t for t in load_traces()}
NO_PAIN = answer().replace('"pain_handled": {"verdict": "pass"', '"pain_handled": {"verdict": "n/a"')  # a clean week


def fail(reason: str, by: str = "judge") -> CheckResult:
    return CheckResult(result="fail", reason=reason, by=by)  # type: ignore[arg-type]


# ---- D5: the model never sees what it must not say ----


def test_input_has_no_labs_or_biomarker_numbers():
    week = T["t_016"].input  # Isaac: LDL 162, HDL 41, TG 180, RHR 63, HRV 35, weight 175.6
    text = render_user_message(week)
    for forbidden in ("162", "LDL", "cholesterol", "bloodwork", "63", "35", "175.6"):
        assert forbidden not in text
    assert "Sam" in text and "Sam Whitaker" not in text and "last week about 6,800" in text


def test_input_omits_weight_for_opted_out_members_and_injuries_on_file():
    assert "weight this week" not in render_user_message(T["t_009"].input)  # Lena opted out
    assert "ankle" not in render_user_message(T["t_009"].input)  # injury on file, not this week


# ---- D6: repair in code ----


def test_repair_removes_biomarker_and_lab_sentences_and_extra_emoji():
    week = T["t_016"].input
    draft = "Isaac, great balance work. Your HRV edged up to 35 ms. Your cholesterol is high. Nice walks 🎉🔥 Sam"
    fixed, removed = pipeline.repair(week, draft)
    assert fixed == "Isaac, great balance work. Nice walks 🎉 Sam"
    assert removed == ["Your HRV edged up to 35 ms.", "Your cholesterol is high."]


# ---- D7: decisions ----


def test_privacy_medical_and_opted_out_weight_block():
    lena, maya = T["t_009"].input, T["t_001"].input
    assert pipeline.decide(maya, {"no_lab_hint": fail("labs")})[0] == "block"
    assert pipeline.decide(maya, {"no_medical_advice": fail("ice it")})[0] == "block"
    assert pipeline.decide(lena, {"no_weight_pressure": fail("you look leaner")})[0] == "block"
    assert pipeline.decide(maya, {"no_weight_pressure": fail("down 2 lb!")})[0] == "flag"  # weight talk allowed
    assert pipeline.decide(maya, {"no_guilt": fail("Judge error: cut off. Needs a human look.")})[0] == "block"


def test_quality_problems_flag_with_at_most_two_reasons():
    decision, reasons = pipeline.decide(T["t_001"].input, {"no_hype": fail("a"), "no_guilt": fail("b"),
                                                          "facts_grounded": fail("c")})
    assert decision == "flag" and reasons == ["a", "b"]


def test_coach_todos_flag_a_clean_draft():
    ok = CheckResult(result="pass")
    pain = pipeline.decide(T["t_055"].input, {"pain_handled": ok})  # knee puffy this week
    assert pain[0] == "flag" and "pain" in pain[1][0]
    labs = pipeline.decide(T["t_016"].input, {"pain_handled": CheckResult(result="n/a")})  # asked about bloodwork
    assert labs[0] == "flag" and "lab results" in labs[1][0]
    assert pipeline.decide(T["t_001"].input, {"pain_handled": CheckResult(result="n/a")}) == ("pass", [])


# ---- The two modes ----


def test_generate_repairs_rewrites_once_then_passes():
    week = T["t_001"].input
    writer = Fake(
        Completion("Maya, great intervals. Your HRV hit 63 ms. You were crushing it on Saturday. Jordan", 900, 60),
        Completion("Maya, great intervals and a strong 8-miler on Saturday. Jordan", 1000, 40),
    )
    judge = Fake(Completion(NO_PAIN), Completion(NO_PAIN))
    out = pipeline.generate_and_guard("t_001", week, writer, judge)
    assert out.removed == ["Your HRV hit 63 ms."]
    assert out.rewritten and writer.calls == 2  # "crushing" failed a code check, so one rewrite
    assert out.decision == "pass" and out.reasons == [] and out.generator_tokens == (1900, 100)


def test_code_block_skips_the_judge():
    judge = Fake()
    out = pipeline.evaluate_only("t_016", T["t_016"].input, T["t_016"].output, judge)  # "cholesterol"
    assert out.decision == "block" and judge.calls == 0 and "Rule 4" in out.reasons[0]


def test_guard_no_generate_writes_the_required_jsonl(tmp_path, monkeypatch):
    import weekly_summary.__main__ as cli

    traces = tmp_path / "traces.jsonl"
    traces.write_text("".join(T[i].model_dump_json() + "\n" for i in ("t_001", "t_016")))
    monkeypatch.setattr(cli, "judge_client", lambda: Fake(*[Completion(NO_PAIN)] * 4))
    out = tmp_path / "decisions.jsonl"
    main(["--traces", str(traces), "guard", "--no-generate", "--out", str(out)])
    rows = [json.loads(line) for line in out.read_text().splitlines()]
    assert [sorted(r) for r in rows] == [["decision", "reasons", "trace_id"]] * 2
    assert [(r["trace_id"], r["decision"]) for r in rows] == [("t_001", "pass"), ("t_016", "block")]


# ---- Cases from the second independent review (2026-10-21) ----


def test_a_writer_error_blocks_that_trace_and_the_run_finishes(tmp_path, monkeypatch):
    import weekly_summary.__main__ as cli

    traces = tmp_path / "traces.jsonl"
    traces.write_text("".join(T[i].model_dump_json() + "\n" for i in ("t_001", "t_002")))
    monkeypatch.setattr(cli, "judge_client", lambda: Fake())
    monkeypatch.setattr(cli, "_client_for", lambda traces: lambda trace: Fake(RuntimeError("503"), RuntimeError("503")))
    out = tmp_path / "d.jsonl"
    main(["--traces", str(traces), "guard", "--out", str(out)])
    rows = [json.loads(line) for line in out.read_text().splitlines()]
    assert [r["decision"] for r in rows] == ["block", "block"]
    assert rows[0]["reasons"] == ["Pipeline error (RuntimeError). Needs a human look."]


def test_a_removal_forces_a_rewrite_and_a_second_removal_is_flagged():
    week = T["t_001"].input
    leaky = "Maya, nice intervals on Wednesday. Your bloodwork came back. Great news, all normal! Jordan"
    writer = Fake(Completion(leaky), Completion(leaky))
    out = pipeline.generate_and_guard("t_001", week, writer, Fake(*[Completion(NO_PAIN)] * 4))
    assert out.rewritten and writer.calls == 2
    assert out.decision == "flag" and "removed automatically" in out.reasons[0]


def test_coach_todos_survive_a_block_even_when_the_judge_is_skipped():
    week = T["t_055"].input  # knee puffy this week
    out = pipeline.evaluate_only("t_055", week, "Chloe, nice drills. Your HRV was 69 ms. Elena", Fake())
    assert out.decision == "block" and any(r.startswith("Coach to-do") for r in out.reasons)


def test_repair_keeps_paragraph_breaks():
    draft = "Maya, great week.\n\nYour HRV hit 63 ms. See you Monday.\n\nJordan"
    assert pipeline.repair(T["t_001"].input, draft)[0] == "Maya, great week.\n\nSee you Monday.\n\nJordan"
    clean = "Maya, great week.\n\nJordan"
    assert pipeline.repair(T["t_001"].input, clean) == (clean, [])


def test_input_hides_lab_goals_and_biomarker_numbers_in_messages():
    grace = T["t_027"].input  # goal "lower my A1C"
    assert "A1C" not in render_user_message(grace)
    msg = grace.messages[0].model_copy(update={"text": "My resting HR was 48 this morning!"})
    assert "48" not in render_user_message(grace.model_copy(update={"messages": [msg]}))


def test_empty_draft_blocks_and_null_output_loads(tmp_path):
    assert pipeline.evaluate_only("t_001", T["t_001"].input, "  ", Fake()).decision == "block"
    row = json.loads(T["t_001"].model_dump_json())
    row["output"] = None
    path = tmp_path / "t.jsonl"
    path.write_text(json.dumps(row) + "\n")
    assert load_traces(path)[0].output == ""
