"""Functions for sending emails."""
from threading import Thread

from flask import current_app
from flask_mail import Message

from pika import mail


class FlaskThread(Thread):
    """Thread able to run flask context dependant code."""
    def __init__(self, target=None, args=(), **kwargs):
        super().__init__(target=target, args=args, **kwargs)
        # noinspection PyUnresolvedReferences,PyProtectedMember
        self.app = current_app._get_current_object()

    def run(self):
        with self.app.app_context():
            super().run()


def _send_async_email(msg: Message):
    """Thread function to send mail."""
    with current_app.app_context():
        mail.send(msg)


def send_email(to: str, subject: str, text_body: str, html_body: str):
    """
    Send flask mail. The sending is done in a thread to prevent locking flask.
    :param to: Recipient of the email.
    :type to: str
    :param subject: Subject of the email.
    :type subject: str
    :param text_body: Text body of the email.
    :type text_body: str
    :param html_body: HTML body of the email.
    :type html_body: str
    """
    message = Message(subject, sender='PIKA <pika@jollyrodger.ch>', recipients=[to])
    message.body = text_body
    message.html = html_body
    FlaskThread(target=_send_async_email, args=(message,)).start()
