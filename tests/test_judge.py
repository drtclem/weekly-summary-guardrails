import json

from weekly_summary.data import load_traces
from weekly_summary.evals.judge import JUDGE_CHECKS, SYSTEM, judge
from weekly_summary.llm import Completion

WEEK = load_traces()[0].input


def answer(**fails: str) -> str:
    checks = {name: {"verdict": "pass", "reason": ""} for name in JUDGE_CHECKS}
    checks.update({name: {"verdict": "fail", "reason": why} for name, why in fails.items()})
    return json.dumps({"checks": checks})


class Fake:
    model = "fake"

    def __init__(self, *replies: Completion | Exception) -> None:
        self.replies = list(replies)
        self.calls = 0

    def complete(self, system: str, user: str) -> str:
        return self.complete_with_usage(system, user).text

    def complete_with_usage(self, system: str, user: str) -> Completion:
        self.calls += 1
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply


def test_clean_answer_is_one_call():
    run = judge(WEEK, "draft", Fake(Completion(answer(), 100, 20)))
    assert run.calls == 1 and run.input_tokens == 100 and run.output_tokens == 20
    assert {r.result for r in run.checks.values()} == {"pass"}


def test_a_fail_is_confirmed_by_a_second_call():
    run = judge(WEEK, "draft", Fake(Completion(answer(no_lab_hint="cholesterol")), Completion(answer(no_lab_hint="x"))))
    assert run.calls == 2 and run.checks["no_lab_hint"].result == "fail" and run.flakes == []
    assert run.checks["no_lab_hint"].reason == "cholesterol"


def test_disagreement_is_a_flake_not_a_failure():
    run = judge(WEEK, "draft", Fake(Completion(answer(no_guilt="maybe")), Completion(answer())))
    assert run.checks["no_guilt"].result == "pass" and run.flakes == ["no_guilt"]


def test_disagreement_on_medical_or_privacy_keeps_the_fail():
    run = judge(WEEK, "draft", Fake(Completion(answer(no_lab_hint="results came in")), Completion(answer())))
    assert run.checks["no_lab_hint"].result == "fail" and run.flakes == ["no_lab_hint"]


def test_na_is_only_allowed_where_the_check_says_so():
    lab_na = answer().replace('"no_lab_hint": {"verdict": "pass"', '"no_lab_hint": {"verdict": "n/a"')
    run = judge(WEEK, "draft", Fake(Completion(lab_na), Completion(lab_na)))
    assert run.checks["no_lab_hint"].result == "fail" and run.errors == 2
    pain_na = answer().replace('"pain_handled": {"verdict": "pass"', '"pain_handled": {"verdict": "n/a"')
    assert judge(WEEK, "draft", Fake(Completion(pain_na))).checks["pain_handled"].result == "n/a"


def test_an_error_then_a_good_answer_uses_the_good_answer_without_flakes():
    run = judge(WEEK, "draft", Fake(RuntimeError("429"), Completion(answer())))
    assert {r.result for r in run.checks.values()} == {"pass"} and run.flakes == [] and run.errors == 1


def test_fails_closed_on_api_error_cut_off_and_garbage():
    for bad in (RuntimeError("timeout"), Completion(answer(), truncated=True), Completion("I think it's fine")):
        run = judge(WEEK, "draft", Fake(bad, bad))
        assert {r.result for r in run.checks.values()} == {"fail"}
        assert all(r.reason.startswith("Judge error") for r in run.checks.values())
        assert run.errors == 2


def test_missing_check_or_bad_verdict_fails_closed():
    partial = json.dumps({"checks": {"no_guilt": {"verdict": "pass"}}})
    odd = answer().replace('"pass"', '"maybe"', 1)
    for bad in (partial, odd):
        run = judge(WEEK, "draft", Fake(Completion(bad), Completion(bad)))
        assert {r.result for r in run.checks.values()} == {"fail"}


def test_prompt_lists_every_check():
    assert all(name in SYSTEM for name in JUDGE_CHECKS)


def test_default_judge_is_haiku_and_overridable(monkeypatch):
    from weekly_summary.evals.judge import judge_client

    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")
    monkeypatch.delenv("JUDGE_MODEL", raising=False)
    monkeypatch.delenv("JUDGE_PROVIDER", raising=False)
    assert judge_client().model == "claude-haiku-5-5"
    monkeypatch.setenv("JUDGE_MODEL", "claude-sonnet-5-5")
    assert judge_client().model == "claude-sonnet-5-5"
