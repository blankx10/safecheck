from services.scam_rules import analyze_scam_text


def test_high_risk_text():
    result = analyze_scam_text(
        "您的银行卡被冻结，请立即把验证码发给银行客服并转账到安全账户 http://bit.ly/abc"
    )
    assert result["risk_level"] == "高"
    assert result["risk_score"] >= 60
    assert result["reasons"]
    assert result["advice"]
    assert "仅供参考" in result["disclaimer"]


def test_medium_risk_text():
    result = analyze_scam_text("快递到了请加微信私聊")
    assert result["risk_level"] in ("中", "高")
    assert result["risk_score"] >= 30


def test_low_risk_text():
    result = analyze_scam_text("今晚一起吃饭，地点还是老地方")
    assert result["risk_level"] == "低"
    assert result["risk_score"] <= 29
