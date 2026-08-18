#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
建筑材料数据库 API 服务
运行方式: python api_server.py
访问地址: http://localhost:5188
"""

import os
import json
import sqlite3
import hashlib
import qrcode
import subprocess
import re
import uuid
import base64
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

from flask import (
    Flask, g, request, jsonify,
    send_from_directory, send_file
)

# ============================================================
# 配置
# ============================================================
BASE_DIR   = Path(__file__).parent
DB_PATH    = BASE_DIR / 'materials.db'
QR_DIR     = BASE_DIR / 'qr_codes'
STATIC_DIR = BASE_DIR.parent / 'MaterialWeb-v1.0' / 'client'  # 2026-07-14 改:MaterialWeb-v1.0 的 index.html 在 client/ 下
UPLOAD_DIR = BASE_DIR / 'uploads'
ALLOWED_EXTS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}

os.makedirs(QR_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = Flask(__name__, static_folder=str(STATIC_DIR), static_url_path='/')
app.config['JSON_AS_ASCII'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

# CORS: 允许所有源（本地开发用，2026-07-01 增加）
@app.after_request
def add_cors(resp):
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    # HTML 静态文件防缓存（避免改完 CSS/JS 浏览器看不到）
    ct = resp.headers.get('Content-Type', '')
    if 'text/html' in ct or 'text/css' in ct or 'javascript' in ct:
        resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        resp.headers['Pragma'] = 'no-cache'
        resp.headers['Expires'] = '0'
    return resp
@app.route('/<path:_>', methods=['OPTIONS'])
@app.route('/', methods=['OPTIONS'])
def _preflight(_=None):
    return ('', 204)

# ============================================================
# 数据库连接
# ============================================================
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(str(DB_PATH))
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def row_to_dict(row):
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

# ============================================================
# 辅助函数
# ============================================================
def gen_qr_code(content: str, filename: str) -> str:
    """生成二维码，返回文件路径"""
    qr_path = QR_DIR / f"{filename}.png"
    if not qr_path.exists():
        qr = qrcode.make(content)
        qr.save(str(qr_path))
    return str(qr_path)

def calc_material_cost(material_row, quantity: float) -> dict:
    """计算单种材料成本"""
    unit_price = float(material_row['unit_price'] or 0)
    labor      = float(material_row['labor_cost'] or 0)
    loss       = float(material_row['loss_factor'] or 1.0)

    material_cost = unit_price * quantity * loss
    labor_cost    = labor * quantity
    total         = material_cost + labor_cost

    return {
        'material_cost': round(material_cost, 2),
        'labor_cost':    round(labor_cost, 2),
        'total_cost':    round(total, 2),
        'loss_factor':   loss,
        'unit_price':    unit_price,
        'labor_unit':    labor
    }

# ============================================================
# 首页
# ============================================================
@app.route('/')
def index():
    return send_from_directory(STATIC_DIR, 'index.html')

# ============================================================
# 材料 API
# ============================================================

@app.route('/api/materials')
def get_materials():
    """获取材料列表，支持过滤"""
    db = get_db()
    query = request.args

    sql = '''
        SELECT m.*, c.name AS category_name, c.code AS category_code
        FROM materials m
        LEFT JOIN categories c ON m.category_id = c.id
        WHERE m.status = 'active'
    '''
    params = []

    if query.get('category'):
        sql += ' AND c.code LIKE ?'
        params.append(f"{query['category']}%")

    if query.get('fire_rating'):
        sql += ' AND m.fire_rating = ?'
        params.append(query['fire_rating'])

    if query.get('cost_tier'):
        sql += ' AND m.cost_tier = ?'
        params.append(query['cost_tier'])

    if query.get('keyword'):
        sql += ' AND (m.name_cn LIKE ? OR m.name_en LIKE ? OR m.sub_category LIKE ?)'
        kw = f"%{query['keyword']}%"
        params.extend([kw, kw, kw])

    sql += ' ORDER BY m.name_cn'

    rows = db.execute(sql, params).fetchall()
    return jsonify(rows_to_list(rows))

@app.route('/api/materials/<int:material_id>')
def get_material(material_id):
    """获取单个材料详情"""
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

    # 补充供应商详情
    if d.get('suppliers_json'):
        supplier_ids = d['suppliers_json'] if isinstance(d['suppliers_json'], list) else []
        suppliers = db.execute(
            'SELECT * FROM suppliers WHERE id IN ({})'.format(
                ','.join('?' * len(supplier_ids))
            ), supplier_ids
        ).fetchall() if supplier_ids else []
        d['suppliers'] = rows_to_list(suppliers)

    return jsonify(d)

@app.route('/api/materials/search')
def search_materials():
    """关键词搜索材料"""
    keyword = request.args.get('q', '')
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

# ============================================================
# 分类 API
# ============================================================

@app.route('/api/categories')
def get_categories():
    """获取分类树"""
    db = get_db()
    rows = db.execute(
        'SELECT * FROM categories ORDER BY sort_order, code'
    ).fetchall()
    return jsonify(rows_to_list(rows))

# ============================================================
# 供应商 API
# ============================================================

@app.route('/api/suppliers')
def get_suppliers():
    """获取供应商列表"""
    db = get_db()
    rows = db.execute('SELECT * FROM suppliers ORDER BY name').fetchall()
    return jsonify(rows_to_list(rows))

# ============================================================
# 考试知识 API
# ============================================================

@app.route('/api/exam')
def get_exam_knowledge():
    """获取考试知识点"""
    db = get_db()
    rows = db.execute('''
        SELECT e.*, c.name AS category_name
        FROM exam_knowledge e
        LEFT JOIN categories c ON e.category_id = c.id
        ORDER BY e.chapter, e.section
    ''').fetchall()
    return jsonify(rows_to_list(rows))

@app.route('/api/exam/chapter/<chapter>')
def get_exam_by_chapter(chapter):
    """按章节获取考试知识点"""
    db = get_db()
    rows = db.execute('''
        SELECT e.*, c.name AS category_name
        FROM exam_knowledge e
        LEFT JOIN categories c ON e.category_id = c.id
        WHERE e.chapter = ?
        ORDER BY e.section
    ''', [chapter]).fetchall()
    return jsonify(rows_to_list(rows))

# ============================================================
# 项目管理 API
# ============================================================

@app.route('/api/projects')
def get_projects():
    """获取项目列表"""
    db = get_db()
    rows = db.execute('SELECT * FROM projects ORDER BY created_at DESC').fetchall()
    return jsonify(rows_to_list(rows))

@app.route('/api/projects', methods=['POST'])
def create_project():
    """创建项目"""
    db = get_db()
    data = request.get_json()

    name = data.get('name', '未命名项目')
    ptype = data.get('type', '')
    area  = data.get('area', 0)

    # 生成项目编号
    count = db.execute('SELECT COUNT(*) FROM projects').fetchone()[0]
    code = f"PRJ_{str(count + 1).zfill(4)}"

    cursor = db.execute('''
        INSERT INTO projects (code, name, type, area)
        VALUES (?, ?, ?, ?)
    ''', [code, name, ptype, area])
    db.commit()

    return jsonify({'id': cursor.lastrowid, 'code': code}), 201

@app.route('/api/projects/<int:project_id>')
def get_project(project_id):
    """获取项目详情"""
    db = get_db()
    project = db.execute('SELECT * FROM projects WHERE id = ?', [project_id]).fetchone()
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

    # 计算总造价
    total = sum(float(r['unit_cost'] or 0) * float(r['quantity'] or 0) * float(r['loss_factor'] or 1)
                for r in materials)
    d['total_cost'] = round(total, 2)

    return jsonify(d)

@app.route('/api/projects/<int:project_id>/materials', methods=['POST'])
def add_project_material(project_id):
    """向项目添加材料"""
    db = get_db()
    data = request.get_json()

    material_id = data.get('material_id')
    quantity    = data.get('quantity', 0)
    location    = data.get('location', '')
    unit_cost   = data.get('unit_cost')

    # 校验材料存在
    m = db.execute('SELECT * FROM materials WHERE id = ?', [material_id]).fetchone()
    if not m:
        return jsonify({'error': '材料不存在', 'material_id': material_id}), 400

    # 如果没指定单价，从材料表取
    if unit_cost is None or unit_cost == 0:
        unit_cost = float(m['unit_price'] or 0)

    cursor = db.execute('''
        INSERT INTO project_materials (project_id, material_id, quantity, location, unit_cost)
        VALUES (?, ?, ?, ?, ?)
    ''', [project_id, material_id, quantity, location, unit_cost])
    db.commit()

    return jsonify({'id': cursor.lastrowid}), 201

@app.route('/api/projects/<int:project_id>/materials/<int:pm_id>', methods=['DELETE'])
def remove_project_material(project_id, pm_id):
    """从项目移除材料"""
    db = get_db()
    db.execute('DELETE FROM project_materials WHERE id = ? AND project_id = ?', [pm_id, project_id])
    db.commit()
    return jsonify({'ok': True})

@app.route('/api/projects/<int:project_id>/cost-summary')
def get_cost_summary(project_id):
    """获取项目材料成本汇总"""
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

    summary = rows_to_list(rows)
    grand_total = sum(float(r['total'] or 0) for r in summary)

    return jsonify({
        'items': summary,
        'grand_total': round(grand_total, 2),
        'area': db.execute('SELECT area FROM projects WHERE id = ?', [project_id]).fetchone()['area'] or 0,
        'cost_per_sqm': round(grand_total / max(
            db.execute('SELECT area FROM projects WHERE id = ?', [project_id]).fetchone()['area'] or 1, 1
        ), 2)
    })

# ============================================================
# 二维码 API
# ============================================================

@app.route('/api/materials/<int:material_id>/qr')
def get_material_qr(material_id):
    """获取材料二维码"""
    db = get_db()
    row = db.execute('SELECT * FROM materials WHERE id = ?', [material_id]).fetchone()
    if not row:
        return jsonify({'error': '材料不存在'}), 404

    # 如果没有生成过，生成二维码
    if not row['qr_code_path'] or not Path(row['qr_code_path']).exists():
        qr_content = f"mavis://material/{row['code']}"
        filename   = f"mat_{row['code']}"
        path       = gen_qr_code(qr_content, filename)
        db.execute('UPDATE materials SET qr_code_path = ?, qr_content = ? WHERE id = ?',
                    [path, qr_content, material_id])
        db.commit()
    else:
        path = row['qr_code_path']

    return send_from_directory(QR_DIR, Path(path).name)

# ============================================================
# 文档生成 API
# ============================================================

@app.route('/api/projects/<int:project_id>/export/docx')
def export_docx(project_id):
    """导出项目材料说明书 Word 文档（简化实现，返回 JSON 结构供前端处理）"""
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

    # 构建导出数据
    export_data = {
        'project': row_to_dict(project),
        'materials': [],
        'total_cost': 0
    }

    for r in materials:
        d = row_to_dict(r)
        unit_p = float(r['unit_price'] or 0)
        labor  = float(r['labor_cost'] or 0)
        qty    = float(r['quantity'] or 0)
        loss   = float(r['loss_factor'] or 1.0)
        subtotal = (unit_p + labor) * qty * loss
        d['subtotal'] = round(subtotal, 2)
        export_data['materials'].append(d)
        export_data['total_cost'] += subtotal

    export_data['total_cost'] = round(export_data['total_cost'], 2)

    return jsonify(export_data)

# ============================================================
# 媒体服务（图片展示 + CAD 文件下载）
# ============================================================
MEDIA_DIR = BASE_DIR / 'media'
IMAGES_DIR = MEDIA_DIR / 'images'
CAD_DIR    = MEDIA_DIR / 'cad'
os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(CAD_DIR, exist_ok=True)

@app.route('/api/media/images/<path:filename>')
def serve_image(filename):
    """提供材料/构造图片"""
    return send_from_directory(str(IMAGES_DIR), filename)

@app.route('/api/media/cad/<path:filename>')
def download_cad(filename):
    """下载 CAD 文件（支持 DWG/SKP/PDF/DXF）"""
    return send_from_directory(
        str(CAD_DIR),
        filename,
        as_attachment=True,
        download_name=filename
    )

@app.route('/api/media/list/<int:material_id>')
def list_media(material_id):
    """列出某材料的所有媒体文件"""
    db = get_db()
    row = db.execute('SELECT image_urls, cad_files FROM materials WHERE id = ?', [material_id]).fetchone()
    if not row:
        return jsonify({'error': '材料不存在'}), 404
    return jsonify({
        'images': row['image_urls'] if row['image_urls'] else [],
        'cad_files': row['cad_files'] if row['cad_files'] else []
    })

# ============================================================
# AI 图像选材 (2026-07-01)
# ============================================================

ANALYZE_PROMPT = """请仔细分析这张建筑相关图片，按以下 JSON 格式输出（**只输出 JSON**，不要其他文字，不要 markdown 标记）：

