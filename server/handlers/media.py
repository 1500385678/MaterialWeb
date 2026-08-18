"""媒体服务 · 图片 / CAD / uploads 三类静态
/api/media/images/<file> · /api/media/cad/<file> · /uploads/<file>
"""
import json
import logging
from flask import Blueprint, send_from_directory, jsonify
from ..core import get_db
from .. import config

logger = logging.getLogger(__name__)

bp = Blueprint('media', __name__)

@bp.get('/api/media/images/<path:filename>')
def serve_image(filename: str):
    config.IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    return send_from_directory(str(config.IMAGES_DIR), filename)

@bp.get('/api/media/cad/<path:filename>')
def download_cad(filename: str):
    """CAD 文件下载(DWG/SKP/PDF/DXF)"""
    config.CAD_DIR.mkdir(parents=True, exist_ok=True)
    return send_from_directory(
        str(config.CAD_DIR), filename,
        as_attachment=True, download_name=filename,
    )

@bp.get('/uploads/<path:filename>')
def serve_upload(filename: str):
    """AI 上传图片(供前端预览)"""
    config.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    return send_from_directory(str(config.UPLOAD_DIR), filename)

@bp.get('/api/media/list/<int:material_id>')
def list_media(material_id: int):
    db = get_db()
    row = db.execute(
        'SELECT image_urls, cad_files FROM materials WHERE id = ?', [material_id]
    ).fetchone()
    if not row:
        return jsonify({'error': '材料不存在'}), 404
    def _parse(v):
        if not v: return []
        try: return json.loads(v)
        except (OSError, IOError, ValueError) as exc:
            logger.warning('media._parse: parse value failed: %r', exc)
            return []
    return jsonify({
        'images':    _parse(row['image_urls']),
        'cad_files': _parse(row['cad_files']),
    })

def register(app): app.register_blueprint(bp)
