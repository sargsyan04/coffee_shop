from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from src.core import settings

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


async def send_verification_email(email_to: str, token: str):
    print(f"[DEV] Код подтверждения для {email_to}: {token}")
    # verification_url = f"http://localhost:8080/user/verify-email?token={token}"
    #
    # html_content = f"""
    # <html>
    #     <body>
    #         <h3>Welcome!</h3>
    #         <p>Please verify your email address by clicking the link below:</p>
    #         <p><a href="{verification_url}" style="padding: 10px; background-color: #007bff; color: white; text-decoration: none; border-radius: 5px;">Verify Email</a></p>
    #         <p>This link will expire in 24 hours.</p>
    #     </body>
    # </html>
    # """
    #
    # message = MessageSchema(
    #     subject="Verify Your Email Address",
    #     recipients=[email_to],
    #     body=html_content,
    #     subtype=MessageType.html
    # )
    #
    # fm = FastMail(conf)
    # await fm.send_message(message)
