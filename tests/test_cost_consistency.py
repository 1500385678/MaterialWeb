"""造价口径一致性测试(铁律 — 2026-08-13 夜间迭代批 2 加 · P0 Verifier row 328)

背景:
  detail() / cost-summary() / export_docx() 三个端点曾用 3 套公式计算 total,
  同一项目可能返 3 个不同数字。本次抽 _effective_unit_cost(pm, m) helper,
  三端点统一走 pm.unit_cost 优先 / m.unit_price + m.labor_cost 回退。

验证:
  1) helper 自身:pm.unit_cost > 0 用覆盖;否则回退
  2) 三端点对同一项目返的 total_cost / grand_total / total_cost 一致
  3) export_docx 旧 bug:r['loss_factor'] 在 pm 表不存在,SQL 没 select m.loss_factor → KeyError,已修
  4) cost-summary 按 (category, unit) 分组聚合正确

用法:python tests/test_cost_consistency.py
依赖:Flask test_client + 临时 SQLite,不依赖 db/materials.db 真实数据
"""
import sys
import sqlite3
import tempfile
from pathlib import Path

ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT))


def _build_test_db() -> str:
    """建一个临时 SQLite,挂载 projects / materials / project_materials / categories,
    并塞 1 个项目 + 2 条材料(一条覆盖 / 一条回退)用于一致性断言。
    """
    tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    tmp.close()
    db_path = tmp.name

    schema = Path(ROOT / 'db' / 'init_schema.sql').read_text(encoding='utf-8')
    conn = sqlite3.connect(db_path)
    conn.executescript(schema)

    # 注入测试 fixtures(categories.code NOT NULL,需补;init_schema 末尾已占 id 1-32,改用 100/101 避冲突)
    conn.execute("INSERT INTO categories (id, code, name) VALUES (100, 'test.wall', '墙面')")
    conn.execute("INSERT INTO categories (id, code, name) VALUES (101, 'test.floor', '地面')")

    # m1 乳胶漆(墙面):用户覆盖 unit_cost=300(优先);m.unit_price=200, labor=80 → 回退=280
    conn.execute("""
        INSERT INTO materials (id, code, name_cn, category_id, unit, unit_price, labor_cost, loss_factor, fire_rating)
        VALUES (1, 'MAT_T01', '测试乳胶漆', 100, '元/m²', 200, 80, 1.05, 'A1')
    """)
    # m2 实木地板(地面):用户不覆盖 → 走回退 m.unit_price=500 + labor=100=600
    conn.execute("""
        INSERT INTO materials (id, code, name_cn, category_id, unit, unit_price, labor_cost, loss_factor, fire_rating)
        VALUES (2, 'MAT_T02', '测试实木地板', 101, '元/m²', 500, 100, 1.10, 'B1')
    """)

    conn.execute("INSERT INTO projects (id, code, name, type, area) VALUES (1, 'PRJ_T01', '测试项目', 'residential', 100)")

    # pm1:覆盖 unit_cost=300, quantity=50
    # pm2:不覆盖 unit_cost=0,  quantity=30
    conn.execute("""
        INSERT INTO project_materials (project_id, material_id, quantity, location, unit_cost)
        VALUES (1, 1, 50, '客厅', 300)
    """)
    conn.execute("""
        INSERT INTO project_materials (project_id, material_id, quantity, location, unit_cost)
        VALUES (1, 2, 30, '卧室', 0)
    """)
    conn.commit()
    conn.close()
    return db_path


def _assert_equal(actual, expect: float, label: str, tol: float = 0.01):
    ok = abs(actual - expect) < tol
    flag = '✅' if ok else '❌'
    print(f'{flag} {label:50s} actual={actual:>12.2f}  expect={expect:>12.2f}')
    assert ok, f'{label}: actual={actual}, expect={expect}'


