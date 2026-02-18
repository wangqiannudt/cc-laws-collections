"""爬虫服务"""
import hashlib
import logging
import os
import re
import tempfile
import time
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin, urlparse

import pdfplumber
import requests
from bs4 import BeautifulSoup
from docx import Document

from app.config import settings
from app.models.law import (
    Law,
    create_law,
    get_law_by_hash,
    get_law_by_source_url,
    update_law,
    create_crawl_log,
)

logger = logging.getLogger(__name__)


class CrawlerService:
    """爬虫服务类"""

    def __init__(self, db):
        self.db = db
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        })
        self.attachment_dir = settings.attachment_dir
        self.attachment_dir.mkdir(parents=True, exist_ok=True)

    def _request_with_retry(self, url: str, **kwargs) -> Optional[requests.Response]:
        """带重试的请求"""
        kwargs.setdefault("timeout", settings.crawler_timeout)

        for attempt in range(settings.crawler_max_retries):
            try:
                response = self.session.get(url, **kwargs)
                response.raise_for_status()
                # 修复编码问题：weain 网站返回 ISO-8859-1 但实际是 UTF-8
                if response.encoding == 'ISO-8859-1' and response.apparent_encoding:
                    response.encoding = response.apparent_encoding
                return response
            except requests.RequestException as e:
                logger.warning(f"请求失败 (尝试 {attempt + 1}/{settings.crawler_max_retries}): {url}, 错误: {e}")
                if attempt < settings.crawler_max_retries - 1:
                    time.sleep(settings.crawler_request_delay * (attempt + 1))
        return None

    def _post_with_retry(self, url: str, data: dict, **kwargs) -> Optional[requests.Response]:
        """带重试的 POST 请求"""
        kwargs.setdefault("timeout", settings.crawler_timeout)

        for attempt in range(settings.crawler_max_retries):
            try:
                response = self.session.post(url, data=data, **kwargs)
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                logger.warning(f"POST 请求失败 (尝试 {attempt + 1}/{settings.crawler_max_retries}): {url}, 错误: {e}")
                if attempt < settings.crawler_max_retries - 1:
                    time.sleep(settings.crawler_request_delay * (attempt + 1))
        return None

    def _fetch_list_via_api(self, lmid: str, page: int = 1) -> Optional[dict]:
        """通过 JSON API 获取列表数据"""
        params = {
            "lmid": lmid,
            "currentPage": page,
        }

        response = self._request_with_retry(settings.crawler_api_url, params=params)
        if not response:
            return None

        try:
            result = response.json()
            if "list" in result:
                return result["list"]
            logger.warning(f"API 返回格式异常: {result}")
            return None
        except Exception as e:
            logger.error(f"解析 API 响应失败: {e}")
            return None

    def _get_total_pages(self, lmid: str) -> int:
        """获取分类的总页数"""
        list_data = self._fetch_list_via_api(lmid, page=1)
        if not list_data:
            return 0

        total_num = list_data.get("totalNum", 0)
        if total_num == 0:
            return 0

        # 计算总页数
        import math
        return math.ceil(total_num / settings.crawler_page_size)

    def _compute_hash(self, title: str, content: Optional[str] = None) -> str:
        """计算内容哈希"""
        data = title
        if content:
            data += content[:1000]  # 取前1000字符参与哈希
        return hashlib.sha256(data.encode("utf-8")).hexdigest()

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """解析日期字符串"""
        if not date_str:
            return None

        # 尝试多种日期格式
        formats = [
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%Y年%m月%d日",
            "%Y.%m.%d",
            "%Y-%m",
            "%Y/%m",
            "%Y年%m月",
        ]

        date_str = date_str.strip()
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        # 尝试提取年月日
        match = re.search(r"(\d{4})[年/-](\d{1,2})[月/-]?(\d{1,2})?", date_str)
        if match:
            year, month = int(match.group(1)), int(match.group(2))
            day = int(match.group(3)) if match.group(3) else 1
            try:
                return datetime(year, month, day)
            except ValueError:
                return None

        return None

    def crawl_category(self, category_name: str) -> int:
        """爬取指定分类的法规（使用 API）"""
        category_code = settings.categories.get(category_name)
        lmid = settings.category_lmids.get(category_name)

        if not category_code or not lmid:
            logger.error(f"未知的分类或缺少 lmid: {category_name}")
            return 0

        logger.info(f"开始爬取分类: {category_name}, lmid: {lmid}")

        # 获取总页数
        total_pages = self._get_total_pages(lmid)
        if total_pages == 0:
            logger.warning(f"分类 {category_name} 没有数据或无法获取页数")
            return 0

        logger.info(f"分类 {category_name} 共 {total_pages} 页")
        total_count = 0

        try:
            # 遍历所有页面
            for page in range(1, total_pages + 1):
                logger.info(f"正在爬取第 {page}/{total_pages} 页...")

                list_data = self._fetch_list_via_api(lmid, page)
                if not list_data:
                    logger.warning(f"第 {page} 页数据获取失败，跳过")
                    continue

                content_list = list_data.get("contentList", [])
                if not content_list:
                    logger.info(f"第 {page} 页没有数据，跳过")
                    continue

                for item in content_list:
                    try:
                        # 构建 详情页 URL
                        pc_url = item.get("pcUrl", "")
                        if not pc_url:
                            continue

                        detail_url = urljoin(settings.crawler_base_url, pc_url)

                        # 从 API 数据中获取日期
                        fbsj = item.get("FBSJ", "")
                        api_date = self._parse_date(fbsj) if fbsj else None

                        # 爬取详情页
                        law_data = self._crawl_detail_page(detail_url, category_name)
                        if law_data:
                            # 如果 API 有日期但详情页没解析到，使用 API 的日期
                            if api_date and not law_data.get("publish_date"):
                                law_data["publish_date"] = api_date

                            # 检查是否已存在
                            existing = get_law_by_hash(self.db, law_data["hash"])
                            if existing:
                                update_law(self.db, existing, law_data)
                                logger.debug(f"更新法规: {law_data['title']}")
                            else:
                                create_law(self.db, law_data)
                                logger.debug(f"新增法规: {law_data['title']}")
                            total_count += 1

                        # 详情页请求间隔
                        time.sleep(settings.crawler_detail_delay)

                    except Exception as e:
                        logger.error(f"爬取详情页失败: {item.get('BT', 'unknown')}, 错误: {e}")
                        continue

                # 页面请求间隔
                time.sleep(settings.crawler_request_delay)

            # 记录爬取日志
            create_crawl_log(self.db, {
                "category": category_name,
                "status": "success",
                "count": total_count,
                "error_message": None,
            })

            logger.info(f"分类 {category_name} 爬取完成，共 {total_count} 条")

        except Exception as e:
            logger.error(f"爬取分类 {category_name} 失败: {e}")
            create_crawl_log(self.db, {
                "category": category_name,
                "status": "failed",
                "count": total_count,
                "error_message": str(e),
            })

        return total_count

    def _parse_list_page(self, soup: BeautifulSoup, base_url: str) -> list[dict]:
        """解析列表页，获取法规链接"""
        links = []

        # 尝试多种常见的列表结构
        # 策略1：查找 ul/li 或 ol/li 结构
        list_items = soup.select("ul li a, ol li a")

        # 策略2：查找带有特定 class 的链接
        if not list_items:
            list_items = soup.select("a[href*='detail'], a[href*='content'], a[href*='.shtml']")

        # 策略3：查找表格中的链接
        if not list_items:
            list_items = soup.select("table a")

        for item in list_items:
            href = item.get("href", "")
            title = item.get_text(strip=True)

            if not title or not href:
                continue

            # 过滤非法规链接
            if any(x in href.lower() for x in ["javascript:", "mailto:", "#"]):
                continue

            # 构建完整 URL
            full_url = urljoin(base_url, href)

            # 尝试从上下文获取日期
            date_str = None
            parent = item.parent
            if parent:
                # 查找日期文本
                date_match = re.search(
                    r"(\d{4}[年/-]\d{1,2}[月/-]\d{1,2}[日]?|\d{4}-\d{2}-\d{2})",
                    parent.get_text(),
                )
                if date_match:
                    date_str = date_match.group(1)

            links.append({
                "url": full_url,
                "title": title,
                "date_str": date_str,
            })

        return links

    def _crawl_detail_page(self, url: str, category: str) -> Optional[dict]:
        """爬取详情页"""
        response = self._request_with_retry(url)
        if not response:
            return None

        soup = BeautifulSoup(response.text, "lxml")

        # 提取标题
        title = self._extract_title(soup)
        if not title:
            logger.warning(f"无法提取标题: {url}")
            return None

        # 提取发布日期
        publish_date = self._extract_publish_date(soup)

        # 提取正文内容
        content = self._extract_content(soup)

        # 查找附件
        file_url, file_path, file_content = self._process_attachments(soup, url, title)

        # 计算哈希
        content_hash = self._compute_hash(title, content)

        return {
            "title": title,
            "category": category,
            "publish_date": publish_date,
            "content": content,
            "source_url": url,
            "file_url": file_url,
            "file_path": file_path,
            "file_content": file_content,
            "hash": content_hash,
        }

    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """提取标题"""
        # 尝试多种标题选择器（weain 网站优先）
        selectors = [
            "#nonSecretTitle",  # weain 网站标题
            "h1",
            "h2.title",
            "h2",
            ".article-title",
            ".news-title",
            ".content-title",
            "title",
        ]

        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                title = element.get_text(strip=True)
                # 清理标题
                title = re.sub(r"\s+", " ", title)
                title = re.sub(r"[-_|].*$", "", title)  # 移除网站名称后缀
                if len(title) > 5:  # 标题至少要有一定长度
                    return title.strip()

        return None

    def _extract_publish_date(self, soup: BeautifulSoup) -> Optional[datetime]:
        """提取发布日期"""
        # 在页面文本中查找日期
        text = soup.get_text()
        date_patterns = [
            r"发布[日期时间：:\s]*(\d{4}[年/-]\d{1,2}[月/-]\d{1,2}[日]?)",
            r"(\d{4}[年/-]\d{1,2}[月/-]\d{1,2}[日]?)",
            r"(\d{4}-\d{2}-\d{2})",
        ]

        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                return self._parse_date(match.group(1))

        return None

    def _extract_content(self, soup: BeautifulSoup) -> Optional[str]:
        """提取正文内容"""
        # 尝试多种内容容器选择器（weain 网站优先）
        selectors = [
            "div.txt#content",  # weain 网站正文
            ".article-content",
            ".news-content",
            ".content",
            ".article-body",
            "#content",
            "article",
            ".TRS_Editor",
            ".Custom_UnifyPE",
        ]

        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                # 清理内容
                for tag in element.select("script, style, nav, header, footer"):
                    tag.decompose()
                return str(element)

        # 如果没有找到，尝试获取所有段落
        paragraphs = soup.find_all("p")
        if paragraphs:
            content = "\n".join(str(p) for p in paragraphs if p.get_text(strip=True))
            if len(content) > 100:
                return content

        return None

    def _process_attachments(self, soup: BeautifulSoup, base_url: str, title: str) -> tuple:
        """处理附件"""
        file_url = None
        file_path = None
        file_content = None

        # 查找附件链接
        attachment_extensions = [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".zip", ".rar", ".7z", ".jpg", ".jpeg", ".png"]
        attachment_links = []

        # 优先查找 weain 网站的附件区域
        enclosure = soup.select_one("#enclosureName a")
        if enclosure and enclosure.get("href"):
            attachment_links.append(urljoin(base_url, enclosure["href"]))

        # 通用查找
        for a in soup.find_all("a", href=True):
            href = a["href"].lower()
            if any(ext in href for ext in attachment_extensions):
                full_url = urljoin(base_url, a["href"])
                if full_url not in attachment_links:
                    attachment_links.append(full_url)

        if not attachment_links:
            return file_url, file_path, file_content

        # 处理第一个附件
        file_url = attachment_links[0]

        try:
            # 下载附件
            file_path, file_content = self._download_and_parse_attachment(file_url, title)
            logger.info(f"附件处理完成: {file_path}")
        except Exception as e:
            logger.error(f"附件处理失败: {file_url}, 错误: {e}")

        return file_url, file_path, file_content

    def _download_and_parse_attachment(self, url: str, title: str) -> tuple[Optional[str], Optional[str]]:
        """下载并解析附件"""
        response = self._request_with_retry(url, stream=True)
        if not response:
            return None, None

        # 获取文件名
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
        if not filename:
            filename = f"{title[:50]}.dat"

        # 清理文件名
        filename = re.sub(r'[<>:"/\\|?*]', "_", filename)

        # 确定存储目录（按年份）
        year_dir = self.attachment_dir / str(datetime.now().year)
        year_dir.mkdir(parents=True, exist_ok=True)

        # 保存文件
        file_path = year_dir / filename
        with open(file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        # 解析文件内容
        file_content = self._parse_file_content(file_path)

        return str(file_path), file_content

    def _parse_file_content(self, file_path: Path) -> Optional[str]:
        """解析文件内容"""
        suffix = file_path.suffix.lower()

        try:
            if suffix == ".pdf":
                return self._parse_pdf(file_path)
            elif suffix == ".docx":
                return self._parse_docx(file_path)
            elif suffix == ".doc":
                # .doc 格式需要特殊处理，这里返回提示
                logger.warning(f"不支持 .doc 格式，请手动转换: {file_path}")
                return f"[.doc 格式文件，需手动查看: {file_path.name}]"
            elif suffix == ".txt":
                return file_path.read_text(encoding="utf-8", errors="ignore")
            elif suffix in [".zip", ".rar", ".7z"]:
                return self._parse_archive(file_path)
            else:
                logger.warning(f"不支持的文件格式: {suffix}")
                return None
        except Exception as e:
            logger.error(f"解析文件失败 {file_path}: {e}")
            return None

    def _parse_pdf(self, file_path: Path) -> Optional[str]:
        """解析 PDF 文件"""
        text_parts = []
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
        except Exception as e:
            logger.error(f"PDF 解析失败: {e}")

        return "\n".join(text_parts) if text_parts else None

    def _parse_docx(self, file_path: Path) -> Optional[str]:
        """解析 Word 文档"""
        try:
            doc = Document(file_path)
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            return "\n".join(paragraphs)
        except Exception as e:
            logger.error(f"Word 解析失败: {e}")
            return None

    def _parse_archive(self, file_path: Path) -> Optional[str]:
        """解析压缩包"""
        extracted_texts = []

        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                if file_path.suffix.lower() == ".zip":
                    with zipfile.ZipFile(file_path, "r") as zf:
                        zf.extractall(temp_dir)
                elif file_path.suffix.lower() == ".7z":
                    import py7zr
                    with py7zr.SevenZipFile(file_path, mode="r") as szf:
                        szf.extractall(temp_dir)
                elif file_path.suffix.lower() == ".rar":
                    import rarfile
                    with rarfile.RarFile(file_path, "r") as rf:
                        rf.extractall(temp_dir)
                else:
                    return None

                # 递归解析解压后的文件
                for root, _, files in os.walk(temp_dir):
                    for name in files:
                        inner_path = Path(root) / name
                        inner_text = self._parse_file_content(inner_path)
                        if inner_text:
                            extracted_texts.append(f"=== {name} ===\n{inner_text}")

            except Exception as e:
                logger.error(f"解压失败: {e}")
                return None

        return "\n\n".join(extracted_texts) if extracted_texts else None

    def crawl_all(self) -> int:
        """爬取所有分类"""
        total = 0
        for category_name in settings.categories.keys():
            count = self.crawl_category(category_name)
            total += count
            # 分类之间的间隔
            time.sleep(settings.crawler_request_delay * 2)

        logger.info(f"全部爬取完成，共 {total} 条法规")
        return total
