"""PDF 导出 · /api/schemes/<id>/export/pdf
reportlab + 中文字体(自动探测 msyh.ttc / simhei / Noto Sans CJK)
"""
import io
import json
import os
import re
from flask import Blueprint, send_file
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib import colors as rl_colors
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle,
)
from ..core import get_db
from .. import config

bp = Blueprint('pdf_export', __name__)


def _load_zh_font():
    """启动时尝试多种中文字体路径,返回 (regular, bold) font name"""
    ZH, ZHB = 'Helvetica', 'Helvetica-Bold'
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
                ZH, ZHB = 'zh', 'zh-bold'
                print(f"[PDF] Loaded Chinese font: {fp}")
                break
            except Exception as e:
                print(f"[PDF] Failed {fp}: {e}")
    return ZH, ZHB


ZH_FONT, ZH_FONT_BOLD = _load_zh_font()


def _styles():
    base = getSampleStyleSheet()['Normal']
    return {
        'title':    ParagraphStyle('T',  fontName=ZH_FONT_BOLD, fontSize=20, leading=26, textColor=rl_colors.HexColor('#ff9e4a'), spaceAfter=4),
        'subtitle': ParagraphStyle('S',  fontName=ZH_FONT,      fontSize=10, leading=14, textColor=rl_colors.grey, spaceAfter=12),
        'h2':       ParagraphStyle('H2', fontName=ZH_FONT_BOLD, fontSize=13, leading=18, textColor=rl_colors.HexColor('#ff9e4a'), spaceBefore=10, spaceAfter=8),
        'body':     ParagraphStyle('B',  fontName=ZH_FONT,      fontSize=10, leading=15, spaceAfter=4),
        'label':    ParagraphStyle('L',  fontName=ZH_FONT,      fontSize=9,  leading=13, textColor=rl_colors.grey),
        'cell':     ParagraphStyle('C',  fontName=ZH_FONT,      fontSize=8,  leading=11),
        'cellB':    ParagraphStyle('CB', fontName=ZH_FONT_BOLD, fontSize=9,  leading=12),
        'center':   ParagraphStyle('CT', fontName=ZH_FONT,      fontSize=9,  leading=12, alignment=1),
        'footer':   ParagraphStyle('F',  fontName=ZH_FONT,      fontSize=9,  leading=12, textColor=rl_colors.grey, alignment=1),
    }


