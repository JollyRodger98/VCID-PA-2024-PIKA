"""Pages to show setting pages."""
from flask import Blueprint, render_template
from flask_login import login_required, current_user

bp = Blueprint('profile', __name__)


@bp.route("/dashboard")
@login_required
def dashboard():
    """Page with user overview."""
    full_name = f"{current_user.first_name or ''} {current_user.last_name or ''}"
    return render_template("admin/dashboard.html", full_name=full_name)


@bp.route("/settings")
@login_required
def settings():
    """Page with user settings."""
    return render_template("admin/settings.html")
