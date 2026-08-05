"""MaterialWeb v1.0 · 建筑材料数据库后端
参考 CanvasWeb-v2.5 框架:主程序 vs 支程序 · 单文件 ≤250 行
"""
__version__ = '1.0.0'

# 顶层 API 暴露(便于 from server import create_app)
from .core import create_app, get_db, row_to_dict, rows_to_list, to_text_list  # noqa
from . import config  # noqa
