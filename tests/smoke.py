"""Smoke test · 8 项快检(所有核心 API 端点)
用法:python tests/smoke.py
"""
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT))

from server import config  # noqa: E402

BASE = f'http://127.0.0.1:{config.PORT}'
# 端口说明:v1.0 启动用 8087(8086 被僵尸进程占用,杀不掉,改端口)


def _resolve_detail_id():
    """从 /api/materials 拿一个真实 id(没有就返 None)"""
    try:
        with urllib.request.urlopen(f'{BASE}/api/materials?limit=1', timeout=5) as r:
            data = json.loads(r.read())
            return data[0]['id'] if data else None
    except Exception:
        return None


CASES = [
    ('categories',         f'{BASE}/api/categories',         'GET'),
    ('suppliers',          f'{BASE}/api/suppliers',          'GET'),
    ('materials_list',     f'{BASE}/api/materials?limit=3',  'GET'),
    ('materials_search',   f'{BASE}/api/materials/search?q=' + urllib.parse.quote('花岗岩'), 'GET'),
    ('projects_list',      f'{BASE}/api/projects',           'GET'),
    ('exam_chapter_4_1',   f'{BASE}/api/exam/chapter/4.1',   'GET'),
    ('schemes_list',       f'{BASE}/api/schemes',            'GET'),
    # detail 用动态 id(等 list 跑完再注入)
    ('materials_detail',   None, 'GET'),
]


def hit(url, method='GET', body=None):
    data = None
    headers = {}
    if body:
        data = body if isinstance(body, bytes) else str(body).encode('utf-8')
        headers['Content-Type'] = 'application/json'
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, len(r.read())
    except urllib.error.HTTPError as e:
        return e.code, 0
    except Exception as e:
        return 0, str(e)[:50]


def main():
    t0 = time.time()
    print(f'Smoke test · {BASE}')
    print('-' * 50)
    # 先拿一个真实 id
    real_id = _resolve_detail_id()
    for i, (n, u, m) in enumerate(CASES):
        if n == 'materials_detail':
            if real_id:
                CASES[i] = (n, f'{BASE}/api/materials/{real_id}', m)
            else:
                CASES[i] = (n, f'{BASE}/api/materials', m)   # 退到 list
    passed = 0
    for name, url, method in CASES:
        status, size = hit(url, method)
        ok = status in (200, 201, 204)
        if ok: passed += 1
        flag = '✅' if ok else '❌'
        print(f'{flag} {name:20s} {method:5s} {status:3d}  bytes={size}')
    print('-' * 50)
    print(f'✅ {passed}/{len(CASES)} endpoints OK · {time.time()-t0:.2f}s')
    sys.exit(0 if passed == len(CASES) else 1)


if __name__ == '__main__':
    main()
