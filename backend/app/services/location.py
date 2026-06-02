import json
from typing import Any, Dict, Iterable, Optional

import httpx

from app.core.config import settings
from app.core.request_logging import request_logger


def _empty_location() -> Dict[str, Optional[str]]:
    """生成空位置结构。

    :return: 统一的位置字段字典
    """
    return {
        "address": None,
        "province": None,
        "city": None,
        "district": None,
        "street": None,
    }


def _gps_unresolved_location() -> Dict[str, Optional[str]]:
    """生成 GPS 无法解析的位置结构。

    :return: 统一的位置字段字典
    """
    location = _empty_location()
    location["address"] = "GPS无法解析"
    return location


def _clean_text(value: Any) -> Optional[str]:
    """清理接口返回的文本字段。

    :param value: 原始字段值
    :return: 去空白后的文本，空值返回 None
    """
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _deep_pick(payload: Any, keys: Iterable[str]) -> Optional[str]:
    """从嵌套响应中按候选字段名提取第一个有效值。

    :param payload: 接口响应体
    :param keys: 候选字段名
    :return: 第一个非空文本
    """
    if isinstance(payload, dict):
        for key in keys:
            value = _clean_text(payload.get(key))
            if value:
                return value
        for value in payload.values():
            picked = _deep_pick(value, keys)
            if picked:
                return picked
    if isinstance(payload, list):
        for item in payload:
            picked = _deep_pick(item, keys)
            if picked:
                return picked
    return None


def _normalize_location_payload(payload: Any) -> Dict[str, Optional[str]]:
    """兼容不同供应商的反解析响应结构。

    :param payload: 供应商原始响应
    :return: 统一的位置字段字典
    """
    return {
        "address": _deep_pick(
            payload,
            ("address", "formatted_address", "formattedAddress", "display_name", "full_address", "fullAddress", "addr"),
        ),
        "province": _deep_pick(payload, ("province", "provinceName", "state", "principalSubdivision")),
        "city": _deep_pick(payload, ("city", "cityName", "town")),
        "district": _deep_pick(payload, ("district", "districtName", "county", "countyName", "adname", "region", "locality")),
        "street": _deep_pick(payload, ("street", "streetName", "road", "roadName", "township")),
    }


def _has_location_text(location: Dict[str, Optional[str]]) -> bool:
    """判断反解析结果是否包含可展示地址。

    :param location: 统一的位置字段字典
    :return: 是否至少存在一个行政地址字段
    """
    return any(
        location.get(key)
        for key in ("address", "province", "city", "district", "street")
    )


async def _reverse_geocode_aliyun_market(
    latitude: float,
    longitude: float,
    timeout_seconds: int,
) -> Dict[str, Optional[str]]:
    """通过阿里云云市场 AppCode 接口解析经纬度。

    :param latitude: 纬度
    :param longitude: 经度
    :param timeout_seconds: 请求超时时间，单位秒
    :return: 统一的位置字段字典
    """
    api_url = settings.LOCATION_GEOCODE_API_URL.strip()
    app_code = settings.LOCATION_GEOCODE_APP_CODE.strip()
    if not api_url or not app_code:
        request_logger.warning("aliyun market location geocode skipped: api url or app code is empty")
        return _empty_location()

    location_param = settings.LOCATION_GEOCODE_LOCATION_PARAM.strip()
    if location_param:
        # 该云市场接口要求 location=经度,纬度；单独配置可避免影响其他供应商。
        params = {location_param: f"{longitude:.7f},{latitude:.7f}"}
    else:
        params = {
            settings.LOCATION_GEOCODE_LAT_PARAM.strip() or "lat": f"{latitude:.7f}",
            settings.LOCATION_GEOCODE_LNG_PARAM.strip() or "lng": f"{longitude:.7f}",
        }
    coord_type_param = settings.LOCATION_GEOCODE_COORD_TYPE_PARAM.strip()
    coord_type = settings.LOCATION_GEOCODE_COORD_TYPE.strip()
    if coord_type_param and coord_type:
        params[coord_type_param] = coord_type

    try:
        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            method = settings.LOCATION_GEOCODE_HTTP_METHOD.strip().upper() or "GET"
            request_kwargs = {"params": params} if method == "GET" else {"data": params}
            resp = await client.request(
                method=method,
                url=api_url,
                **request_kwargs,
                headers={
                    "Authorization": f"APPCODE {app_code}",
                    "Accept": "application/json",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            )
            request_logger.info(
                "aliyun market location geocode request: "
                f"{method} {json.dumps(params, ensure_ascii=False)} ==> status:{getattr(resp, 'status_code', '')}"
            )
            resp.raise_for_status()
            payload = resp.json()
    except Exception as e:
        request_logger.error(f"request aliyun market location geocode failed: {e}")
        return _empty_location()

    return _normalize_location_payload(payload)


async def _reverse_geocode_nominatim(
    latitude: float,
    longitude: float,
    timeout_seconds: int,
) -> Dict[str, Optional[str]]:
    """使用 OpenStreetMap Nominatim 解析经纬度。

    :param latitude: 纬度
    :param longitude: 经度
    :param timeout_seconds: 请求超时时间，单位秒
    :return: 统一的位置字段字典
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
                f"request: {json.dumps(params, ensure_ascii=False)} ==>  response :{getattr(resp, 'text', '')}"
            )
            resp.raise_for_status()
            payload = resp.json()
    except Exception as e:
        request_logger.error(f'request nominatim failed: {e}')
        return _empty_location()

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


async def reverse_geocode(
    latitude: float,
    longitude: float,
    timeout_seconds: Optional[int] = None,
) -> Dict[str, Optional[str]]:
    """按配置解析 GPS 经纬度为行政地址。

    :param latitude: 纬度
    :param longitude: 经度
    :param timeout_seconds: 请求超时时间，未传时使用系统配置
    :return: 统一的位置字段字典
    """
    resolved_timeout = timeout_seconds or int(settings.LOCATION_GEOCODE_TIMEOUT_SECONDS)
    provider = settings.LOCATION_GEOCODE_PROVIDER.strip().lower()
    if provider in {"aliyun", "aliyun_market", "wechat_gps"}:
        # 新采购接口走阿里云云市场 AppCode 鉴权；旧 Nominatim 仅作为未配置时的默认实现。
        if settings.LOCATION_GEOCODE_API_URL.strip() and settings.LOCATION_GEOCODE_APP_CODE.strip():
            location = await _reverse_geocode_aliyun_market(latitude, longitude, resolved_timeout)
            if _has_location_text(location):
                return location
            request_logger.warning("aliyun market location geocode empty, mark gps unresolved")
            return _gps_unresolved_location()
        request_logger.warning("aliyun market location geocode skipped: api url or app code is empty")
        return _gps_unresolved_location()
    location = await _reverse_geocode_nominatim(latitude, longitude, resolved_timeout)
    if _has_location_text(location):
        return location
    request_logger.warning("nominatim location geocode empty, mark gps unresolved")
    return _gps_unresolved_location()
