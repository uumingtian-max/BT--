#!/bin/bash
echo "====================================="
echo "ai-agent-project（黑光）启动"
echo "====================================="
echo "1. SGLang..."
cd ./sglang && ./start_sglang_30B.sh &
sleep 10
echo "2. 后端..."
cd ./backend && ./start_backend.sh &
sleep 5
echo "3. 前端..."
cd ./frontend && npm install && npm run dev &
echo "====================================="
echo "前端: http://localhost:5173"
echo "指令: #黑光私密形态"
echo "====================================="
