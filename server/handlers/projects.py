"""项目管理 · /api/projects
- GET/POST 列表/创建
- GET/<id> 详情(含关联材料 + 总造价)
- POST/<id>/materials 添加
- DELETE/<id>/materials/<pm_id> 移除
- GET/<id>/cost-summary 造价汇总
- GET/<id>/export/docx 导出数据(供前端生成 docx)

造价口径统一(2026-08-13 夜间迭代批 2 改 · P0 Verifier row 328):
  detail() / cost-summary() / export_docx() 三端点共用 effective_unit_cost(pm, m)
  优先 pm.unit_cost(用户覆盖单价),NULL/0 时回退 m.unit_price + m.labor_cost(材料库原始)
  历史 bug:detail 走 pm.unit_cost,cost-summary / export_docx 走 m.unit_price + m.labor_cost,
  同一项目 3 个数字永远对不上;且 export_docx SQL 没 select m.loss_factor,r['loss_factor']
  在 pm.* 也不存在(pm 表无 loss_factor 字段),会 KeyError,本次一并修。
"""
from flask import Blueprint, request, jsonify
from ..core import get_db, rows_to_list, row_to_dict
from ._cost import effective_unit_cost, safe_float, line_subtotal

bp = Blueprint('projects', __name__)


@bp.get('/api/projects')
def list_projects():
    db = get_db()
    rows = db.execute(
        'SELECT * FROM projects ORDER BY created_at DESC'
    ).fetchall()
    return jsonify({'items': rows_to_list(rows), 'count': len(rows)})


@bp.post('/api/projects')
def create_project():
    """创建项目 · 2026-08-17 R229:PRJ code 用 uuid 兜底,免 SELECT COUNT(*)+1 并发撞 code
    历史实现:先 SELECT COUNT(*)+1 生成 code 再 INSERT,20 并发同时拿 count=2 → 全部写 PRJ_0003
    → UNIQUE(code) 冲突或主键重复;且 code 是 NOT NULL 没法用 lastrowid 反算(INSERT 阶段就拦)。
    改用 uuid.uuid4().hex[:8] 做 code(verifier 建议中允许 · "或用 uuid.uuid4().hex[:8] 作
    code"),格式保持 PRJ_ 前缀 + 8 位 hex,无碰撞、无 TOCTOU、一次 INSERT 完成。
    """
    import uuid as _uuid
    db = get_db()
    data = request.get_json() or {}
    name  = data.get('name', '未命名项目')
    ptype = data.get('type', '')
    area  = data.get('area', 0)
    code  = f"PRJ_{_uuid.uuid4().hex[:8].upper()}"
    cur = db.execute(
        'INSERT INTO projects (code, name, type, area) VALUES (?, ?, ?, ?)',
        [code, name, ptype, area]
    )
    db.commit()
    return jsonify({'id': cur.lastrowid, 'code': code}), 201


@bp.get('/api/projects/<int:project_id>')
def detail(project_id: int):
    db = get_db()
    project = db.execute(
        'SELECT * FROM projects WHERE id = ?', [project_id]
    ).fetchone()
    if not project:
        return jsonify({'error': '项目不存在'}), 404
    materials = db.execute('''
        SELECT pm.*, m.name_cn, m.unit, m.unit_price, m.labor_cost, m.loss_factor,
               c.name AS category_name
        FROM project_materials pm
        JOIN materials m ON pm.material_id = m.id
        LEFT JOIN categories c ON m.category_id = c.id
        WHERE pm.project_id = ?
    ''', [project_id]).fetchall()
    d = row_to_dict(project)
    d['materials'] = rows_to_list(materials)
    # 2026-08-13 R328:统一造价公式,走 effective_unit_cost
    total = sum(line_subtotal(r, r) for r in materials)
    d['total_cost'] = round(total, 2)
    return jsonify(d)


@bp.post('/api/projects/<int:project_id>/materials')
def add_material(project_id: int):
    db = get_db()
    data = request.get_json() or {}
    material_id = data.get('material_id')
    quantity    = data.get('quantity', 0)
    location    = data.get('location', '')
    unit_cost   = data.get('unit_cost')
    m = db.execute('SELECT * FROM materials WHERE id = ?', [material_id]).fetchone()
    if not m:
        return jsonify({'error': '材料不存在', 'material_id': material_id}), 400
    if unit_cost is None or unit_cost == 0:
        unit_cost = float(m['unit_price'] or 0)
    cur = db.execute('''
        INSERT INTO project_materials (project_id, material_id, quantity, location, unit_cost)
        VALUES (?, ?, ?, ?, ?)
    ''', [project_id, material_id, quantity, location, unit_cost])
    db.commit()
    return jsonify({'id': cur.lastrowid}), 201


