"""路径 / 端口 / 目录常量
改这里 → 同步 _archive 里原始 init_db.py 的 DB_PATH 引用
端口/host 是单一事实源(§6.2),daemon.py / 文档 / README 必须从这里 import,不再各自硬编码
"""
import os
from pathlib import Path

# 项目根(本文件所在 server/ 的上一级)
ROOT = Path(__file__).parent.parent.resolve()

# 数据/资源目录
DB_PATH     = ROOT / 'db' / 'materials.db'

# 价格库(独立 db,跨库引用) · 兄弟项目 MaterialWebPrices
# 2026-08-18 路径已迁 Defense\MaterialWebPrices\prices.db(原 Attack\价格库\ 废弃)
PRICES_DB_PATH = Path(r'D:\Mac\Mac\Mac\workteam\05_space\03_architect\Defense\06-Material\Defense\MaterialWebPrices\prices.db')
PRICES_KEYWORDS_PATH = ROOT / 'data' / 'material_price_keywords.json'
UPLOAD_DIR  = ROOT / 'data' / 'uploads'
QR_DIR      = ROOT / 'data' / 'qr_codes'
IMAGES_DIR  = ROOT / 'data' / 'media' / 'images'
CAD_DIR     = ROOT / 'data' / 'media' / 'cad'
STATIC_DIR  = ROOT / 'client'        # 前端静态资源

# 服务
# HOST 默认 127.0.0.1(本机,铁律 #6「写权限限本机 IP」)
# 如需临时 LAN 暴露:`MW_HOST=0.0.0.0 python scripts/daemon.py`
HOST        = os.getenv('MW_HOST', '127.0.0.1')
# canonical · 改这里只此一处 · daemon.py 必须 from server.config import PORT
# 2026-08-06 verifier 提示:历史曾跑 8093(被僵尸进程占 8086 时临时换),daemon.py 现在与 config.py 同步
PORT        = 8086
# DEBUG 默认 1(开发模式,启用 reloader)· 生产(detached daemon)务必 MW_DEBUG=0
# 走 env 切换,daemon.py 在 Popen 前强制写 0,关闭 werkzeug watchdog(避免 server.out 噪音)
DEBUG       = os.getenv('MW_DEBUG', '1' if __debug__ else '0') == '1'

# 限制
ALLOWED_EXTS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}
MAX_UPLOAD  = 16 * 1024 * 1024       # 16MB

# CORS
# dev 默认 '*'(本地开发全开)
# prod 设 MW_CORS_ORIGIN='https://your.domain'(空串 = 不带 CORS 头,浏览器拒绝跨域)
CORS_ORIGIN = os.getenv('MW_CORS_ORIGIN', '*')

# 写权限白名单(铁律 #6)
# 任何 remote_addr 不在白名单 且 method 是写操作 → 返 403
# 默认本机环回(127.0.0.1 + ::1) + ::ffff:127.0.0.1(IPv4-mapped IPv6)
# 临时 LAN 例外:`MW_ALLOWED_LAN_IPS=192.168.1.5,10.0.0.20 python scripts/daemon.py`
WRITE_METHODS = frozenset({'POST', 'PUT', 'DELETE', 'PATCH'})
_DEFAULT_LAN_IPS = {'127.0.0.1', '::1', '::ffff:127.0.0.1'}
ALLOWED_LAN_IPS = _DEFAULT_LAN_IPS | {
    ip.strip() for ip in os.getenv('MW_ALLOWED_LAN_IPS', '').split(',') if ip.strip()
}

# AI 视觉默认超时
VISION_TIMEOUT = 120
