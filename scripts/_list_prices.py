"""列出价格库所有 distinct material_name,用于 MaterialWeb 端 18 材料映射"""
import sqlite3
db = sqlite3.connect('D:/Mac/Mac/Mac/workteam/05_space/03_architect/Defense/06-Material/Attack/价格库/prices.db')
db.row_factory = sqlite3.Row
rows = db.execute('''SELECT DISTINCT material_name
                     FROM material_spec_prices
                     ORDER BY material_name''').fetchall()
print(f"共 {len(rows)} 个 distinct material_name")
for r in rows:
    print(f"  {r['material_name']}")
