"""列出所有 active 材料,用于 v0.0.5 price_code 映射"""
import sqlite3
db = sqlite3.connect('db/materials.db')
db.row_factory = sqlite3.Row
rows = db.execute('''SELECT id, code, name_cn, category_id
                     FROM materials
                     WHERE status="active"
                     ORDER BY id''').fetchall()
print(f"共 {len(rows)} 条 active 材料")
for r in rows:
    print(f"  {r['id']:>3}  {r['code']:<10}  {r['name_cn']}")
