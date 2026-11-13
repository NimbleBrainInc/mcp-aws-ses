"""AWS SES MCP Server - FastMCP Implementation."""

import logging
import os
import sys

from dotenv import load_dotenv
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from starlette.requests import Request
from starlette.responses import JSONResponse

from .api_client import SESClient, SESError
from .api_models import SendEmailResponse

# Diagnostics go to stderr (stdout is reserved for JSON-RPC), never to the client: MCP's
# logging capability is deprecated as of the 2026-07-28 protocol (SEP-2577). A failure the
# caller must see is raised as a ToolError.
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("mcp_aws_ses")

load_dotenv()

mcp = FastMCP("AWS SES")

_client: SESClient | None = None


def get_client() -> SESClient:
    """Get or create the SES client.

    Raises:
        ToolError: when AWS credentials are not set, so the caller sees why the tool failed.
    """
    global _client
    if _client is None:
        access_key_id = os.environ.get("AWS_ACCESS_KEY_ID")
        secret_access_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
        region = os.environ.get("AWS_SES_REGION", "us-east-1")
        if not access_key_id:
            logger.error("AWS_ACCESS_KEY_ID is not set")
            raise ToolError("AWS_ACCESS_KEY_ID environment variable is required")
        if not secret_access_key:
            logger.error("AWS_SECRET_ACCESS_KEY is not set")
            raise ToolError("AWS_SECRET_ACCESS_KEY environment variable is required")
        _client = SESClient(
            region=region,
            access_key_id=access_key_id,
            secret_access_key=secret_access_key,
        )
    return _client


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    """Health check endpoint for monitoring."""
    return JSONResponse({"status": "healthy", "service": "mcp-aws-ses"})


@mcp.tool()
async def send_email(
    to: str,
    subject: str,
    body: str,
    from_email: str | None = None,
    cc: str | None = None,
    bcc: str | None = None,
) -> SendEmailResponse:
    """Send an email using AWS SES.

    Args:
        to: Recipient email address.
        subject: Email subject line.
        body: Email body (HTML supported).
        from_email: Sender email address. Falls back to AWS_SES_FROM_EMAIL env var.
        cc: CC recipients, comma-separated.
        bcc: BCC recipients, comma-separated.

    Returns:
        Send result with message ID and timestamp.
    """
    client = get_client()

    sender = from_email or os.environ.get("AWS_SES_FROM_EMAIL")
    if not sender:
        raise ToolError(
            "Sender email is required. Provide from_email parameter "
            "or set the AWS_SES_FROM_EMAIL environment variable."
        )

    try:
        return await client.send_email(
            to=to,
            subject=subject,
            body=body,
            from_email=sender,
            cc=cc,
            bcc=bcc,
        )
    except SESError as e:
        logger.warning("send_email failed: %s", e.message)
        raise ToolError(f"AWS SES error: {e.message}") from e


# ASGI entrypoint (nimbletools-core container deployment)
app = mcp.http_app()

# Stdio entrypoint (mpak / Claude Desktop)
if __name__ == "__main__":
    logger.info("Running in stdio mode")
    mcp.run()
