import sqlite3
c = sqlite3.connect(r'D:\Mac\Mac\workteam\05_space\03_architect\_ArchitectLib\MaterialDb\materials.db')
c.row_factory = sqlite3.Row
print('=== project_materials 全表 ===')
rows = c.execute('SELECT * FROM project_materials').fetchall()
for r in rows:
    print(dict(r))

print('\n=== material id=3 ===')
m = c.execute('SELECT id, code, name_cn, unit_price, labor_cost, loss_factor FROM materials WHERE id=3').fetchone()
print(dict(m))

print('\n=== 手工算 ===')
pm = c.execute('SELECT * FROM project_materials WHERE project_id=2').fetchone()
m = c.execute('SELECT * FROM materials WHERE id=?', [pm['material_id']]).fetchone()
total = (m['unit_price'] + m['labor_cost']) * pm['quantity'] * m['loss_factor']
print(f'手工算 total: {total}')