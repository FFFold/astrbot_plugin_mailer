from __future__ import annotations

from dataclasses import dataclass
from email.message import EmailMessage

import aiosmtplib


@dataclass(slots=True)
class SMTPSettings:
    host: str
    port: int
    username: str
    password: str
    use_tls: bool
    use_starttls: bool


async def send_message(
    settings: SMTPSettings,
    message: EmailMessage,
    sender: str,
    recipients: list[str],
) -> tuple[str, str]:
    response = await aiosmtplib.send(
        message,
        hostname=settings.host,
        port=settings.port,
        username=settings.username or None,
        password=settings.password or None,
        sender=sender,
        recipients=recipients,
        use_tls=settings.use_tls,
        start_tls=settings.use_starttls,
    )
    status_code, status_message = response
    decoded = (
        status_message.decode("utf-8", errors="replace")
        if isinstance(status_message, bytes)
        else str(status_message)
    )
    return str(status_code), decoded
