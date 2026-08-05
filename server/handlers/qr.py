"""材料二维码 · /api/materials/<id>/qr
生成一次缓存,后续直接返回文件
"""
from pathlib import Path
import qrcode
from flask import Blueprint, send_from_directory
from ..core import get_db
from .. import config

bp = Blueprint('qr', __name__)


@bp.get('/api/materials/<int:material_id>/qr')
def get_qr(material_id: int):
    db = get_db()
    row = db.execute('SELECT * FROM materials WHERE id = ?', [material_id]).fetchone()
    if not row:
        return {'error': '材料不存在'}, 404

    if not row['qr_code_path'] or not Path(row['qr_code_path']).exists():
        qr_content = f"mavis://material/{row['code']}"
        filename   = f"mat_{row['code']}.png"
        qr_path    = config.QR_DIR / filename
        qr_path.parent.mkdir(parents=True, exist_ok=True)
        if not qr_path.exists():
            qr = qrcode.make(qr_content)
            qr.save(str(qr_path))
        db.execute(
            'UPDATE materials SET qr_code_path = ?, qr_content = ? WHERE id = ?',
            [str(qr_path), qr_content, material_id]
        )
        db.commit()
        path = str(qr_path)
    else:
        path = row['qr_code_path']

    return send_from_directory(config.QR_DIR, Path(path).name)

def register(app): app.register_blueprint(bp)
