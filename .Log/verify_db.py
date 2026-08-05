"""验证 materials.db 数据"""
import sqlite3
import json

conn = sqlite3.connect(r'D:\Mac\Mac\Mac\workteam\05_space\03_architect\Defense\06-Material\_ArchiDefenseMaterial\MaterialWeb\db\materials.db')
conn.row_factory = sqlite3.Row

print('=== materials 加列 ===')
cols = [r['name'] for r in conn.execute('PRAGMA table_info(materials)')]
print('material_language:', 'material_language' in cols)
print('language_notes:', 'language_notes' in cols)

print()
print('=== 18 种材料 language ===')
for r in conn.execute('SELECT code, name_cn, material_language, language_notes FROM materials ORDER BY code'):
    if r['material_language']:
        print('  %-12s | %-14s | %-30s | %s' % (r['code'], r['name_cn'][:14], r['material_language'], r['language_notes'][:25] if r['language_notes'] else ''))

print()
print('=== references ===')
total = conn.execute('SELECT COUNT(*) FROM material_references').fetchone()[0]
print('total:', total)
for r in conn.execute('''
    SELECT m.code, m.name_cn, r.project_name, r.designer, r.city, r.year, r.part, r.comment
    FROM material_references r
    JOIN materials m ON m.id = r.material_id
    ORDER BY m.code, r.sort_order
'''):
    print('  [%s/%s] %s · %s / %s / %s / %s' % (r['code'], r['name_cn'][:8], r['project_name'], r['designer'] or '?', r['city'] or '?', r['year'] or '?', r['part'] or '?'))
    print('       点评: %s' % (r['comment'] or ''))
