"""
Payment Monitor for Hermes Autonomous Services
Checks for incoming USDT/ETH payments on the business wallet.
Auto-creates API keys when payments are detected.

Runs via cron every 5 minutes, no personal info needed.
"""
import json, os, time, hashlib, sqlite3
from datetime import datetime
import httpx

# Config
BUSINESS_DIR = "/home/ali/business"
WALLET_PATH = f"{BUSINESS_DIR}/state/wallet.json"
API_KEYS_DB = f"{BUSINESS_DIR}/state/api_keys.db"
PAYMENTS_DB = f"{BUSINESS_DIR}/state/payments.db"

# USDT ERC-20 contract on Ethereum
USDT_CONTRACT = "0xdAC17F958D2ee523a2206206994597C13D831ec7"
RPC_URL = "https://eth-mainnet.public.blastapi.io"

# Pricing tiers (in USDT)
TIERS = {
    5: {"name": "Starter", "daily_limit": 10000, "description": "10K req/day"},
    20: {"name": "Pro", "daily_limit": 50000, "description": "50K req/day"},
    50: {"name": "Enterprise", "daily_limit": 200000, "description": "200K req/day"},
}

TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"


def init_db():
    conn = sqlite3.connect(PAYMENTS_DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            tx_hash TEXT PRIMARY KEY,
            from_addr TEXT NOT NULL,
            to_addr TEXT NOT NULL,
            amount DECIMAL NOT NULL,
            token TEXT DEFAULT 'USDT',
            block_number INTEGER,
            detected_at TEXT DEFAULT (datetime('now')),
            processed INTEGER DEFAULT 0,
            api_key TEXT
        )
    """)
    conn.commit()
    return conn


def get_wallet_address():
    with open(WALLET_PATH) as f:
        return json.load(f)["address"]


def rpc_call(method, params):
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": int(time.time())
    }
    resp = httpx.post(RPC_URL, json=payload, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    if "error" in data:
        raise Exception(f"RPC error: {data['error']}")
    return data["result"]


def check_balances(address):
    """Check both USDT and ETH balances."""
    # USDT balance
    padded_addr = address[2:].lower().zfill(64)
    data = f"0x70a08231{padded_addr}"
    result = rpc_call("eth_call", [{
        "to": USDT_CONTRACT,
        "data": data
    }, "latest"])
    usdt = int(result, 16) / 10**6 if result else 0

    # ETH balance
    result = rpc_call("eth_getBalance", [address, "latest"])
    eth = int(result, 16) / 10**18 if result else 0

    return usdt, eth


def get_new_transfers(address, from_block=None):
    """Get Transfer events to our address, iterating in small block ranges."""
    state_file = f"{BUSINESS_DIR}/state/last_checked_block.txt"

    if from_block is None:
        try:
            with open(state_file) as f:
                last = int(f.read().strip())
        except (FileNotFoundError, ValueError):
            latest_hex = rpc_call("eth_blockNumber", [])
            last = int(latest_hex, 16)

        from_block = last
        latest_hex = rpc_call("eth_blockNumber", [])
        latest = int(latest_hex, 16)
    else:
        latest_hex = rpc_call("eth_blockNumber", [])
        latest = int(latest_hex, 16)

    # Iterate in 8-block chunks to respect provider limits
    all_logs = []
    chunk_size = 8
    for start in range(from_block, min(latest, from_block + 200), chunk_size):
        end = min(start + chunk_size, latest)
        params = [{
            "fromBlock": hex(start),
            "toBlock": hex(end),
            "address": USDT_CONTRACT,
            "topics": [
                TRANSFER_TOPIC,
                None,
                "0x000000000000000000000000" + address[2:].lower()
            ]
        }]
        try:
            logs = rpc_call("eth_getLogs", params)
            if logs:
                all_logs.extend(logs)
        except Exception as e:
            print(f"  Skipping blocks {start}-{end}: {str(e)[:60]}")
            continue

        # Small delay to avoid rate limits
        time.sleep(0.1)

    transfers = []
    for log in all_logs:
        from_addr = "0x" + log["topics"][1][26:]
        to_addr = "0x" + log["topics"][2][26:]
        amount = int(log["data"], 16) / 10**6
        transfers.append({
            "tx_hash": log["transactionHash"],
            "from": from_addr,
            "to": to_addr,
            "amount": amount,
            "block": int(log["blockNumber"], 16)
        })

    # Save progress
    try:
        with open(state_file, "w") as f:
            f.write(str(latest))
    except Exception:
        pass

    return transfers


def run():
    wallet = get_wallet_address()
    conn = init_db()
    usdt_balance, eth_balance = check_balances(wallet)
    transfers = get_new_transfers(wallet)

    print(f"USDT: {usdt_balance:.2f} | ETH: {eth_balance:.6f} | New TXs: {len(transfers)}")

    for tx in transfers:
        existing = conn.execute(
            "SELECT * FROM payments WHERE tx_hash = ?", (tx["tx_hash"],)
        ).fetchone()

        if existing:
            continue

        conn.execute(
            "INSERT OR IGNORE INTO payments (tx_hash, from_addr, to_addr, amount, block_number) "
            "VALUES (?, ?, ?, ?, ?)",
            (tx["tx_hash"], tx["from"], tx["to"], tx["amount"], tx["block"])
        )
        conn.commit()

        print(f"  💰 {tx['amount']:.2f} USDT from {tx['from'][:12]}...")

        # Find best tier
        best = None
        for amt, tier in sorted(TIERS.items(), reverse=True):
            if tx["amount"] >= amt:
                best = tier
                break

        if not best:
            print(f"  ⚠️  Below minimum ($5), recording but no key issued")
            conn.execute("UPDATE payments SET processed=1 WHERE tx_hash=?", (tx["tx_hash"],))
            conn.commit()
            continue

        # Generate API key for sender
        api_key = hashlib.sha256(f"{tx['from']}:{tx['tx_hash']}:{time.time()}".encode()).hexdigest()[:24]

        kc = sqlite3.connect(API_KEYS_DB)
        kc.execute("INSERT OR IGNORE INTO api_keys (key, owner, daily_limit) VALUES (?, ?, ?)",
                    (api_key, tx["from"], best["daily_limit"]))
        kc.commit()
        kc.close()

        conn.execute("UPDATE payments SET processed=1, api_key=? WHERE tx_hash=?",
                     (api_key, tx["tx_hash"]))
        conn.commit()

        print(f"  ✅ {best['name']} activated ({best['daily_limit']}/day)")
        print(f"  🔑 {api_key}")

    # Count stats
    total_tx = conn.execute("SELECT COUNT(*) FROM payments").fetchone()[0]
    total_usdt = conn.execute("SELECT COALESCE(SUM(amount), 0) FROM payments").fetchone()[0]
    keys_conn = sqlite3.connect(API_KEYS_DB)
    active_keys = keys_conn.execute("SELECT COUNT(*) FROM api_keys WHERE active=1").fetchone()[0]
    keys_conn.close()
    conn.close()

    # Save last checked block
    try:
        if transfers:
            last_block = max(t["block"] for t in transfers)
            with open(f"{BUSINESS_DIR}/state/last_checked_block.txt", "w") as f:
                f.write(str(last_block))
    except Exception:
        pass

    print(f"\n📊 Total: {total_tx} payments | {total_usdt:.2f} USDT | {active_keys} active keys")


if __name__ == "__main__":
    print(f"=== Payment Monitor === {datetime.utcnow().isoformat()}")
    run()
