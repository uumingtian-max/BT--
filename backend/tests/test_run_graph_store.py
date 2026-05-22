from __future__ import annotations


def test_run_graph_lifecycle(tmp_path, monkeypatch):
    import run_graph_store

    monkeypatch.setattr(run_graph_store, "DB_PATH", str(tmp_path / "run_graph.db"))
    run_graph_store.init_run_graph_db()

    run = run_graph_store.start_run_graph(
        source="automation",
        kind="project_check",
        title="项目检查",
        target="all",
        metadata={"job_id": "job-1"},
    )
    assert run["source"] == "automation"
    assert run["status"] == "running"
    assert run["metadata"]["job_id"] == "job-1"

    step = run_graph_store.add_run_step(
        run_id=run["id"],
        step_type="command",
        name="backend_compile",
        status="success",
        input_data={"cmd": ["python", "-m", "py_compile"]},
        output_data={"exit_code": 0},
        duration_ms=12,
    )
    assert step["step_index"] == 0
    assert step["output"]["exit_code"] == 0

    event = run_graph_store.store_visual_event(
        {
            "run_id": run["id"],
            "type": "automation_step_finished",
            "source": "automation",
            "title": "步骤完成",
            "status": "success",
            "payload": {"label": "backend_compile"},
        }
    )
    assert event["payload"]["label"] == "backend_compile"

    finished = run_graph_store.finish_run_graph(
        run["id"],
        status="success",
        summary="项目检查通过",
        duration_ms=99,
    )
    assert finished["status"] == "success"
    assert finished["steps"][0]["name"] == "backend_compile"

    graphs = run_graph_store.list_run_graphs(source="automation")
    assert graphs[0]["id"] == run["id"]

    events = run_graph_store.list_visual_events(source="automation", run_id=run["id"])
    assert events[0]["type"] == "automation_step_finished"
