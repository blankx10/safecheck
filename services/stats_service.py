from sqlalchemy import func

from extensions import db
from models import Feedback, PasswordCheckLog, QuizAnswer, ScamCheck


def get_public_stats() -> dict:
    """只返回聚合数字，不包含 session、原文或哈希。"""
    total_scam = ScamCheck.query.count()
    level_rows = (
        db.session.query(ScamCheck.risk_level, func.count(ScamCheck.id))
        .group_by(ScamCheck.risk_level)
        .all()
    )
    risk_dist = {"低": 0, "中": 0, "高": 0}
    for level, count in level_rows:
        if level in risk_dist:
            risk_dist[level] = count

    quiz_total = QuizAnswer.query.count()
    quiz_correct = QuizAnswer.query.filter_by(is_correct=True).count()
    accuracy = round((quiz_correct / quiz_total) * 100, 1) if quiz_total else 0.0

    feedback_count = Feedback.query.count()
    avg_rating = db.session.query(func.avg(Feedback.rating)).scalar()
    avg_rating = round(float(avg_rating), 1) if avg_rating else 0.0

    return {
        "scam_check_count": total_scam,
        "risk_distribution": risk_dist,
        "quiz_answer_count": quiz_total,
        "quiz_accuracy_percent": accuracy,
        "feedback_count": feedback_count,
        "feedback_avg_rating": avg_rating,
        "password_check_count": PasswordCheckLog.query.count(),
    }
