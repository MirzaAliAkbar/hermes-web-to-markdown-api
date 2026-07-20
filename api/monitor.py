"""
Hermes Website Change Monitor — Second Product
Monitors webpages for changes and triggers webhooks.
"""
import os, json, hashlib, sqlite3, datetime, time
import httpx
import trafilatura

MONITOR_DB = os.path.join(os.path.dirname(__file__), "..", "state", "monitors.db")


def get_db():
    conn = sqlite3.connect(MONITOR_DB)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS monitors (
            id TEXT PRIMARY KEY,
            api_key TEXT NOT NULL,
            url TEXT NOT NULL,
            interval_minutes INTEGER DEFAULT 60,
            webhook_url TEXT DEFAULT '',
            last_content_hash TEXT DEFAULT '',
            last_checked TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now')),
            active INTEGER DEFAULT 1,
            change_count INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    return conn


def hash_content(html):
    """Hash the extracted content to detect changes."""
    text = trafilatura.extract(html, output_format="txt", include_comments=False)
    if text:
        return hashlib.sha256(text.encode()).hexdigest()[:16]
    return hashlib.sha256(html.encode()).hexdigest()[:16]


async def check_monitor(monitor_id):
    """Check a single monitored URL for changes."""
    conn = get_db()
    row = conn.execute("SELECT * FROM monitors WHERE id = ? AND active = 1", (monitor_id,)).fetchone()
    if not row:
        conn.close()
        return {"error": "Monitor not found"}

    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.get(row["url"], headers={"User-Agent": "HermesMonitor/1.0"})
            resp.raise_for_status()
            html = resp.text
    except Exception as e:
        conn.execute("UPDATE monitors SET last_checked = datetime('now') WHERE id = ?", (monitor_id,))
        conn.commit()
        conn.close()
        return {"error": f"Fetch failed: {e}"}

    new_hash = hash_content(html)
    old_hash = row["last_content_hash"]

    changed = old_hash and new_hash != old_hash

    conn.execute(
        "UPDATE monitors SET last_content_hash = ?, last_checked = datetime('now'), change_count = change_count + ? WHERE id = ?",
        (new_hash, 1 if changed else 0, monitor_id)
    )
    conn.commit()

    result = {
        "monitor_id": monitor_id,
        "url": row["url"],
        "changed": changed,
        "old_hash": old_hash,
        "new_hash": new_hash,
    }

    # Fire webhook if changed and webhook is configured
    if changed and row["webhook_url"]:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                await client.post(row["webhook_url"], json=result)
        except:
            pass

    conn.close()
    return result


def check_all_due():
    """Check all monitors that are due for checking. Called by cron."""
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM monitors WHERE active = 1 AND (last_checked = '' OR "
        "datetime('now') > datetime(last_checked, '+' || interval_minutes || ' minutes'))"
    ).fetchall()
    conn.close()

    results = []
    for row in rows:
        import asyncio
        result = asyncio.run(check_monitor(row["id"]))
        results.append(result)
        time.sleep(1)  # Rate limit

    return results
