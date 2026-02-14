# AWS SES MCP Server

[![mpak](https://img.shields.io/badge/mpak-registry-blue)](https://mpak.dev/packages/@nimblebraininc/aws-ses?utm_source=github&utm_medium=readme&utm_campaign=mcp-aws-ses)
[![NimbleBrain](https://img.shields.io/badge/NimbleBrain-nimblebrain.ai-purple)](https://nimblebrain.ai?utm_source=github&utm_medium=readme&utm_campaign=mcp-aws-ses)
[![Discord](https://img.shields.io/badge/Discord-community-5865F2)](https://nimblebrain.ai/discord?utm_source=github&utm_medium=readme&utm_campaign=mcp-aws-ses)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A [Model Context Protocol](https://modelcontextprotocol.io) (MCP) server that sends emails using [AWS Simple Email Service (SES)](https://aws.amazon.com/ses/). Send HTML or plain text emails with CC/BCC support from any MCP client.

**[View on mpak registry](https://mpak.dev/packages/@nimblebraininc/aws-ses?utm_source=github&utm_medium=readme&utm_campaign=mcp-aws-ses)** | **Built by [NimbleBrain](https://nimblebrain.ai?utm_source=github&utm_medium=readme&utm_campaign=mcp-aws-ses)**

## Install

Install with [mpak](https://mpak.dev?utm_source=github&utm_medium=readme&utm_campaign=mcp-aws-ses):

```bash
mpak install @nimblebraininc/aws-ses
```

### Configuration

You need an AWS account with SES enabled, a verified sender email address, and IAM credentials with SES permissions.

```bash
mpak config set @nimblebraininc/aws-ses aws_access_key_id YOUR_ACCESS_KEY
mpak config set @nimblebraininc/aws-ses aws_secret_access_key YOUR_SECRET_KEY
mpak config set @nimblebraininc/aws-ses from_email your-verified@email.com
```

Optionally set the region (defaults to `us-east-1`):

```bash
mpak config set @nimblebraininc/aws-ses aws_region us-west-2
```

### Claude Code

```bash
claude mcp add aws-ses -- mpak run @nimblebraininc/aws-ses
```

### Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "aws-ses": {
      "command": "mpak",
      "args": ["run", "@nimblebraininc/aws-ses"]
    }
  }
}
```

See the [mpak registry page](https://mpak.dev/packages/@nimblebraininc/aws-ses?utm_source=github&utm_medium=readme&utm_campaign=mcp-aws-ses) for full install options.

## Tools

### send_email

Send an email using AWS SES. Supports HTML bodies with automatic plain text fallback.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `to` | `string` | Yes | Recipient email address |
| `subject` | `string` | Yes | Email subject line |
| `body` | `string` | Yes | Email body (HTML supported) |
| `from_email` | `string` | No | Sender email (defaults to `AWS_SES_FROM_EMAIL`) |
| `cc` | `string` | No | CC recipients, comma-separated |
| `bcc` | `string` | No | BCC recipients, comma-separated |

**Example call:**

```json
{
  "name": "send_email",
  "arguments": {
    "to": "recipient@example.com",
    "subject": "Weekly Report",
    "body": "<h1>Weekly Report</h1><p>Here are this week's highlights...</p>"
  }
}
```

**Example response:**

```json
{
  "success": true,
  "message_id": "0102018f-1234-5678-abcd-example",
  "timestamp": "2026-02-13T10:00:00+00:00",
  "to": "recipient@example.com",
  "subject": "Weekly Report"
}
```

## Quick Start

### Local Development

```bash
git clone https://github.com/NimbleBrainInc/mcp-aws-ses.git
cd mcp-aws-ses

# Install dependencies
uv sync

# Set credentials
cp .env.example .env
# Edit .env with your AWS credentials

# Run the server (stdio mode)
uv run python -m mcp_aws_ses.server
```

The server supports HTTP transport with:
- Health check: `GET /health`
- MCP endpoint: `POST /mcp`

## Development

```bash
# Install with dev dependencies
uv sync --group dev

# Run all checks (format, lint, typecheck, unit tests)
make check

# Run unit tests
make test

# Run with coverage
make test-cov
```

## About

AWS SES MCP Server is published on the [mpak registry](https://mpak.dev?utm_source=github&utm_medium=readme&utm_campaign=mcp-aws-ses) and built by [NimbleBrain](https://nimblebrain.ai?utm_source=github&utm_medium=readme&utm_campaign=mcp-aws-ses). mpak is an open registry for [Model Context Protocol](https://modelcontextprotocol.io) servers.

- [mpak registry](https://mpak.dev?utm_source=github&utm_medium=readme&utm_campaign=mcp-aws-ses)
- [NimbleBrain](https://nimblebrain.ai?utm_source=github&utm_medium=readme&utm_campaign=mcp-aws-ses)
- [MCP specification](https://modelcontextprotocol.io)
- [Discord community](https://nimblebrain.ai/discord?utm_source=github&utm_medium=readme&utm_campaign=mcp-aws-ses)

## License

MIT
