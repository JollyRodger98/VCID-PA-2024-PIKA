"""WTForms compatible widgets"""
from markupsafe import Markup
from wtforms.widgets import html_params


class Button:  # pylint: disable=too-few-public-methods
    """WTForms button widget."""
    html_params = staticmethod(html_params)

    def __init__(self, button_type=None, icon=None):
        if button_type is not None:
            self.button_type = button_type
        if icon is not None:
            self.icon = icon

    def __call__(self, field, **kwargs):
        kwargs.setdefault("id", field.id)
        kwargs.setdefault("class", "btn btn-success")
        kwargs.setdefault("type", self.button_type)
        kwargs["role"] = "button"
        if "value" not in kwargs:
            kwargs["value"] = field.label.text
        if hasattr(self, "icon"):
            return Markup(
                f"<button {self.html_params(name=field.name, **kwargs)}>{self.icon} {kwargs["value"]}</button>"
            )

        return Markup(f"<button {self.html_params(name=field.name, **kwargs)}>{kwargs["value"]}</button>")


class SubmitButton(Button):  # pylint: disable=too-few-public-methods
    """WTForms submit button widget. Used for replacing input widget in submit field."""
    button_type = "submit"
