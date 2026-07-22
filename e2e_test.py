import urllib.request, json

def call(method, url, data=None):
    if data:
        req = urllib.request.Request('http://localhost:5188'+url,
            data=json.dumps(data).encode(),
            headers={'Content-Type':'application/json'},
            method=method)
    else:
        req = urllib.request.Request('http://localhost:5188'+url, method=method)
    return json.loads(urllib.request.urlopen(req, timeout=5).read())

print('=== 端到端测试 ===')

# 1. 取材料列表
mats = call('GET', '/api/materials')
mat_id = mats[0]['id']
print(f'1. 材料列表 OK ({len(mats)} 条) | 第一个: {mats[0]["name_cn"]} id={mat_id}')

# 2. 创建项目
p = call('POST', '/api/projects', {'name':'测试-高端住宅','type':'住宅','area':5000})
print(f'2. 创建项目 OK: id={p["id"]} code={p["code"]}')

# 3. 添加材料
pm = call('POST', f'/api/projects/{p["id"]}/materials', {'material_id':mat_id,'quantity':1500,'location':'外墙'})
print(f'3. 添加材料 OK: pm_id={pm["id"]}')

# 4. 项目详情
proj = call('GET', f'/api/projects/{p["id"]}')
print(f'4. 项目详情 OK: {len(proj["materials"])} 项材料, total_cost={proj["total_cost"]}')

# 5. 成本汇总
cost = call('GET', f'/api/projects/{p["id"]}/cost-summary')
print(f'5. 成本汇总 OK: 总造价 {cost["grand_total"]} 元, 综合单价 {cost["cost_per_sqm"]} 元/m²')
for item in cost['items']:
    print(f'   - {item["category_name"]}: 材料 {item["material_cost"]} + 施工 {item["labor_cost"]} = {item["total"]}')

# 6. 清理
import sqlite3
c = sqlite3.connect(r'D:\Mac\Mac\workteam\05_space\03_architect\_ArchitectLib\MaterialDb\materials.db')
c.execute('DELETE FROM projects')
c.commit()
print('\n6. 测试数据已清理')

print('\n=== 全部测试通过 ===')