"""PDF 导出异步端点 · 配合 server/workers/pdf_pool.py
P0 修 2026-08-09 夜间迭代批 3:doc.build 同步阻塞 Flask 主线程,
改用 POST 提交 + GET 查状态 + GET 下载,前端轮询拿产物。

    POST /api/schemes/<sid>/export/pdf
        → {task_id, status:"pending", status_url}
    GET  /api/schemes/<sid>/export/pdf/status/<task_id>
        → {status:"pending|done|error|unknown", ...}
    GET  /api/schemes/<sid>/export/pdf/download/<task_id>
        → application/pdf(产物文件)
"""
from flask import Blueprint, send_file
from .pdf_export import build_pdf
from ..workers import pdf_pool

bp = Blueprint('pdf_tasks', __name__)


@bp.post('/api/schemes/<int:sid>/export/pdf')
def submit(sid: int):
    """异步提交 PDF 导出,立刻返 task_id(不阻塞)"""
    task_id = pdf_pool.submit(sid, build_pdf)
    return {
        'task_id':    task_id,
        'status':     'pending',
        'status_url': f'/api/schemes/{sid}/export/pdf/status/{task_id}',
    }, 202


@bp.get('/api/schemes/<int:sid>/export/pdf/status/<task_id>')
def task_status(sid, task_id):
    """查任务状态。前端轮询这个端点拿 progress / download_url"""
    st = pdf_pool.status(task_id)
    # 未知 task_id 给 404,便于前端区分
    if st.get('status') == 'unknown':
        return st, 404
    return st


@bp.get('/api/schemes/<int:sid>/export/pdf/download/<task_id>')
def task_download(sid, task_id):
    """下载已完成任务的 PDF 产物(走 pdf_pool 缓存)"""
    path = pdf_pool.result_path(task_id)
    if not path:
        return {'error': 'PDF 未就绪或已过期(>1h)'}, 404
    return send_file(path, mimetype='application/pdf', as_attachment=True)


def register(app): app.register_blueprint(bp)
