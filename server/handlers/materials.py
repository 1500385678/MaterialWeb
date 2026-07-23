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
    db = get_db()
    q = request.args
    sql = '''
        SELECT m.*, c.name AS category_name, c.code AS category_code
        FROM materials m
        LEFT JOIN categories c ON m.category_id = c.id
        WHERE m.status = 'active'
    '''
    params = []
    if q.get('category'):
        sql += ' AND c.code LIKE ?'
        params.append(f"{q['category']}%")
    if q.get('fire_rating'):
        sql += ' AND m.fire_rating = ?'
        params.append(q['fire_rating'])
    if q.get('cost_tier'):
        sql += ' AND m.cost_tier = ?'
        params.append(q['cost_tier'])
    if q.get('keyword'):
        sql += ' AND (m.name_cn LIKE ? OR m.name_en LIKE ? OR m.sub_category LIKE ?)'
        kw = f"%{q['keyword']}%"
        params.extend([kw, kw, kw])
    order_key = q.get('order_by', 'name_cn')
    sql += ' ORDER BY ' + ORDER_BY_MAP.get(order_key, 'm.name_cn')
    if q.get('limit'):
        try: sql += ' LIMIT ' + str(int(q['limit']))
        except Exception: pass
    rows = db.execute(sql, params).fetchall()
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


def register(app): app.register_blueprint(bp)
