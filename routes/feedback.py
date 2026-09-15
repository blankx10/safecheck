from flask import Blueprint, current_app, jsonify, render_template

from extensions import db, limiter
from models import Feedback
from routes import get_payload, json_error, normalize_session_id

bp = Blueprint("feedback", __name__)


@bp.get("/feedback")
def feedback_page():
    return render_template("feedback.html")


@bp.post("/api/feedback")
@limiter.limit("10 per hour")
def submit_feedback():
    payload = get_payload()
    if payload is None:
        return json_error("请使用 JSON 提交", 415)

    session_id = normalize_session_id(payload.get("session_id"))
    if not session_id:
        return json_error("缺少有效的 session_id")

    try:
        rating = int(payload.get("rating"))
    except (TypeError, ValueError):
        return json_error("评分必须是 1 到 5 的整数")
    if rating < 1 or rating > 5:
        return json_error("评分必须是 1 到 5")

    comment = (payload.get("comment") or "").strip()
    max_len = current_app.config.get("MAX_FEEDBACK_LENGTH", 500)
    if len(comment) > max_len:
        return json_error(f"评论最多 {max_len} 字")

    db.session.add(Feedback(session_id=session_id, rating=rating, comment=comment or None))
    db.session.commit()
    return jsonify({"ok": True, "message": "感谢反馈"})
