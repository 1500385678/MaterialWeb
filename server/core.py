"""Flask app 实例 + 通用工具(DB 连接 / row 转换 / CORS)
所有 handler 通过 from .core import get_db, row_to_dict, rows_to_list 引用
"""
import json
import os
import sqlite3
from flask import Flask, g, request, send_from_directory
from werkzeug.middleware.proxy_fix import ProxyFix
from . import config


# 铁律 #5 · 静态前端 no-store 白名单(精确 MIME · 小写 · 不含 charset)
# 见 CONTROL.md 铁律 #5 + tests/test_cache_headers.py
# 2026-08-11 夜间迭代批 2 改 · P2 Verifier row 71
_NO_STORE_TYPES = frozenset({
    'text/html',
    'text/css',
    'application/javascript',
    'text/javascript',
})


def create_app() -> Flask:
    """工厂模式,便于测试和多实例"""
    app = Flask(
        __name__,
        static_folder=str(config.STATIC_DIR),
        static_url_path='/',
    )
    app.config['JSON_AS_ASCII'] = False
    app.config['MAX_CONTENT_LENGTH'] = config.MAX_UPLOAD

    # 铁律 #6 · 反代场景安全(client 伪造 XFF 头会被忽略,只有反代方在 ProxyFix
    # 信任链上才生效)。MW_PROXY_COUNT 控制信任的反代层数(默认 1)。
    # 直连部署:remote_addr 仍是客户端真实 IP(无 XFF 头时不修正)
    # 反代部署:反代方需在每层都保留/追加 XFF,否则 remote_addr 退化为反代自身 IP
    proxy_count = int(os.getenv('MW_PROXY_COUNT', '1'))
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=proxy_count)

    # DB 连接生命周期
    @app.teardown_appcontext
    def close_db(_exc):
        db = g.pop('db', None)
        if db is not None:
            db.close()

    # CORS + 静态防缓存 + 写权限 IP 白名单(铁律 #6)
    @app.before_request
    def _check_write_permission():
        """写操作(POST/PUT/DELETE/PATCH)仅允许白名单 IP,GET 限流不限源

        安全前提:create_app 顶部已装 ProxyFix,request.remote_addr 已被修正为
        真实客户端 IP(直连)或最外层反代信任链上的 IP(反代部署)。
        绝不再裸读 X-Forwarded-For 头 — 客户端可任意伪造。
        """
        if request.method in config.WRITE_METHODS:
            client_ip = request.remote_addr or ''
            if client_ip not in config.ALLOWED_LAN_IPS:
                from flask import jsonify
                return jsonify({
                    'error': 'forbidden',
                    'message': f'write method {request.method} not allowed from {client_ip}',
                    'allowed': sorted(config.ALLOWED_LAN_IPS),
                }), 403
        return None

    @app.after_request
    def add_cors(resp):
        resp.headers['Access-Control-Allow-Origin']  = config.CORS_ORIGIN
        resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        # 铁律 #5 · 静态前端禁缓存(AI 改完不生效问题)
        # 白名单精确匹配:text/html, text/css, application/javascript, text/javascript
        # 不再 substring('javascript' 误伤 / 漏 application/ecmascript 等)
        # 2026-08-11 夜间迭代批 2 改 · P2 Verifier row 71
        ct = (resp.headers.get('Content-Type', '') or '').split(';')[0].strip().lower()
        if ct in _NO_STORE_TYPES:
            resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            resp.headers['Pragma']        = 'no-cache'
            resp.headers['Expires']       = '0'
            # 避免 gzip 缓存串 — 反代/浏览器按 Accept-Encoding 区分缓存条目
            resp.headers['Vary'] = 'Accept-Encoding'
        return resp

    @app.route('/<path:_>', methods=['OPTIONS'])
    def _preflight_path(_):
        return ('', 204)

    @app.route('/', methods=['GET', 'OPTIONS'])
    def index():
        """主页 — 显式路由避免 Flask 把 / 视作"只 OPTIONS"返 405"""
        if request.method == 'OPTIONS':
            return ('', 204)
        return send_from_directory(config.STATIC_DIR, 'index.html')

    # 蓝图注册
    from .routes import register_blueprints
    register_blueprints(app)

    # PDF 任务线程池(P0 修 2026-08-09 夜间迭代批 3)· 延迟到第一次 submit 时才 init,
    # 避免测试场景下也拉起 worker。
    from .workers import pdf_pool
    pdf_pool.init_pool()
    return app


def get_db():
    """每个请求一个连接,g.db 缓存

    首次连接启用 WAL + 5s busy_timeout,满足 § 6.7「20 并发」铁律
    (默认 rollback journal 模式下,读阻塞读 → 20 并发必崩)
    """
    if 'db' not in g:
        g.db = sqlite3.connect(
            str(config.DB_PATH),
            timeout=10,        # 连接池锁等待 10s
        )
        g.db.row_factory = sqlite3.Row
        # WAL + NORMAL 让读不阻塞写,满足 20 并发不卡
        g.db.execute('PRAGMA journal_mode=WAL')
        g.db.execute('PRAGMA synchronous=NORMAL')
        g.db.execute('PRAGMA busy_timeout=5000')
    return g.db


def row_to_dict(row):
    """Row → dict,自动尝试解析 JSON 字段"""
    if row is None:
        return None
    d = dict(row)
    for k, v in d.items():
        if isinstance(v, str):
            try:
                d[k] = json.loads(v)
            except (json.JSONDecodeError, TypeError):
                pass
    return d


def rows_to_list(rows):
    return [row_to_dict(r) for r in rows]


def to_text_list(v):
    """JSON 字符串或裸字符串 → list[str]"""
    if not v:
        return []
    try:
        arr = json.loads(v)
        if isinstance(arr, list):
            return [str(x) for x in arr]
    except Exception:
        pass
    return [str(v)]
