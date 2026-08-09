"""列出价格库所有 distinct material_name,用于 MaterialWeb 端 18 材料映射

v0.0.6 · 2026-08-10 批 2 夜间迭代
  原 D:/Mac/Mac/Mac/.../Attack/价格库/prices.db 硬编码仅 Win 机器可用,
  改成 ROOT 相对 + 探测顺序,Mac / Linux / Windows 三平台通用。
  对齐 server/config.py:17 PRICES_DB_PATH (4baa3a8 批 2 P1②)。
"""
import sqlite3
from pathlib import Path

ROOT = Path(__file__).parent.parent.resolve()

# 探测顺序:本项目 data/ → 兄弟项目 Attack/价格库/ → 兜底 None
PRICES_CANDIDATES = [
    ROOT / 'data' / 'prices.db',
    ROOT.parent / 'Attack' / '价格库' / 'prices.db',
]

db_path = next((p for p in PRICES_CANDIDATES if p.exists()), None)
if db_path is None:
    print(f'❌ 价格库不存在,试过:')
    for p in PRICES_CANDIDATES:
        print(f'   - {p}')
    raise SystemExit(1)

print(f'📂 价格库: {db_path}')
db = sqlite3.connect(str(db_path))
db.row_factory = sqlite3.Row
rows = db.execute('''SELECT DISTINCT material_name
                     FROM material_spec_prices
                     ORDER BY material_name''').fetchall()
print(f"共 {len(rows)} 个 distinct material_name")
for r in rows:
    print(f"  {r['material_name']}")
