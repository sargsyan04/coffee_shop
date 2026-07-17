from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType

from src.core import settings, LOGO_PATH

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
    VALIDATE_CERTS=True
)


# ============================================================
# --> Email Templates <--
# ============================================================

def build_verification_email_html(code: str) -> str:
    return f"""
    <div style="margin:0; padding:0; background-color:#faf6f0; font-family: Arial, Helvetica, sans-serif;">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#faf6f0; padding:40px 0;">
            <tr>
                <td align="center">
                    <table role="presentation" width="480" cellpadding="0" cellspacing="0"
                           style="background-color:#ffffff; border-radius:16px; overflow:hidden; box-shadow:0 4px 16px rgba(74,47,28,0.08);">

                        <!-- Header -->
                        <tr>
                            <td style="background: linear-gradient(135deg, #a97c50, #4a2f1c); padding:32px; text-align:center;">
                                <img src="cid:logo" alt="Coffee Shop" width="48" height="48" style="display:block; margin:0 auto;">
                                <h1 style="color:#f7f1ea; font-size:22px; margin:8px 0 0; font-weight:600;">
                                    Coffee Shop
                                </h1>
                            </td>
                        </tr>

                        <!-- Body -->
                        <tr>
                            <td style="padding:40px 36px; text-align:center;">
                                <p style="color:#2b2018; font-size:16px; margin:0 0 8px; font-weight:600;">
                                    Подтвердите вашу почту
                                </p>
                                <p style="color:#7a5c3e; font-size:14px; margin:0 0 28px; line-height:1.5;">
                                    Введите этот код в приложении, чтобы завершить подтверждение.
                                    Код действителен в течение 15 минут.
                                </p>

                                <div style="background-color:#f2ebe0; border-radius:10px; padding:20px; margin-bottom:28px;">
                                    <span style="font-size:32px; font-weight:700; letter-spacing:8px; color:#4a2f1c;">
                                        {code}
                                    </span>
                                </div>

                                <p style="color:#9a8a76; font-size:12px; margin:0;">
                                    Если вы не запрашивали этот код — просто проигнорируйте это письмо.
                                </p>
                            </td>
                        </tr>

                        <!-- Footer -->
                        <tr>
                            <td style="background-color:#f2ebe0; padding:20px; text-align:center;">
                                <p style="color:#9a8a76; font-size:11px; margin:0;">
                                    © Coffee Shop. Это автоматическое письмо, отвечать на него не нужно.
                                </p>
                            </td>
                        </tr>

                    </table>
                </td>
            </tr>
        </table>
    </div>
    """


# ============================================================
# --> Email Sending <--
# ============================================================

async def send_verification_email(email_to: str, code: str):
    print(f"[DEV] Verification code for {email_to}: {code}")

    message = MessageSchema(
        subject="Coffee Shop — код подтверждения",
        recipients=[email_to],
        body=build_verification_email_html(code),
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