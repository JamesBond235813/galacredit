from pathlib import Path
import os
import sys
from typing import Dict, List, Optional

from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]


def resolve_profile(argv: Optional[List[str]] = None, env: Optional[Dict[str, str]] = None) -> Optional[str]:
    """解析启动 profile，优先环境变量，其次命令行参数。

    :param argv: 命令行参数列表
    :param env: 环境变量映射
    :return: profile 字符串，未指定时返回 None
    """
    env_map = env or os.environ
    profile_from_env = (env_map.get("APP_PROFILE") or "").strip()
    if profile_from_env:
        return profile_from_env

    args = argv if argv is not None else sys.argv
    for arg in args[1:]:
        if arg.startswith("--profile="):
            profile = arg.split("=", 1)[1].strip()
            if profile:
                return profile
    return None


def resolve_env_file(base_dir: Path, profile: Optional[str]) -> Path:
    """根据 profile 解析环境文件路径。

    :param base_dir: 后端项目根目录
    :param profile: profile 名称
    :return: 环境文件路径
    """
    if profile:
        return base_dir / f".env.{profile}"
    return base_dir / ".env"


ACTIVE_PROFILE = resolve_profile()
ENV_FILE = resolve_env_file(BASE_DIR, ACTIVE_PROFILE)

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    PROJECT_NAME: str = "Credit Loan Platform API"
    API_V1_STR: str = "/api"
    APP_PORT: int = 8001
    
    # 数据库配置
    MYSQL_USER: str = "jhl"
    MYSQL_PASSWORD: str = ""
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: str = "3306"
    MYSQL_DATABASE: str = "credit_loan_db"
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    SQL_SLOW_MS: int = 200
    
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"

    @property
    def SQLALCHEMY_ASYNC_DATABASE_URI(self) -> str:
        return f"mysql+aiomysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
        
    # JWT 认证配置
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 7 days
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30
    SMS_CODE_MOCK_ENABLED: bool = False
    SMS_MOCK_CODE: str = "635147"
    SMS_PHONE_COOLDOWN_SECONDS: int = 60
    SMS_IP_RATE_LIMIT_PER_MINUTE: int = 10
    SMS_CODE_EXPIRE_SECONDS: int = 300
    PASSWORD_LOGIN_MAX_ATTEMPTS: int = 5
    PASSWORD_LOGIN_WINDOW_SECONDS: int = 300
    PASSWORD_LOGIN_FREEZE_SECONDS: int = 1800
    CHANNEL_LINK_PREFIX: str = "https://xxx.xx"
    CAPTCHA_SLIDER_TOLERANCE_PX: int = 5
    CAPTCHA_SLIDER_MIN_ELAPSED_MS: int = 1200
    CAPTCHA_SLIDER_CHALLENGE_EXPIRE_SECONDS: int = 180
    CAPTCHA_SLIDER_CHALLENGE_MAX_FAILS: int = 3
    CAPTCHA_SLIDER_TICKET_EXPIRE_SECONDS: int = 180
    CAPTCHA_SLIDER_MIN_WIDTH: int = 280
    CAPTCHA_SLIDER_MAX_WIDTH: int = 420
    CAPTCHA_SLIDER_HEIGHT: int = 160
    CAPTCHA_SLIDER_BLOCK_SIZE: int = 44

    # Panorama 风控配置
    RISK_REPORT_CACHE_DAYS: int = 14
    RISK_PANORAMA_ENABLED: bool = True
    RISK_PANORAMA_API_URL: str = ""
    RISK_PANORAMA_MERCHANT_NO: str = ""
    RISK_PANORAMA_ACCESS_KEY: str = ""
    RISK_PANORAMA_SECRET_KEY: str = ""
    RISK_PROBE_A_ENABLED: bool = False
    RISK_PROBE_C_ENABLED: bool = True
    RISK_LEGOU_ENABLED: bool = True
    RISK_LEGOU_BLACKLIST_URL: str = "https://api.legou1688.com/finance-center/v1/blacklist/match"
    RISK_LEGOU_TOKEN: str = ""
    RISK_LEGOU_TIMEOUT_SECONDS: int = 8

    # e签宝身份核验配置
    ESIGN_IDENTITY_ENABLED: bool = False
    ESIGN_IDENTITY_MOCK_ENABLED: bool = False
    ESIGN_APP_ID: str = ""
    ESIGN_APP_SECRET: str = ""
    ESIGN_OPENAPI_BASE_URL: str = "https://openapi.esign.cn"
    ESIGN_HTTP_TIMEOUT_SECONDS: int = 15
    ESIGN_FACE_CONFIDENCE_THRESHOLD: float = 70.0
    ESIGN_HTTP_PROXY: str=""

    USER_UPLOAD_DIR: str = "uploads"
    IP138_TOKEN: str = ""
    IP138_API_URL: str = "https://api.ip138.com/ipdata/"
    LOGIN_DISTANCE_RISK_HOURS: int = 4
    LOGIN_DISTANCE_RISK_KM: float = 30.0

    LOG_DIR: str = "logs"
    LOG_APP_FILE: str = "app.log"
    LOG_REQUEST_FILE: str = "request.log"
    LOG_RESPONSE_FILE: str = "response.log"
    LOG_ERROR_FILE: str = "error.log"
    LOG_FILE_NAME: str = "backend.log"
    LOG_FORMATTER: str = "[%(asctime)s.%(msecs)03d] [tid: %(tid)s] %(levelname)s in %(module)s: %(message)s"
    LOG_OUTPUT: str = "txt"
    LOG_RETENTION_DAYS: int = 90
    LOG_TZ: str = "Asia/Shanghai"
    LOG_LEVEL: str = "INFO"
    TID_HEADER_NAME: str = "X-Trace-Id"
    LOG_REQUEST_BODY_ENABLED: bool = False
    LOG_RESPONSE_BODY_ENABLED: bool = False

    #阿里云短信
    ALI_SMS_VC_TEMPLATE_CODE: str = ''
    ALI_SMS_ACC_KEY: str = ''
    ALI_SMS_ACC_SECRET: str = ''
    ALI_SMS_ENDPOINT: str = 'dysmsapi.aliyuncs.com'
    ALI_SMS_SIGN: str = ''

settings = Settings()
