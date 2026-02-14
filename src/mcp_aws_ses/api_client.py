"""AWS SES API client."""

import asyncio
import os
import re
from datetime import UTC, datetime
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from .api_models import SendEmailResponse


class SESError(Exception):
    """AWS SES API error."""

    def __init__(
        self, message: str, code: str | None = None, details: dict[str, Any] | None = None
    ) -> None:
        self.message = message
        self.code = code
        self.details = details
        super().__init__(f"AWS SES Error: {message}")


def _strip_html_tags(html: str) -> str:
    """Strip HTML tags to produce a plain text fallback."""
    return re.sub(r"<[^>]+>", "", html)


def _parse_email_list(emails: str) -> list[str]:
    """Parse a comma-separated string of email addresses into a list."""
    return [e.strip() for e in emails.split(",") if e.strip()]


def _validate_email(email: str) -> bool:
    """Basic email format validation."""
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email))


class SESClient:
    """Client for AWS Simple Email Service."""

    def __init__(
        self,
        region: str | None = None,
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
    ) -> None:
        self._region = region or os.environ.get("AWS_SES_REGION", "us-east-1")
        self._access_key_id = access_key_id or os.environ.get("AWS_ACCESS_KEY_ID")
        self._secret_access_key = secret_access_key or os.environ.get("AWS_SECRET_ACCESS_KEY")

        if not self._access_key_id:
            raise ValueError(
                "AWS_ACCESS_KEY_ID is required. "
                "Provide it as a parameter or set the AWS_ACCESS_KEY_ID environment variable."
            )
        if not self._secret_access_key:
            raise ValueError(
                "AWS_SECRET_ACCESS_KEY is required. "
                "Provide it as a parameter or set the AWS_SECRET_ACCESS_KEY environment variable."
            )

        self._client: Any = boto3.client(
            "ses",
            region_name=self._region,
            aws_access_key_id=self._access_key_id,
            aws_secret_access_key=self._secret_access_key,
        )

    def _send_email_sync(
        self,
        to: str,
        subject: str,
        body: str,
        from_email: str,
        cc: str | None = None,
        bcc: str | None = None,
    ) -> SendEmailResponse:
        """Send an email synchronously using boto3.

        Args:
            to: Recipient email address.
            subject: Email subject line.
            body: Email body (HTML supported).
            from_email: Sender email address.
            cc: CC recipients, comma-separated.
            bcc: BCC recipients, comma-separated.

        Returns:
            SendEmailResponse with message ID and status.
        """
        if not _validate_email(to):
            raise SESError(f"Invalid recipient email address: {to}")
        if not _validate_email(from_email):
            raise SESError(f"Invalid sender email address: {from_email}")

        destination: dict[str, list[str]] = {
            "ToAddresses": [to],
        }
        if cc:
            cc_list = _parse_email_list(cc)
            for addr in cc_list:
                if not _validate_email(addr):
                    raise SESError(f"Invalid CC email address: {addr}")
            destination["CcAddresses"] = cc_list
        if bcc:
            bcc_list = _parse_email_list(bcc)
            for addr in bcc_list:
                if not _validate_email(addr):
                    raise SESError(f"Invalid BCC email address: {addr}")
            destination["BccAddresses"] = bcc_list

        plain_text = _strip_html_tags(body)

        try:
            response = self._client.send_email(
                Source=from_email,
                Destination=destination,
                Message={
                    "Subject": {
                        "Data": subject,
                        "Charset": "UTF-8",
                    },
                    "Body": {
                        "Text": {
                            "Data": plain_text,
                            "Charset": "UTF-8",
                        },
                        "Html": {
                            "Data": body,
                            "Charset": "UTF-8",
                        },
                    },
                },
            )

            return SendEmailResponse(
                success=True,
                message_id=response["MessageId"],
                timestamp=datetime.now(UTC).isoformat(),
                to=to,
                subject=subject,
            )
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]
            raise SESError(error_message, code=error_code, details=e.response["Error"]) from e
        except BotoCoreError as e:
            raise SESError(f"AWS SDK error: {e}") from e

    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        from_email: str,
        cc: str | None = None,
        bcc: str | None = None,
    ) -> SendEmailResponse:
        """Send an email asynchronously.

        Args:
            to: Recipient email address.
            subject: Email subject line.
            body: Email body (HTML supported).
            from_email: Sender email address.
            cc: CC recipients, comma-separated.
            bcc: BCC recipients, comma-separated.

        Returns:
            SendEmailResponse with message ID and status.
        """
        return await asyncio.to_thread(
            self._send_email_sync,
            to=to,
            subject=subject,
            body=body,
            from_email=from_email,
            cc=cc,
            bcc=bcc,
        )

    async def test_connection(self) -> dict[str, Any]:
        """Test the AWS SES connection by verifying credentials.

        Returns:
            Dict with success status and optional error.
        """
        try:
            result: Any = await asyncio.to_thread(
                self._client.get_send_quota,
            )
            return {
                "success": True,
                "max_24_hour_send": result.get("Max24HourSend", 0),
                "sent_last_24_hours": result.get("SentLast24Hours", 0),
            }
        except (ClientError, BotoCoreError) as e:
            return {"success": False, "error": str(e)}
