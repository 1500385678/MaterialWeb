"""路由注册表 · 加新端点 = 在 handlers/ 加文件 + 在这里 import + register
**这是主程序** · 改之前三思
"""
def register_blueprints(app):
    from .handlers import (
        materials, categories, suppliers, exam, projects,
        qr, media, vision, search_by, schemes, pdf_export, pdf_tasks,
        concept, prices,
    )
    for mod in (materials, categories, suppliers, exam, projects,
                qr, media, vision, search_by, schemes, pdf_export, pdf_tasks,
                concept, prices):
        mod.register(app)
