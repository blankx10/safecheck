# 安心查 SafeCheck

面向普通网民、留学生、老人和学生的隐私优先安全自查网站。无需注册，打开即可使用。

核心能力：可疑短信/链接规则引擎、浏览器内密码泄露自查（HIBP k-匿名 + zxcvbn）、账号加固清单、防诈骗情景测验。

本站不收集密码，不保存可疑信息原文，不访问恶意链接，不扫描他人网络，不承诺绝对安全。

## 本地运行

```bash
cd safecheck
python -m venv venv
```

Windows：

```bash
venv\Scripts\activate
```

macOS / Linux：

```bash
source venv/bin/activate
```

然后：

```bash
pip install -r requirements.txt
copy .env.example .env
flask --app app init-db
flask --app app seed-db
flask --app app run --debug
```

浏览器打开 http://127.0.0.1:5000

运行测试：

```bash
pytest
```

## 环境变量

见 `.env.example`：

- `SECRET_KEY`：请改成随机字符串
- `DATABASE_URL`：本地可用 `sqlite:///safecheck.db`
- `RATELIMIT_STORAGE_URI`：本地可用 `memory://`

生产环境把 `DATABASE_URL` 设为 Supabase Postgres 连接串。若以 `postgres://` 开头，应用会自动改成 `postgresql://`。

## 数据库初始化

`flask --app app init-db` 创建表。  
`flask --app app seed-db` 写入 25 条加固清单和 20 道测验（已有数据时不会重复插入）。

## Render 部署

1. 把本目录推送到 GitHub 仓库。
2. 在 Render 新建 Web Service，根目录选 `safecheck`（若仓库就是本项目则留空）。
3. 运行时选 Python。
4. Start Command：`gunicorn app:app`
5. Health Check Path：`/health`。
6. 环境变量：`SECRET_KEY`、`DATABASE_URL`、`RATELIMIT_STORAGE_URI=memory://`
7. 首次发布后可用 Render Shell 执行 `flask --app app init-db` 与 `flask --app app seed-db`。

免费实例会休眠，这是正常现象。

部署完成后，Render 会提供一个类似 `https://safecheck-xxxx.onrender.com` 的公开网址，任何人都可以访问。若需要自定义网址，在 Render 的 Settings -> Custom Domains 绑定自己的域名。

## Supabase Postgres

1. 创建免费项目，复制 URI。
2. 需要时开启 SSL（连接串常含 `sslmode=require`）。
3. 填入 Render 的 `DATABASE_URL`。
4. 不要把数据库密码提交到 Git。

## 隐私说明

- 密码只在浏览器计算 SHA-1，仅把前 5 位交给同源代理查询；代理再请求 `api.pwnedpasswords.com`，密码和完整哈希不会离开浏览器。
- 可疑文本只存 SHA-256 哈希和风险标签。
- 统计页只展示合计数字。
- 页面底部均有免责声明。

## English Case Study Draft

SafeCheck is a zero-login web MVP that helps non-experts reduce everyday account risk. Suspicious messages are scored by a transparent keyword/regex engine without fetching URLs. Password checks use the HIBP range API so the server never sees passwords. A 25-item checklist and a 20-question scam quiz turn advice into actions. The stack (Flask, SQLite/Postgres, HTMX, Tailwind CDN) stays within a near-zero budget on Render.

## 博客选题

1. 为什么密码不能上传：k-匿名如何保护用户。
2. 反诈骗规则引擎设计：权重、等级与“不点击链接”的边界。
