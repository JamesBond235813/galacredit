import json
from typing import Dict, Optional

import httpx

from app.core.request_logging import request_logger


async def reverse_geocode(latitude: float, longitude: float, timeout_seconds: int = 8) -> Dict[str, Optional[str]]:
    """
    轻量反向地理编码（OpenStreetMap Nominatim）。
    失败时返回空结构，不影响主流程。
    """
    try:
        params = {
            "format": "jsonv2",
            "lat": f"{latitude:.7f}",
            "lon": f"{longitude:.7f}",
            "accept-language": "zh-CN",
            "addressdetails": 1,
        }
        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            resp = await client.get(
                url="https://nominatim.openstreetmap.org/reverse",
                params=params,
                headers={
                    "User-Agent": "credit-list-h5/1.0 (location reverse geocode)",
                    "Accept": "application/json",
                },
            )
            request_logger.info(
                f"request: {json.dumps(params)} ==>  response :{getattr(resp, 'text', '')}"
            )
            resp.raise_for_status()
            payload = resp.json()
    except Exception as e:
        request_logger.error(f'request nominatim failed: {e}')
        return {
            "address": None,
            "province": None,
            "city": None,
            "district": None,
            "street": None,
        }

    address_obj = payload.get("address") if isinstance(payload, dict) else {}
    address_obj = address_obj if isinstance(address_obj, dict) else {}

    province = (
        address_obj.get("state")
        or address_obj.get("province")
        or address_obj.get("region")
    )
    city = (
        address_obj.get("city")
        or address_obj.get("town")
        or address_obj.get("county")
    )
    district = (
        address_obj.get("county")
        or address_obj.get("city_district")
        or address_obj.get("district")
        or address_obj.get("suburb")
    )
    street = (
        address_obj.get("suburb")
        or address_obj.get("neighbourhood")
        or address_obj.get("road")
        or address_obj.get("village")
    )

    return {
        "address": str(payload.get("display_name") or "").strip() or None,
        "province": str(province or "").strip() or None,
        "city": str(city or "").strip() or None,
        "district": str(district or "").strip() or None,
        "street": str(street or "").strip() or None,
    }
