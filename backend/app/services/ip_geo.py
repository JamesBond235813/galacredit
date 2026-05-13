from typing import Any, Dict

import httpx

from app.core.config import settings


def _empty_geo() -> Dict[str, str]:
    return {"country": "", "province": "", "city": "", "district": "", "detail": ""}


async def resolve_ip_geo(ip: str) -> Dict[str, str]:
    if not ip or ip in {"unknown", "127.0.0.1", "::1", "localhost"} or not settings.IP138_TOKEN:
        return _empty_geo()
    try:
        async with httpx.AsyncClient(timeout=2) as client:
            resp = await client.get(
                settings.IP138_API_URL,
                params={"ip": ip, "datatype": "json"},
                headers={"token": settings.IP138_TOKEN},
            )
            resp.raise_for_status()
            payload: Dict[str, Any] = resp.json()
    except Exception:
        return _empty_geo()

    data = payload.get("data") if isinstance(payload.get("data"), list) else []
    parts = [str(item or "").strip() for item in data]
    return {
        "country": parts[0] if len(parts) > 0 else "",
        "province": parts[1] if len(parts) > 1 else "",
        "city": parts[2] if len(parts) > 2 else "",
        "district": parts[3] if len(parts) > 3 else "",
        "detail": " / ".join([item for item in parts if item]),
    }
