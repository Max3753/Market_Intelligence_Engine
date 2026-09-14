"""Application settings loaded from environment / .env file."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for the MIE backend.

    All values can be overridden via environment variables or a .env file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # --- Infrastructure ---
    DATABASE_URL: str = (
        "postgresql+asyncpg://mie:mie@localhost:5432/mie"
    )
    REDIS_URL: str = "redis://localhost:6379/0"

    # --- LLM ---
    LLM_BASE_URL: str = "https://api.deepseek.com/v1"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "deepseek-chat"

    # --- Crawling ---
    CRAWL_INTERVAL_MINUTES: int = 60
    # 周期调度器：false 时不按时间自动爬取（Human-in-the-Loop，手动触发）
    CRAWL_SCHEDULER_ENABLED: bool = False

    # --- Automation ---
    # 爬取成功后自动跑分析→聚类→评分流水线（false 则保持手动触发）
    # 默认关闭：分析消耗 LLM 额度，由人决定何时触发
    AUTO_PIPELINE: bool = False

    # --- Environment ---
    ENV: str = "development"

    # --- Github ---
    GITHUB_TOKEN: str = ""
    # 启动播种：设置后自动创建该仓库的 GitHub 数据源（如 "microsoft/vscode"）
    GITHUB_REPO: str = ""
    # 播种的 GitHub 源使用的代理；空字符串 = 直连（服务器无本地代理时用）
    GITHUB_PROXY: str = ""

    # --- Zhihu ---
    ZHIHU_COOKIES: str = ""

settings = Settings()
