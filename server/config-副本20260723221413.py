"""路径 / 端口 / 目录常量
改这里 → 同步 _archive 里原始 init_db.py 的 DB_PATH 引用 + scripts/daemon.py 的 PORT
"""
from pathlib import Path

# 项目根(本文件所在 server/ 的上一级)
ROOT = Path(__file__).parent.parent.resolve()

# 数据/资源目录
DB_PATH     = ROOT / 'db' / 'materials.db'
UPLOAD_DIR  = ROOT / 'data' / 'uploads'
QR_DIR      = ROOT / 'data' / 'qr_codes'
IMAGES_DIR  = ROOT / 'data' / 'media' / 'images'
CAD_DIR     = ROOT / 'data' / 'media' / 'cad'
STATIC_DIR  = ROOT / 'client'        # 前端静态资源

# 服务
HOST        = '0.0.0.0'
PORT        = 8091                   # 顺延 CanvasWeb 8085 / 8086~8090 被 SketchUp 占,临时 8091
DEBUG       = True                   # dev 模式,生产改 False

# 限制
ALLOWED_EXTS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}
MAX_UPLOAD  = 16 * 1024 * 1024       # 16MB

# CORS(本地开发全开)
CORS_ORIGIN = '*'

# AI 视觉默认超时
VISION_TIMEOUT = 120