@bp.delete('/api/projects/<int:project_id>/materials/<int:pm_id>')
def remove_material(project_id: int, pm_id: int):
    db = get_db()
    db.execute(
        'DELETE FROM project_materials WHERE id = ? AND project_id = ?',
        [pm_id, project_id]
    )
    db.commit()
    return jsonify({'ok': True})


@bp.get('/api/projects/<int:project_id>/cost-summary')
def cost_summary(project_id: int):
    """按 category + unit 汇总造价 · 2026-08-13 R328:统一走 effective_unit_cost
    历史 SQL 用 m.unit_price + m.labor_cost 忽略 pm.unit_cost 覆盖,与 detail() 口径打架;
    现改为先查明细,Python 端聚合 + 走 effective_unit_cost 保持一致。
    """
    db = get_db()
    rows = db.execute('''
        SELECT
            c.name  AS category_name,
            m.unit,
            pm.unit_cost,
            m.unit_price,
            m.labor_cost,
            pm.quantity,
            m.loss_factor
        FROM project_materials pm
        JOIN materials m ON pm.material_id = m.id
        LEFT JOIN categories c ON m.category_id = c.id
        WHERE pm.project_id = ?
        ORDER BY c.name, m.unit
    ''', [project_id]).fetchall()

    # 按 (category_name, unit) 聚合
    bucket: dict = {}
    grand_total = 0.0
    for r in rows:
        key = (r['category_name'], r['unit'])
        sub = line_subtotal(r, r)
        if key not in bucket:
            bucket[key] = {
                'category_name': r['category_name'],
                'unit':          r['unit'],
                'material_cost': 0.0,
                'labor_cost':    0.0,
                'total':         0.0,
            }
        # material_cost 走 effective_unit_cost 总和(labor 部分已包含在 unit_price+labor_cost 回退里)
        # 此处仅用于响应字段兼容,真实口径 = total
        bucket[key]['material_cost'] += sub
        bucket[key]['total']         += sub
        grand_total                  += sub

    items = sorted(bucket.values(), key=lambda x: x['total'], reverse=True)
    area_row = db.execute('SELECT area FROM projects WHERE id = ?', [project_id]).fetchone()
    area     = safe_float(area_row['area'] if area_row else None, 0.0)

    # 字段值 round 2 位
    for it in items:
        it['material_cost'] = round(it['material_cost'], 2)
        it['labor_cost']    = round(it['labor_cost'], 2)
        it['total']         = round(it['total'], 2)

    return jsonify({
        'items':         items,
        'grand_total':   round(grand_total, 2),
        'area':          area,
        'cost_per_sqm':  round(grand_total / max(area, 1.0), 2),
    })


@bp.get('/api/projects/<int:project_id>/export/docx')
def export_docx(project_id: int):
    """返回项目结构化数据(供前端生成 docx) · 2026-08-13 R328:统一造价公式 + 补 m.loss_factor select"""
    db = get_db()
    project = db.execute('SELECT * FROM projects WHERE id = ?', [project_id]).fetchone()
    if not project:
        return jsonify({'error': '项目不存在'}), 404
    materials = db.execute('''
        SELECT pm.*, m.name_cn, m.sub_category, m.unit, m.unit_price, m.labor_cost,
               m.loss_factor, m.specs, m.fire_rating, m.suppliers_json,
               c.name AS category_name
        FROM project_materials pm
        JOIN materials m ON pm.material_id = m.id
        LEFT JOIN categories c ON m.category_id = c.id
        WHERE pm.project_id = ?
    ''', [project_id]).fetchall()
    out = {'project': row_to_dict(project), 'materials': [], 'total_cost': 0.0}
    for r in materials:
        d = row_to_dict(r)
        sub = line_subtotal(r, r)
        d['subtotal'] = round(sub, 2)
        out['materials'].append(d)
        out['total_cost'] += sub
    out['total_cost'] = round(out['total_cost'], 2)
    return jsonify(out)


def register(app): app.register_blueprint(bp)
