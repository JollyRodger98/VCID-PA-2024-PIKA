"""Authentication routes and endpoints"""
from datetime import datetime, timedelta, timezone

import jwt
from flask import render_template, redirect, url_for, request, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_babel import gettext as _
from pika import db
from pika.auth import bp
from pika.models import Users
from .forms import LoginForm, RegistrationForm
from .mail import send_email


@bp.route('/register', methods=["GET"])
def register_page():
    """Registration page."""
    form = RegistrationForm()
    return render_template("auth/register.html", title="Register", form=form)


@bp.route('/register', methods=["POST"])
def register_form():
    """Handle user registration form and create new user."""
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.data.get("new_username")
        password = form.data.get("new_password")
        email = form.data.get("new_email")
        confirm_password = form.data.get("new_confirm_password")

        user = Users.query.filter_by(username=username).first()
        if user:
            flash(_("That username is taken. Please choose another one."), "danger")
            return render_template("auth/register.html", title="Register", form=form)

        user = Users.query.filter_by(email=email).first()
        if user:
            flash(_("That E-Mail is already in use. Please use another one."), "danger")
            return render_template("auth/register.html", title="Register", form=form)

        if password != confirm_password:
            flash(_("Passwords don't match."), "danger")
            return render_template("auth/register.html", title="Register", form=form)

        new_user = Users()
        new_user.username = username
        new_user.password = generate_password_hash(password, "pbkdf2:sha256")
        new_user.email = email
        new_user.active = False

        db.session.add(new_user)
        db.session.commit()

        activation_token = jwt.encode(
            payload={'user_id': new_user.user_id, 'exp': datetime.now(timezone.utc) + timedelta(minutes=90)},
            key=current_app.config['SECRET_KEY'],
            algorithm='HS256'
        )
        send_email(
            new_user.email,
            _('Activate PIKA Account'),
            render_template('mail/activation/activation.txt', username=new_user.username, token=activation_token),
            render_template('mail/activation/activation.html', username=new_user.username, token=activation_token),
        )

        flash(_("Your account has been created"), "success")
        return redirect(url_for("auth.login_page"))

    return render_template("auth/register.html", title="Register", form=form)


@bp.route('/login')
def login_page():
    """Login Page"""
    form = LoginForm()
    return render_template("auth/login.html", title="Login", form=form)


@bp.route('/login', methods=["POST"])
def login_form():
    """Handle login form and log user in."""
    form = LoginForm(prefix="nav")
    if not form.login.data:
        form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user: Users = Users.query.filter_by(username=username, active=True).first()

        if not user or not check_password_hash(user.password, password):
            flash(_("Invalid username or password"), "warning")
            return render_template("auth/login.html", title="Login", form=LoginForm(data={"username": username}))

        login_user(user)
        user.last_login = datetime.now(timezone.utc)
        db.session.commit()

        return redirect(request.args.get("next") or url_for("admin.user.profile.dashboard"))

    return redirect(request.referrer)


@bp.route('/logout')
@login_required
def logout():
    """Log user out."""
    logout_user()
    flash(_("You have been logged out."), "success")
    return redirect(url_for("index"))


@bp.route('/activate', methods=['GET'])
def activate():
    """Endpoint for account activation via activation email with jwt token."""
    token = request.args.get('token')
    try:
        data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        page_title = _('Activate Account')
        title = _('Token Expired')
        description = _(
            'The link to activate your account has expired. To resend an activation email please contact the'
            ' site administration.')
        return render_template('errors/error.html', page_title=page_title, title=title, description=description)

    user = db.session.get(Users, data.get('user_id'))
    user.active = True
    db.session.commit()
    flash(_('Your account has been activated'), 'success')

    return redirect(url_for('index'))


@bp.route('/deactivate')
@login_required
def deactivate():
    """Endpoint for account deactivation."""
    user: Users = Users.query.get(current_user.user_id)
    user.active = False
    db.session.commit()
    logout_user()
    return redirect(url_for("index"))
