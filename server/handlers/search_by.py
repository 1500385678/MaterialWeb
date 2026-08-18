"""关键词检索评分 · /api/search_by_analysis
根据视觉模型的分析结果,在 materials 表里按多字段打分排序
"""
from flask import Blueprint, request, jsonify
from ..core import get_db, to_text_list

bp = Blueprint('search_by', __name__)


# ---------------------------------------------------------------
# 性能契约(2026-08-11 夜间迭代批 2 改 · P1 Verifier row 70):
# 当材料库 ≤ 1000 行时,SQL 预过滤 LIMIT 500 → Python 精排 500 行
# → P95 < 200ms(实测 search_bench.py · 100 次调用)
# 当材料库 > 5000 行时,改 FTS5 虚拟表(暂未启用,见 _PRE_FILTER_LIMIT)
# ---------------------------------------------------------------
_PRE_FILTER_LIMIT = 500  # 预过滤后保留上限(性能契约 1)
_SCORE_FIELDS = (
    'm.name_cn', 'm.name_en', 'm.sub_category',
    'c.name', 'm.visual_desc', 'm.applications_json',
)


def _build_prefilter(all_kw):
    """生成 WHERE 子句 + params。
    规则:任一 keyword 命中任一字段则保留(OR-of-OR)。
    空关键词表时无预过滤(全表扫,只发生在 identified_materials-only 场景)。
    """
    if not all_kw:
        return '', []
    groups, params = [], []
    for kw in all_kw:
        kw_like = f'%{kw}%'
        group = ' OR '.join(f'{f} LIKE ?' for f in _SCORE_FIELDS)
        groups.append(f'({group})')
        params.extend([kw_like] * len(_SCORE_FIELDS))
    return f' AND ({" OR ".join(groups)})', params


def _passes_filters(mat, filters):
    """用户层过滤(铁律 §6.7 · cost_tier / fire_rating / category_id)"""
    if filters.get('cost_tier')   and mat.get('cost_tier')   != filters['cost_tier']:   return False
    if filters.get('fire_rating') and mat.get('fire_rating') != filters['fire_rating']: return False
    if filters.get('category_id') and mat.get('category_id') != filters['category_id']: return False
    return True


def _score_row(mat, all_kw, materials):
    """对单条材料按 8 字段评分 + 置信度加成。返回 (score, matched) 元组。
    8 字段权重:name_cn=10 / name_en=5 / sub_category=4 / category=3 /
    visual_desc=3 / application=2 / color_series=2 / texture=1
    """
    name_cn  = mat.get('name_cn') or ''
    name_en  = (mat.get('name_en') or '').lower()
    sub_cat  = mat.get('sub_category') or ''
    cat_name = mat.get('category_name') or ''
    vis_desc = mat.get('visual_desc') or ''

    score, matched = 0, []
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

    # 置信度加成(AI 视觉模型给出的 identified_materials 自带 0~1 置信度)
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

    return score, matched


@bp.post('/api/search_by_analysis')
def search_by_analysis():
    data = request.get_json() or {}
    keywords  = data.get('search_keywords') or []
    materials = data.get('identified_materials') or []
    filters   = data.get('filters') or {}

    if not keywords and not materials:
        return jsonify({'error': 'search_keywords 或 identified_materials 至少一个'}), 400

    # 汇总搜索词(去重保序)
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
    where_extra, where_params = _build_prefilter(all_kw)
    # SQL 预过滤:OR-LIKE 粗筛 500 行(性能契约 1)→ Python 精排
    # 字符字段大小写敏感(LIKE 默认),材料库 18 行时无可见效果,扩张后必须
    sql = f'''
        SELECT m.*, c.name AS category_name
        FROM materials m
        LEFT JOIN categories c ON c.id = m.category_id
        WHERE m.status = 'active' {where_extra}
        LIMIT {_PRE_FILTER_LIMIT}
    '''
    rows = db.execute(sql, where_params).fetchall()

    scored = []
    for r in rows:
        mat = dict(r)
        if not _passes_filters(mat, filters):
            continue
        score, matched = _score_row(mat, all_kw, materials)
        if score > 0:
            mat['score']            = round(score, 2)
            mat['matched_fields']   = list(set(f for f, _ in matched))
            mat['matched_keywords'] = list(set(k for _, k in matched))
            scored.append(mat)

    scored.sort(key=lambda x: x['score'], reverse=True)
    # top[:30] = 性能契约 2 · 前端 30 条卡片一屏展示,超过会折叠;
    # 不是 50/100 是因为 30 是「>0 分」内前 30,与「分页」无关
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
