"""路径 / 端口 / 目录常量
改这里 → 同步 _archive 里原始 init_db.py 的 DB_PATH 引用
端口/host 是单一事实源(§6.2),daemon.py / 文档 / README 必须从这里 import,不再各自硬编码
"""
from pathlib import Path

# 项目根(本文件所在 server/ 的上一级)
ROOT = Path(__file__).parent.parent.resolve()

# 数据/资源目录
DB_PATH     = ROOT / 'db' / 'materials.db'

# 价格库(独立 db,跨库引用) · 兄弟项目 MaterialWebPrices
# 优先相对路径 ROOT/data/prices.db(Mac / Linux / Windows 通用)
# Mac 暂未启用价格库 — 文件不存在时 prices handler 会 try/except 兜底
PRICES_DB_PATH = ROOT / 'data' / 'prices.db'
PRICES_KEYWORDS_PATH = ROOT / 'data' / 'material_price_keywords.json'
UPLOAD_DIR  = ROOT / 'data' / 'uploads'
QR_DIR      = ROOT / 'data' / 'qr_codes'
IMAGES_DIR  = ROOT / 'data' / 'media' / 'images'
CAD_DIR     = ROOT / 'data' / 'media' / 'cad'
STATIC_DIR  = ROOT / 'client'        # 前端静态资源

# 服务
HOST        = '0.0.0.0'
# canonical · 改这里只此一处 · daemon.py 必须 from server.config import PORT
# 2026-08-06 verifier 提示:历史曾跑 8093(被僵尸进程占 8086 时临时换),daemon.py 现在与 config.py 同步
PORT        = 8086
DEBUG       = True                   # dev 模式,生产改 False

# 限制
ALLOWED_EXTS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}
MAX_UPLOAD  = 16 * 1024 * 1024       # 16MB

# CORS(本地开发全开)
CORS_ORIGIN = '*'

# AI 视觉默认超时
VISION_TIMEOUT = 120
