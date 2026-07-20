"""
Hermes Autonomous Services - Web-to-Markdown API

Extracts clean markdown content from web URLs.
Designed for consumption by LLMs, AI agents, and automated systems.

Jafari Halal: Provides real utility (content extraction as a service),
no gambling, no interest, no gharar.
"""

import os
import json
import hashlib
import time
import sqlite3
import sys
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel
import trafilatura
import httpx
from api.activity import log, set_focus, set_goal, increment_stat, get_status

app = FastAPI(
    title="Hermes Web-to-Markdown API",
    description="Clean web content extraction for AI agents. Pass a URL, get clean markdown.",
    version="1.0.0",
    docs_url="/docs",
)

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "state", "api_keys.db")
RATE_LIMIT = 100  # requests per day free tier


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS api_keys (
            key TEXT PRIMARY KEY,
            owner TEXT NOT NULL,
            daily_limit INTEGER DEFAULT 100,
            created_at TEXT DEFAULT (datetime('now')),
            active INTEGER DEFAULT 1
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            api_key TEXT NOT NULL,
            endpoint TEXT NOT NULL,
            timestamp TEXT DEFAULT (datetime('now')),
            url TEXT,
            status TEXT DEFAULT 'success'
        )
    """)
    conn.commit()
    return conn


class ExtractRequest(BaseModel):
    url: str


@app.on_event("startup")
async def startup():
    get_db().close()


WALLET_PATH = os.path.join(os.path.dirname(__file__), "..", "state", "wallet.json")


def get_wallet_address():
    try:
        with open(WALLET_PATH) as f:
            return json.load(f)["address"]
    except (FileNotFoundError, json.JSONDecodeError):
        return "Wallet not configured"


@app.get("/")
async def root():
    return {
        "service": "Hermes Web-to-Markdown API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
        "pricing": "/billing",
        "usage": "POST /extract with { 'url': 'https://...' }",
        "halal": True,
        "jurisdiction": "Jafari Fiqh"
    }


@app.on_event("startup")
async def log_startup():
    log("system", "API server started")
    set_focus("Serving Web-to-Markdown API")
    set_goal("Get first API user or $1 revenue today")


@app.get("/status")
async def status():
    """Live activity feed - shows what Hermes is doing right now."""
    return get_status()


AGENT_JSON = os.path.join(os.path.dirname(__file__), "agent.json")


@app.get("/agent.json")
async def agent_discovery():
    """AI agent discovery file - lets other agents find this API."""
    if os.path.exists(AGENT_JSON):
        with open(AGENT_JSON) as f:
            return JSONResponse(json.load(f))
    return {"error": "Not found"}


@app.get("/robots.txt")
async def robots():
    return HTMLResponse("User-agent: *\nAllow: /\nSitemap: https://collectors-nearly-lyrics-press.trycloudflare.com/sitemap.xml\n")


@app.get("/sitemap.xml")
async def sitemap():
    return HTMLResponse("""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
