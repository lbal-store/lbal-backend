from __future__ import annotations

import logging

import requests

from app.core.config import Settings
from app.core.errors import ApplicationError, ErrorCode


BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"
logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def send_verification_code(self, email: str, code: str) -> None:
        if not self.settings.brevo_api_key or not self.settings.email_from:
            logger.warning("Email credentials missing, skipping verification email for %s", email)
            return

        payload = {
            "sender": {
                "email": self.settings.email_from,
                "name": self.settings.email_from_name or self.settings.project_name,
            },
            "to": [{"email": email}],
            "subject": "Verify your email",
            "htmlContent": f"<p>Your verification code is <strong>{code}</strong>. It expires soon.</p>",
        }
        headers = {
            "api-key": self.settings.brevo_api_key,
            "accept": "application/json",
            "content-type": "application/json",
        }

        response = requests.post(BREVO_API_URL, json=payload, headers=headers, timeout=10)
        if response.status_code >= 400:
            logger.error("Failed to send verification email: %s - %s", response.status_code, response.text)
            raise ApplicationError(
                code=ErrorCode.HTTP_ERROR,
                message="Failed to send verification email.",
                status_code=502,
            )
