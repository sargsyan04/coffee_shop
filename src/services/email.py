from pathlib import Path

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from jinja2 import Environment, FileSystemLoader

from src.core import LOGO_PATH, settings

# ============================================================
# --> SMTP Configuration <--
# ============================================================

conf = ConnectionConfig(
    MAIL_USERNAME=settings.SMTP_USERNAME,
    MAIL_PASSWORD=settings.SMTP_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.SMTP_SERVER,
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=True,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
)

BASE_DIR = Path(__file__).resolve().parent.parent


# ============================================================
# --> Email Templates <--
# ============================================================

env = Environment(
    loader=FileSystemLoader(BASE_DIR / "templates")
)

def render_email(template_name: str, **context) -> str:
    template = env.get_template(template_name)
    return template.render(**context)


# ============================================================
# --> Email Sending <--
# ============================================================


async def send_verification_email(email_to: str, code: str):
    print(f"[DEV] Verification code for {email_to}: {code}")

    message = MessageSchema(
        subject="Coffee Shop — код подтверждения",
        recipients=[email_to],
        body=render_email(
            "verify_email.html",
            code=code,
        ),
        subtype=MessageType.html,
        attachments=[
            {
                "file": str(LOGO_PATH),
                "headers": {
                    "Content-ID": "<logo>",
                    "Content-Disposition": "inline",
                },
                "mime_type": "image",
                "mime_subtype": "png",
            }
        ],
    )

    fm = FastMail(conf)
    await fm.send_message(message)
