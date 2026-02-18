"""定时任务调度"""
import logging
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.config import settings
from app.database import SessionLocal

logger = logging.getLogger(__name__)

# 调度器实例
scheduler = BackgroundScheduler()


def crawl_all_categories():
    """爬取所有分类"""
    from app.services.crawler import CrawlerService
    from app.models.law import create_crawl_log

    logger.info("开始定时爬取任务")
    db = SessionLocal()
    try:
        crawler = CrawlerService(db)
        count = crawler.crawl_all()
        create_crawl_log(db, {
            "category": "全部",
            "status": "success",
            "count": count,
            "error_message": None,
        })
        logger.info(f"定时爬取完成，共爬取 {count} 条法规")
    except Exception as e:
        logger.error(f"定时爬取失败: {e}")
        create_crawl_log(db, {
            "category": "全部",
            "status": "failed",
            "count": 0,
            "error_message": str(e),
        })
    finally:
        db.close()


def start_scheduler():
    """启动调度器"""
    # 添加定时任务：每48小时执行一次
    scheduler.add_job(
        crawl_all_categories,
        trigger=IntervalTrigger(hours=settings.scheduler_interval_hours),
        id="crawl_all_laws",
        name="爬取所有法规",
        replace_existing=True,
    )

    scheduler.start()
    logger.info(f"调度器已启动，间隔: {settings.scheduler_interval_hours} 小时")


def stop_scheduler():
    """停止调度器"""
    scheduler.shutdown()
    logger.info("调度器已停止")
