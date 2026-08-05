"""概念文案生成器 · 基于材料组合 + 部位 + 风格生成 200-300 字方案概念
POST /api/generate_concept
{
  "materials": ["GRC_001", "UHPC_001", "GLASS_001"],
  "part": "外墙",
  "style": "现代",
  "project_type": "商业综合体"
}
→ { "concept": "...", "language_combined": ["精致", "现代", ...], "highlights": [...] }
"""
import json
import random
from collections import Counter
from flask import Blueprint, request, jsonify
from ..core import get_db, rows_to_list

bp = Blueprint('concept', __name__)


# ============================================================
# 模板:按"主体材料 + 部位"组合
# ============================================================
OPENERS = [
    '本案以{style}为基调,',
    '方案立面取{style}之意,',
    '面向{project_type}的使用场景,',
    '设计以{style}语言展开,',
    '从{project_type}的空间体验出发,',
]

PART_FRAGMENTS = {
    '外墙': '{part}作为建筑的"皮肤",承担表情与节奏的双重职责。',
    '幕墙': '{part}系统以"通透"与"实体"的对比塑造体量。',
    '屋面': '{part}处理以"第五立面"的态度对待,从空中俯瞰亦经得起审视。',
    '室内': '{part}设计强调触感与温度,以可感知的材质语言定义空间情绪。',
    '地面': '{part}作为空间底色,大尺度展开,引导人流并强化场所感。',
    '景观': '{part}选材回应场地气质,以自然肌理与人工精度对话。',
}

# 风格 → 收尾模板
CLOSERS = {
    '现代':     '整体立面在{lang_summary}之间取得平衡,呈现{visual}的当代气质。',
    '极简':     '所有材料服务于"少即是多"的减法逻辑,呈现{visual}的克制美学。',
    '新中式':   '在传统语汇与现代工艺之间寻找平衡,呈现{visual}的本土现代性。',
    '工业':     '保留材料的原始肌理与构造逻辑,呈现{visual}的工业诗意。',
    '侘寂':     '以时间与不完美为美,呈现{visual}的安静力量。',
    '古典':     '强调比例、秩序与材料的永恒感,呈现{visual}的庄重。',
}

# 风格默认 visual 描述
VISUAL_DEFAULTS = {
    '现代':   '简洁有力',
    '极简':   '冷静克制',
    '新中式': '温润内敛',
    '工业':   '粗犷有力',
    '侘寂':   '安静诗意',
    '古典':   '庄重典雅',
    '高技派': '精密冷峻',
}


def combine_language(materials: list, db) -> list:
    """合并多种材料的 language tags,返回按频次排序的合并列表"""
    all_tags = []
    for m in materials:
        row = db.execute('SELECT material_language FROM materials WHERE id = ? OR code = ?',
                         [m, m]).fetchone()
        if not row: continue
        langs = row['material_language']
        if isinstance(langs, str):
            try: langs = json.loads(langs)
            except Exception: continue
        if isinstance(langs, list):
            all_tags.extend(langs)
    if not all_tags: return []
    # 按频次排序,稳定但去重
    cnt = Counter(all_tags)
    return [t for t, _ in cnt.most_common()]


def generate_concept_text(materials_data: list, part: str, style: str, project_type: str,
                          combined_langs: list) -> str:
    """拼接概念文案"""
    if not materials_data:
        return ''
    opener = random.choice(OPENERS).format(style=style, project_type=project_type or '本项目')
    part_text = PART_FRAGMENTS.get(part, '{part}的材料组合在质感与尺度上呼应整体设计意图。').format(part=part)
    # 描述材料组合
    mat_names = [m['name_cn'] for m in materials_data if m.get('name_cn')]
    if len(mat_names) >= 2:
        mat_text = '主体选用{first}与{second}的组合,{}共同塑造{style}的视觉语言。'.format(
            '辅以其他材料的层次过渡,' if len(mat_names) > 2 else '',
            first=mat_names[0],
            second=mat_names[1] if len(mat_names) > 1 else mat_names[0],
            style=style,
        )
    else:
        mat_text = f'主体选用{mat_names[0] if mat_names else "该材料"},以其质感与尺度定义{style}的视觉语言。'
    # 语言 summary
    lang_summary = '、'.join(combined_langs[:4]) if combined_langs else '材料的本真'
    visual = VISUAL_DEFAULTS.get(style, '明确')
    closer = CLOSERS.get(style, CLOSERS['现代']).format(lang_summary=lang_summary, visual=visual)
    # 拼接
    return (opener + part_text + mat_text + closer).strip()


@bp.post('/api/generate_concept')
def generate_concept():
    """基于材料组合生成概念文案"""
    data = request.get_json(silent=True) or {}
    mat_inputs = data.get('materials') or []
    part = data.get('part') or '外墙'
    style = data.get('style') or '现代'
    project_type = data.get('project_type') or '建筑方案'

    if not mat_inputs:
        return jsonify({'error': '请提供 materials 列表(材料 code 或 id)'}), 400

    db = get_db()
    # 解析材料(支持 code 或 id)
    materials_data = []
    for m in mat_inputs:
        row = db.execute('''
            SELECT m.*, c.name AS category_name
            FROM materials m LEFT JOIN categories c ON m.category_id = c.id
            WHERE m.id = ? OR m.code = ?
        ''', [m, m]).fetchone()
        if row:
            materials_data.append(dict(row))

    if not materials_data:
        return jsonify({'error': '未找到任何有效材料'}), 404

    # 合并 language
    combined = combine_language(mat_inputs, db)
    # 生成文案
    text = generate_concept_text(materials_data, part, style, project_type, combined)
    # highlights:每种材料的 language_notes
    highlights = [
        {'code': m['code'], 'name': m['name_cn'], 'notes': m.get('language_notes')}
        for m in materials_data if m.get('language_notes')
    ]
    return jsonify({
        'concept': text,
        'language_combined': combined,
        'highlights': highlights,
        'word_count': len(text),
    })


def register(app): app.register_blueprint(bp)
