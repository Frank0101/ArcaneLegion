from domain.run.models import ActionResult, ExecutionResult


def test_success_true_when_all_steps_pass() -> None:
    result = ExecutionResult(action_results={
        "coder": ActionResult(output="done"),
        "reviewer": ActionResult(output="approved", success=True),
    })

    assert result.success is True


def test_success_true_when_no_step_has_explicit_result() -> None:
    result = ExecutionResult(action_results={
        "coder": ActionResult(output="done"),
    })

    assert result.success is True


def test_success_false_when_one_step_fails() -> None:
    result = ExecutionResult(action_results={
        "coder": ActionResult(output="done"),
        "reviewer": ActionResult(output="rejected", success=False),
    })

    assert result.success is False


def test_error_message_none_when_all_steps_pass() -> None:
    result = ExecutionResult(action_results={
        "coder": ActionResult(output="done"),
        "reviewer": ActionResult(output="approved", success=True),
    })

    assert result.error_message is None


def test_error_message_returns_output_of_first_failure() -> None:
    result = ExecutionResult(action_results={
        "coder": ActionResult(output="coder failed", success=False),
        "reviewer": ActionResult(output="reviewer failed", success=False),
    })

    assert result.error_message == "coder failed"


def test_error_message_none_when_no_action_results() -> None:
    result = ExecutionResult(action_results={})

    assert result.error_message is None
