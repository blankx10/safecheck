import json

from flask import Blueprint, jsonify, render_template

from extensions import db, limiter
from models import QuizAnswer, QuizScenario
from routes import get_payload, json_error, normalize_session_id

bp = Blueprint("quiz", __name__)


@bp.get("/quiz")
def quiz_page():
    return render_template("quiz.html")


@bp.get("/api/quiz")
@limiter.limit("30 per minute")
def get_quiz():
    scenarios = QuizScenario.query.order_by(QuizScenario.sort_order.asc()).all()
    payload = []
    for item in scenarios:
        payload.append(
            {
                "id": item.id,
                "category": item.category,
                "question": item.question,
                "options": json.loads(item.options_json),
            }
        )
    return jsonify({"questions": payload})


@bp.post("/api/quiz/answer")
@limiter.limit("30 per minute")
def answer_quiz():
    payload = get_payload()
    if payload is None:
        return json_error("请使用 JSON 提交", 415)

    session_id = normalize_session_id(payload.get("session_id"))
    if not session_id:
        return json_error("缺少有效的 session_id")
    try:
        scenario_id = int(payload.get("scenario_id"))
        chosen_index = int(payload.get("chosen_index"))
    except (TypeError, ValueError):
        return json_error("题目或选项无效")

    scenario = db.session.get(QuizScenario, scenario_id)
    if not scenario:
        return json_error("题目不存在", 404)

    is_correct = chosen_index == scenario.correct_index
    db.session.add(
        QuizAnswer(
            session_id=session_id,
            scenario_id=scenario_id,
            chosen_index=chosen_index,
            is_correct=is_correct,
        )
    )
    db.session.commit()
    return jsonify(
        {
            "is_correct": is_correct,
            "correct_index": scenario.correct_index,
            "explanation": scenario.explanation,
        }
    )
