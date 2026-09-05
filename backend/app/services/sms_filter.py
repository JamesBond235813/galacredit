"""短信风控数据最小化过滤工具。"""

import re
from datetime import datetime, timedelta
from functools import lru_cache
from itertools import islice
from pathlib import Path
from typing import Any, Iterable, Optional

from app.core.config import settings


DEFAULT_KEYWORD_FILE = Path(__file__).resolve().parents[3] / "3rd_doc" / "sms_keys20260602.csv"
MAX_SMS_ROWS = 5000
MAX_SMS_ADDRESS_LENGTH = 120
MAX_SMS_BODY_LENGTH = 2000
TRUSTED_SMS_BRIDGES = frozenset({"galacreditnativerisk", "galacreditnative", "uniappnativerisk"})


def sms_collection_allowed(
    *,
    platform: Any,
    app_channel: Any,
    consent_sms: Any,
    native_bridge: Any = None,
    source: Any = None,
) -> bool:
    """判断短信采集是否满足渠道和平台边界。

    :param platform: 客户端平台标识
    :param app_channel: 发布渠道标识
    :param consent_sms: 用户是否单独同意短信复核
    :param native_bridge: 原生短信桥接标识
    :param source: 客户端数据来源标识
    :return: 仅可信原生桥、内部 Android 且用户同意时返回 True
    """
    bridge = str(native_bridge or "").strip().lower()
    data_source = str(source or "").strip().lower()
    return bool(
        consent_sms
        and str(platform or "").strip().lower() == "android"
        and str(app_channel or "").strip().lower() == "internal"
        and bridge in TRUSTED_SMS_BRIDGES
        and data_source not in {"h5", "web", "browser"}
    )


def _read_keyword_lines(path: Path) -> list[str]:
    """读取短信关键词文件并清理空白行。

    :param path: 关键词文件路径
    :return: 去重后的关键词列表
    """
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return []
    result: list[str] = []
    for line in content.splitlines():
        keyword = line.strip().lower()
        if keyword and keyword not in result:
            result.append(keyword)
    return result


def load_sms_keywords() -> list[str]:
    """加载 CSV 中的短信关键词。

    :return: 关键词列表；文件不可用时返回空列表
    """
    configured_path = getattr(settings, "SMS_RISK_KEYWORDS_FILE", "")
    path = Path(configured_path) if configured_path else DEFAULT_KEYWORD_FILE
    if not path.is_absolute():
        path = Path(__file__).resolve().parents[2] / path
    return _read_keyword_lines(path)


@lru_cache(maxsize=8)
def _compile_keyword_patterns_cached(keywords: tuple[str, ...]) -> tuple[tuple[str, re.Pattern[str]], ...]:
    """缓存关键词正则，避免每条短信重复编译相同规则。

    :param keywords: 已规范化且有序的关键词元组
    :return: 编译后的关键词与正则元组
    """
    patterns: list[tuple[str, re.Pattern[str]]] = []
    for keyword in keywords:
        escaped = re.escape(keyword)
        # 与 Android/UniApp 保持同一套 ASCII 单词边界；Python 的 \w 会把中文等 Unicode
        # 字符视为单词，导致设备端和服务端在跨语言短信上的命中结果不一致。
        if re.fullmatch(r"[a-z0-9][a-z0-9'-]*", keyword, flags=re.IGNORECASE):
            expression = rf"(?<![A-Za-z0-9_]){escaped}(?![A-Za-z0-9_])"
        else:
            expression = escaped
        patterns.append((keyword, re.compile(expression, re.IGNORECASE)))
    return tuple(patterns)


def _compile_keyword_patterns(keywords: Iterable[str]) -> tuple[tuple[str, re.Pattern[str]], ...]:
    """为关键词构造大小写不敏感的正则表达式。

    :param keywords: 原始关键词
    :return: 关键词及其正则表达式
    """
    normalized = tuple(str(keyword).strip().lower() for keyword in keywords if str(keyword).strip())
    return _compile_keyword_patterns_cached(normalized)


