"""关键词检索评分 · /api/search_by_analysis
根据视觉模型的分析结果,在 materials 表里按多字段打分排序
"""
import json
from flask import Blueprint, request, jsonify
from ..core import get_db, to_text_list

bp = Blueprint('search_by', __name__)


@bp.post('/api/search_by_analysis')
def search_by_analysis():
    data = request.get_json() or {}
    keywords  = data.get('search_keywords') or []
    materials = data.get('identified_materials') or []
    filters   = data.get('filters') or {}

    if not keywords and not materials:
        return jsonify({'error': 'search_keywords 或 identified_materials 至少一个'}), 400

    # 汇总搜索词
    all_kw, seen = [], set()
    for kw in keywords:
        if isinstance(kw, str):
            k = kw.strip()
            if k and k not in seen:
                all_kw.append(k); seen.add(k)
    for m in materials:
        if isinstance(m, dict):
            for f in ('name', 'category_hint', 'color', 'texture'):
                v = (m.get(f) or '').strip()
                if v and v not in seen:
                    all_kw.append(v); seen.add(v)

    db = get_db()
    rows = db.execute('''
        SELECT m.*, c.name AS category_name
        FROM materials m
        LEFT JOIN categories c ON c.id = m.category_id
        WHERE m.status = 'active'
    ''').fetchall()

    scored = []
    for r in rows:
        mat = dict(r)
        score = 0
        matched = []
        name_cn  = mat.get('name_cn') or ''
        name_en  = (mat.get('name_en') or '').lower()
        sub_cat  = mat.get('sub_category') or ''
        cat_name = mat.get('category_name') or ''
        vis_desc = mat.get('visual_desc') or ''

        for kw in all_kw:
            if kw in name_cn:
                score += 10; matched.append(('name_cn', kw))
            if kw.lower() in name_en:
                score += 5;  matched.append(('name_en', kw))
            if kw in sub_cat:
                score += 4;  matched.append(('sub_category', kw))
            if kw in cat_name:
                score += 3;  matched.append(('category', kw))
            if kw in vis_desc:
                score += 3;  matched.append(('visual_desc', kw))
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
            n  = (m.get('name') or '').strip()
            cn = (m.get('category_hint') or '').strip()
            c2 = float(m.get('confidence') or 0)
            if n and (n in name_cn or n in name_en or n in sub_cat or n in cat_name):
                max_conf = max(max_conf, c2)
            elif cn and cn in cat_name:
                max_conf = max(max_conf, c2 * 0.5)
        if max_conf:
            score = score * (0.5 + max_conf)

        # 用户过滤
        if filters.get('cost_tier')   and mat.get('cost_tier')   != filters['cost_tier']:   continue
        if filters.get('fire_rating') and mat.get('fire_rating') != filters['fire_rating']: continue
        if filters.get('category_id') and mat.get('category_id') != filters['category_id']: continue

        if score > 0:
            mat['score']            = round(score, 2)
            mat['matched_fields']   = list(set(f for f, _ in matched))
            mat['matched_keywords'] = list(set(k for _, k in matched))
            scored.append(mat)

    scored.sort(key=lambda x: x['score'], reverse=True)
    top = scored[:30]
    out = [{
        'id': m['id'], 'code': m['code'],
        'name_cn': m['name_cn'], 'name_en': m['name_en'],
        'category_name': m.get('category_name'),
        'sub_category': m['sub_category'], 'visual_desc': m['visual_desc'],
        'unit_price': m['unit_price'], 'unit': m['unit'],
        'cost_tier': m['cost_tier'], 'fire_rating': m['fire_rating'],
        'color_series': m.get('color_series'), 'texture': m.get('texture'),
        'applications': to_text_list(m.get('applications_json')),
        'score': m['score'],
        'matched_fields': m.get('matched_fields', []),
        'matched_keywords': m.get('matched_keywords', []),
    } for m in top]

    return jsonify({
        'count': len(out), 'items': out, 'query_keywords': all_kw,
    })


def register(app): app.register_blueprint(bp)
