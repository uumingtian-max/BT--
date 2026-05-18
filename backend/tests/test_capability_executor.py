from capability_executor import execute_capability_request


def test_executor_dry_run_for_eye_comfort_does_not_execute():
    result = execute_capability_request("屏幕太刺眼了，帮我开护眼模式", dry_run=True)
    assert result["ok"] is True
    assert result["dry_run"] is True
    assert result["executed"] is False
    assert result["capability_id"] == "system.eye_comfort"
    assert result["requires_confirmation"] is True
    assert result["plan"]


def test_executor_blocks_confirm_capability_even_when_not_dry_run():
    result = execute_capability_request("整理一下我的桌面文件", dry_run=False)
    assert result["ok"] is True
    assert result["executed"] is False
    assert result["requires_confirmation"] is True
    assert "需要确认" in result["summary"] or "风险" in result["summary"]


def test_executor_unknown_request_returns_safe_failure():
    result = execute_capability_request("嗯", dry_run=True)
    assert result["ok"] is False
    assert result["executed"] is False
    assert result["capability_id"] == "unknown"
