from fastapi import Request


def resolve_client_ip(request: Request, default_ip: str = "unknown") -> str:
    """解析请求来源IP，优先取代理头。

    :param request: FastAPI 请求对象
    :param default_ip: 取不到IP时的默认值
    :return: 客户端IP
    """
    forwarded_for = (request.headers.get("x-forwarded-for") or "").strip()
    if forwarded_for:
        first_ip = forwarded_for.split(",")[0].strip()
        if first_ip:
            return first_ip

    real_ip = (request.headers.get("x-real-ip") or "").strip()
    if real_ip:
        return real_ip

    if request.client and request.client.host:
        return request.client.host
    return default_ip
