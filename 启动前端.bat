@echo off
title DeviationAI - 启动前端
cd /d "%~dp0frontend"
echo 🚀 启动前端服务...
call npm run dev
pause