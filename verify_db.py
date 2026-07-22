import sqlite3
db = r'D:\Mac\Mac\workteam\05_space\03_architect\_ArchitectLib\MaterialDb\materials.db'
c = sqlite3.connect(db)
c.row_factory = sqlite3.Row

# Tables
tables = c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
print("=== 表结构 ===")
for r in tables:
    cols = c.execute(f"PRAGMA table_info('{r[0]}')").fetchall()
    print(f"  {r[0]}: {len(cols)} 列")

# Summary
cats = c.execute('SELECT COUNT(*) FROM categories').fetchone()[0]
mats = c.execute('SELECT COUNT(*) FROM materials').fetchone()[0]
sups = c.execute('SELECT COUNT(*) FROM suppliers').fetchone()[0]
eks  = c.execute('SELECT COUNT(*) FROM exam_knowledge').fetchone()[0]
prjs = c.execute('SELECT COUNT(*) FROM projects').fetchone()[0]
print(f"\n=== 数据统计 ===")
print(f"  分类: {cats}")
print(f"  材料: {mats}")
print(f"  供应商: {sups}")
print(f"  考试知识点: {eks}")
print(f"  项目: {prjs}")

# Top materials
print(f"\n=== 材料列表 ===")
mats = c.execute('SELECT code, name_cn, fire_rating, unit_price, cost_tier FROM materials WHERE status="active"').fetchall()
for m in mats:
    print(f"  {m[0]:12} | {m[1]:15} | 防火:{m[2] or '-':4} | {m[3] or 0:>6}元/m² | {m[4]}")
