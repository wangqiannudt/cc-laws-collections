"""法规相关 API 路由"""
import math
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy import desc, or_
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.law import Law, CrawlLog, create_crawl_log
from app.schemas.law import (
    LawListResponse,
    LawResponse,
    CrawlLogResponse,
    CrawlStatusResponse,
    CrawlStartResponse,
    CategoryResponse,
)

router = APIRouter(prefix="/api/laws", tags=["laws"])


@router.get("", response_model=LawListResponse)
def get_laws(
    category: Optional[str] = Query(None, description="分类筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    sort: str = Query("-publish_date", description="排序字段，-表示降序"),
    db: Session = Depends(get_db),
):
    """获取法规列表"""
    query = db.query(Law)

    # 分类筛选
    if category:
        query = query.filter(Law.category == category)

    # 排序
    sort_field = sort.lstrip("-")
    if sort_field == "publish_date":
        order_col = Law.publish_date
    elif sort_field == "created_at":
        order_col = Law.created_at
    elif sort_field == "title":
        order_col = Law.title
    else:
        order_col = Law.publish_date

    if sort.startswith("-"):
        query = query.order_by(desc(order_col))
    else:
        query = query.order_by(order_col)

    # 总数
    total = query.count()

    # 分页
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()

    return LawListResponse(
        items=[LawResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/search", response_model=LawListResponse)
def search_laws(
    keyword: str = Query(..., min_length=1, description="搜索关键词"),
    category: Optional[str] = Query(None, description="分类筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
):
    """关键词搜索法规"""
    query = db.query(Law)

    # 关键词搜索（标题、正文、附件内容）
    search_pattern = f"%{keyword}%"
    query = query.filter(
        or_(
            Law.title.ilike(search_pattern),
            Law.content.ilike(search_pattern),
            Law.file_content.ilike(search_pattern),
        )
    )

    # 分类筛选
    if category:
        query = query.filter(Law.category == category)

    # 按发布日期降序
    query = query.order_by(desc(Law.publish_date))

    # 总数
    total = query.count()

    # 分页
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()

    return LawListResponse(
        items=[LawResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/timeline")
def get_timeline(
    year: Optional[int] = Query(None, description="年份筛选"),
    category: Optional[str] = Query(None, description="分类筛选"),
    db: Session = Depends(get_db),
):
    """按时间线获取法规"""
    query = db.query(Law)

    # 年份筛选
    if year:
        query = query.filter(Law.publish_date >= f"{year}-01-01").filter(
            Law.publish_date <= f"{year}-12-31"
        )

    # 分类筛选
    if category:
        query = query.filter(Law.category == category)

    # 按发布日期降序
    query = query.order_by(desc(Law.publish_date))

    items = query.all()

    # 按年月分组
    timeline = {}
    for item in items:
        if item.publish_date:
            year_month = item.publish_date.strftime("%Y-%m")
            if year_month not in timeline:
                timeline[year_month] = []
            timeline[year_month].append(LawResponse.model_validate(item))

    return {"timeline": timeline, "years": sorted(set(k[:4] for k in timeline.keys()), reverse=True)}


@router.get("/{law_id}", response_model=LawResponse)
def get_law_detail(law_id: int, db: Session = Depends(get_db)):
    """获取法规详情"""
    law = db.query(Law).filter(Law.id == law_id).first()
    if not law:
        raise HTTPException(status_code=404, detail="法规不存在")
    return LawResponse.model_validate(law)


@router.get("/{law_id}/download")
def download_attachment(law_id: int, db: Session = Depends(get_db)):
    """下载法规附件"""
    law = db.query(Law).filter(Law.id == law_id).first()
    if not law:
        raise HTTPException(status_code=404, detail="法规不存在")

    if not law.file_path:
        raise HTTPException(status_code=404, detail="该法规没有本地附件")

    # 构建完整文件路径
    file_path = Path(settings.attachment_dir) / law.file_path
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="附件文件不存在")

    # 获取文件名
    filename = law.file_path.split("/")[-1] if law.file_path else "attachment"
    # 中文文件名编码
    encoded_filename = quote(filename)

    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
        }
    )


# 爬取相关 API
crawl_router = APIRouter(prefix="/api/crawl", tags=["crawl"])

# 全局爬取状态
_crawl_status = {
    "is_running": False,
    "last_crawl_time": None,
    "last_crawl_status": None,
    "last_crawl_count": None,
}


def get_crawl_status_from_db(db: Session) -> dict:
    """从数据库获取爬取状态"""
    last_log = (
        db.query(CrawlLog)
        .order_by(desc(CrawlLog.created_at))
        .first()
    )
    if last_log:
        _crawl_status["last_crawl_time"] = last_log.created_at
        _crawl_status["last_crawl_status"] = last_log.status
        _crawl_status["last_crawl_count"] = last_log.count
    return _crawl_status


@crawl_router.get("/status", response_model=CrawlStatusResponse)
def get_crawl_status(db: Session = Depends(get_db)):
    """获取爬取状态"""
    status = get_crawl_status_from_db(db)
    return CrawlStatusResponse(
        is_running=status["is_running"],
        last_crawl_time=status["last_crawl_time"],
        last_crawl_status=status["last_crawl_status"],
        last_crawl_count=status["last_crawl_count"],
    )


@crawl_router.post("/start", response_model=CrawlStartResponse)
def start_crawl(
    category: Optional[str] = Query(None, description="指定分类，不传则爬取全部"),
    db: Session = Depends(get_db),
):
    """手动触发爬取"""
    global _crawl_status

    if _crawl_status["is_running"]:
        raise HTTPException(status_code=400, detail="爬取任务正在进行中")

    # 这里只是触发，实际爬取在后台执行
    from app.services.crawler import CrawlerService

    _crawl_status["is_running"] = True

    try:
        crawler = CrawlerService(db)
        if category:
            count = crawler.crawl_category(category)
        else:
            count = crawler.crawl_all()

        _crawl_status["is_running"] = False
        _crawl_status["last_crawl_time"] = datetime.utcnow()
        _crawl_status["last_crawl_status"] = "success"
        _crawl_status["last_crawl_count"] = count

        return CrawlStartResponse(
            message="爬取完成",
            task_id=None,
        )
    except Exception as e:
        _crawl_status["is_running"] = False
        _crawl_status["last_crawl_time"] = datetime.utcnow()
        _crawl_status["last_crawl_status"] = "failed"
        _crawl_status["last_crawl_count"] = 0

        # 记录错误日志
        create_crawl_log(db, {
            "category": category or "全部",
            "status": "failed",
            "count": 0,
            "error_message": str(e),
        })

        raise HTTPException(status_code=500, detail=f"爬取失败: {str(e)}")


# 分类 API
category_router = APIRouter(prefix="/api/categories", tags=["categories"])


@category_router.get("", response_model=list[CategoryResponse])
def get_categories():
    """获取分类列表"""
    from app.config import settings

    return [
        CategoryResponse(name=name, code=code)
        for name, code in settings.categories.items()
    ]
