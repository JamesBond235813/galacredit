from pathlib import Path

from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BASE_DIR / ".env"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    PROJECT_NAME: str = "Credit Loan Platform API"
    API_V1_STR: str = "/api"
    
    # 数据库配置
    MYSQL_USER: str = "jhl"
    MYSQL_PASSWORD: str = "cnptj*#SGYN^y5Fa"
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: str = "3306"
    MYSQL_DATABASE: str = "credit_loan_db"
    
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"

    @property
    def SQLALCHEMY_ASYNC_DATABASE_URI(self) -> str:
        return f"mysql+aiomysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
        
    # JWT 认证配置
    SECRET_KEY: str = "b47c8f6154b2d3550af3b9187a4128ef"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 7 days
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30
    SMS_CODE_MOCK_ENABLED: bool = True
    SMS_MOCK_CODE: str = "635147"
    SMS_PHONE_COOLDOWN_SECONDS: int = 60
    SMS_IP_RATE_LIMIT_PER_MINUTE: int = 10
    SMS_CODE_EXPIRE_SECONDS: int = 300
    PASSWORD_LOGIN_MAX_ATTEMPTS: int = 5
    PASSWORD_LOGIN_WINDOW_SECONDS: int = 300
    PASSWORD_LOGIN_FREEZE_SECONDS: int = 1800

    # Panorama 风控配置
    RISK_REPORT_CACHE_DAYS: int = 30
    RISK_PANORAMA_ENABLED: bool = True
    RISK_PANORAMA_API_URL: str = ""
    RISK_PANORAMA_MERCHANT_NO: str = ""
    RISK_PANORAMA_ACCESS_KEY: str = ""
    RISK_PANORAMA_SECRET_KEY: str = ""

    # e签宝身份核验配置
    ESIGN_IDENTITY_ENABLED: bool = False
    ESIGN_APP_ID: str = ""
    ESIGN_APP_SECRET: str = ""
    ESIGN_OPENAPI_BASE_URL: str = "https://openapi.esign.cn"
    ESIGN_HTTP_TIMEOUT_SECONDS: int = 15
    ESIGN_FACE_CONFIDENCE_THRESHOLD: float = 70.0
    ESIGN_HTTP_PROXY: str=""

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

settings = Settings()
