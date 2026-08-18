"""search_by_analysis 性能基准(P1 Verifier row 70)
灌 1000 行 fixture → 跑 100 次搜索 → 断言 P95 < 200ms
2026-08-11 夜间迭代批 2 加

用法:python tests/search_bench.py
依赖:Flask test_client(不依赖外部 server)
"""
import sys
import time
import statistics
from pathlib import Path

ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT))

from server import create_app  # noqa: E402


# 性能契约 P95 < 200ms(对应 _PRE_FILTER_LIMIT=500 + Python 8 字段精排)
P95_BUDGET_MS = 200.0
FIXTURE_COUNT = 1000
RUN_COUNT     = 100
BENCH_CODE_PREFIX = '__BENCH_'  # fixture 标记,清理时按 prefix 删


# 10 个关键词(模拟 AI 视觉模型典型输出)
KEYWORDS = [
    '石材', '花岗岩', '大理石', '幕墙', '干挂',
    '防火', 'A级', '天然', '灰色', '抛光',
]


def _seed_fixtures(app, n: int):
    """灌 n 行 fixture 进 materials 表,返回 (start_id, end_id) 闭区间"""
    from server.core import get_db
    with app.app_context():
        db = get_db()
        # 灌前先清旧 fixture(幂等)
        db.execute(f"DELETE FROM materials WHERE code LIKE '{BENCH_CODE_PREFIX}%'")
        db.commit()
        # 拿一个合法 category_id
        cat_row = db.execute('SELECT id FROM categories LIMIT 1').fetchone()
        cat_id = cat_row[0] if cat_row else None
        rows = []
        for i in range(n):
            code = f'{BENCH_CODE_PREFIX}{i:04d}'
            # 混合构造:60% 命中关键词,40% 不命中
            kw = KEYWORDS[i % len(KEYWORDS)] if i % 5 < 3 else f'随机{i}'
            # 14 列 · 严格匹配 INSERT 占位符
            rows.append((
                code, f'测试材料-{i}', f'BenchMat{i}',  # code, name_cn, name_en
                cat_id, f'子分类-{kw}',                    # category_id, sub_category
                'A1', 100.0, '元/m²', '中',               # fire_rating, unit_price, unit, cost_tier
                f'["{kw}"]',                              # applications_json
                f'[{kw}系列]', f'["{kw}"]',               # texture, color_series
                f'外观描述 {kw}',                          # visual_desc
                'active',                                  # status
            ))
        db.executemany('''
            INSERT INTO materials
            (code, name_cn, name_en, category_id, sub_category,
             fire_rating, unit_price, unit, cost_tier,
             applications_json, texture, color_series, visual_desc, status)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ''', rows)
        db.commit()
        first_id = db.execute(
            f"SELECT id FROM materials WHERE code='{BENCH_CODE_PREFIX}0000'"
        ).fetchone()[0]
    return first_id, first_id + n - 1


def _cleanup_fixtures(app):
    from server.core import get_db
    with app.app_context():
        db = get_db()
        db.execute(f"DELETE FROM materials WHERE code LIKE '{BENCH_CODE_PREFIX}%'")
        db.commit()


def main():
    print(f'search_by_analysis 性能基准 · n={FIXTURE_COUNT} fixtures · run={RUN_COUNT} 次')
    print('-' * 60)
    app = create_app()
    client = app.test_client()

    try:
        _seed_fixtures(app, FIXTURE_COUNT)
        print(f'已灌 {FIXTURE_COUNT} 行 fixture')

        body = {
            'search_keywords': KEYWORDS,
            'identified_materials': [],
        }
        # 热身 5 次(避开 JIT/缓存冷启动)
        for _ in range(5):
            client.post('/api/search_by_analysis', json=body)

        timings = []
        for i in range(RUN_COUNT):
            t0 = time.perf_counter()
            r = client.post('/api/search_by_analysis', json=body)
            dt = (time.perf_counter() - t0) * 1000  # ms
            if r.status_code != 200:
                print(f'❌ 第 {i+1} 次 status={r.status_code}')
                return 1
            timings.append(dt)

        timings.sort()
        p50 = timings[len(timings)//2]
        p95 = timings[int(len(timings) * 0.95)]
        p99 = timings[int(len(timings) * 0.99)]
        avg = statistics.mean(timings)
        mx  = max(timings)
        print(f'完成 {RUN_COUNT} 次调用:')
        print(f'  avg = {avg:6.2f}ms')
        print(f'  p50 = {p50:6.2f}ms')
        print(f'  p95 = {p95:6.2f}ms   ← 契约预算 {P95_BUDGET_MS:.0f}ms')
        print(f'  p99 = {p99:6.2f}ms')
        print(f'  max = {mx:6.2f}ms')

        ok = p95 < P95_BUDGET_MS
        flag = '✅' if ok else '❌'
        print('-' * 60)
        print(f'{flag} P95 {p95:.2f}ms {"<" if ok else ">="} {P95_BUDGET_MS:.0f}ms · {"达标" if ok else "超预算"}')
        return 0 if ok else 1
    finally:
        _cleanup_fixtures(app)
        print('已清 fixture')


if __name__ == '__main__':
    sys.exit(main())
