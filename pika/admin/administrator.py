"""Pages and endpoints exclusively for administrators"""
from datetime import datetime, timezone, timedelta

import jwt
from flask import Blueprint, render_template, redirect, url_for, flash, current_app
from flask_login import login_required

from pika import db
from pika.auth import send_email, role_required
from pika.models import Role, Users
from .forms import RenewTokenForm, RevokeTokenForm, EnableDisableForm, RoleChangeForm, SendActivationEmailForm

bp = Blueprint('administrator', __name__)


@bp.route('/users', methods=['GET'])
@login_required
@role_required(roles=['admin', 'superuser'])
def users():
    """Page with account details of all users."""
    all_users = Users.query.all()
    now = datetime.now(tz=timezone.utc).astimezone()
    renew_form = RenewTokenForm()
    revoke_form = RevokeTokenForm()
    return render_template("admin/users.html", all_users=all_users, now=now, renew_form=renew_form,
                           revoke_form=revoke_form)


@bp.route('/roles', methods=['GET'])
@login_required
@role_required(roles=['admin'])
def roles():
    """Page """
    all_users = Users.query.all()
    all_roles = Role.query.order_by(Role.id).all()
    form = RoleChangeForm()
    return render_template("admin/roles.html", roles=all_roles, users=all_users, form=form)


@bp.route('/roles/remove', methods=['POST'])
@login_required
@role_required(roles=['admin'])
def remove_role():
    """Endpoint to remove a role of a specific user."""
    form = RoleChangeForm()
    if form.validate_on_submit():
        user = db.session.get(Users, form.user_id.data)
        user.roles = [role for role in user.roles if role.id != int(form.role_id.data)]
        db.session.commit()
    else:
        flash('Error', 'danger')
        current_app.logger.debug(form.errors)
    return redirect(url_for('admin.administrator.roles'))


@bp.route('/roles/assign', methods=['POST'])
@login_required
@role_required(roles=['admin'])
def assign_role():
    """Endpoint to assign a role to a specific user."""
    form = RoleChangeForm()
    if form.validate_on_submit():
        user = db.session.get(Users, form.user_id.data)
        role = db.session.get(Role, form.role_id.data)
        user.roles.append(role)
        db.session.commit()
    else:
        flash('Error', 'danger')
        current_app.logger.debug(form.errors)
    return redirect(url_for('admin.administrator.roles'))


@bp.route('/accounts', methods=['GET'])
@login_required
@role_required(roles=['admin'])
def accounts():
    """Page administrating account status"""
    all_users = Users.query.all()
    form = EnableDisableForm()
    mail_form = SendActivationEmailForm()
    return render_template("admin/accounts.html", users=all_users, form=form, mail_form=mail_form)


@bp.route('/token/renew', methods=['POST'])
@login_required
@role_required(roles=['admin'])
def renew_token():
    """Endpoint to renew a API token of a specific user."""
    form = RevokeTokenForm()
    if form.validate_on_submit():
        user = db.session.get(Users, form.user_id.data)
        user.revoke_token()
        user.get_token()
        db.session.commit()
    else:
        flash('Error', 'danger')
        current_app.logger.debug(form.errors)

    return redirect(url_for('admin.administrator.users'))


@bp.route('/token/revoke', methods=['POST'])
@login_required
@role_required(roles=['admin'])
def revoke_token():
    """Endpoint to revoke an API token of a specific user."""
    form = RevokeTokenForm()
    if form.validate_on_submit():
        user = db.session.get(Users, form.user_id.data)
        user.revoke_token()
        user.token = None
        db.session.commit()
    else:
        flash('Error', 'danger')
        current_app.logger.debug(form.errors)

    return redirect(url_for('admin.administrator.users'))


@bp.route('/accounts/enable', methods=['POST'])
@login_required
@role_required(roles=['admin'])
def enable():
    """Endpoint to enable specific account."""
    form = EnableDisableForm()
    if form.validate_on_submit():
        user = db.session.get(Users, form.user_id.data)
        user.active = True
        db.session.commit()
    else:
        flash('Error', 'danger')
        current_app.logger.debug(form.errors)

    return redirect(url_for('admin.administrator.accounts'))


@bp.route('/accounts/disable', methods=['POST'])
@login_required
@role_required(roles=['admin'])
def disable():
    """Endpoint to disable specific account."""
    form = EnableDisableForm()
    if form.validate_on_submit():
        user = db.session.get(Users, form.user_id.data)
        user.active = False
        db.session.commit()
    else:
        flash('Error', 'danger')
        current_app.logger.debug(form.errors)

    return redirect(url_for('admin.administrator.accounts'))


@bp.route('/accounts/send_activation_email', methods=['POST'])
@login_required
@role_required(roles=['admin'])
def send_activation_email():
    """Endpoint to send account activation email to specified user."""
    form = SendActivationEmailForm()
    if form.validate_on_submit():
        user = db.session.get(Users, form.user_id.data)
        activation_token = jwt.encode(
            payload={'user_id': form.user_id.data, 'exp': datetime.now(timezone.utc) + timedelta(minutes=90)},
            key=current_app.config['SECRET_KEY'],
            algorithm='HS256'
        )
        send_email(
            user.email,
            'Activate PIKA Account',
            render_template('mail/activation/activation.txt', username=user.username, token=activation_token),
            render_template('mail/activation/activation.html', username=user.username, token=activation_token),
        )
    return redirect(url_for('admin.administrator.accounts'))
