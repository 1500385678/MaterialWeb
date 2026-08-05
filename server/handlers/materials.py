"""材料 CRUD + 搜索 · /api/materials
- GET /api/materials          列表(支持 category / fire_rating / cost_tier / keyword / order_by)
- GET /api/materials/<id>     详情(含 suppliers)
- GET /api/materials/search?q 关键词搜索(limit 50)
"""
import json
from flask import Blueprint, request, jsonify
from ..core import get_db, rows_to_list, row_to_dict

bp = Blueprint('materials', __name__)

# 允许的排序键 (防 SQL 注入)
ORDER_BY_MAP = {
    'name_cn':        'm.name_cn',
    'created_at_desc': 'm.created_at DESC',
    'created_at':     'm.created_at',
}


def _enrich(row: dict) -> dict:
    """把 image_urls JSON 解析成 list,方便前端直接用"""
    if row.get('image_urls'):
        try: row['images'] = json.loads(row['image_urls']) or []
        except Exception: row['images'] = []
    else:
        row['images'] = []
    return row


@bp.get('/api/materials')
def list_materials():
    """材料列表(分页)

    查询参数:
      - category / fire_rating / cost_tier / keyword: 过滤(同前)
      - order_by: 排序键(防 SQL 注入,见 ORDER_BY_MAP)
      - page: 1-based 页码(默认 1)
      - page_size: 每页条数(默认 24,最大 200)
      - limit: 兼容旧版,直接 LIMIT n(无分页 total),保留不动

    返回(分页模式):
      { rows: [...], total: int, page: int, page_size: int }

    返回(legacy limit 模式):
      [...]  —— 保持老前端兼容
    """
    db = get_db()
    q = request.args
    where_sql = " WHERE m.status = 'active'"
    params = []
    if q.get('category'):
        where_sql += ' AND c.code LIKE ?'
        params.append(f"{q['category']}%")
    if q.get('fire_rating'):
        where_sql += ' AND m.fire_rating = ?'
        params.append(q['fire_rating'])
    if q.get('cost_tier'):
        where_sql += ' AND m.cost_tier = ?'
        params.append(q['cost_tier'])
    if q.get('keyword'):
        where_sql += ' AND (m.name_cn LIKE ? OR m.name_en LIKE ? OR m.sub_category LIKE ?)'
        kw = f"%{q['keyword']}%"
        params.extend([kw, kw, kw])
    order_key = q.get('order_by', 'name_cn')
    order_sql = ' ORDER BY ' + ORDER_BY_MAP.get(order_key, 'm.name_cn')

    # —— 分页模式 (page + page_size) ——
    if q.get('page') or q.get('page_size'):
        try:
            page = max(1, int(q.get('page', 1)))
            page_size = int(q.get('page_size', 24))
        except (TypeError, ValueError):
            page, page_size = 1, 24
        # 上限 200,避免误传 page_size=10000 一次拉爆
        page_size = max(1, min(page_size, 200))
        offset = (page - 1) * page_size

        list_sql = (
            'SELECT m.*, c.name AS category_name, c.code AS category_code '
            'FROM materials m '
            'LEFT JOIN categories c ON m.category_id = c.id'
            + where_sql + order_sql + ' LIMIT ? OFFSET ?'
        )
        rows = db.execute(list_sql, params + [page_size, offset]).fetchall()

        count_sql = (
            'SELECT COUNT(*) AS total '
            'FROM materials m '
            'LEFT JOIN categories c ON m.category_id = c.id'
            + where_sql
        )
        total = db.execute(count_sql, params).fetchone()['total']

        return jsonify({
            'rows': [_enrich(r) for r in rows_to_list(rows)],
            'total': total,
            'page': page,
            'page_size': page_size,
        })

    # —— legacy 模式 (limit only) ——
    list_sql = (
        'SELECT m.*, c.name AS category_name, c.code AS category_code '
        'FROM materials m '
        'LEFT JOIN categories c ON m.category_id = c.id'
        + where_sql + order_sql
    )
    if q.get('limit'):
        try:
            list_sql += ' LIMIT ' + str(int(q['limit']))
        except (TypeError, ValueError):
            pass
    rows = db.execute(list_sql, params).fetchall()
    return jsonify([_enrich(r) for r in rows_to_list(rows)])


@bp.get('/api/materials/search')
def search():
    """关键词全文搜索(limit 50)"""
    keyword = request.args.get('q', '').strip()
    if not keyword:
        return jsonify([])
    db = get_db()
    rows = db.execute('''
        SELECT m.*, c.name AS category_name
        FROM materials m
        LEFT JOIN categories c ON m.category_id = c.id
        WHERE m.status = 'active'
          AND (m.name_cn LIKE ? OR m.name_en LIKE ? OR m.sub_category LIKE ?)
        ORDER BY m.name_cn
        LIMIT 50
    ''', [f'%{keyword}%', f'%{keyword}%', f'%{keyword}%']).fetchall()
    return jsonify(rows_to_list(rows))


@bp.get('/api/materials/<int:material_id>')
def detail(material_id: int):
    """材料详情(自动补 suppliers)"""
    db = get_db()
    row = db.execute('''
        SELECT m.*, c.name AS category_name, c.code AS category_code
        FROM materials m
        LEFT JOIN categories c ON m.category_id = c.id
        WHERE m.id = ?
    ''', [material_id]).fetchone()
    if not row:
        return jsonify({'error': '材料不存在'}), 404

    d = row_to_dict(row)
    _enrich(d)
    if d.get('suppliers_json'):
        ids = d['suppliers_json'] if isinstance(d['suppliers_json'], list) else []
        if ids:
            ph = ','.join('?' * len(ids))
            sup = db.execute(
                f'SELECT * FROM suppliers WHERE id IN ({ph})', ids
            ).fetchall()
            d['suppliers'] = rows_to_list(sup)
    return jsonify(d)


@bp.get('/api/materials/<int:material_id>/references')
def material_references(material_id: int):
    """材料真实工程参考"""
    db = get_db()
    rows = db.execute('''
        SELECT id, material_id, project_name, designer, city, year, part,
               image_url, image_source, comment, sort_order
        FROM material_references
        WHERE material_id = ?
        ORDER BY sort_order, id
    ''', [material_id]).fetchall()
    return jsonify(rows_to_list(rows))


@bp.get('/api/materials/languages/all')
def all_languages():
    """所有用过的 language 词云(去重 + 频次)"""
    db = get_db()
    rows = db.execute('''
        SELECT material_language FROM materials
        WHERE status = 'active' AND material_language IS NOT NULL
          AND material_language != '[]'
    ''').fetchall()
    from collections import Counter
    cnt = Counter()
    for r in rows:
        langs = r['material_language']
        if isinstance(langs, str):
            try:
                langs = json.loads(langs)
            except Exception:
                continue
        if isinstance(langs, list):
            for t in langs:
                cnt[t] += 1
    return jsonify([{'tag': t, 'count': c} for t, c in cnt.most_common()])


def register(app): app.register_blueprint(bp)
