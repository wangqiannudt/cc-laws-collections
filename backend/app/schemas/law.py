"""法规 Pydantic 模型"""
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class LawBase(BaseModel):
    """法规基础模型"""

    title: str
    category: str
    publish_date: Optional[date] = None
    content: Optional[str] = None
    source_url: str
    file_url: Optional[str] = None
    file_path: Optional[str] = None
    file_content: Optional[str] = None
    is_internal: int = 0


class LawCreate(LawBase):
    """创建法规请求模型"""

    hash: Optional[str] = None


class LawResponse(LawBase):
    """法规响应模型"""

    id: int
    created_at: datetime
    updated_at: datetime
    hash: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class LawListResponse(BaseModel):
    """法规列表响应模型"""

    items: list[LawResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class CrawlLogResponse(BaseModel):
    """爬取日志响应模型"""

    id: int
    category: str
    status: str
    count: int
    error_message: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CrawlStatusResponse(BaseModel):
    """爬取状态响应模型"""

    is_running: bool
    last_crawl_time: Optional[datetime] = None
    last_crawl_status: Optional[str] = None
    last_crawl_count: Optional[int] = None


class CrawlStartResponse(BaseModel):
    """触发爬取响应模型"""

    message: str
    task_id: Optional[str] = None


class CategoryResponse(BaseModel):
    """分类响应模型"""

    name: str
    code: Optional[str] = None
