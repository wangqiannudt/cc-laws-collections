"""法规数据模型"""
from datetime import date, datetime

from sqlalchemy import Column, DateTime, Integer, String, Text, Date, Index
from sqlalchemy.orm import Session

from app.database import Base


class Law(Base):
    """法规表"""

    __tablename__ = "laws"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False, comment="法规标题")
    category = Column(String(50), nullable=False, comment="分类")
    publish_date = Column(Date, nullable=True, comment="发布日期")
    content = Column(Text, nullable=True, comment="法规正文内容（HTML）")
    source_url = Column(String(500), nullable=False, comment="原文链接")
    file_url = Column(String(500), nullable=True, comment="附件下载链接")
    file_path = Column(String(500), nullable=True, comment="本地附件存储路径")
    file_content = Column(Text, nullable=True, comment="附件解析后的文本内容")
    is_internal = Column(Integer, default=0, comment="是否为内部法规")
    created_at = Column(DateTime, default=datetime.utcnow, comment="入库时间")
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间"
    )
    hash = Column(String(64), nullable=True, comment="内容哈希（用于增量更新）")

    __table_args__ = (
        Index("idx_law_category", "category"),
        Index("idx_law_publish_date", "publish_date"),
        Index("idx_law_hash", "hash"),
    )

    def __repr__(self):
        return f"<Law(id={self.id}, title='{self.title}', category='{self.category}')>"


class CrawlLog(Base):
    """爬取日志表"""

    __tablename__ = "crawl_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String(50), nullable=False, comment="爬取的分类")
    status = Column(String(20), nullable=False, comment="状态：success/failed")
    count = Column(Integer, default=0, comment="爬取数量")
    error_message = Column(Text, nullable=True, comment="错误信息")
    created_at = Column(DateTime, default=datetime.utcnow, comment="爬取时间")

    def __repr__(self):
        return f"<CrawlLog(id={self.id}, category='{self.category}', status='{self.status}')>"


def get_law_by_hash(db: Session, hash_value: str) -> Law | None:
    """根据哈希值获取法规"""
    return db.query(Law).filter(Law.hash == hash_value).first()


def get_law_by_source_url(db: Session, source_url: str) -> Law | None:
    """根据来源 URL 获取法规"""
    return db.query(Law).filter(Law.source_url == source_url).first()


def create_law(db: Session, law_data: dict) -> Law:
    """创建法规记录"""
    law = Law(**law_data)
    db.add(law)
    db.commit()
    db.refresh(law)
    return law


def update_law(db: Session, law: Law, update_data: dict) -> Law:
    """更新法规记录"""
    for key, value in update_data.items():
        setattr(law, key, value)
    db.commit()
    db.refresh(law)
    return law


def create_crawl_log(db: Session, log_data: dict) -> CrawlLog:
    """创建爬取日志"""
    log = CrawlLog(**log_data)
    db.add(log)
    db.commit()
    db.refresh(log)
    return log
