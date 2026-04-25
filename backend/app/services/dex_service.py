import httpx
from app.core.config import settings

# Официальный актуальный endpoint согласно docs.dexscreener.com/api/reference
# GET /token-pairs/v1/{chainId}/{tokenAddress}
DEX_API_V1 = "https://api.dexscreener.com/token-pairs/v1"


async def get_pair_data() -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{DEX_API_V1}/ton/{settings.DF_TOKEN_ADDRESS}",
            timeout=10.0,
        )
        resp.raise_for_status()
        # Endpoint возвращает список пар напрямую (не обёрнут в {"pairs": [...]})
        pairs = resp.json()
        if not pairs or not isinstance(pairs, list):
            return {}
        # Берём пару с наибольшей ликвидностью — основная пара
        pairs_sorted = sorted(
            pairs,
            key=lambda p: float(p.get("liquidity", {}).get("usd") or 0),
            reverse=True,
        )
        return pairs_sorted[0]


async def get_token_stats() -> dict:
    pair = await get_pair_data()
    if not pair:
        return {}

    return {
        "price_usd": pair.get("priceUsd"),
        "price_native": pair.get("priceNative"),
        "liquidity_usd": pair.get("liquidity", {}).get("usd"),
        "volume_24h": pair.get("volume", {}).get("h24"),
        "price_change_1h": pair.get("priceChange", {}).get("h1"),
        "price_change_6h": pair.get("priceChange", {}).get("h6"),
        "price_change_24h": pair.get("priceChange", {}).get("h24"),
        "txns_24h_buys": pair.get("txns", {}).get("h24", {}).get("buys"),
        "txns_24h_sells": pair.get("txns", {}).get("h24", {}).get("sells"),
        "pair_url": pair.get("url"),
        "dex_id": pair.get("dexId"),
        "fdv": pair.get("fdv"),
        "market_cap": pair.get("marketCap"),
    }