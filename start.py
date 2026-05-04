"""
启动脚本 - DeviationAI
自动启动后端 + 打开浏览器
"""
import subprocess
import webbrowser
import time
import sys
import os

BACKEND_PORT = 8000
FRONTEND_PORT = 5173

def main():
    # 启动后端
    print("🚀 启动后端服务...")
    backend_dir = os.path.join(os.path.dirname(__file__), "backend")
    backend_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--reload", "--port", str(BACKEND_PORT)],
        cwd=backend_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    
    # 等待后端启动
    time.sleep(3)
    
    # 启动前端 (Vite dev server)
    print("🚀 启动前端服务...")
    frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")
    frontend_proc = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=frontend_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    
    # 等待前端启动
    time.sleep(5)
    
    # 打开浏览器
    print(f"🌐 打开浏览器 http://localhost:{FRONTEND_PORT}")
    webbrowser.open(f"http://localhost:{FRONTEND_PORT}")
    
    print("\n✅ DeviationAI 已启动！")
    print(f"   前端: http://localhost:{FRONTEND_PORT}")
    print(f"   后端: http://localhost:{BACKEND_PORT}")
    print("\n按 Ctrl+C 停止所有服务")
    
    try:
        backend_proc.wait()
    except KeyboardInterrupt:
        backend_proc.terminate()
        frontend_proc.terminate()
        print("\n👋 服务已停止")

if __name__ == "__main__":
    main()