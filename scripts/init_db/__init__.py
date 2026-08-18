"""scripts.init_db · 入口,组合 schema + seed

MaterialWeb v1.1 · 从原 scripts/init_db.py(404 行,超铁律#1 250 行)拆出
夜间迭代批 2 (01:00) 改 · P1 Verifier row 16

使用:
  python scripts/init_db.py          # 5 行 wrapper 转调 main()
  python -m scripts.init_db          # 直接调本 __init__
  python scripts/init_db/__init__.py # 同上

拆 3 文件:
  schema.py — DB 路径 + 建表 + 增量加列 (1515 bytes)
  seed.py   — 词库 + 18 材料语言 + 6 工程参考 + 4 个 seed_* (14980 bytes)
  __init__.py — 本文件,入口 main() glue (~30 行)
"""
import sys

from .schema import init_db, add_columns_if_missing, DB_PATH, SCHEMA
from .seed import (
    seed_materials, seed_suppliers, seed_material_language, seed_material_references,
)


def main():
    """兼容 Windows GBK PowerShell:让 print 走 UTF-8"""
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    print(f'DB:     {DB_PATH}')
    print(f'SCHEMA: {SCHEMA}')
    if not SCHEMA.exists():
        print(f'[ERR] 找不到 schema: {SCHEMA}')
        sys.exit(1)
    conn = init_db()
    add_columns_if_missing(conn)
    seed_suppliers(conn)
    seed_materials(conn)
    seed_material_language(conn)
    seed_material_references(conn)
    conn.close()
    print('[done]')


__all__ = [
    'init_db', 'add_columns_if_missing',
    'seed_materials', 'seed_suppliers', 'seed_material_language', 'seed_material_references',
    'DB_PATH', 'SCHEMA', 'main',
]


if __name__ == '__main__':
    main()