<url><loc>https://collectors-nearly-lyrics-press.trycloudflare.com/</loc><priority>1.0</priority></url>
<url><loc>https://collectors-nearly-lyrics-press.trycloudflare.com/billing</loc><priority>0.9</priority></url>
<url><loc>https://collectors-nearly-lyrics-press.trycloudflare.com/dashboard</loc><priority>0.8</priority></url>
<url><loc>https://collectors-nearly-lyrics-press.trycloudflare.com/docs</loc><priority>0.7</priority></url>
</urlset>""")


@app.get("/billing")
async def billing():
    wallet = get_wallet_address()
    return {
        "accepted_tokens": ["USDT (ERC-20)", "ETH"],
        "network": "Ethereum",
        "wallet_address": wallet,
        "tiers": [
            {"name": "Free", "amount_usd": 0, "requests_per_day": 100, "description": "Test the API"},
            {"name": "Starter", "amount_usd": 5, "requests_per_day": 10000, "description": "For individuals and small projects"},
            {"name": "Pro", "amount_usd": 20, "requests_per_day": 50000, "description": "For growing applications"},
            {"name": "Enterprise", "amount_usd": 50, "requests_per_day": 200000, "description": "For high-volume needs"},
        ],
        "how_to_pay": [
            "1. Send USDT (ERC-20) or ETH to the wallet address above",
            "2. System detects payment automatically within 5 minutes",
            "3. A new API key is generated and linked to your sending wallet",
            "4. Use /claim?wallet=YOUR_SENDING_WALLET to retrieve your key"
        ],
        "halal": True,
        "jurisdiction": "Jafari Fiqh - No riba, no qimar, no gharar"
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.get("/claim")
async def claim_key(wallet: str):
    """After paying, use this to retrieve your API key by providing the wallet you sent from."""
    payments_db = os.path.join(os.path.dirname(__file__), "..", "state", "payments.db")
    if not os.path.exists(payments_db):
        return {"error": "No payments found", "wallet": wallet}

    conn = sqlite3.connect(payments_db)
    row = conn.execute(
        "SELECT api_key, amount FROM payments WHERE from_addr = ? AND api_key IS NOT NULL ORDER BY detected_at DESC LIMIT 1",
        (wallet,)
    ).fetchone()
    conn.close()

    if row:
        return {"success": True, "api_key": row[0], "amount_paid": row[1]}
    return {"error": "No key found for this wallet. Payment may still be processing (up to 5 min).", "wallet": wallet}


def verify_key(x_api_key: str = Header(...)):
    conn = get_db()
    row = conn.execute("SELECT * FROM api_keys WHERE key = ? AND active = 1", (x_api_key,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=401, detail="Invalid or inactive API key")

    # Check rate limit
    today = datetime.utcnow().strftime("%Y-%m-%d")
    conn = get_db()
    count = conn.execute(
        "SELECT COUNT(*) as cnt FROM usage WHERE api_key = ? AND date(timestamp) = ?",
        (x_api_key, today)
    ).fetchone()
    conn.close()

    if count and count["cnt"] >= row["daily_limit"]:
        raise HTTPException(status_code=429, detail=f"Rate limit exceeded ({row['daily_limit']}/day)")

    return x_api_key


@app.post("/extract")
async def extract(request: ExtractRequest, x_api_key: str = Header(None)):
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing X-API-Key header")

    # Verify key and rate limit
    conn = get_db()
    key_row = conn.execute("SELECT * FROM api_keys WHERE key = ? AND active = 1", (x_api_key,)).fetchone()
    if not key_row:
        conn.close()
        raise HTTPException(status_code=401, detail="Invalid or inactive API key")

    today = datetime.utcnow().strftime("%Y-%m-%d")
    count = conn.execute(
        "SELECT COUNT(*) as cnt FROM usage WHERE api_key = ? AND date(timestamp) = ?",
        (x_api_key, today)
    ).fetchone()
    if count and count["cnt"] >= key_row["daily_limit"]:
        conn.close()
        raise HTTPException(status_code=429, detail=f"Rate limit exceeded ({key_row['daily_limit']}/day)")

    # Validate URL
    url = request.url.strip()
    if not url.startswith(("http://", "https://")):
        conn.close()
        raise HTTPException(status_code=400, detail="URL must start with http:// or https://")

    # Extract content
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.get(url, headers={
                "User-Agent": "HermesBot/1.0 (compatible; content extractor)"
            })
            resp.raise_for_status()
            html = resp.text
    except httpx.HTTPStatusError as e:
        conn.execute("INSERT INTO usage (api_key, endpoint, url, status) VALUES (?, 'extract', ?, 'error')",
                     (x_api_key, url))
        conn.commit()
        conn.close()
        raise HTTPException(status_code=502, detail=f"Remote server error: {e.response.status_code}")
    except Exception as e:
        conn.execute("INSERT INTO usage (api_key, endpoint, url, status) VALUES (?, 'extract', ?, 'error')",
                     (x_api_key, url))
        conn.commit()
        conn.close()
        raise HTTPException(status_code=502, detail=f"Failed to fetch URL: {str(e)}")

    # Extract markdown
    try:
        result = trafilatura.extract(html, output_format="markdown", with_metadata=True)
        if not result:
            result = trafilatura.extract(html, output_format="markdown", no_fallback=False)
        title = trafilatura.extract(html, output_format="txt", include_comments=False)
        if title:
            title = title[:200]
    except Exception as e:
        conn.execute("INSERT INTO usage (api_key, endpoint, url, status) VALUES (?, 'extract', ?, 'error')",
                     (x_api_key, url))
        conn.commit()
        conn.close()
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")

    if not result:
        result = "*Could not extract content from this page.*"

    # Log success
    conn.execute("INSERT INTO usage (api_key, endpoint, url, status) VALUES (?, 'extract', ?, 'success')",
                 (x_api_key, url))
    conn.commit()
    conn.close()

    return {
        "success": True,
        "url": url,
        "content_length": len(result),
        "markdown": result
    }


@app.post("/admin/generate-key")
async def generate_key(request: Request):
    body = await request.json()
    owner = body.get("owner", "anonymous")
    daily_limit = body.get("daily_limit", RATE_LIMIT)

    key = hashlib.sha256(f"{owner}:{time.time()}:{os.urandom(16).hex()}".encode()).hexdigest()[:24]
    conn = get_db()
    conn.execute("INSERT INTO api_keys (key, owner, daily_limit) VALUES (?, ?, ?)",
                 (key, owner, daily_limit))
    conn.commit()
    conn.close()
    return {"api_key": key, "owner": owner, "daily_limit": daily_limit}


DASHBOARD_HTML = os.path.join(os.path.dirname(__file__), "dashboard.html")
TIER_NAMES = {10000: "Starter", 50000: "Pro", 200000: "Enterprise"}


@app.get("/dashboard")
async def dashboard():
    if os.path.exists(DASHBOARD_HTML):
        with open(DASHBOARD_HTML) as f:
            return HTMLResponse(f.read())
    return {"error": "Dashboard not found"}


@app.get("/dashboard-data")
async def dashboard_data():
    # Wallet balance
    usdt = eth = 0
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
        from scripts.payment_monitor import check_balances, get_wallet_address
        wallet = get_wallet_address()
        usdt, eth = check_balances(wallet)
    except Exception:
        pass

    # Payments
    payments_db = os.path.join(os.path.dirname(__file__), "..", "state", "payments.db")
    payments = []
    total_rev = 0.0
    pay_count = 0
    if os.path.exists(payments_db):
        conn = sqlite3.connect(payments_db)
        rows = conn.execute(
            "SELECT from_addr, amount, api_key, detected_at FROM payments WHERE processed=1 ORDER BY detected_at DESC LIMIT 20"
        ).fetchall()
        for r in rows:
            tier = TIER_NAMES.get(conn.execute(
                "SELECT daily_limit FROM api_keys WHERE key=?", (r[2],)
            ).fetchone()[0]) if r[2] and conn.execute(
                "SELECT daily_limit FROM api_keys WHERE key=?", (r[2],)
            ).fetchone() else "Starter"
            payments.append({"from": r[0], "amount": r[1], "api_key": r[2], "date": r[3], "tier": tier})
            total_rev += r[1]
            pay_count += 1
        conn.close()

    # API keys & usage
    conn = get_db()
    active = conn.execute("SELECT COUNT(*) FROM api_keys WHERE active=1").fetchone()[0]
    total_reqs = conn.execute("SELECT COUNT(*) FROM usage").fetchone()[0]
    conn.close()

    # Strategy from state
    strategy = "Building Web-to-Markdown API and payment system"
    state_path = os.path.join(os.path.dirname(__file__), "..", "state.json")
    if os.path.exists(state_path):
        with open(state_path) as f:
            s = json.load(f)
            strat = s.get("daily_strategy", {})
            if strat:
                last = list(strat.values())[-1]
                strategy = str(last)

    return {
        "wallet_usdt": usdt,
        "wallet_eth": eth,
        "total_revenue": total_rev,
        "payment_count": pay_count,
        "active_keys": active,
        "total_requests": total_reqs,
        "payments": payments[:10],
        "strategy": strategy
    }


@app.get("/admin/usage/{api_key}")
async def check_usage(api_key: str):
    conn = get_db()
    rows = conn.execute(
        "SELECT COUNT(*) as total, SUM(CASE WHEN status='success' THEN 1 ELSE 0 END) as success, "
        "SUM(CASE WHEN status='error' THEN 1 ELSE 0 END) as errors "
        "FROM usage WHERE api_key = ?", (api_key,)
    ).fetchone()
    conn.close()
    return dict(rows) if rows else {"total": 0, "success": 0, "errors": 0}
