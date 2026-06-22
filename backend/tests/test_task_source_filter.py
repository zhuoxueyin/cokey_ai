from app.services.task_service import _apply_task_source_filter, _workspace_task_clause


def test_workspace_filter_excludes_canvas():
    base = {"user_id": "u1"}
    q = _apply_task_source_filter(base, "workspace")
    assert "$and" in q
    assert _workspace_task_clause() in q["$and"]


def test_canvas_filter_only_canvas():
    base = {"user_id": "u1"}
    q = _apply_task_source_filter(base, "canvas")
    assert "$and" in q
    canvas_part = q["$and"][1]
    assert canvas_part["canvas_project_id"]["$exists"] is True


def test_no_source_unchanged():
    base = {"status": "success"}
    q = _apply_task_source_filter(base, None)
    assert q == base