def _parse_sms_time(value: Any) -> Optional[datetime]:
    """解析短信时间字段。

    :param value: 时间原始值
    :return: 无时区的本地时间，无法解析时返回 None
    """
    if isinstance(value, datetime):
        return value.replace(tzinfo=None)
    if isinstance(value, (int, float)) and value > 0:
        timestamp = float(value)
        if timestamp < 100_000_000_000:
            timestamp *= 1000
        try:
            return datetime.fromtimestamp(timestamp / 1000).replace(tzinfo=None)
        except (OverflowError, OSError, ValueError):
            return None
    text = str(value or "").strip()
    if not text:
        return None
    normalized = text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        parsed = None
        for pattern in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y/%m/%d %H:%M:%S"):
            try:
                parsed = datetime.strptime(text, pattern)
                break
            except ValueError:
                continue
    if parsed is None:
        return None
    if parsed.tzinfo is not None:
        return parsed.astimezone().replace(tzinfo=None)
    return parsed


def match_sms_keywords(text: str, keywords: Optional[Iterable[str]] = None) -> list[str]:
    """返回短信正文命中的 CSV 关键词。

    :param text: 短信发送方、标题和正文拼接文本
    :param keywords: 可选关键词列表，未提供时读取项目配置
    :return: 按关键词文件顺序返回的命中项
    """
    normalized = " ".join(str(text or "").split())
    if not normalized:
        return []
    patterns = _compile_keyword_patterns(keywords if keywords is not None else load_sms_keywords())
    return [keyword for keyword, pattern in patterns if pattern.search(normalized)]


def filter_sms_messages(
    messages: Iterable[dict[str, Any]],
    *,
    now: Optional[datetime] = None,
    window_days: Optional[int] = None,
    keywords: Optional[Iterable[str]] = None,
) -> list[dict[str, Any]]:
    """仅保留近 90 天且命中关键词的短信，并移除非必要字段。

    :param messages: 设备读取到的短信列表
    :param now: 过滤基准时间，主要用于测试
    :param window_days: 时间窗口天数，默认使用配置值
    :param keywords: 可选关键词列表，未提供时读取 CSV
    :return: 可用于本地摘要和第三方上传的最小化短信列表
    """
    current_time = (now or datetime.now()).replace(tzinfo=None)
    days = int(window_days or getattr(settings, "SMS_RISK_WINDOW_DAYS", 90))
    cutoff = current_time - timedelta(days=days)
    patterns = _compile_keyword_patterns(keywords if keywords is not None else load_sms_keywords())
    result: list[dict[str, Any]] = []
    for item in islice(messages or [], MAX_SMS_ROWS):
        if not isinstance(item, dict):
            continue
        sms_time = _parse_sms_time(item.get("time") or item.get("timestamp") or item.get("date"))
        # 没有可验证时间的短信不上传，避免时间窗口失效。
        if sms_time is None or sms_time < cutoff or sms_time > current_time:
            continue
        sender = str(item.get("address") or item.get("sender") or "").strip()[:MAX_SMS_ADDRESS_LENGTH]
        body = str(item.get("body") or "").strip()[:MAX_SMS_BODY_LENGTH]
        title = str(item.get("title") or "").strip()[:MAX_SMS_ADDRESS_LENGTH]
        normalized = " ".join((sender, title, body))
        hits = [keyword for keyword, pattern in patterns if pattern.search(normalized)]
        if not hits:
            continue
        try:
            message_type = 2 if int(item.get("type") or 1) == 2 else 1
        except (TypeError, ValueError):
            message_type = 1
        try:
            read_flag = 1 if int(item.get("read") or 0) == 1 else 0
        except (TypeError, ValueError):
            read_flag = 0
        result.append(
            {
                "address": sender,
                "body": body,
                "type": message_type,
                "time": sms_time.strftime("%Y-%m-%d %H:%M:%S"),
                "read": read_flag,
                "keywords": hits,
            }
        )
    return result
