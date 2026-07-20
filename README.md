# Hermes Web-to-Markdown API

**Clean web content extraction for AI agents and automated systems.**

Pass any URL → get clean markdown. Built for LLMs, autonomous agents, and developers who need reliable web-to-text conversion.

## Features

- **Single endpoint** — `POST /extract` with a URL, get clean markdown
- **Fast** — Powered by trafilatura, extracts in seconds
- **Agent-friendly** — JSON response, designed for programmatic use
- **Halal** — Jafari Fiqh compliant. No riba, no qimar, no gharar.

## Quick Start

```bash
curl -X POST https://hermes-api.trycloudflare.com/extract \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://en.wikipedia.org/wiki/Artificial_intelligence"}'
```

**Response:**
```json
{
  "success": true,
  "url": "https://...",
  "content_length": 12345,
  "markdown": "# Title\n\nClean content..."
}
```

## Pricing

| Tier | Price | Requests/Day |
|------|-------|-------------|
| Free | $0 | 100 |
| Starter | $5 USDT | 10,000 |
| Pro | $20 USDT | 50,000 |
| Enterprise | $50 USDT | 200,000 |

**Payment:** Send USDT (ERC-20) or ETH to the wallet address shown at `/billing`. System auto-detects payment and issues your API key within 5 minutes.

## Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | Service info |
| `GET /billing` | Pricing and wallet address |
| `GET /dashboard` | Business dashboard |
| `POST /extract` | Extract markdown from URL |
| `GET /claim?wallet=0x...` | Retrieve API key after payment |

## Technical Details

- **Server:** FastAPI + uvicorn
- **Extraction:** trafilatura (markdown output)
- **Auth:** API key via `X-API-Key` header
- **Rate limit:** Configurable per key
- **Blockchain:** Ethereum ERC-20 USDT payments
- **Host:** Self-hosted, 24/7 operation

## Self-Hosted

This API runs on a Lenovo ThinkPad (i5-6200U, 8GB) with Cloudflare Tunnel for public access. No cloud vendor, no KYC required.

---

*Part of [Hermes Autonomous Services](https://github.com/MirzaAliAkbar/hermes-web-to-markdown-api)*
