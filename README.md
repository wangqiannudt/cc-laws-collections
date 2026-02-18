# 法规标准爬取和管理系统

从全军武器装备采购信息网（https://www.weain.mil.cn/fgbz/list.shtml）爬取和管理法规标准内容。

## 功能特性

- 爬取并整理"政策法规"模块的4个分类：国家颁布法规、军队颁布法规、联合颁布法规、其他法规
- 按时间线整理法规内容
- 支持关键词查询和展示
- 定时自动检测网站更新（默认每48小时）
- 附件自动下载与解析（支持 PDF、Word、压缩包等）

## 技术栈

- **后端**: Python 3.10+ / FastAPI / SQLAlchemy / APScheduler
- **前端**: Vue 3 / Vite / Element Plus
- **数据库**: SQLite

## 快速开始

### 后端启动

```bash
# 进入后端目录
cd backend

# 安装依赖
pip install -r requirements.txt

# 启动服务
uvicorn app.main:app --reload --port 8000
```

### 前端启动

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 访问应用

- 前端页面: http://localhost:5173
- 后端 API 文档: http://localhost:8000/docs

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/laws | 获取法规列表（支持分页、分类筛选） |
| GET | /api/laws/{id} | 获取法规详情 |
| GET | /api/laws/search | 关键词搜索 |
| GET | /api/laws/timeline | 按时间线获取法规 |
| POST | /api/crawl/start | 手动触发爬取 |
| GET | /api/crawl/status | 获取爬取状态 |
| GET | /api/categories | 获取分类列表 |

## 目录结构

```
laws-collection/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 入口
│   │   ├── config.py            # 配置文件
│   │   ├── database.py          # 数据库连接
│   │   ├── models/              # 数据模型
│   │   ├── schemas/             # Pydantic 模型
│   │   ├── services/            # 业务逻辑
│   │   ├── api/                 # API 路由
│   │   └── scheduler/           # 定时任务
│   └── tests/                   # 测试
├── frontend/
│   ├── src/
│   │   ├── views/               # 页面组件
│   │   ├── api/                 # API 调用
│   │   └── router/              # 路由配置
│   └── vite.config.js
└── data/
    ├── laws.db                  # SQLite 数据库
    └── attachments/             # 附件存储
```

## 配置

可通过环境变量或 `.env` 文件配置：

```env
# 数据库
DATABASE_URL=sqlite:///./data/laws.db

# 爬虫配置
CRAWLER_REQUEST_DELAY=1.5
CRAWLER_MAX_RETRIES=3

# 定时任务（小时）
SCHEDULER_INTERVAL_HOURS=48
```

## 注意事项

1. 爬虫请求间隔默认 1.5 秒，请勿设置过短以免对目标网站造成压力
2. 部分附件格式（如 .doc）可能无法自动解析，需手动查看
3. 首次运行会自动创建数据库和表结构

## License

MIT
