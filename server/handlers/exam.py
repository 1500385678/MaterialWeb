"""考试知识点 · /api/exam + /api/exam/chapter/<chapter>
按章节整理一级注册建筑师考试材料
"""
from flask import Blueprint
from ..core import get_db, rows_to_list

bp = Blueprint('exam', __name__)

@bp.get('/api/exam')
def list_all():
    """全部知识点(按 chapter, section 排序)"""
    db = get_db()
    rows = db.execute('''
        SELECT e.*, c.name AS category_name
        FROM exam_knowledge e
        LEFT JOIN categories c ON e.category_id = c.id
        ORDER BY e.chapter, e.section
    ''').fetchall()
    return {'items': rows_to_list(rows), 'count': len(rows)}

@bp.get('/api/exam/chapter/<chapter>')
def by_chapter(chapter: str):
    """按章节(如 '4.1')取知识点"""
    db = get_db()
    rows = db.execute('''
        SELECT e.*, c.name AS category_name
        FROM exam_knowledge e
        LEFT JOIN categories c ON e.category_id = c.id
        WHERE e.chapter = ?
        ORDER BY e.section
    ''', [chapter]).fetchall()
    return {'items': rows_to_list(rows), 'count': len(rows)}

def register(app): app.register_blueprint(bp)
