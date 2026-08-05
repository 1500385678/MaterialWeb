"""Flask app 实例 + 通用工具(DB 连接 / row 转换 / CORS)
所有 handler 通过 from .core import get_db, row_to_dict, rows_to_list 引用
"""
import json
import sqlite3
from flask import Flask, g, request, send_from_directory
from . import config


def create_app() -> Flask:
    """工厂模式,便于测试和多实例"""
    app = Flask(
        __name__,
        static_folder=str(config.STATIC_DIR),
        static_url_path='/',
    )
    app.config['JSON_AS_ASCII'] = False
    app.config['MAX_CONTENT_LENGTH'] = config.MAX_UPLOAD

    # DB 连接生命周期
    @app.teardown_appcontext
    def close_db(_exc):
        db = g.pop('db', None)
        if db is not None:
            db.close()

    # CORS + 静态防缓存
    @app.after_request
    def add_cors(resp):
        resp.headers['Access-Control-Allow-Origin']  = config.CORS_ORIGIN
        resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        ct = resp.headers.get('Content-Type', '')
        if any(s in ct for s in ('text/html', 'text/css', 'javascript')):
            resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            resp.headers['Pragma']        = 'no-cache'
            resp.headers['Expires']       = '0'
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
