#!/bin/bash
# 法规标准管理系统 - 一键停止脚本

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
PID_DIR="$PROJECT_ROOT/.pids"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   法规标准管理系统 - 停止脚本${NC}"
echo -e "${GREEN}========================================${NC}"

# 停止后端
stop_backend() {
    if [ -f "$PID_DIR/backend.pid" ]; then
        PID=$(cat "$PID_DIR/backend.pid")
        if kill -0 "$PID" 2>/dev/null; then
            kill "$PID" 2>/dev/null
            echo -e "${GREEN}✓ 后端服务已停止 (PID: $PID)${NC}"
        else
            echo -e "${YELLOW}后端服务进程不存在${NC}"
        fi
        rm -f "$PID_DIR/backend.pid"
    else
        echo -e "${YELLOW}未找到后端服务 PID 文件${NC}"
    fi

    # 确保所有 uvicorn 进程都已停止
    pkill -f "uvicorn app.main:app" 2>/dev/null || true
}

# 停止前端
stop_frontend() {
    if [ -f "$PID_DIR/frontend.pid" ]; then
        PID=$(cat "$PID_DIR/frontend.pid")
        if kill -0 "$PID" 2>/dev/null; then
            kill "$PID" 2>/dev/null
            echo -e "${GREEN}✓ 前端服务已停止 (PID: $PID)${NC}"
        else
            echo -e "${YELLOW}前端服务进程不存在${NC}"
        fi
        rm -f "$PID_DIR/frontend.pid"
    else
        echo -e "${YELLOW}未找到前端服务 PID 文件${NC}"
    fi

    # 确保所有 vite 进程都已停止
    pkill -f "vite" 2>/dev/null || true
}

# 主流程
stop_backend
stop_frontend

# 清理 PID 目录
rm -rf "$PID_DIR" 2>/dev/null || true

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   所有服务已停止${NC}"
echo -e "${GREEN}========================================${NC}"
