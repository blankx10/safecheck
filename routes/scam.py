import hashlib
import json
import logging
import re
import subprocess

from flask import Blueprint, current_app, render_template, request, jsonify

from extensions import db, limiter
from models import PasswordCheckLog, ScamCheck
from routes import get_payload, json_error, normalize_session_id
from services.scam_rules import analyze_scam_text

bp = Blueprint("scam", __name__)
logger = logging.getLogger(__name__)
PASSWORD_RANGE_PREFIX = re.compile(r"^[0-9A-Fa-f]{5}$")


@bp.get("/scam")
def scam_page():
    return render_template("scam.html")


@bp.post("/api/scam-check")
@limiter.limit("20 per minute")
def scam_check():
    payload = get_payload()
    if payload is None:
        return json_error("请使用 JSON 提交", 415)

    text = (payload.get("text") or "").strip()
    session_id = normalize_session_id(payload.get("session_id"))
    max_len = current_app.config.get("MAX_SCAM_TEXT_LENGTH", 5000)

    if not session_id:
        return json_error("缺少有效的 session_id")
    if not text:
        return json_error("请粘贴要检查的内容")
    if len(text) > max_len:
        return json_error(f"内容过长，最多 {max_len} 字")

    result = analyze_scam_text(text)
    text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()

    record = ScamCheck(
        session_id=session_id,
        text_hash=text_hash,
        risk_score=result["risk_score"],
        risk_level=result["risk_level"],
        reasons_json=json.dumps(result["reasons"], ensure_ascii=False),
    )
    db.session.add(record)
    db.session.commit()
    logger.info("scam-check saved hash_prefix=%s score=%s", text_hash[:8], result["risk_score"])

    if request.headers.get("HX-Request"):
        return render_template("partials/scam_result.html", result=result)
    return jsonify(result)


@bp.get("/api/password-check-range/<prefix>")
@limiter.limit("30 per minute")
def password_check_range(prefix):
    if not PASSWORD_RANGE_PREFIX.fullmatch(prefix):
        return json_error("无效的哈希前缀", 400)

    try:
        response = subprocess.run(
            [
                "curl",
                "--fail",
                "--silent",
                "--show-error",
                "--max-time",
                "10",
                "-H",
                "Add-Padding: true",
                "-A",
                "SafeCheck/1.0",
                f"https://api.pwnedpasswords.com/range/{prefix.upper()}",
            ],
            capture_output=True,
            check=True,
            timeout=12,
        )
        return current_app.response_class(
            response.stdout,
            status=200,
            mimetype="text/plain",
        )
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
        logger.warning("password range lookup failed: %s", error)
        return json_error("泄露库暂时不可用", 502)


@bp.post("/api/password-check-count")
@limiter.limit("30 per minute")
def password_check_count():
    payload = get_payload()
    if payload is None:
        return json_error("请使用 JSON 提交", 415)
    session_id = normalize_session_id(payload.get("session_id"))
    if not session_id:
        return json_error("缺少有效的 session_id")
    db.session.add(PasswordCheckLog(session_id=session_id))
    db.session.commit()
    return jsonify({"ok": True})
