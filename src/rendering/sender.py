"""SMTP email sender for FormCoach Trend Engine briefs.

Sends rendered HTML emails via SMTP with proper error handling,
TLS support, and logging.
"""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class EmailSendError(Exception):
    """Raised when email delivery fails."""


def send_email(
    html: str,
    recipient: str,
    theme: str,
    email_config: Dict[str, Any],
    plain_text: Optional[str] = None,
) -> bool:
    """Send an HTML email via SMTP.

    Parameters
    ----------
    html : str
        Rendered HTML body.
    recipient : str
        Recipient email address.
    theme : str
        Theme name used to build the subject line.
    email_config : dict
        SMTP configuration with keys:

        - ``smtp_host`` (str): SMTP server hostname.
        - ``smtp_port`` (int): SMTP server port (default 587).
        - ``smtp_user`` (str): SMTP username / sender address.
        - ``smtp_pass`` (str): SMTP password or app-specific password.
        - ``from_name`` (str, optional): Display name for the sender.
        - ``use_tls`` (bool, optional): Whether to use STARTTLS
          (default ``True``).
    plain_text : str, optional
        Plain-text fallback body. If omitted, a minimal fallback is
        generated automatically.

    Returns
    -------
    bool
        ``True`` if the email was sent successfully.

    Raises
    ------
    EmailSendError
        If delivery fails after exhausting retries.
    ValueError
        If required configuration keys are missing.
    """
    # ── Validate config ────────────────────────────────────────────
    required_keys = ("smtp_host", "smtp_user", "smtp_pass")
    missing = [k for k in required_keys if not email_config.get(k)]
    if missing:
        raise ValueError(
            f"Missing required email_config keys: {', '.join(missing)}"
        )

    smtp_host: str = email_config["smtp_host"]
    smtp_port: int = int(email_config.get("smtp_port", 587))
    smtp_user: str = email_config["smtp_user"]
    smtp_pass: str = email_config["smtp_pass"]
    from_name: str = email_config.get("from_name", "Trend Engine")
    use_tls: bool = email_config.get("use_tls", True)

    # ── Build message ──────────────────────────────────────────────
    msg = MIMEMultipart("alternative")
    from datetime import datetime
    timestamp = datetime.now().strftime("%b %d, %Y %I:%M %p")
    msg["Subject"] = f"Your Weekly Data Feed: {theme} — {timestamp}"
    msg["From"] = f"{from_name} <{smtp_user}>"
    msg["To"] = recipient

    # Plain-text fallback
    if not plain_text:
        plain_text = (
            f"Weekly Trend Data Feed\n"
            f"Theme: {theme}\n\n"
            f"View this email in an HTML-capable client for the full brief."
        )

    msg.attach(MIMEText(plain_text, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))

    # ── Send ───────────────────────────────────────────────────────
    try:
        logger.info(
            "Connecting to SMTP %s:%d (TLS=%s)", smtp_host, smtp_port, use_tls
        )
        with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
            server.ehlo()
            if use_tls:
                server.starttls()
                server.ehlo()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, [recipient], msg.as_string())
        logger.info("Email sent successfully to %s", recipient)
        return True

    except smtplib.SMTPAuthenticationError as exc:
        logger.error("SMTP authentication failed: %s", exc)
        raise EmailSendError(
            f"SMTP authentication failed for {smtp_user}"
        ) from exc

    except smtplib.SMTPException as exc:
        logger.error("SMTP error sending to %s: %s", recipient, exc)
        raise EmailSendError(
            f"Failed to send email to {recipient}: {exc}"
        ) from exc

    except OSError as exc:
        logger.error("Network error connecting to %s:%d: %s", smtp_host, smtp_port, exc)
        raise EmailSendError(
            f"Network error connecting to {smtp_host}:{smtp_port}"
        ) from exc
