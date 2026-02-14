"""Pydantic models for AWS SES MCP Server responses."""

from pydantic import BaseModel, Field


class SendEmailResponse(BaseModel):
    """Response model for send_email tool."""

    success: bool = Field(..., description="Whether the email was sent successfully")
    message_id: str = Field(..., description="AWS SES message ID")
    timestamp: str = Field(..., description="ISO 8601 timestamp of when the email was sent")
    to: str = Field(..., description="Recipient email address")
    subject: str = Field(..., description="Email subject line")
