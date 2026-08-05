"""测试 concept API 的真实输出(写文件避免 PowerShell GBK 截字符)"""
import json
import urllib.request

url = 'http://127.0.0.1:8093/api/generate_concept'
body = json.dumps({
    'materials': ['GRC_001', 'UHPC_001', 'GLASS_001'],
    'part': '幕墙',
    'style': '现代',
    'project_type': '商业综合体',
}, ensure_ascii=False).encode('utf-8')
req = urllib.request.Request(url, data=body, method='POST',
                              headers={'Content-Type': 'application/json; charset=utf-8'})
with urllib.request.urlopen(req, timeout=10) as r:
    d = json.loads(r.read().decode('utf-8'))

out = r'D:\Mac\Mac\Mac\workteam\05_space\03_architect\Defense\06-Material\_ArchiDefenseMaterial\MaterialWeb\.Log\test_concept_output.md'
with open(out, 'w', encoding='utf-8') as f:
    f.write('# 概念文案生成测试\n\n')
    f.write('**输入** materials: GRC_001 / UHPC_001 / GLASS_001, part: 幕墙, style: 现代, project_type: 商业综合体\n\n')
    f.write('**输出**:\n\n')
    f.write('> ' + d['concept'] + '\n\n')
    f.write('**字数**: ' + str(d['word_count']) + '\n\n')
    f.write('**合并语言**: ' + ' / '.join(d['language_combined']) + '\n\n')
    f.write('**材料亮点**:\n')
    for h in d['highlights']:
        f.write(f"- **{h['name']}** ({h['code']}): {h['notes']}\n")

print('written to:', out)
print('concept:')
print(d['concept'])
