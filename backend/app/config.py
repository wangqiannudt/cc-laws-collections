"""应用配置"""
from pathlib import Path
from pydantic_settings import BaseSettings

# 项目根目录（config.py 在 backend/app/ 下，需要往上两级）
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"


class Settings(BaseSettings):
    """应用配置类"""

    # 应用
    app_name: str = "国家军队采购法规管理系统"
    app_version: str = "1.0.0"
    debug: bool = True

    # 数据库（使用绝对路径）
    database_url: str = f"sqlite:///{DATA_DIR / 'laws.db'}"

    # 爬虫配置
    crawler_base_url: str = "https://www.weain.mil.cn"
    crawler_request_delay: float = 1.5  # 请求间隔（秒）
    crawler_max_retries: int = 3
    crawler_timeout: int = 30

    # 附件存储（使用绝对路径）
    attachment_dir: Path = DATA_DIR / "attachments"

    # 定时任务
    scheduler_interval_hours: int = 48  # 每48小时执行一次

    # 分类映射（路径）
    categories: dict = {
        "国家颁布法规": "fgzc/gjbbfg",
        "军队颁布法规": "fgzc/jdbbfg",
        "联合颁布法规": "fgzc/gjhjdlhbbfg",
        "其他法规": "fgzc/qtfg",
        "内部法规": None,  # 内部法规不爬取
    }

    # 栏目 ID 映射（用于 API 调用）
    category_lmids: dict = {
        "国家颁布法规": "1151698121890283522",
        "军队颁布法规": "1151698324215119874",
        "联合颁布法规": "1151698442653876226",
        "其他法规": "1151698547024936962",
    }

    # API 配置
    crawler_api_url: str = "https://www.weain.mil.cn/api/regulations/search"
    crawler_page_size: int = 20  # API 每页数量
    crawler_detail_delay: float = 2.0  # 详情页请求间隔

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
