from markupsafe import Markup

def nl2br(value):
    """Convert newlines to <br> tags."""
    if not value:
        return ""
    return Markup(value.replace('\n', '<br>')) 