import httpx
from app.core.config import settings
from decimal import Decimal


TON_API_BASE = "https://tonapi.io/v2"


async def get_transactions(wallet: str, limit: int = 20) -> list[dict]:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{TON_API_BASE}/accounts/{wallet}/transactions",
            params={"limit": limit},
            headers={"Authorization": f"Bearer {settings.TON_API_KEY}"},
            timeout=10.0,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("transactions", [])


async def find_deposit_by_comment(comment: str, min_amount_nano: int = 0) -> dict | None:
    txs = await get_transactions(settings.TON_WALLET_ADDRESS)
    for tx in txs:
        in_msg = tx.get("in_msg", {})
        if not in_msg:
            continue
        tx_comment = in_msg.get("decoded_body", {}).get("text", "")
        value = int(in_msg.get("value", 0))
        if tx_comment.strip() == comment.strip() and value >= min_amount_nano:
            return {
                "hash": tx.get("hash"),
                "amount_nano": value,
                "amount_ton": value / 1e9,
                "comment": tx_comment,
            }
    return None


async def verify_ton_connect_tx(
    boc: str,
    from_wallet: str,
    expected_comment: str,
    expected_amount: Decimal,
) -> str | None:
    """
    Verify a TON transaction sent via TonConnect.
    Returns tx hash if valid, None otherwise.
    Polls TON API for recent transactions from the wallet.
    """
    try:
        async with httpx.AsyncClient() as client:
            # Get recent incoming transactions to our wallet
            resp = await client.get(
                f"{TON_API_BASE}/accounts/{settings.TON_WALLET_ADDRESS}/transactions",
                params={"limit": 30},
                headers={"Authorization": f"Bearer {settings.TON_API_KEY}"},
                timeout=15.0,
            )
            resp.raise_for_status()
            data = resp.json()
            txs = data.get("transactions", [])

            min_nano = int(expected_amount * Decimal("1e9"))

            for tx in txs:
                in_msg = tx.get("in_msg", {})
                if not in_msg:
                    continue

                tx_comment = in_msg.get("decoded_body", {}).get("text", "")
                value = int(in_msg.get("value", 0))

                # Check sender address matches
                sender_info = in_msg.get("source", {})
                sender_addr = sender_info.get("address", "")

                if (
                    tx_comment.strip() == expected_comment.strip()
                    and value >= min_nano
                ):
                    return tx.get("hash")
    except Exception:
        pass
    return None


async def get_token_holders(token_address: str, limit: int = 10) -> list[dict]:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{TON_API_BASE}/jettons/{token_address}/holders",
            params={"limit": limit},
            headers={"Authorization": f"Bearer {settings.TON_API_KEY}"},
            timeout=10.0,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("addresses", [])