{{
  "scene_description": "整体场景的简短中文描述（一两句话，描述图中的建筑/空间/构件）",
  "context": "建筑场景判断（外墙/室内/景观/屋顶/幕墙/其他之一）",
  "style": "建筑风格（现代/极简/新中式/欧式/工业/其他之一）",
  "identified_materials": [
    {{
      "name": "材质名称（中文，2-6字）",
      "category_hint": "材质大类（金属/石材/木材/玻璃/混凝土/涂料/砖/陶瓷/其他之一）",
      "color": "颜色（如：浅灰、暖白、深棕）",
      "texture": "质感（如：光滑、粗糙、哑光、自然纹理）",
      "location_in_image": "在图中的位置（前景/中景/背景，或更具体位置）",
      "confidence": 0.0 到 1.0 之间的浮点数，表示识别确信度
    }}
  ],
  "search_keywords": ["用于数据库搜索的中文关键词数组，例如：['石材', '幕墙', '金属', '灰色', '住宅外墙']"]
}}

{user_context}

要求：
1. identified_materials 至少识别 1 个，最多 8 个，按重要程度排序
2. search_keywords 是去重后的中文关键词列表，3-10 个，用于后续数据库搜索
3. 严格按 JSON 格式输出，不要加 ``` 标记，不要解释
"""


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[-1].lower() in ALLOWED_EXTS


# ============================================================
# OpenAI 兼容视觉模型 (2026-07-01)
# ============================================================
def _chat_completion(api_url, api_key, model_name, messages, max_tokens=2000, timeout=120):
    """调用 OpenAI 兼容的 chat/completions 接口，返回 (content_str, raw_dict)"""
    url = api_url.rstrip('/')
    if not url.endswith('/chat/completions'):
        url = url + '/v1/chat/completions' if '/v1' not in url else url + '/chat/completions'
    payload = {
        'model': model_name,
        'messages': messages,
        'max_tokens': max_tokens
    }
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode('utf-8'),
        headers=headers, method='POST'
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = json.loads(resp.read().decode('utf-8'))
    content = raw.get('choices', [{}])[0].get('message', {}).get('content', '')
    return content, raw


def call_openai_vision(api_url, api_key, model_name, image_path, prompt):
    """用 OpenAI 兼容协议调用视觉模型"""
    with open(image_path, 'rb') as f:
        b64 = base64.b64encode(f.read()).decode('utf-8')
    ext = image_path.rsplit('.', 1)[-1].lower()
    mime = {
        'jpg': 'image/jpeg', 'jpeg': 'image/jpeg',
        'png': 'image/png', 'webp': 'image/webp', 'gif': 'image/gif'
    }.get(ext, 'image/png')
    messages = [{
        'role': 'user',
        'content': [
            {'type': 'text', 'text': prompt},
            {'type': 'image_url', 'image_url': {'url': f'data:{mime};base64,{b64}'}}
        ]
    }]
    return _chat_completion(api_url, api_key, model_name, messages)[0]


@app.route('/api/test_model', methods=['POST'])
def test_model():
    """测试视觉模型连接（不传图，只发个 ping）"""
    data = request.get_json() or {}
    api_url = (data.get('api_url') or '').strip()
    api_key = (data.get('api_key') or '').strip()
    model_name = (data.get('model_name') or '').strip()
    if not api_url or not api_key or not model_name:
        return jsonify({'ok': False, 'error': 'API URL、API Key、模型名 都需要填写'}), 400
    try:
        content, raw = _chat_completion(
            api_url, api_key, model_name,
            messages=[{'role': 'user', 'content': 'reply with one word: pong'}],
            max_tokens=10, timeout=15
        )
        return jsonify({
            'ok': True,
            'message': '连接成功 ✓',
            'sample': (content or '').strip()[:80] or '(空响应)',
            'model': raw.get('model', model_name)
        })
    except urllib.error.HTTPError as e:
        body = ''
        try: body = e.read().decode('utf-8', errors='ignore')[:300]
        except: pass
        return jsonify({
            'ok': False,
            'error': f'HTTP {e.code} {e.reason}',
            'detail': body
        }), e.code
    except urllib.error.URLError as e:
        return jsonify({'ok': False, 'error': f'无法连接: {e.reason}'}), 502
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/analyze_image', methods=['POST'])
def analyze_image():
    """接收图片 + 可选上下文，调视觉模型，返回结构化分析。
       优先使用请求中携带的 api_url/api_key/model_name（用户自定义），
       否则回退到系统 matrix MCP。"""
    if 'image' not in request.files:
        return jsonify({'error': '未上传图片'}), 400
    f = request.files['image']
    if not f or not f.filename:
        return jsonify({'error': '文件无效'}), 400
    if not allowed_file(f.filename):
        return jsonify({'error': f'仅支持 {", ".join(ALLOWED_EXTS)} 格式'}), 400

    # 1. 保存图片
    ext = f.filename.rsplit('.', 1)[-1].lower()
    fname = f'ai_{uuid.uuid4().hex[:12]}.{ext}'
    fpath = UPLOAD_DIR / fname
    f.save(str(fpath))
    abs_path = str(fpath.resolve()).replace('\\', '/')

    # 2. 构造 prompt
    user_ctx_raw = request.form.get('context', '').strip()
    user_ctx = ''
    if user_ctx_raw:
        try:
            ctx_obj = json.loads(user_ctx_raw)
            lines = [f'- {k}: {v}' for k, v in ctx_obj.items() if v]
            if lines:
                user_ctx = '用户的额外上下文：\n' + '\n'.join(lines)
        except Exception:
            user_ctx = f'用户的额外上下文：{user_ctx_raw}'
    prompt = ANALYZE_PROMPT.format(user_context=user_ctx)

    # 3. 读用户自定义模型配置
    custom_url   = (request.form.get('api_url') or '').strip()
    custom_key   = (request.form.get('api_key') or '').strip()
    custom_model = (request.form.get('model_name') or '').strip()
    use_custom = bool(custom_url and custom_key and custom_model)

    analysis = None
    engine = 'matrix MCP'

    try:
        if use_custom:
            engine = f'自定义({custom_model})'
            try:
                text = call_openai_vision(custom_url, custom_key, custom_model, abs_path, prompt)
                stdout = text
            except urllib.error.HTTPError as e:
                body = ''
                try: body = e.read().decode('utf-8', errors='ignore')[:500]
                except: pass
                return jsonify({
                    'error': f'自定义模型 HTTP {e.code} {e.reason}',
                    'detail': body
                }), e.code
            except Exception as e:
                return jsonify({'error': f'自定义模型调用失败: {e}'}), 500
        else:
            # 走 matrix MCP
            req_file = UPLOAD_DIR / f'_req_{uuid.uuid4().hex[:8]}.json'
            payload = {
                'image_info': [{
                    'file': abs_path,
                    'prompt': prompt
                }]
            }
            req_file.write_text(json.dumps(payload, ensure_ascii=False), encoding='utf-8')
            try:
                result = subprocess.run(
                    ['mavis', 'mcp', 'call', 'matrix', 'matrix_describe_images', '--file', str(req_file)],
                    capture_output=True, text=True, timeout=120, encoding='utf-8'
                )
                stdout = result.stdout or ''
            except subprocess.TimeoutExpired:
                return jsonify({'error': '视觉模型调用超时（120s）'}), 504
            except Exception as e:
                return jsonify({'error': f'视觉模型调用失败: {e}'}), 500
            finally:
                try: req_file.unlink()
                except Exception: pass

        # 解析返回（两种引擎都期望 JSON）
        m = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', stdout, re.DOTALL)
        if m:
            json_str = m.group(1)
        else:
            start = stdout.find('{')
            end = stdout.rfind('}')
            json_str = stdout[start:end+1] if (start != -1 and end != -1 and end > start) else ''
        try:
            analysis = json.loads(json_str)
        except Exception as e:
            return jsonify({
                'error': f'{engine} 返回无法解析: {e}',
                'raw': stdout[:2000]
            }), 500
    except Exception as e:
        return jsonify({'error': f'分析过程出错: {e}'}), 500

    # 4. 兜底字段
    analysis.setdefault('scene_description', '')
    analysis.setdefault('context', '其他')
    analysis.setdefault('style', '其他')
    if not isinstance(analysis.get('identified_materials'), list):
        analysis['identified_materials'] = []
    if not isinstance(analysis.get('search_keywords'), list):
        analysis['search_keywords'] = []

    return jsonify({
        'analysis': analysis,
        'image_url': f'/uploads/{fname}',
        'image_filename': fname,
        'engine': engine
    })


@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    """提供 AI 上传图片的访问（供前端预览）"""
    return send_from_directory(str(UPLOAD_DIR), filename)


@app.route('/api/search_by_analysis', methods=['POST'])
def search_by_analysis():
    """根据分析结果在 MaterialDB 中检索匹配材质"""
    data = request.get_json() or {}
    keywords = data.get('search_keywords') or []
    materials = data.get('identified_materials') or []
    user_filters = data.get('filters') or {}

    if not keywords and not materials:
        return jsonify({'error': 'search_keywords 或 identified_materials 至少需要一个'}), 400

    db = get_db()

    # 汇总所有搜索词
    all_kw = []
    seen = set()
    for kw in keywords:
        if isinstance(kw, str):
            k = kw.strip()
            if k and k not in seen:
                all_kw.append(k); seen.add(k)
    for m in materials:
        if isinstance(m, dict):
            for f in ['name', 'category_hint', 'color', 'texture']:
                v = (m.get(f) or '').strip()
                if v and v not in seen:
                    all_kw.append(v); seen.add(v)

    def to_text_list(v):
        if not v: return []
        try:
            arr = json.loads(v)
            if isinstance(arr, list):
                return [str(x) for x in arr]
        except Exception: pass
        return [str(v)]

    rows = db.execute("""
        SELECT m.*, c.name AS category_name
        FROM materials m
        LEFT JOIN categories c ON c.category_id = c.id
        WHERE m.status = 'active'
    """).fetchall() if False else db.execute("""
        SELECT m.*, c.name AS category_name
        FROM materials m
        LEFT JOIN categories c ON c.id = m.category_id
        WHERE m.status = 'active'
    """).fetchall()

    scored = []
    for r in rows:
        mat = dict(r)
        score = 0
        matched = []
        name_cn = mat.get('name_cn') or ''
        name_en = (mat.get('name_en') or '').lower()
        sub_cat = mat.get('sub_category') or ''
        cat_name = mat.get('category_name') or ''
        visual_desc = mat.get('visual_desc') or ''

        for kw in all_kw:
            if kw in name_cn:
                score += 10; matched.append(('name_cn', kw))
            if kw.lower() in name_en:
                score += 5; matched.append(('name_en', kw))
            if kw in sub_cat:
                score += 4; matched.append(('sub_category', kw))
            if kw in cat_name:
                score += 3; matched.append(('category', kw))
            if kw in visual_desc:
                score += 3; matched.append(('visual_desc', kw))
            for app in to_text_list(mat.get('applications_json')):
                if kw in app:
                    score += 2; matched.append(('application', kw)); break
            for cs in to_text_list(mat.get('color_series')):
                if kw in cs:
                    score += 2; matched.append(('color_series', kw)); break
            for t in to_text_list(mat.get('texture')):
                if kw in t:
                    score += 1; matched.append(('texture', kw)); break

        # 置信度加成
        max_conf = 0
        for m in materials:
            if not isinstance(m, dict): continue
            n = (m.get('name') or '').strip()
            cn = (m.get('category_hint') or '').strip()
            c2 = float(m.get('confidence') or 0)
            if n and (n in name_cn or n in name_en or n in sub_cat or n in cat_name):
                max_conf = max(max_conf, c2)
            elif cn and cn in cat_name:
                max_conf = max(max_conf, c2 * 0.5)
        if max_conf:
            score = score * (0.5 + max_conf)

        # 用户过滤
        if user_filters.get('cost_tier') and mat.get('cost_tier') != user_filters['cost_tier']:
            continue
        if user_filters.get('fire_rating') and mat.get('fire_rating') != user_filters['fire_rating']:
            continue
        if user_filters.get('category_id') and mat.get('category_id') != user_filters['category_id']:
            continue

        if score > 0:
            mat['score'] = round(score, 2)
            mat['matched_fields'] = list(set(f for f, _ in matched))
            mat['matched_keywords'] = list(set(k for _, k in matched))
            scored.append(mat)

    scored.sort(key=lambda x: x['score'], reverse=True)
    top = scored[:30]

    out = []
    for m in top:
        out.append({
            'id': m['id'],
            'code': m['code'],
            'name_cn': m['name_cn'],
            'name_en': m['name_en'],
            'category_name': m.get('category_name'),
            'sub_category': m['sub_category'],
            'visual_desc': m['visual_desc'],
            'unit_price': m['unit_price'],
            'unit': m['unit'],
            'cost_tier': m['cost_tier'],
            'fire_rating': m['fire_rating'],
            'color_series': m.get('color_series'),
            'texture': m.get('texture'),
            'applications': to_text_list(m.get('applications_json')),
            'score': m['score'],
            'matched_fields': m.get('matched_fields', []),
            'matched_keywords': m.get('matched_keywords', [])
        })

    return jsonify({
        'count': len(out),
        'items': out,
        'query_keywords': all_kw
    })


@app.route('/api/save_scheme', methods=['POST'])
def save_scheme():
    """保存选材方案（含 AI 上下文：图片 + 分析 JSON，方便重载）"""
    data = request.get_json() or {}
    name = (data.get('name') or '').strip() or f"AI方案-{datetime.now().strftime('%Y%m%d-%H%M')}"
    description = (data.get('description') or '').strip()
    project_id = data.get('project_id')
    materials = data.get('materials') or []
    image_filename = (data.get('image_filename') or '').strip()
    analysis = data.get('analysis') or {}
    # 搜索结果（用于"重载"时直接跳到 Step 4）
    search_results = data.get('search_results') or []
    selected_ids = data.get('selected_ids') or []

    if not materials:
        return jsonify({'error': '至少选一个材质'}), 400

    db = get_db()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # 打包"会话上下文"JSON：场景描述/识别材质/关键词/搜索结果/选中id
    session_ctx = {
        'analysis': analysis,
        'search_results': search_results,
        'selected_ids': selected_ids
    }

    cur = db.execute(
        'INSERT INTO material_schemes (project_id, name, description, status, created_at, image_filename, analysis_json, updated_at) '
        'VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
        (project_id, name, description, 'active', now, image_filename, json.dumps(session_ctx, ensure_ascii=False), now)
    )
    scheme_id = cur.lastrowid

    rows = []
    for m in materials:
        rows.append((
            scheme_id,
            int(m['material_id']),
            float(m.get('score') or 0),
            m.get('score_reason') or '',
            1 if m.get('is_selected') else 0
        ))
    db.executemany(
        'INSERT INTO scheme_materials (scheme_id, material_id, score, score_reason, is_selected) VALUES (?, ?, ?, ?, ?)',
        rows
    )
    db.commit()

    return jsonify({
        'scheme_id': scheme_id,
        'name': name,
        'material_count': len(rows),
        'image_url': f'/uploads/{image_filename}' if image_filename else None
    })


@app.route('/api/schemes', methods=['GET'])
def list_schemes():
    """列出所有方案"""
    db = get_db()
    rows = db.execute("""
        SELECT s.id, s.name, s.description, s.status, s.created_at, s.project_id,
               s.image_filename, s.updated_at,
               p.name AS project_name,
               (SELECT COUNT(*) FROM scheme_materials WHERE scheme_id = s.id) AS material_count
        FROM material_schemes s
        LEFT JOIN projects p ON p.id = s.project_id
        ORDER BY COALESCE(s.updated_at, s.created_at) DESC
    """).fetchall()
    items = []
    for r in rows:
        d = dict(r)
        d['image_url'] = f"/uploads/{d['image_filename']}" if d.get('image_filename') else None
        items.append(d)
    return jsonify({
        'count': len(items),
        'items': items
    })


@app.route('/api/schemes/<int:scheme_id>', methods=['GET'])
def get_scheme(scheme_id):
    """获取方案详情（带完整材质列表 + 会话上下文）"""
    db = get_db()
    s = db.execute('SELECT * FROM material_schemes WHERE id = ?', (scheme_id,)).fetchone()
    if not s:
        return jsonify({'error': '方案不存在'}), 404
    scheme = dict(s)
    if scheme.get('image_filename'):
        scheme['image_url'] = f"/uploads/{scheme['image_filename']}"
    # 解析会话上下文
    ctx = {}
    if scheme.get('analysis_json'):
        try: ctx = json.loads(scheme['analysis_json'])
        except: pass
    scheme['session'] = ctx
    rows = db.execute("""
        SELECT sm.id AS sm_id, sm.score, sm.score_reason, sm.is_selected,
               m.id, m.code, m.name_cn, m.name_en, m.visual_desc, m.unit_price, m.unit,
               m.cost_tier, m.fire_rating, c.name AS category_name
        FROM scheme_materials sm
        JOIN materials m ON m.id = sm.material_id
        LEFT JOIN categories c ON c.id = m.category_id
        WHERE sm.scheme_id = ?
        ORDER BY sm.score DESC
    """, (scheme_id,)).fetchall()
    scheme['materials'] = [dict(r) for r in rows]
    return jsonify(scheme)


@app.route('/api/schemes/<int:scheme_id>', methods=['DELETE'])
def delete_scheme(scheme_id):
    """删除方案"""
    db = get_db()
    s = db.execute('SELECT id, image_filename FROM material_schemes WHERE id = ?', (scheme_id,)).fetchone()
    if not s:
        return jsonify({'error': '方案不存在'}), 404
    db.execute('DELETE FROM scheme_materials WHERE scheme_id = ?', (scheme_id,))
    db.execute('DELETE FROM material_schemes WHERE id = ?', (scheme_id,))
    db.commit()
    return jsonify({'deleted': scheme_id, 'image_filename': s['image_filename']})


@app.route('/api/schemes/<int:scheme_id>/reload', methods=['GET'])
def reload_scheme(scheme_id):
    """返回方案的可重载会话状态（分析结果 + 搜索结果 + 选中项），供前端跳到 AI 流程任意步"""
    db = get_db()
    s = db.execute('SELECT * FROM material_schemes WHERE id = ?', (scheme_id,)).fetchone()
    if not s:
        return jsonify({'error': '方案不存在'}), 404
    scheme = dict(s)
    if scheme.get('image_filename'):
        scheme['image_url'] = f"/uploads/{scheme['image_filename']}"
    ctx = {}
    if scheme.get('analysis_json'):
        try: ctx = json.loads(scheme['analysis_json'])
        except: pass
    return jsonify({
        'scheme_id': scheme_id,
        'name': scheme['name'],
        'description': scheme['description'],
        'image_url': scheme.get('image_url'),
        'image_filename': scheme.get('image_filename'),
        'session': ctx
    })


# ============================================================
# PDF 导出 (2026-07-01)
# ============================================================
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors as rl_colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle, PageBreak
import io

# 注册中文字体（启动时尝试多种）
ZH_FONT = 'Helvetica'
ZH_FONT_BOLD = 'Helvetica-Bold'
for fp in [
    r'C:\Windows\Fonts\msyh.ttc',
    r'C:\Windows\Fonts\msyhbd.ttc',
    r'C:\Windows\Fonts\simhei.ttf',
    r'C:\Windows\Fonts\simsun.ttc',
    '/System/Library/Fonts/PingFang.ttc',
    '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
    '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
]:
    if os.path.exists(fp):
        try:
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            pdfmetrics.registerFont(TTFont('zh', fp))
            pdfmetrics.registerFont(TTFont('zh-bold', fp))
            ZH_FONT = 'zh'
            ZH_FONT_BOLD = 'zh-bold'
            print(f"[PDF] Loaded Chinese font: {fp}")
            break
        except Exception as e:
            print(f"[PDF] Failed to load {fp}: {e}")


@app.route('/api/schemes/<int:scheme_id>/export/pdf', methods=['GET'])
def export_scheme_pdf(scheme_id):
    """导出方案为 PDF（包含图片 + AI 上下文 + 材质清单）"""
    db = get_db()
    s = db.execute('SELECT * FROM material_schemes WHERE id = ?', (scheme_id,)).fetchone()
    if not s:
        return jsonify({'error': '方案不存在'}), 404
    scheme = dict(s)

    mats = db.execute("""
        SELECT sm.id AS sm_id, sm.score, sm.score_reason, sm.is_selected,
               m.id, m.code, m.name_cn, m.name_en, m.visual_desc, m.unit_price, m.unit,
               m.cost_tier, m.fire_rating, c.name AS category_name
        FROM scheme_materials sm
        JOIN materials m ON m.id = sm.material_id
        LEFT JOIN categories c ON c.id = m.category_id
        WHERE sm.scheme_id = ?
        ORDER BY sm.score DESC
    """, (scheme_id,)).fetchall()

    ctx = {}
    if scheme.get('analysis_json'):
        try: ctx = json.loads(scheme['analysis_json'])
        except: pass
    analysis = ctx.get('analysis') or {}

    # 生成 PDF
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=1.8*cm, bottomMargin=1.8*cm,
        leftMargin=2*cm, rightMargin=2*cm,
        title=scheme['name'], author='MaterialWeb AI 选材'
    )

    base = getSampleStyleSheet()['Normal']
    title_s = ParagraphStyle('Title', fontName=ZH_FONT_BOLD, fontSize=20, leading=26, textColor=rl_colors.HexColor('#ff9e4a'), spaceAfter=4)
    subtitle_s = ParagraphStyle('Sub', fontName=ZH_FONT, fontSize=10, leading=14, textColor=rl_colors.grey, spaceAfter=12)
    h2_s = ParagraphStyle('H2', fontName=ZH_FONT_BOLD, fontSize=13, leading=18, textColor=rl_colors.HexColor('#ff9e4a'), spaceBefore=10, spaceAfter=8)
    body_s = ParagraphStyle('Body', fontName=ZH_FONT, fontSize=10, leading=15, spaceAfter=4)
    label_s = ParagraphStyle('Lbl', fontName=ZH_FONT, fontSize=9, leading=13, textColor=rl_colors.grey)
    cell_s = ParagraphStyle('Cell', fontName=ZH_FONT, fontSize=8, leading=11)
    cell_b_s = ParagraphStyle('CellB', fontName=ZH_FONT_BOLD, fontSize=9, leading=12)
    center_s = ParagraphStyle('C', fontName=ZH_FONT, fontSize=9, leading=12, alignment=1)
    footer_s = ParagraphStyle('F', fontName=ZH_FONT, fontSize=9, leading=12, textColor=rl_colors.grey, alignment=1)

    story = []

    # 标题
    story.append(Paragraph(scheme['name'], title_s))
    meta = f"创建时间: {scheme.get('created_at', '—')}   |   材质数量: {len(mats)}"
    if scheme.get('project_id'):
        meta += f"   |   关联项目: #{scheme['project_id']}"
    story.append(Paragraph(meta, subtitle_s))

    # 缩略图
    if scheme.get('image_filename'):
        img_path = UPLOAD_DIR / scheme['image_filename']
        if img_path.exists():
            try:
                img = RLImage(str(img_path), width=10*cm, height=7.5*cm, kind='proportional')
                img.hAlign = 'CENTER'
                story.append(img)
                story.append(Spacer(1, 6))
            except Exception as e:
                print(f"[PDF] Image error: {e}")

    # 描述
    if scheme.get('description'):
        story.append(Paragraph('方案描述', h2_s))
        story.append(Paragraph(scheme['description'].replace('\n', '<br/>'), body_s))

    # AI 场景分析
    if analysis:
        story.append(Paragraph('AI 场景分析', h2_s))
        if analysis.get('scene_description'):
            story.append(Paragraph(f"<b>场景：</b>{analysis['scene_description']}", body_s))
        ctx_st = analysis.get('context') or '—'
        style_st = analysis.get('style') or '—'
        story.append(Paragraph(f"<b>类型：</b>{ctx_st}　　<b>风格：</b>{style_st}", body_s))
        if analysis.get('identified_materials'):
            items = analysis['identified_materials']
            names = '、'.join([m.get('name', '—') for m in items[:8]])
            story.append(Paragraph(f"<b>识别材质：</b>{names}", body_s))
        if analysis.get('search_keywords'):
            kws = '、'.join(analysis['search_keywords'][:8])
            story.append(Paragraph(f"<b>关键词：</b>{kws}", body_s))

    # 材质清单表
    story.append(Paragraph(f'材质清单（{len(mats)} 项）', h2_s))
    data = [[
        Paragraph('<b>#</b>', cell_b_s),
        Paragraph('<b>名称</b>', cell_b_s),
        Paragraph('<b>类别</b>', cell_b_s),
        Paragraph('<b>防火</b>', cell_b_s),
        Paragraph('<b>造价</b>', cell_b_s),
        Paragraph('<b>单价</b>', cell_b_s),
        Paragraph('<b>匹配分</b>', cell_b_s),
        Paragraph('<b>描述</b>', cell_b_s)
    ]]
    for i, m in enumerate(mats, 1):
        m = dict(m)
        name_html = f"{m.get('name_cn','')}<br/><font size=7 color=grey>{m.get('name_en','')}</font>"
        desc_html = (m.get('visual_desc') or '—').replace('\n', '<br/>')
        data.append([
            Paragraph(str(i), center_s),
            Paragraph(name_html, cell_s),
            Paragraph(m.get('category_name') or '—', cell_s),
            Paragraph(m.get('fire_rating') or '—', center_s),
            Paragraph(m.get('cost_tier') or '—', center_s),
            Paragraph(f"¥{m.get('unit_price', 0)}/{m.get('unit','m²')}", cell_s),
            Paragraph(str(m.get('score', 0)), center_s),
            Paragraph(desc_html, cell_s)
        ])
    table = Table(data, colWidths=[0.8*cm, 3.5*cm, 1.8*cm, 1*cm, 1*cm, 1.8*cm, 1*cm, 6*cm], repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), rl_colors.HexColor('#ff9e4a')),
        ('TEXTCOLOR', (0,0), (-1,0), rl_colors.white),
        ('GRID', (0,0), (-1,-1), 0.4, rl_colors.grey),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [rl_colors.white, rl_colors.HexColor('#fafafa')]),
    ]))
    story.append(table)

    # 命中详情
    story.append(Spacer(1, 8))
    story.append(Paragraph('命中详情', h2_s))
    for i, m in enumerate(mats, 1):
        m = dict(m)
        story.append(Paragraph(f"<b>{i}. {m.get('name_cn','')}</b>　匹配分 {m.get('score', 0)}", cell_b_s))
        story.append(Paragraph(f"　{(m.get('score_reason') or '—').replace(',', '，')}", cell_s))
        story.append(Spacer(1, 3))

    # 底部
    story.append(Spacer(1, 16))
    story.append(Paragraph('— 本方案由 MaterialWeb AI 选材生成 —', footer_s))

    doc.build(story)
    buf.seek(0)

    safe_name = re.sub(r'[\\/:*?"<>|]', '_', scheme['name'])
    filename = f"{safe_name}_{scheme_id}.pdf"
    return send_file(
        buf,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename
    )


# ============================================================
# 启动
# ============================================================
if __name__ == '__main__':
    print(f"🏗  建筑材料数据库 API")
    print(f"   数据库: {DB_PATH}")
    print(f"   静态文件: {STATIC_DIR}")
    print(f"   访问: http://localhost:5188")
    print(f"   API文档: http://localhost:5188/api/materials")
    app.run(host='0.0.0.0', port=5188, debug=True)
