"""Global routes"""
import json
from datetime import datetime, timedelta, timezone

from flask import render_template, redirect, url_for, flash, current_app, session, abort, request
from flask_login import current_user, login_required

from pika import db
from pika.community import bp
from pika.models import Users, Posts, Threads
from .data import Thread, User
from .forms import PostForm, EditPostForm, ContactForm
from .util import increment_thread_view


@bp.before_request
def before_request():
    """
    Create key in session if it does not exist.
    """
    session.setdefault("threads_visited", {})


@bp.errorhandler(404)
def page_not_found(error):
    """Handle missing threads"""
    return render_template("errors/404.html", description=error.description), 404


@bp.route('/')
def index():
    """
    Main community page
    """
    users = Users.query.order_by(Users.last_login.desc()).limit(5).all()
    users = [user.username for user in users]

    new_threads = (Threads.query
                   .order_by(Threads.created.desc())
                   .limit(5)
                   .all()
                   )
    new_threads = [Thread.from_orm(thread) for thread in new_threads]

    active_threads = (Threads.query
                      .order_by(Threads.last_updated.desc())
                      .where(Threads.last_updated < datetime.now(timezone.utc),
                             Threads.last_updated > datetime.now(timezone.utc) - timedelta(days=1))
                      .limit(5)
                      .all()
                      )
    active_threads = [Thread.from_orm(thread) for thread in active_threads]

    popular_threads = (Threads.query
                       .where(Threads.views >= 100)
                       .where(Threads.last_updated < datetime.now(timezone.utc),
                              Threads.last_updated > datetime.now(timezone.utc) - timedelta(days=1))
                       .order_by(Threads.last_updated.desc())
                       .limit(5)
                       .all()
                       )
    popular_threads = [Thread.from_orm(thread) for thread in popular_threads]

    return render_template("community/index.html", all_users=users, new_threads=new_threads,
                           active_threads=active_threads, popular_threads=popular_threads)


@bp.route('/thread/<int:thread_id>', methods=['GET'])
def thread_page(thread_id):
    """
    Page to display a thread
    :param thread_id: ID of the thread to display
    """
    form = PostForm()
    thread_query = Threads.query.get(thread_id)
    if thread_query is None:
        abort(404, "<i class=\"bi bi-threads me-2\"></i>This thread does not exist")

    increment_thread_view(thread_id)

    thread = Thread.from_orm(thread_query)
    thread.posts.sort(key=lambda _post: _post.created)

    author_posts = []
    for post in thread.posts:
        if post.author.user_id == getattr(current_user, "user_id", None):
            author_posts.append({**post.model_dump(exclude={'author', "created"}), "author_id": post.author.user_id})

    edit_form = EditPostForm()

    return render_template("community/thread.html", thread=thread, form=form, author_posts=author_posts,
                           edit_form=edit_form)


@bp.route('/thread/<int:thread_id>/post', methods=['POST'])
@login_required
def post_add_form(thread_id):
    """
    Add a post to the thread
    :param thread_id: The ID of the thread to add the post to
    """
    form = PostForm()
    if form.validate_on_submit():
        activity_time = datetime.now(timezone.utc)
        thread: Threads = Threads.query.get(thread_id)
        post = Posts(
            content=form.content.data,
            thread_id=thread_id,
            author_id=current_user.user_id,
            created=activity_time,
        )
        thread.last_updated = activity_time
        db.session.add(post)
        db.session.commit()
    return redirect(url_for('community.thread_page', thread_id=thread_id))


@bp.route('/thread/<int:thread_id>/post/edit', methods=['POST'])
@login_required
def post_edit_form(thread_id):
    """
    Edit a post in the thread
    :param thread_id: ID of the thread the post belongs to
    """
    form = EditPostForm()
    if form.validate_on_submit():
        author_id = int(form.author_id.data)
        post_id = int(form.post_id.data)
        post_content = form.content.data
        post: Posts = Posts.query.get(post_id)
        # Check if edited post author id, the current user id and the author id of the freshly queried post from the
        # database are identical to make sure no unauthorized edits are taking place.
        if current_user.user_id == post.author_id and current_user.user_id == author_id:
            post.content = post_content
            db.session.commit()
    else:
        for error in form.errors.values():
            flash(error, "warning")
    return redirect(url_for('community.thread_page', thread_id=thread_id))


@bp.route('/faq', methods=['GET'])
def faq_page():
    """
    Display the FAQ page
    """
    from flask_babel import get_locale
    with current_app.open_resource("community/static/questions.json", mode="r") as file:
        questions = json.loads(file.read())
    language = get_locale().language

    questions.sort(key=lambda _question: _question['order'])
    questions = [{'question': _question[language]['question'], 'answer': _question[language]['answer']} for _question in
                 questions]
    for _question in questions:
        _question['answer'] = _question['answer'].format(contact_form=url_for("community.contact"))

    return render_template("community/faq.html", questions=questions)


@bp.route('/profile/<string:username>')
def profile(username):
    """
    Display the public profile page
    :param username: Username of the user
    """
    user = Users.query.filter_by(username=username).first()
    user = User.from_orm(user)
    return render_template("community/public_profile.html", user=user)


@bp.route("/contact")
def contact():
    """Page with contact form"""
    subject = request.args.get("subject", "")
    email = current_user.email if current_user.is_authenticated else ''
    form = ContactForm(data={"subject": subject, "email": email})
    return render_template("community/contact.html", form=form)


@bp.route("/contact", methods=["POST"])
def contact_form():
    """Endpoint to handle contact form and redirect to mailto url."""
    form = ContactForm()
    return redirect(
        f"mailto:pika@jollyrodger.ch?subject={form.subject.data}&body={form.message.data}&cc={form.email.data}")