def main():
    db_path = _build_test_db()
    print(f'临时 DB: {db_path}')

    # 覆写 server.config.DB_PATH,让 get_db 走到临时库
    from server import config
    original_db_path = config.DB_PATH
    config.DB_PATH = Path(db_path)

    try:
        from server import create_app
        app = create_app()
        client = app.test_client()
    finally:
        # create_app 里 pdf_pool.init_pool() 会真实拉起,需要 tearDown
        pass

    print()
    print('=== 1) helper 自身单测 ===')
    from server.handlers.projects import _effective_unit_cost
    h1 = _effective_unit_cost({'unit_cost': 300}, {'unit_price': 200, 'labor_cost': 80})
    _assert_equal(h1, 300.0, 'override 走 pm.unit_cost')
    h2 = _effective_unit_cost({'unit_cost': 0},   {'unit_price': 200, 'labor_cost': 80})
    _assert_equal(h2, 280.0, 'unit_cost=0 回退 m.unit_price+labor_cost')
    h3 = _effective_unit_cost({'unit_cost': None}, {'unit_price': 500, 'labor_cost': 100})
    _assert_equal(h3, 600.0, 'unit_cost=None 回退 m.unit_price+labor_cost')
    h4 = _effective_unit_cost({'unit_cost': 300}, {'unit_price': 500, 'labor_cost': 100})
    _assert_equal(h4, 300.0, '覆盖优先:即使 m 更贵也用 300')

    print()
    print('=== 2) 三端点 total 一致 ===')
    # 期望 total:
    #   pm1: 300 * 50 * 1.05 = 15750
    #   pm2: (500+100) * 30 * 1.10 = 19800
    #   sum: 35550
    expect_total = 35550.0

    # detail()
    r1 = client.get('/api/projects/1')
    assert r1.status_code == 200, f'detail status={r1.status_code}'
    d1 = r1.get_json()
    _assert_equal(d1['total_cost'], expect_total, 'GET /api/projects/<id> total_cost')

    # cost-summary()
    r2 = client.get('/api/projects/1/cost-summary')
    assert r2.status_code == 200, f'cost-summary status={r2.status_code}'
    d2 = r2.get_json()
    _assert_equal(d2['grand_total'], expect_total, 'GET /api/projects/<id>/cost-summary grand_total')

    # export_docx()
    r3 = client.get('/api/projects/1/export/docx')
    assert r3.status_code == 200, f'export_docx status={r3.status_code}'
    d3 = r3.get_json()
    _assert_equal(d3['total_cost'], expect_total, 'GET /api/projects/<id>/export/docx total_cost')

    print()
    print('=== 3) export_docx 旧 KeyError 已修 ===')
    # 旧 bug:r['loss_factor'] 在 pm.* 不存在,SQL 又没 select m.loss_factor → KeyError
    # 现已 SQL 补 m.loss_factor,断言每条材料都有 subtotal 字段
    for m in d3['materials']:
        assert 'subtotal' in m, f'export_docx 材料缺 subtotal: {m}'
        assert isinstance(m['subtotal'], (int, float)), f'subtotal 非数值: {m}'

    print()
    print('=== 4) cost-summary 按 (category, unit) 聚合 ===')
    items = d2['items']
    # 期望 2 组:(墙面, 元/m²) = 15750;(地面, 元/m²) = 19800
    by_cat = {it['category_name']: it['total'] for it in items}
    _assert_equal(by_cat.get('墙面', 0), 15750.0, 'category 墙面 total = 300*50*1.05')
    _assert_equal(by_cat.get('地面', 0), 19800.0, 'category 地面 total = 600*30*1.10')

    # 恢复原始 DB_PATH
    config.DB_PATH = original_db_path
    Path(db_path).unlink(missing_ok=True)

    print()
    print('-' * 60)
    print('✅ 全部造价口径一致性断言通过')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except AssertionError as e:
        print(f'\n❌ 测试失败: {e}')
        sys.exit(1)
