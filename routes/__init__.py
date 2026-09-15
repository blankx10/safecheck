from flask import jsonify, request


def get_payload():
    """POST 接口优先读 JSON；HTMX 表单作为例外读取 form。"""
    if request.is_json:
        return request.get_json(silent=True) or {}
    if request.headers.get("HX-Request"):
        return request.form.to_dict()
    return None


def json_error(message, status=400):
    return jsonify({"ok": False, "error": message}), status


def normalize_session_id(value):
    text = (value or "").strip()
    if not text or len(text) > 64:
        return None
    return text
