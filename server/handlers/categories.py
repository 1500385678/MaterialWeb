"""分类树 · /api/categories
单文件,一次性返回全部分类
"""
from flask import Blueprint
from ..core import get_db, rows_to_list

bp = Blueprint('categories', __name__)

@bp.get('/api/categories')
def list_categories():
    db = get_db()
    rows = db.execute(
        'SELECT * FROM categories ORDER BY sort_order, code'
    ).fetchall()
    return {'items': rows_to_list(rows), 'count': len(rows)}

def register(app): app.register_blueprint(bp)
