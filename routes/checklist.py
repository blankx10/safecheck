from datetime import datetime

from flask import Blueprint, jsonify, render_template, request

from extensions import db, limiter
from models import ChecklistItem, UserProgress
from routes import get_payload, json_error, normalize_session_id

bp = Blueprint("checklist", __name__)

CATEGORY_ORDER = ["邮箱", "银行/支付", "社交", "学校/工作", "云盘/照片"]


@bp.get("/checklist")
def checklist_page():
    return render_template("checklist.html")


@bp.get("/api/checklist")
@limiter.limit("30 per minute")
def get_checklist():
    session_id = normalize_session_id(request.args.get("session_id"))
    if not session_id:
        return json_error("缺少有效的 session_id")

    items = ChecklistItem.query.order_by(ChecklistItem.sort_order.asc()).all()
    progress_rows = UserProgress.query.filter_by(session_id=session_id).all()
    completed_map = {row.item_id: row.completed for row in progress_rows}

    grouped = {name: [] for name in CATEGORY_ORDER}
    completed_count = 0
    for item in items:
        done = bool(completed_map.get(item.id))
        if done:
            completed_count += 1
        grouped.setdefault(item.category, []).append(
            {
                "id": item.id,
                "title": item.title,
                "description": item.description,
                "priority": item.priority,
                "completed": done,
            }
        )

    categories = []
    for name in CATEGORY_ORDER:
        if grouped.get(name):
            categories.append({"name": name, "items": grouped[name]})
    for name, group_items in grouped.items():
        if name not in CATEGORY_ORDER and group_items:
            categories.append({"name": name, "items": group_items})

    return jsonify(
        {
            "categories": categories,
            "progress": {"total": len(items), "completed": completed_count},
        }
    )


@bp.post("/api/checklist/toggle")
@limiter.limit("30 per minute")
def toggle_checklist():
    payload = get_payload()
    if payload is None:
        return json_error("请使用 JSON 提交", 415)

    session_id = normalize_session_id(payload.get("session_id"))
    item_id = payload.get("item_id")
    completed = payload.get("completed")
    if not session_id:
        return json_error("缺少有效的 session_id")
    try:
        item_id = int(item_id)
    except (TypeError, ValueError):
        return json_error("item_id 无效")
    if not isinstance(completed, bool):
        if str(completed).lower() in {"true", "1", "on"}:
            completed = True
        elif str(completed).lower() in {"false", "0", "off"}:
            completed = False
        else:
            return json_error("completed 必须是布尔值")

    item = db.session.get(ChecklistItem, item_id)
    if not item:
        return json_error("清单项不存在", 404)

    row = UserProgress.query.filter_by(session_id=session_id, item_id=item_id).first()
    if row:
        row.completed = completed
        row.updated_at = datetime.utcnow()
    else:
        row = UserProgress(session_id=session_id, item_id=item_id, completed=completed)
        db.session.add(row)
    db.session.commit()
    return jsonify({"ok": True})
