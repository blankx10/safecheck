import re

DISCLAIMER = "本结果由规则引擎生成，仅供参考，不构成法律或安全保证。"

DEFAULT_ADVICE = [
    "不要点击陌生链接，不要下载对方要求的 App",
    "不要转账，不要提供验证码、密码或身份证",
    "通过官方 App、官网或卡背面电话自行核实",
    "可疑短信可向 12321 举报",
]

RULES = [
    {
        "id": "urgent_keywords",
        "keywords": [
            "冻结",
            "安全账户",
            "转账",
            "验证码",
            "屏幕共享",
            "点击链接",
            "下载app",
            "下载 app",
        ],
        "weight": 30,
        "reason": "出现冻结、转账、验证码、屏幕共享等危险操作要求",
        "advice": "不要按对方要求转账或共享屏幕",
    },
    {
        "id": "short_link",
        "regex": (
            r"(bit\.ly|tinyurl|t\.cn|shorturl|https?://\d{1,3}(?:\.\d{1,3}){3}"
            r"|xn--|[\w.-]+\.(xyz|top|click|gq|tk)\b)"
        ),
        "weight": 20,
        "reason": "出现短链、IP 地址或可疑域名",
        "advice": "不要打开短链，改用官方渠道查询",
    },
    {
        "id": "impersonation",
        "keywords": [
            "银行客服",
            "大使馆",
            "领事馆",
            "快递",
            "奖学金",
            "房东",
            "官方客服",
            "公安",
            "检察院",
        ],
        "weight": 15,
        "reason": "可能冒充银行、使馆、快递、奖学金、房东或客服",
        "advice": "挂断后拨打你已知的官方电话",
    },
    {
        "id": "identity",
        "keywords": ["身份证", "银行卡", "密码", "验证码", "cvv", "网银盾"],
        "weight": 35,
        "reason": "要求提供身份证、银行卡、密码或验证码",
        "advice": "任何索要证件和验证码的请求都应拒绝",
    },
    {
        "id": "urgency",
        "keywords": ["立即", "马上", "24小时", "24 小时", "否则", "即将关闭", "最后机会"],
        "weight": 15,
        "reason": "制造紧迫感，催你来不及思考",
        "advice": "越催你越要停下来核实",
    },
    {
        "id": "weird_text",
        "regex": r"[！!]{2,}|[？?]{2,}|[\u3000]|[ａ-ｚＡ-Ｚ０-９]",
        "weight": 10,
        "reason": "标点异常或中英文全角混用",
        "advice": "官方通知一般不会满篇奇怪符号",
    },
    {
        "id": "chat_app",
        "keywords": ["加qq", "加 qq", "加微信", "加v", "telegram", "whatsapp", "私聊"],
        "weight": 15,
        "reason": "要求加 QQ、微信、Telegram 或 WhatsApp",
        "advice": "把你带到私人聊天是诈骗常见步骤",
    },
    {
        "id": "prize",
        "keywords": ["中奖", "退税", "补贴", "高薪兼职", "刷单", "免费领"],
        "weight": 20,
        "reason": "承诺中奖、退税、补贴或高薪兼职",
        "advice": "天上掉钱的消息优先当诈骗处理",
    },
]


def _level(score: int) -> str:
    if score <= 29:
        return "低"
    if score <= 59:
        return "中"
    return "高"


def analyze_scam_text(text: str) -> dict:
    lowered = (text or "").lower()
    score = 0
    reasons = []
    advice = []

    for rule in RULES:
        hit = False
        if "keywords" in rule:
            hit = any(keyword.lower() in lowered for keyword in rule["keywords"])
        if not hit and "regex" in rule:
            hit = re.search(rule["regex"], lowered, flags=re.I) is not None
        if hit:
            score += rule["weight"]
            reasons.append(rule["reason"])
            advice.append(rule["advice"])

    score = min(score, 100)
    if not advice:
        advice = ["未命中高危规则，仍请保持警惕，不要点击不明链接"]

    merged_advice = list(dict.fromkeys(advice + DEFAULT_ADVICE))
    return {
        "risk_score": score,
        "risk_level": _level(score),
        "reasons": reasons or ["未匹配到典型诈骗话术"],
        "advice": merged_advice[:6],
        "disclaimer": DISCLAIMER,
    }
