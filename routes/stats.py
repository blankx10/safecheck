from flask import Blueprint, jsonify, render_template

from extensions import limiter
from services.stats_service import get_public_stats

bp = Blueprint("stats", __name__)


@bp.get("/stats")
def stats_page():
    return render_template("stats.html", stats=get_public_stats())


@bp.get("/api/stats")
@limiter.limit("30 per minute")
def stats_api():
    return jsonify(get_public_stats())
