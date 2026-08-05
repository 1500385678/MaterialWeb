"""供应商 · /api/suppliers
"""
from flask import Blueprint
from ..core import get_db, rows_to_list

bp = Blueprint('suppliers', __name__)

@bp.get('/api/suppliers')
def list_suppliers():
    db = get_db()
    rows = db.execute('SELECT * FROM suppliers ORDER BY name').fetchall()
    return {'items': rows_to_list(rows), 'count': len(rows)}

def register(app): app.register_blueprint(bp)
