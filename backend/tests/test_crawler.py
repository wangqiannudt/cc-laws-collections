"""爬虫服务测试"""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock


class TestCrawlerService:
    """爬虫服务测试类"""

    def test_compute_hash(self):
        """测试哈希计算"""
        from app.services.crawler import CrawlerService

        db = Mock()
        crawler = CrawlerService(db)

        hash1 = crawler._compute_hash("测试标题", "测试内容")
        hash2 = crawler._compute_hash("测试标题", "测试内容")
        hash3 = crawler._compute_hash("测试标题", "不同内容")

        assert hash1 == hash2  # 相同输入应产生相同哈希
        assert hash1 != hash3  # 不同输入应产生不同哈希
        assert len(hash1) == 64  # SHA256 输出64个字符

    def test_parse_date(self):
        """测试日期解析"""
        from app.services.crawler import CrawlerService

        db = Mock()
        crawler = CrawlerService(db)

        # 测试各种日期格式
        assert crawler._parse_date("2024-01-15") == datetime(2024, 1, 15)
        assert crawler._parse_date("2024/01/15") == datetime(2024, 1, 15)
        assert crawler._parse_date("2024年1月15日") == datetime(2024, 1, 15)
        assert crawler._parse_date("2024年01月") == datetime(2024, 1, 1)
        assert crawler._parse_date("无效日期") is None

    def test_parse_list_page(self):
        """测试列表页解析"""
        from app.services.crawler import CrawlerService
        from bs4 import BeautifulSoup

        db = Mock()
        crawler = CrawlerService(db)

        html = """
        <html>
            <body>
                <ul>
                    <li><a href="/detail/1.html">法规标题1</a></li>
                    <li><a href="/detail/2.html">法规标题2</a></li>
                </ul>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, "lxml")
        links = crawler._parse_list_page(soup, "https://example.com/list")

        assert len(links) == 2
        assert links[0]["title"] == "法规标题1"
        assert links[0]["url"] == "https://example.com/detail/1.html"

    def test_extract_title(self):
        """测试标题提取"""
        from app.services.crawler import CrawlerService
        from bs4 import BeautifulSoup

        db = Mock()
        crawler = CrawlerService(db)

        html = """
        <html>
            <head><title>页面标题 - 网站名</title></head>
            <body>
                <h1>法规真实标题</h1>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, "lxml")
        title = crawler._extract_title(soup)

        assert title == "法规真实标题"


class TestLawModel:
    """法规模型测试"""

    def test_law_creation(self):
        """测试法规创建"""
        from app.models.law import Law

        law = Law(
            title="测试法规",
            category="国家颁布法规",
            source_url="https://example.com/law/1",
        )

        assert law.title == "测试法规"
        assert law.category == "国家颁布法规"


class TestAPI:
    """API 测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        from fastapi.testclient import TestClient
        from app.main import app

        return TestClient(app)

    def test_root_endpoint(self, client):
        """测试根路径"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data

    def test_health_endpoint(self, client):
        """测试健康检查"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_categories_endpoint(self, client):
        """测试分类接口"""
        response = client.get("/api/categories")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 4
        assert any(c["name"] == "国家颁布法规" for c in data)
