"""项目管理 · /api/projects
- GET/POST 列表/创建
- GET/<id> 详情(含关联材料 + 总造价)
- POST/<id>/materials 添加
- DELETE/<id>/materials/<pm_id> 移除
- GET/<id>/cost-summary 造价汇总
- GET/<id>/export/docx 导出数据(供前端生成 docx)
"""
from flask import Blueprint, request, jsonify
from ..core import get_db, rows_to_list, row_to_dict

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
    db = get_db()
    data = request.get_json() or {}
    name  = data.get('name', '未命名项目')
    ptype = data.get('type', '')
    area  = data.get('area', 0)
    count = db.execute('SELECT COUNT(*) FROM projects').fetchone()[0]
    code  = f"PRJ_{str(count + 1).zfill(4)}"
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
    total = sum(
        float(r['unit_cost'] or 0) * float(r['quantity'] or 0) * float(r['loss_factor'] or 1)
        for r in materials
    )
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
    """按 category + unit 汇总造价"""
    db = get_db()
    rows = db.execute('''
        SELECT
            c.name  AS category_name,
            m.unit,
            SUM(m.unit_price * pm.quantity * m.loss_factor) AS material_cost,
            SUM(m.labor_cost * pm.quantity) AS labor_cost,
            SUM((m.unit_price + m.labor_cost) * pm.quantity * m.loss_factor) AS total
        FROM project_materials pm
        JOIN materials m ON pm.material_id = m.id
        LEFT JOIN categories c ON m.category_id = c.id
        WHERE pm.project_id = ?
        GROUP BY c.name, m.unit
        ORDER BY total DESC
    ''', [project_id]).fetchall()
    items    = rows_to_list(rows)
    total    = sum(float(r['total'] or 0) for r in items)
    area_row = db.execute('SELECT area FROM projects WHERE id = ?', [project_id]).fetchone()
    area     = float(area_row['area'] or 0) if area_row else 0
    return jsonify({
        'items': items,
        'grand_total': round(total, 2),
        'area': area,
        'cost_per_sqm': round(total / max(area, 1), 2),
    })


@bp.get('/api/projects/<int:project_id>/export/docx')
def export_docx(project_id: int):
    """返回项目结构化数据(供前端生成 docx)"""
    db = get_db()
    project = db.execute('SELECT * FROM projects WHERE id = ?', [project_id]).fetchone()
    if not project:
        return jsonify({'error': '项目不存在'}), 404
    materials = db.execute('''
        SELECT pm.*, m.name_cn, m.sub_category, m.unit, m.unit_price, m.labor_cost,
               m.specs, m.fire_rating, m.suppliers_json, c.name AS category_name
        FROM project_materials pm
        JOIN materials m ON pm.material_id = m.id
        LEFT JOIN categories c ON m.category_id = c.id
        WHERE pm.project_id = ?
    ''', [project_id]).fetchall()
    out = {'project': row_to_dict(project), 'materials': [], 'total_cost': 0}
    for r in materials:
        d = row_to_dict(r)
        sub = (float(r['unit_price'] or 0) + float(r['labor_cost'] or 0)) \
              * float(r['quantity'] or 0) * float(r['loss_factor'] or 1.0)
        d['subtotal'] = round(sub, 2)
        out['materials'].append(d)
        out['total_cost'] += sub
    out['total_cost'] = round(out['total_cost'], 2)
    return jsonify(out)


def register(app): app.register_blueprint(bp)
