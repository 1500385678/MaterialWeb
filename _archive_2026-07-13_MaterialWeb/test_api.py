import urllib.request, json

def test(url):
    r = urllib.request.urlopen('http://localhost:5188' + url, timeout=5)
    return json.loads(r.read())

print('=== API 健康检查 ===')
print('材料列表:', len(test('/api/materials')), '条')
print('供应商:',   len(test('/api/suppliers')), '条')
print('项目:',     len(test('/api/projects')), '个')
print('考试(4.1):', len(test('/api/exam/chapter/4.1')), '条')

# 测试新建项目
req = urllib.request.Request(
    'http://localhost:5188/api/projects',
    data=json.dumps({'name':'测试-高端住宅','type':'住宅','area':5000}).encode(),
    headers={'Content-Type':'application/json'},
    method='POST'
)
r = json.loads(urllib.request.urlopen(req, timeout=5).read())
print('创建项目:', 'id=' + str(r['id']), 'code=' + r['code'])

# 测试添加材料到项目
req2 = urllib.request.Request(
    'http://localhost:5188/api/projects/' + str(r['id']) + '/materials',
    data=json.dumps({'material_id': 3, 'quantity': 2000, 'location': '外墙'}).encode(),
    headers={'Content-Type':'application/json'},
    method='POST'
)
r2 = json.loads(urllib.request.urlopen(req2, timeout=5).read())
print('添加材料:', 'pm_id=' + str(r2['id']))

# 测试成本汇总
cost = test('/api/projects/' + str(r['id']) + '/cost-summary')
print('总造价:', cost['grand_total'], '元')
print('综合单价:', cost['cost_per_sqm'], '元/m²')
print('分项:', cost['items'])