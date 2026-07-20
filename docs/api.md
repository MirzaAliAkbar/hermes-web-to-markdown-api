# Hermes Web-to-Markdown API

**Clean web content extraction for AI agents and automated systems.**

## Base URL

```
http://localhost:8777
```

*Note: Public URL will be provided once Cloudflare Tunnel is configured.*

## Authentication

All requests require an `X-API-Key` header.

```bash
curl -X POST http://localhost:8777/extract \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

## Endpoints

### `GET /`

Service info and status.

### `GET /health`

Health check. Returns `{"status": "healthy"}`.

### `POST /extract`

Extract clean markdown from a URL.

**Request:**
```json
{
  "url": "https://en.wikipedia.org/wiki/Artificial_intelligence"
}
```

**Response:**
```json
{
  "success": true,
  "url": "https://en.wikipedia.org/wiki/...",
  "content_length": 12345,
  "markdown": "# Title\n\nClean markdown content..."
}
```

**Errors:**
- `401` — Missing or invalid API key
- `429` — Rate limit exceeded
- `400` — Invalid URL
- `502` — Failed to fetch remote URL

### `POST /admin/generate-key`

Generate a new API key. Requires API key with admin privileges.

### `GET /admin/usage/{api_key}`

Check usage stats for a key.

## Rate Limits

- Free tier: **100 requests/day** per API key
- Contact for higher limits

## Agent Discovery

This API is designed for consumption by LLMs and autonomous agents.
It provides clean, structured text from web URLs — ideal for:
- Research and data gathering
- Content monitoring
- Training data preparation
- Web page analysis
