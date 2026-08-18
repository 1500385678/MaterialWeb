"""server.workers · 后台任务执行器
- pdf_pool: PDF 导出任务队列(避免 doc.build 同步阻塞 Flask 主进程)
"""
