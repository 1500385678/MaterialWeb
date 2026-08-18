"""init_db.schema · DB 路径常量 + 建表 + 增量加列

MaterialWeb v1.1 · 从原 scripts/init_db.py(404 行,超铁律#1 250 行)拆出
夜间迭代批 2 (01:00) 改 · P1 Verifier row 16
"""
import sqlite3
from pathlib import Path

# 项目根(以 schema.py 自身位置推)
BASE_DIR = Path(__file__).parent.parent.parent  # scripts/init_db/schema.py → 项目根
DB_PATH  = BASE_DIR / 'db' / 'materials.db'
SCHEMA   = BASE_DIR / 'db' / 'init_schema.sql'


def init_db() -> sqlite3.Connection:
    """建表(读 init_schema.sql)"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.executescript(open(SCHEMA, encoding='utf-8').read())
    conn.commit()
    print(f'[ok] 表结构已就绪: {DB_PATH}')
    return conn


def add_columns_if_missing(conn):
    """增量加列(对已存在 DB 兼容)"""
    targets = [
        ('materials', 'material_language', "TEXT DEFAULT '[]'"),
        ('materials', 'language_notes',    "TEXT DEFAULT NULL"),
    ]
    for table, col, decl in targets:
        cur = conn.execute(f"PRAGMA table_info({table})")
        existing = {row['name'] for row in cur.fetchall()}
        if col in existing:
            continue
        try:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {decl}")
            print(f'  [ok] 加列 {table}.{col}')
        except sqlite3.OperationalError as e:
            print(f'  [!] 加列 {table}.{col} 失败: {e}')
    conn.commit()