@bp.get('/api/schemes/<int:sid>/export/pdf')
def export_pdf(sid: int):
    db = get_db()
    s = db.execute('SELECT * FROM material_schemes WHERE id = ?', (sid,)).fetchone()
    if not s:
        return {'error': '方案不存在'}, 404
    sch = dict(s)

    mats = db.execute('''
        SELECT sm.id AS sm_id, sm.score, sm.score_reason, sm.is_selected,
               m.id, m.code, m.name_cn, m.name_en, m.visual_desc, m.unit_price, m.unit,
               m.cost_tier, m.fire_rating, c.name AS category_name
        FROM scheme_materials sm
        JOIN materials m ON m.id = sm.material_id
        LEFT JOIN categories c ON c.id = m.category_id
        WHERE sm.scheme_id = ?
        ORDER BY sm.score DESC
    ''', (sid,)).fetchall()

    ctx = {}
    if sch.get('analysis_json'):
        try: ctx = json.loads(sch['analysis_json'])
        except: pass
    analysis = ctx.get('analysis') or {}

    s_ = _styles()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=1.8*cm, bottomMargin=1.8*cm,
        leftMargin=2*cm, rightMargin=2*cm,
        title=sch['name'], author='MaterialWeb AI 选材',
    )
    story = []

    # 标题 + 元数据
    story.append(Paragraph(sch['name'], s_['title']))
    meta = f"创建时间: {sch.get('created_at', '—')}   |   材质数量: {len(mats)}"
    if sch.get('project_id'):
        meta += f"   |   关联项目: #{sch['project_id']}"
    story.append(Paragraph(meta, s_['subtitle']))

    # 缩略图
    if sch.get('image_filename'):
        img_path = config.UPLOAD_DIR / sch['image_filename']
        if img_path.exists():
            try:
                img = RLImage(str(img_path), width=10*cm, height=7.5*cm, kind='proportional')
                img.hAlign = 'CENTER'
                story.append(img)
                story.append(Spacer(1, 6))
            except Exception as e:
                print(f"[PDF] Image error: {e}")

    if sch.get('description'):
        story.append(Paragraph('方案描述', s_['h2']))
        story.append(Paragraph(sch['description'].replace('\n', '<br/>'), s_['body']))

    if analysis:
        story.append(Paragraph('AI 场景分析', s_['h2']))
        if analysis.get('scene_description'):
            story.append(Paragraph(f"<b>场景:</b>{analysis['scene_description']}", s_['body']))
        story.append(Paragraph(
            f"<b>类型:</b>{analysis.get('context') or '—'}　　<b>风格:</b>{analysis.get('style') or '—'}",
            s_['body'],
        ))
        if analysis.get('identified_materials'):
            names = '、'.join([m.get('name', '—') for m in analysis['identified_materials'][:8]])
            story.append(Paragraph(f"<b>识别材质:</b>{names}", s_['body']))
        if analysis.get('search_keywords'):
            kws = '、'.join(analysis['search_keywords'][:8])
            story.append(Paragraph(f"<b>关键词:</b>{kws}", s_['body']))

    # 材质清单
    story.append(Paragraph(f'材质清单({len(mats)} 项)', s_['h2']))
    data = [[
        Paragraph('<b>#</b>',       s_['cellB']),
        Paragraph('<b>名称</b>',     s_['cellB']),
        Paragraph('<b>类别</b>',     s_['cellB']),
        Paragraph('<b>防火</b>',     s_['cellB']),
        Paragraph('<b>造价</b>',     s_['cellB']),
        Paragraph('<b>单价</b>',     s_['cellB']),
        Paragraph('<b>匹配分</b>',   s_['cellB']),
        Paragraph('<b>描述</b>',     s_['cellB']),
    ]]
    for i, m in enumerate(mats, 1):
        m = dict(m)
        name_html = f"{m.get('name_cn','')}<br/><font size=7 color=grey>{m.get('name_en','')}</font>"
        desc_html = (m.get('visual_desc') or '—').replace('\n', '<br/>')
        data.append([
            Paragraph(str(i), s_['center']),
            Paragraph(name_html, s_['cell']),
            Paragraph(m.get('category_name') or '—', s_['cell']),
            Paragraph(m.get('fire_rating') or '—', s_['center']),
            Paragraph(m.get('cost_tier') or '—', s_['center']),
            Paragraph(f"¥{m.get('unit_price', 0)}/{m.get('unit','m²')}", s_['cell']),
            Paragraph(str(m.get('score', 0)), s_['center']),
            Paragraph(desc_html, s_['cell']),
        ])
    table = Table(data, colWidths=[0.8*cm, 3.5*cm, 1.8*cm, 1*cm, 1*cm, 1.8*cm, 1*cm, 6*cm], repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND',  (0,0), (-1,0), rl_colors.HexColor('#ff9e4a')),
        ('TEXTCOLOR',   (0,0), (-1,0), rl_colors.white),
        ('GRID',        (0,0), (-1,-1), 0.4, rl_colors.grey),
        ('VALIGN',      (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING',(0,0), (-1,-1), 4),
        ('TOPPADDING',  (0,0), (-1,-1), 5),
        ('BOTTOMPADDING',(0,0),(-1,-1), 5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [rl_colors.white, rl_colors.HexColor('#fafafa')]),
    ]))
    story.append(table)

    # 命中详情
    story.append(Spacer(1, 8))
    story.append(Paragraph('命中详情', s_['h2']))
    for i, m in enumerate(mats, 1):
        m = dict(m)
        story.append(Paragraph(f"<b>{i}. {m.get('name_cn','')}</b>　匹配分 {m.get('score', 0)}", s_['cellB']))
        story.append(Paragraph(f"　{(m.get('score_reason') or '—').replace(',', '，')}", s_['cell']))
        story.append(Spacer(1, 3))

    story.append(Spacer(1, 16))
    story.append(Paragraph('— 本方案由 MaterialWeb AI 选材生成 —', s_['footer']))

    doc.build(story)
    buf.seek(0)

    safe_name = re.sub(r'[\\/:*?"<>|]', '_', sch['name'])
    return send_file(
        buf, mimetype='application/pdf',
        as_attachment=True, download_name=f"{safe_name}_{sid}.pdf",
    )


def register(app): app.register_blueprint(bp)
