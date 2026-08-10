"""Cache-Control 头单元测试(铁律 #5)
验证 _NO_STORE_TYPES 白名单 + Vary: Accept-Encoding 行为
2026-08-11 夜间迭代批 2 加 · P2 Verifier row 71

用法:python tests/test_cache_headers.py
依赖:不需要起 server,用 Flask test_client 内存跑
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT))

from server import create_app  # noqa: E402


def _assert_no_store(resp, expect: bool, label: str):
    cc = (resp.headers.get('Cache-Control') or '').lower()
    has = 'no-store' in cc
    flag = '✅' if has == expect else '❌'
    action = 'MUST' if expect else 'NO  '
    print(f'{flag} {label:20s} {action} no-store · Cache-Control={cc!r}')
    assert has == expect, f'{label}: expect no-store={expect}, got Cache-Control={cc!r}'


def _assert_vary(resp, expect: bool, label: str):
    v = (resp.headers.get('Vary') or '').lower()
    has = 'accept-encoding' in v
    flag = '✅' if has == expect else '❌'
    print(f'{flag} {label:20s} Vary Accept-Encoding={"yes" if has else "no"} · Vary={v!r}')
    assert has == expect, f'{label}: expect Vary:Accept-Encoding={expect}, got {v!r}'


def main():
    print('Cache-Control 头白名单测试 · 铁律 #5')
    print('-' * 60)
    app = create_app()
    client = app.test_client()

    cases = [
        # (path,         expect_no_store, label)
        ('/',            True,  'index.html'),     # Flask static → text/html
        ('/index.html',  True,  'index.html (explicit)'),
        ('/css/missing', True,  'css (404 → text/html)'),
    ]

    # 探测 .js / .css / .png 实际路径
    client_dir = ROOT / 'client'
    js_files  = list(client_dir.rglob('*.js'))
    css_files = list(client_dir.rglob('*.css'))
    png_files = list(client_dir.rglob('*.png'))
    if js_files:
        cases.append(('/' + str(js_files[0].relative_to(client_dir)), True,  'js (real)'))
    if css_files:
        cases.append(('/' + str(css_files[0].relative_to(client_dir)), True, 'css (real)'))
    if png_files:
        cases.append(('/' + str(png_files[0].relative_to(client_dir)), False, 'png (real)'))

    # JSON 端点不应被强制 no-store
    cases.append(('/api/categories', False, 'JSON /api/categories'))

    passed = 0
    for path, expect, label in cases:
        resp = client.get(path)
        _assert_no_store(resp, expect, label)
        # Vary 头只在 expect=True 时必加(JSON 不强加)
        _assert_vary(resp, expect, label)
        passed += 1

    print('-' * 60)
    print(f'✅ {passed}/{len(cases)} cache-header 断言通过')
    return 0 if passed == len(cases) else 1


if __name__ == '__main__':
    sys.exit(main())
