#!/bin/bash
# 法规标准管理系统 - 一键启动脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
LOG_DIR="$PROJECT_ROOT/logs"
PID_DIR="$PROJECT_ROOT/.pids"

# 创建必要的目录
mkdir -p "$LOG_DIR" "$PID_DIR" "$PROJECT_ROOT/data/attachments"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   法规标准管理系统 - 启动脚本${NC}"
echo -e "${GREEN}========================================${NC}"

# 检查是否已经在运行
check_running() {
    if [ -f "$PID_DIR/backend.pid" ]; then
        if kill -0 $(cat "$PID_DIR/backend.pid") 2>/dev/null; then
            echo -e "${YELLOW}后端服务已在运行中 (PID: $(cat $PID_DIR/backend.pid))${NC}"
            return 0
        fi
    fi
    return 1
}

# 启动后端
start_backend() {
    echo -e "${YELLOW}[1/2] 启动后端服务...${NC}"

    cd "$BACKEND_DIR"

    # 检查 Python 环境
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}错误: 未找到 Python3，请先安装 Python${NC}"
        exit 1
    fi

    # 检查依赖是否安装
    if ! python3 -c "import fastapi" 2>/dev/null; then
        echo -e "${YELLOW}正在安装后端依赖...${NC}"
        pip3 install -r requirements.txt -q
    fi

    # 启动后端服务
    nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > "$LOG_DIR/backend.log" 2>&1 &
    echo $! > "$PID_DIR/backend.pid"

    sleep 2

    # 验证启动
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ 后端服务启动成功 (PID: $(cat $PID_DIR/backend.pid))${NC}"
        echo -e "  API 文档: http://localhost:8000/docs"
    else
        echo -e "${RED}✗ 后端服务启动失败，请查看日志: $LOG_DIR/backend.log${NC}"
        exit 1
    fi
}

# 启动前端
start_frontend() {
    echo -e "${YELLOW}[2/2] 启动前端服务...${NC}"

    cd "$FRONTEND_DIR"

    # 检查 Node.js 环境
    if ! command -v npm &> /dev/null; then
        echo -e "${RED}错误: 未找到 npm，请先安装 Node.js${NC}"
        exit 1
    fi

    # 检查依赖是否安装
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}正在安装前端依赖...${NC}"
        npm install --silent
    fi

    # 启动前端服务
    nohup npm run dev > "$LOG_DIR/frontend.log" 2>&1 &
    echo $! > "$PID_DIR/frontend.pid"

    sleep 3

    # 验证启动
    if curl -s http://localhost:5173 > /dev/null 2>&1; then
        echo -e "${GREEN}✓ 前端服务启动成功 (PID: $(cat $PID_DIR/frontend.pid))${NC}"
        echo -e "  访问地址: http://localhost:5173"
    else
        echo -e "${RED}✗ 前端服务启动失败，请查看日志: $LOG_DIR/frontend.log${NC}"
        exit 1
    fi
}

# 主流程
if check_running; then
    echo -e "${YELLOW}服务已在运行中，如需重启请先运行 stop.sh${NC}"
    exit 0
fi

start_backend
start_frontend

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   所有服务启动完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "  ${GREEN}前端地址:${NC} http://localhost:5173"
echo -e "  ${GREEN}后端地址:${NC} http://localhost:8000"
echo -e "  ${GREEN}API 文档:${NC} http://localhost:8000/docs"
echo ""
echo -e "  ${YELLOW}停止服务:${NC} ./stop.sh"
echo -e "  ${YELLOW}查看日志:${NC} tail -f logs/backend.log 或 logs/frontend.log"
echo ""
