from flask import Flask

from config import Config
from extensions import db, limiter
from models import ChecklistItem, QuizScenario
from seeds.checklist_items import CHECKLIST_ITEMS
from seeds.quiz_scenarios import QUIZ_SCENARIOS


def create_app(config_object=None):
    app = Flask(__name__)
    app.config.from_object(config_object or Config)

    db.init_app(app)
    limiter.init_app(app)

    from routes.checklist import bp as checklist_bp
    from routes.feedback import bp as feedback_bp
    from routes.main import bp as main_bp
    from routes.password import password_bp
    from routes.quiz import bp as quiz_bp
    from routes.scam import bp as scam_bp
    from routes.stats import bp as stats_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(password_bp)
    app.register_blueprint(scam_bp)
    app.register_blueprint(checklist_bp)
    app.register_blueprint(quiz_bp)
    app.register_blueprint(stats_bp)
    app.register_blueprint(feedback_bp)

    @app.get("/health")
    def health_check():
        return {"status": "ok"}

    @app.after_request
    def set_security_headers(response):
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' https://cdn.tailwindcss.com https://cdnjs.cloudflare.com "
            "https://cdn.jsdelivr.net https://unpkg.com 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://cdnjs.cloudflare.com; "
            "connect-src 'self'; "
            "img-src 'self' data:; "
            "font-src 'self' data:; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-Frame-Options"] = "DENY"
        return response

    @app.cli.command("init-db")
    def init_db():
        db.create_all()
        print("数据库表已创建。")

    @app.cli.command("seed-db")
    def seed_db():
        if ChecklistItem.query.count() == 0:
            for item in CHECKLIST_ITEMS:
                db.session.add(ChecklistItem(**item))
        if QuizScenario.query.count() == 0:
            for item in QUIZ_SCENARIOS:
                db.session.add(QuizScenario(**item))
        db.session.commit()
        print("种子数据已写入。")

    return app


app = create_app()
