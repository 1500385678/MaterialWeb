"""AI 选材方案 · /api/schemes
- POST /api/save_scheme       保存
- GET  /api/schemes           列表
- GET  /api/schemes/<id>      详情(含 materials)
- DELETE /api/schemes/<id>    删除
- GET  /api/schemes/<id>/reload  会话状态(分析 + 搜索 + 选中)
"""
import json
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify
from ..core import get_db

logger = logging.getLogger(__name__)

bp = Blueprint('schemes', __name__)


@bp.post('/api/save_scheme')
def save():
    """保存选材方案(含 AI 会话上下文:图片 + 分析 JSON)"""
    data = request.get_json() or {}
    name    = (data.get('name') or '').strip() or f"AI方案-{datetime.now().strftime('%Y%m%d-%H%M')}"
    desc    = (data.get('description') or '').strip()
    pid     = data.get('project_id')
    mats    = data.get('materials') or []
    img_fn  = (data.get('image_filename') or '').strip()
    analysis = data.get('analysis') or {}
    search_results = data.get('search_results') or []
    selected_ids   = data.get('selected_ids') or []

    if not mats:
        return jsonify({'error': '至少选一个材质'}), 400

    db = get_db()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ctx = {'analysis': analysis, 'search_results': search_results, 'selected_ids': selected_ids}

    cur = db.execute('''
        INSERT INTO material_schemes
            (project_id, name, description, status, created_at, image_filename, analysis_json, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (pid, name, desc, 'active', now, img_fn, json.dumps(ctx, ensure_ascii=False), now))
    sid = cur.lastrowid

    rows = [(
        sid, int(m['material_id']),
        float(m.get('score') or 0),
        m.get('score_reason') or '',
        1 if m.get('is_selected') else 0,
    ) for m in mats]
    db.executemany('''
        INSERT INTO scheme_materials (scheme_id, material_id, score, score_reason, is_selected)
        VALUES (?, ?, ?, ?, ?)
    ''', rows)
    db.commit()

    return jsonify({
        'scheme_id': sid, 'name': name, 'material_count': len(rows),
        'image_url': f'/uploads/{img_fn}' if img_fn else None,
    })


@bp.get('/api/schemes')
def list_all():
    db = get_db()
    rows = db.execute('''
        SELECT s.id, s.name, s.description, s.status, s.created_at, s.project_id,
               s.image_filename, s.updated_at, p.name AS project_name,
               (SELECT COUNT(*) FROM scheme_materials WHERE scheme_id = s.id) AS material_count
        FROM material_schemes s
        LEFT JOIN projects p ON p.id = s.project_id
        ORDER BY COALESCE(s.updated_at, s.created_at) DESC
    ''').fetchall()
    items = []
    for r in rows:
        d = dict(r)
        d['image_url'] = f"/uploads/{d['image_filename']}" if d.get('image_filename') else None
        items.append(d)
    return jsonify({'count': len(items), 'items': items})


def _parse_ctx(raw):
    if not raw: return {}
    try: return json.loads(raw)
    except (OSError, IOError, ValueError) as exc:
        logger.warning('schemes._parse_ctx: parse raw failed: %r', exc)
        return {}


@bp.get('/api/schemes/<int:sid>')
def detail(sid: int):
    db = get_db()
    s = db.execute('SELECT * FROM material_schemes WHERE id = ?', (sid,)).fetchone()
    if not s:
        return jsonify({'error': '方案不存在'}), 404
    sch = dict(s)
    if sch.get('image_filename'):
        sch['image_url'] = f"/uploads/{sch['image_filename']}"
    sch['session'] = _parse_ctx(sch.get('analysis_json'))
    rows = db.execute('''
        SELECT sm.id AS sm_id, sm.score, sm.score_reason, sm.is_selected,
               m.id, m.code, m.name_cn, m.name_en, m.visual_desc, m.unit_price, m.unit,
               m.cost_tier, m.fire_rating, c.name AS category_name
        FROM scheme_materials sm
        JOIN materials m ON m.id = sm.material_id
        LEFT JOIN categories c ON c.id = m.category_id
        WHERE sm.scheme_id = ?
        ORDER BY sm.score DESC
    ''', (sid,)).fetchall()
    sch['materials'] = [dict(r) for r in rows]
    return jsonify(sch)


@bp.delete('/api/schemes/<int:sid>')
def delete(sid: int):
    db = get_db()
    s = db.execute(
        'SELECT id, image_filename FROM material_schemes WHERE id = ?', (sid,)
    ).fetchone()
    if not s:
        return jsonify({'error': '方案不存在'}), 404
    db.execute('DELETE FROM scheme_materials WHERE scheme_id = ?', (sid,))
    db.execute('DELETE FROM material_schemes WHERE id = ?', (sid,))
    db.commit()
    return jsonify({'deleted': sid, 'image_filename': s['image_filename']})


@bp.get('/api/schemes/<int:sid>/reload')
def reload(sid: int):
    """返回会话状态(分析 + 搜索 + 选中),供前端跳到 AI 流程任意步"""
    db = get_db()
    s = db.execute('SELECT * FROM material_schemes WHERE id = ?', (sid,)).fetchone()
    if not s:
        return jsonify({'error': '方案不存在'}), 404
    sch = dict(s)
    if sch.get('image_filename'):
        sch['image_url'] = f"/uploads/{sch['image_filename']}"
    return jsonify({
        'scheme_id': sid, 'name': sch['name'], 'description': sch['description'],
        'image_url': sch.get('image_url'), 'image_filename': sch.get('image_filename'),
        'session': _parse_ctx(sch.get('analysis_json')),
    })


def register(app): app.register_blueprint(bp)
