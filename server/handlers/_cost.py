"""server.handlers._cost · 项目造价公式共享模块

MaterialWeb v1.1 · 从原 server/handlers/projects.py(239 行,临界铁律#1 250 行)拆出
夜间迭代批 2 (01:00) 改 · P1 Verifier row 16

导出 3 个函数,被 3 个端点共享:
  - detail()           · GET  /api/projects/<id>
  - cost_summary()     · GET  /api/projects/<id>/cost-summary
  - export_docx()      · GET  /api/projects/<id>/export/docx

统一口径(2026-08-13 R328 闭环):
  pm.unit_cost 优先,NULL/0 时回退 m.unit_price + m.labor_cost
"""
from __future__ import annotations


def effective_unit_cost(pm, m) -> float:
    """统一造价公式 · pm.unit_cost 优先,NULL/0 时回退 m.unit_price + m.labor_cost

    参数 pm/m 都是 sqlite3.Row 或 dict,字段要求:
      pm.unit_cost       — 用户覆盖单价(可空,0 也视作未设)
      m.unit_price       — 材料库原始单价
      m.labor_cost       — 材料库原始施工费

    返回 float(>= 0)
    """
    try:
        pm_cost = float(pm['unit_cost']) if pm['unit_cost'] is not None else 0.0
    except (KeyError, TypeError, ValueError):
        pm_cost = 0.0
    if pm_cost > 0:
        return pm_cost
    try:
        up = float(m['unit_price']) if m['unit_price'] is not None else 0.0
    except (KeyError, TypeError, ValueError):
        up = 0.0
    try:
        lc = float(m['labor_cost']) if m['labor_cost'] is not None else 0.0
    except (KeyError, TypeError, ValueError):
        lc = 0.0
    return up + lc


def safe_float(v, default: float = 0.0) -> float:
    """Row/dict 字段 → float,空/None/非法都返 default"""
    if v is None:
        return default
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def line_subtotal(pm, m) -> float:
    """单行造价小计 = effective_unit_cost × quantity × loss_factor

    pm 必须是 sqlite3.Row 或 dict,字段要求:
      pm.unit_cost / pm.quantity / pm.loss_factor(项目材料行)
      m.unit_price / m.labor_cost(材料库,回退用)
    """
    return (
        effective_unit_cost(pm, m)
        * safe_float(pm['quantity'], 0.0)
        * safe_float(pm['loss_factor'], 1.0)
    )
