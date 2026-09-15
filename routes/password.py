# 无状态密码泄露查询代理，不收集或存储用户数据。
from flask import Blueprint, current_app, jsonify
import requests

password_bp = Blueprint("password", __name__)

HIBP_BASE = "https://api.pwnedpasswords.com/range/"


@password_bp.route("/api/hibp/<prefix>")
def hibp_proxy(prefix):
    # 只接受 5 位十六进制前缀，绝不接受完整哈希。
    if len(prefix) != 5 or not all(c in "0123456789abcdefABCDEF" for c in prefix):
        return jsonify({"error": "invalid prefix"}), 400

    try:
        response = requests.get(
            HIBP_BASE + prefix.upper(),
            headers={
                "Add-Padding": "true",
                "User-Agent": "SafeCheck/1.0",
            },
            timeout=10,
        )
        response.raise_for_status()
        return response.text, 200, {"Content-Type": "text/plain"}
    except requests.RequestException as error:
        current_app.logger.error(
            "HIBP proxy upstream error: %s", type(error).__name__
        )
        return jsonify({"error": "upstream failed"}), 502
