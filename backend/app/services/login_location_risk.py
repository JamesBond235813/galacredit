import math
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.user import User
from app.services.audit import log_user_event_async
from app.services.location import reverse_geocode


def _distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0088
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


async def apply_login_location(
    db: AsyncSession,
    user: User,
    *,
    latitude: Optional[float],
    longitude: Optional[float],
    accuracy: Optional[float],
    fallback_ip: Optional[str] = None,
) -> None:
    if latitude is None or longitude is None:
        raise ValueError("请先授权获取当前位置")

    now = datetime.now()
    lat = round(float(latitude), 7)
    lon = round(float(longitude), 7)
    previous_lat = user.location_latitude
    previous_lon = user.location_longitude
    previous_time = user.location_updated_at

    if previous_lat and previous_lon and previous_time:
        try:
            distance = _distance_km(float(previous_lat), float(previous_lon), lat, lon)
        except (TypeError, ValueError):
            distance = 0
        within_hours = now - previous_time <= timedelta(hours=settings.LOGIN_DISTANCE_RISK_HOURS)
        if within_hours and distance > float(settings.LOGIN_DISTANCE_RISK_KM):
            user.location_risk_blocked = True
            user.location_risk_at = now
            user.location_risk_reason = (
                f"登录位置异常：{settings.LOGIN_DISTANCE_RISK_HOURS}小时内距离上次登录约{distance:.1f}公里"
            )
            await log_user_event_async(
                db,
                user=user,
                event_type="LOGIN_LOCATION_RISK",
                title="登录位置异常拦截",
                detail=user.location_risk_reason,
            )
            raise ValueError("当前登录环境存在风险，请联系客服处理")

    location = await reverse_geocode(latitude=lat, longitude=lon)
    # GPS 行政区划必须来自经纬度解析；IP 归属地由访问日志单独记录，不能冒充 GPS 地址。
    user.location_latitude = str(lat)
    user.location_longitude = str(lon)
    user.location_accuracy = str(round(float(accuracy), 2)) if accuracy is not None else None
    user.location_source = "h5-login"
    user.location_address = location.get("address")
    user.location_province = location.get("province")
    user.location_city = location.get("city")
    user.location_district = location.get("district")
    user.location_street = location.get("street")
    user.location_updated_at = now
    user.location_risk_blocked = False
    user.location_risk_reason = None
    user.location_risk_at = None
    await log_user_event_async(
        db,
        user=user,
        event_type="LOGIN_LOCATION",
        title="登录定位授权",
        detail={
            "纬度": user.location_latitude,
            "经度": user.location_longitude,
            "省": user.location_province,
            "市": user.location_city,
            "区县": user.location_district,
            "地址": user.location_address,
        },
    )
