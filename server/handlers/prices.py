"""价格库跨库查询 · /api/material_price/<material_id>
- 价格库是独立 db(MaterialWebPrices),跨 db 读取不在 g.db 缓存里
- 通过 material_price_keywords.json 映射 MaterialWeb 18 种材料 → 价格库关键词
- 返回当前价(最新 valid_from)/多档价(同 material_name 不同 spec/craft/brand_tier)
"""
import json
import sqlite3
from flask import Blueprint, jsonify
from ..core import get_db
from .. import config

bp = Blueprint('prices', __name__)

_KEYWORDS_CACHE = None


def _load_keywords() -> dict:
    """读 MaterialWeb 18 材料 → 价格库关键词 OR 列表 映射,缓存到模块全局"""
    global _KEYWORDS_CACHE
    if _KEYWORDS_CACHE is None:
        with open(config.PRICES_KEYWORDS_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # 去掉 _comment
        _KEYWORDS_CACHE = {k: v for k, v in data.items() if not k.startswith('_')}
    return _KEYWORDS_CACHE


def _get_prices_db():
    """每次新建连接 — 价格库是只读,放 g.db 反而污染主请求连接池"""
    conn = sqlite3.connect(str(config.PRICES_DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


@bp.get('/api/material_price/<int:material_id>')
def material_price(material_id: int):
    """单材料当前价

    1. 查 MaterialWeb 材料的 code
    2. 按 mapping 拿关键词列表
    3. 跨 db 查 material_spec_prices LIKE 关键词
    4. 按 valid_from DESC 排序,返回最新价 + 全部价档
    """
    db = get_db()
    row = db.execute('SELECT id, code, name_cn FROM materials WHERE id = ?', [material_id]).fetchone()
    if not row:
        return jsonify({'error': '材料不存在', 'material_id': material_id}), 404

    code = row['code']
    name_cn = row['name_cn']
    keywords = _load_keywords().get(code, [])

    if not keywords:
        return jsonify({
            'material_id': material_id,
            'material_code': code,
            'material_name': name_cn,
            'keywords': [],
            'latest': None,
            'tiers': [],
            'message': '本材料暂未配置价格库关键词',
        })

    # 跨 db 查价格
    pdb = _get_prices_db()
    try:
        # 用 OR 拼接 LIKE
        where_clauses = []
        params = []
        for kw in keywords:
            where_clauses.append('material_name LIKE ?')
            params.append(f'%{kw}%')
        where_sql = ' OR '.join(where_clauses)
        rows = pdb.execute(f'''
            SELECT material_name, category, spec, brand_tier, craft,
                   unit, unit_price_min, unit_price_max, unit_price_avg,
                   price_type, fluctuation, valid_from, valid_to, source_doc
            FROM material_spec_prices
            WHERE {where_sql}
            ORDER BY valid_from DESC, id
        ''', params).fetchall()
    finally:
        pdb.close()

    if not rows:
        return jsonify({
            'material_id': material_id,
            'material_code': code,
            'material_name': name_cn,
            'keywords': keywords,
            'latest': None,
            'tiers': [],
            'message': '价格库暂无对应条目',
        })

    items = [dict(r) for r in rows]
    latest = items[0]  # 已经在 SQL 端按 valid_from DESC 排

    return jsonify({
        'material_id': material_id,
        'material_code': code,
        'material_name': name_cn,
        'keywords': keywords,
        'latest': {
            'material_name': latest['material_name'],
            'category': latest['category'],
            'spec': latest['spec'],
            'brand_tier': latest['brand_tier'],
            'craft': latest['craft'],
            'unit': latest['unit'],
            'unit_price_min': latest['unit_price_min'],
            'unit_price_max': latest['unit_price_max'],
            'unit_price_avg': latest['unit_price_avg'],
            'price_type': latest['price_type'],
            'fluctuation': latest['fluctuation'],
            'valid_from': latest['valid_from'],
            'valid_to': latest['valid_to'],
            'source_doc': latest['source_doc'],
        },
        'tiers': items,  # 所有价档,前端可展开
        'count': len(items),
    })


@bp.get('/api/prices')
def search_prices():
    """价格库全局关键词搜索(不限 material_id)
    q=花岗岩 → 跨 db 查 material_spec_prices LIKE
    """
    from flask import request
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify({'error': '缺少 q 参数', 'results': []}), 400
    pdb = _get_prices_db()
    try:
        rows = pdb.execute('''
            SELECT material_name, category, spec, brand_tier, unit,
                   unit_price_min, unit_price_max, unit_price_avg,
                   price_type, fluctuation, valid_from
            FROM material_spec_prices
            WHERE material_name LIKE ?
            ORDER BY valid_from DESC
            LIMIT 50
        ''', [f'%{q}%']).fetchall()
    finally:
        pdb.close()
    return jsonify({
        'q': q,
        'count': len(rows),
        'results': [dict(r) for r in rows],
    })


@bp.get('/api/prices/stats')
def prices_stats():
    """价格库统计信息(给前端 banner/loading 用)"""
    pdb = _get_prices_db()
    try:
        out = {
            'material_spec_prices': pdb.execute('SELECT COUNT(*) AS c FROM material_spec_prices').fetchone()['c'],
            'suppliers':            pdb.execute('SELECT COUNT(*) AS c FROM suppliers').fetchone()['c'],
            'cost_breakdowns':      pdb.execute('SELECT COUNT(*) AS c FROM cost_breakdowns').fetchone()['c'],
            'regions':              pdb.execute('SELECT COUNT(*) AS c FROM regions').fetchone()['c'],
        }
        out['distinct_materials'] = pdb.execute('SELECT COUNT(DISTINCT material_name) AS c FROM material_spec_prices').fetchone()['c']
        out['source_doc'] = 'MaterialWebPrices (github.com/1500385678/MaterialWebPrices)'
    finally:
        pdb.close()
    return jsonify(out)


def register(app): app.register_blueprint(bp)
