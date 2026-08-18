"""PDF 导出任务队列 · ThreadPoolExecutor 跑 doc.build(story)
避免同步阻塞 Flask 主进程(P0 修 2026-08-09 夜间迭代批 3)

调用模式:
    from server.workers import pdf_pool
    task_id = pdf_pool.submit(scheme_id, build_pdf)
    pdf_pool.status(task_id)        # → {status, ...}
    pdf_pool.result_path(task_id)   # → /abs/path/to.pdf 或 None

任务状态机: pending → done / error
过期清理: gc() 移除 >1h 任务 + 删除产物文件
"""
import os
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event, Lock, Thread

_pool: ThreadPoolExecutor = None
_tasks: dict[str, dict] = {}
_lock = Lock()
MAX_WORKERS = 2
TASK_TTL_SECONDS = 3600          # 1h
GC_INTERVAL_SECONDS = int(os.getenv('MW_PDF_GC_INTERVAL', '600'))  # 10min
EXPORT_DIR_NAME = 'exports'
_gc_thread: Thread = None
_gc_stop = Event()


def _export_dir() -> Path:
    from .. import config
    d = config.ROOT / 'data' / EXPORT_DIR_NAME
    d.mkdir(parents=True, exist_ok=True)
    return d


def init_pool() -> ThreadPoolExecutor:
    global _pool, _gc_thread
    if _pool is None:
        _pool = ThreadPoolExecutor(max_workers=MAX_WORKERS, thread_name_prefix='pdf-')
        _start_gc_loop()
    return _pool


def _start_gc_loop():
    """启动守护线程:每 GC_INTERVAL_SECONDS 调一次 gc(),防止 _tasks / data/exports 泄漏
    (R162 P0 修 2026-08-16 夜间迭代批 1)"""
    global _gc_thread
    if _gc_thread is not None and _gc_thread.is_alive():
        return
    _gc_stop.clear()

    def _loop():
        while not _gc_stop.is_set():
            # 用 wait 而非 sleep,shutdown 时能立即唤醒
            if _gc_stop.wait(GC_INTERVAL_SECONDS):
                break
            try:
                gc()
            except Exception as e:  # noqa: BLE001 守卫线程,绝不冒泡
                import logging
                logging.getLogger('pdf_pool.gc').warning('gc loop tick failed: %r', e)

    _gc_thread = Thread(target=_loop, name='pdf-gc', daemon=True)
    _gc_thread.start()


def submit(scheme_id: int, run_fn) -> str:
    """提交 PDF 导出任务,返 task_id(12 位 hex)"""
    init_pool()
    task_id = uuid.uuid4().hex[:12]
    future = _pool.submit(run_fn, scheme_id, task_id)
    with _lock:
        _tasks[task_id] = {
            'scheme_id':  scheme_id,
            'status':     'pending',
            'future':     future,
            'result_path': None,
            'error':      None,
            'created_at': time.time(),
        }
    future.add_done_callback(lambda f: _on_done(task_id, f))
    return task_id


def _on_done(task_id: str, future):
    with _lock:
        t = _tasks.get(task_id)
        if not t:
            return
        try:
            t['result_path'] = future.result()
            t['status'] = 'done'
        except Exception as e:
            t['status'] = 'error'
            t['error'] = str(e)


def status(task_id: str) -> dict:
    """查任务状态(线程安全 + 不返 future 对象)"""
    with _lock:
        t = _tasks.get(task_id)
    if not t:
        return {'status': 'unknown', 'error': 'task_id 不存在或已过期(>1h 自动清理)'}
    out = {'status': t['status'], 'scheme_id': t['scheme_id'], 'task_id': task_id}
    if t['status'] == 'done':
        out['download_url'] = f'/api/schemes/{t["scheme_id"]}/export/pdf/download/{task_id}'
    elif t['status'] == 'error':
        out['error'] = t['error']
    return out


def result_path(task_id: str):
    with _lock:
        t = _tasks.get(task_id)
    if t and t['status'] == 'done':
        return t['result_path']
    return None


def gc():
    """清理 >1h 的 done/error 任务及其产物文件
    任务按 created_at 判过期;产物文件额外按 mtime 判过期(防长任务 2h+ 完成但 created_at 新鲜)"""
    now = time.time()
    with _lock:
        expired = [tid for tid, t in _tasks.items() if now - t['created_at'] > TASK_TTL_SECONDS]
    for tid in expired:
        with _lock:
            t = _tasks.pop(tid, None)
        if t and t.get('result_path'):
            try:
                Path(t['result_path']).unlink(missing_ok=True)
            except Exception:
                pass
    # 扫盘:产物文件 mtime 超 TTL 即便 _tasks 没记也清(daemon 重启/老文件残留)
    try:
        export_dir = _export_dir()
    except Exception:
        return
    for f in export_dir.glob('*.pdf'):
        try:
            if now - f.stat().st_mtime > TASK_TTL_SECONDS:
                f.unlink(missing_ok=True)
        except Exception:
            continue


def shutdown():
    global _pool, _gc_thread
    _gc_stop.set()  # 唤醒守护线程
    if _pool:
        # shutdown 前先 gc 一轮,把刚 done 的产物也按 mtime 顺手清
        try:
            gc()
        except Exception:
            pass
        _pool.shutdown(wait=False, cancel_futures=True)
        _pool = None
    _gc_thread = None
