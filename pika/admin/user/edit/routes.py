"""Pages and endpoints for user settings."""
from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from pika import db
from pika.models import Users
from .forms import EditNameForm, EditEmailForm, EditPasswordForm

bp = Blueprint('edit', __name__)


@bp.route("/deactivate")
@login_required
def deactivate():
    """Page for confirming the deactivation process."""
    return render_template("admin/deactivate.html")


@bp.route('/name', methods=['GET'])
@login_required
def name_page():
    """Display page for editing the user's name.'"""
    form = EditNameForm()
    return render_template("admin/edit/name.html", form=form)


@bp.route('/name', methods=['POST'])
@login_required
def name_form():
    """Endpoint for handling the edit name form and setting new names in the database."""
    form = EditNameForm()
    if form.validate_on_submit():
        user: Users = Users.query.get(current_user.user_id)
        user.first_name = form.first_name.data
        user.last_name = form.last_name.data
        db.session.commit()
        return redirect(url_for("admin.user.profile.dashboard"))

    return render_template("admin/edit/name.html", form=form)


@bp.route('/email', methods=['GET'])
@login_required
def email_page():
    """Display page which allows users to edit their email."""
    form = EditEmailForm()
    email = current_user.email
    return render_template("admin/edit/email.html", form=form, email=email)


@bp.route('/email', methods=['POST'])
@login_required
def email_form():
    """Endpoint for handling email edit form and setting new email in database."""
    form = EditEmailForm()
    if form.validate_on_submit():
        user: Users = Users.query.filter_by(email=form.data.get("email")).first()
        if user and user.user_id != current_user.user_id:
            flash("Email is already in use")
            return render_template("admin/edit/email.html", form=form, email=form.data.get("email"))

        user: Users = Users.query.get(current_user.user_id)
        user.email = form.data.get("email")
        db.session.commit()
        return redirect(url_for("admin.user.profile.dashboard"))

    return render_template("admin/edit/email.html", form=form)


@bp.route('/password', methods=['GET'])
@login_required
def password_page():
    """Display page which allows users to change their password"""
    form = EditPasswordForm()
    return render_template("admin/edit/password.html", form=form)


@bp.route('/password', methods=['POST'])
@login_required
def password_form():
    """Endpoint for handling the edit password form and setting new password in db."""
    form = EditPasswordForm()
    if form.validate_on_submit():
        user: Users = Users.query.get(current_user.user_id)
        if not check_password_hash(user.password, form.old_password.data):
            flash("Current password is incorrect")
            return render_template("admin/edit/password.html", form=form)

        if form.new_password.data != form.new_password_confirm.data:
            flash("New passwords are not the same")
            return render_template("admin/edit/password.html", form=form)

        user.password = generate_password_hash(form.new_password.data, "pbkdf2:sha256")
        db.session.commit()

        return redirect(url_for("admin.user.profile.dashboard"))

    return render_template("admin/edit/password.html", form=form)
