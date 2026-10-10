"""
Email templates rendered with the stdlib string.Template ($placeholders),
so HTML/CSS braces never collide with substitution and no new dependency
is required. Every template has subject, html, and text variants.

User-derived values (names, messages) are HTML-escaped for the html part
by render_email(); the text part always receives the raw value.
"""
from html import escape
from string import Template
from typing import Dict

_BASE_HTML = Template("""<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f1f5f9;font-family:Arial,Helvetica,sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f1f5f9;padding:24px 12px;">
    <tr><td align="center">
      <table role="presentation" width="560" cellpadding="0" cellspacing="0"
             style="max-width:560px;background:#ffffff;border-radius:12px;overflow:hidden;">
        <tr><td style="background:#0f766e;padding:20px 28px;">
          <span style="color:#ffffff;font-size:18px;font-weight:bold;">$app_name</span>
        </td></tr>
        <tr><td style="padding:28px;color:#1e293b;font-size:15px;line-height:1.6;">
$body
        </td></tr>
        <tr><td style="padding:16px 28px;background:#f8fafc;color:#64748b;font-size:12px;">
          Sent by $app_name. If you did not expect this email, you can safely ignore it.
        </td></tr>
      </table>
    </td></tr>
  </table>
</body></html>""")

_BUTTON = Template(
    '<a href="$url" style="display:inline-block;background:#0f766e;color:#ffffff;'
    'text-decoration:none;padding:12px 24px;border-radius:8px;font-weight:bold;">$label</a>'
)

_TEMPLATES: Dict[str, Dict[str, Template]] = {
    "verify_email": {
        "subject": Template("Verify your email - $app_name"),
        "html": Template(
            """<h2 style="margin:0 0 12px;">Confirm your email address</h2>
<p>Hi $user_name,</p>
<p>Welcome to $app_name. Please confirm your email address to activate your account.</p>
<p style="margin:24px 0;">$_button</p>
<p style="word-break:break-all;color:#64748b;font-size:13px;">Or paste this link into your browser:<br>$verification_url</p>"""
        ),
        "text": Template(
            "Hi $user_name,\n\n"
            "Welcome to $app_name. Please confirm your email address to activate your account:\n"
            "$verification_url\n\n"
            "If you did not create this account, you can ignore this email."
        ),
    },
    "password_reset": {
        "subject": Template("Reset your password - $app_name"),
        "html": Template(
            """<h2 style="margin:0 0 12px;">Password reset request</h2>
<p>Hi $user_name,</p>
<p>We received a request to reset your $app_name password. This link can be used once and expires soon.</p>
<p style="margin:24px 0;">$_button</p>
<p style="word-break:break-all;color:#64748b;font-size:13px;">Or paste this link into your browser:<br>$reset_url</p>
<p style="color:#b91c1c;">If you did not request a reset, your password remains unchanged.</p>"""
        ),
        "text": Template(
            "Hi $user_name,\n\n"
            "We received a request to reset your $app_name password. "
            "This link can be used once and expires soon:\n"
            "$reset_url\n\n"
            "If you did not request a reset, your password remains unchanged."
        ),
    },
    "notification": {
        "subject": Template("$subject"),
        "html": Template(
            """<h2 style="margin:0 0 12px;">$title</h2>
<p>Hi $user_name,</p>
<p>$message</p>
<p style="margin:24px 0;">$_button</p>
<p style="color:#64748b;font-size:13px;">You can turn notification emails off in your profile settings.</p>"""
        ),
        "text": Template(
            "Hi $user_name,\n\n$title\n\n$message\n\n"
            "Open $app_name to see more: $app_url\n"
            "(You can turn notification emails off in your profile settings.)"
        ),
    },
}

# Fields whose values are user-derived and must be escaped in the HTML part.
_ESCAPED_FIELDS = {"user_name", "message", "title", "subject"}


def render_email(
    name: str,
    context: Dict[str, str],
    button_url: str = "",
    button_label: str = "Open PropNoxa",
    app_name: str = "PropNoxa",
    app_url: str = "http://localhost:5173",
) -> tuple:
    """
    Render a template by name into (subject, html_body, text_body).

    Raises KeyError for unknown template names - a programming error, not a
    runtime condition, so callers fail loudly rather than sending a wrong email.
    """
    templates = _TEMPLATES[name]
    full_context = {"app_name": app_name, "app_url": app_url, **context}
    subject = templates["subject"].substitute(full_context)

    escaped = {
        key: (escape(value) if key in _ESCAPED_FIELDS else value)
        for key, value in full_context.items()
    }
    button_html = ""
    if button_url:
        button_html = _BUTTON.substitute(url=escape(button_url), label=escape(button_label))
    body_html = templates["html"].substitute({**escaped, "_button": button_html})
    html_body = _BASE_HTML.substitute({"body": body_html, "app_name": escape(app_name)})
    text_body = templates["text"].substitute(full_context)
    return subject, html_body, text_body
