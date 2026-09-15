from flask import Blueprint, render_template

bp = Blueprint("main", __name__)


@bp.get("/")
def index():
    return render_template("index.html")


@bp.get("/password")
def password_page():
    return render_template("password.html")


@bp.get("/privacy")
def privacy():
    return render_template("privacy.html")


@bp.get("/about")
def about():
    return render_template("about.html")
