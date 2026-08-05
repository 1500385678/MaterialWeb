#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
建筑材料数据库 MaterialDB 启动脚本
运行: python start.py
"""

import subprocess
import sys
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent

def check_deps():
    """检查并安装依赖"""
    try:
        import flask
        import qrcode
    except ImportError:
        print("📦 正在安装依赖…")
        subprocess.check_call(
            [sys.executable, '-m', 'pip', 'install', 'flask', 'qrcode[pil]', '-q']
        )
        print("✅ 依赖安装完成")

def main():
    print("=" * 50)
    print("  建筑材料数据库 MaterialDB")
    print("=" * 50)
    print()

    check_deps()

    # 初始化数据库
    print("[1/2] 初始化数据库…")
    result = subprocess.run(
        [sys.executable, 'init_db.py'],
        cwd=str(BASE_DIR),
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        print("      数据库初始化完成")
    else:
        print("      ⚠️  数据库可能已有数据，继续启动…")
        print(result.stdout[-200:] if result.stdout else '')

    # 启动 API 服务
    print("[2/2] 启动 API 服务…")
    print()
    print("  🌐 浏览器访问: http://localhost:5188")
    print("  📡 API端点:    http://localhost:5188/api/materials")
    print()
    print("  按 Ctrl+Break (Win) 或 Ctrl+C 停止服务")
    print("-" * 50)
    print()

    subprocess.run([sys.executable, 'api_server.py'], cwd=str(BASE_DIR))

if __name__ == '__main__':
    main()
