"""Unit tests for the AWS SES MCP server."""

from unittest.mock import AsyncMock, patch

import pytest
from fastmcp import Client

from mcp_aws_ses.api_client import SESError
from mcp_aws_ses.api_models import SendEmailResponse
from mcp_aws_ses.server import mcp


@pytest.fixture
def mock_response() -> SendEmailResponse:
    """Create a mock send email response."""
    return SendEmailResponse(
        success=True,
        message_id="0102018f-abcd-1234-5678-abcdef123456",
        timestamp="2026-02-13T22:00:00+00:00",
        to="recipient@example.com",
        subject="Test Subject",
    )


@pytest.mark.asyncio
async def test_tools_list() -> None:
    """Test that tools are properly registered."""
    async with Client(mcp) as client:
        tools = await client.list_tools()

        assert len(tools) == 1
        tool_names = [tool.name for tool in tools]
        assert "send_email" in tool_names


@pytest.mark.asyncio
async def test_send_email_tool(mock_response: SendEmailResponse) -> None:
    """Test send_email tool sends an email."""
    with (
        patch("mcp_aws_ses.server.get_client") as mock_get_client,
        patch.dict("os.environ", {"AWS_SES_FROM_EMAIL": "sender@example.com"}),
    ):
        mock_client = AsyncMock()
        mock_client.send_email.return_value = mock_response
        mock_get_client.return_value = mock_client

        async with Client(mcp) as client:
            result = await client.call_tool(
                "send_email",
                {
                    "to": "recipient@example.com",
                    "subject": "Test Subject",
                    "body": "<p>Hello World</p>",
                },
            )

        mock_client.send_email.assert_called_once_with(
            to="recipient@example.com",
            subject="Test Subject",
            body="<p>Hello World</p>",
            from_email="sender@example.com",
            cc=None,
            bcc=None,
        )
        assert result is not None


@pytest.mark.asyncio
async def test_send_email_with_all_params(mock_response: SendEmailResponse) -> None:
    """Test send_email tool with all parameters."""
    with patch("mcp_aws_ses.server.get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.send_email.return_value = mock_response
        mock_get_client.return_value = mock_client

        async with Client(mcp) as client:
            await client.call_tool(
                "send_email",
                {
                    "to": "recipient@example.com",
                    "subject": "Test Subject",
                    "body": "<p>Hello</p>",
                    "from_email": "custom-sender@example.com",
                    "cc": "cc1@example.com, cc2@example.com",
                    "bcc": "bcc@example.com",
                },
            )

        mock_client.send_email.assert_called_once_with(
            to="recipient@example.com",
            subject="Test Subject",
            body="<p>Hello</p>",
            from_email="custom-sender@example.com",
            cc="cc1@example.com, cc2@example.com",
            bcc="bcc@example.com",
        )


def test_send_email_response_model() -> None:
    """Test SendEmailResponse model creation."""
    response = SendEmailResponse(
        success=True,
        message_id="test-message-id",
        timestamp="2026-02-13T22:00:00+00:00",
        to="recipient@example.com",
        subject="Test",
    )
    assert response.success is True
    assert response.message_id == "test-message-id"
    assert response.to == "recipient@example.com"
    assert response.subject == "Test"


@pytest.mark.asyncio
async def test_ses_error_is_reported_as_tool_error() -> None:
    """An SES failure reaches the caller as an error result with its message."""
    with patch("mcp_aws_ses.server.get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.send_email.side_effect = SESError("Email address is not verified")
        mock_get_client.return_value = mock_client

        async with Client(mcp) as client:
            result = await client.call_tool(
                "send_email",
                {"to": "a@example.com", "subject": "s", "body": "b", "from_email": "f@example.com"},
                raise_on_error=False,
            )

        assert result.is_error
        assert "AWS SES error: Email address is not verified" in result.content[0].text


@pytest.mark.asyncio
async def test_missing_credentials_are_reported_as_tool_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Without AWS credentials the caller learns which variable to set."""
    monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)
    monkeypatch.setattr("mcp_aws_ses.server._client", None)

    async with Client(mcp) as client:
        result = await client.call_tool(
            "send_email", {"to": "a@example.com", "subject": "s", "body": "b"}, raise_on_error=False
        )

    assert result.is_error
    assert "AWS_ACCESS_KEY_ID" in result.content[0].text


@pytest.mark.asyncio
async def test_missing_secret_key_is_reported_as_tool_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """With an access key ID but no secret, the caller learns which variable to set."""
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "AKIAEXAMPLE")
    monkeypatch.delenv("AWS_SECRET_ACCESS_KEY", raising=False)
    monkeypatch.setattr("mcp_aws_ses.server._client", None)

    async with Client(mcp) as client:
        result = await client.call_tool(
            "send_email", {"to": "a@example.com", "subject": "s", "body": "b"}, raise_on_error=False
        )

    assert result.is_error
    assert "AWS_SECRET_ACCESS_KEY environment variable is required" in result.content[0].text


@pytest.mark.asyncio
async def test_missing_sender_is_reported_as_tool_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """With no from_email and no AWS_SES_FROM_EMAIL, the caller learns how to give a sender."""
    monkeypatch.delenv("AWS_SES_FROM_EMAIL", raising=False)
    with patch("mcp_aws_ses.server.get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client

        async with Client(mcp) as client:
            result = await client.call_tool(
                "send_email",
                {"to": "a@example.com", "subject": "s", "body": "b"},
                raise_on_error=False,
            )

        assert result.is_error
        assert "Sender email is required" in result.content[0].text
        mock_client.send_email.assert_not_called()
