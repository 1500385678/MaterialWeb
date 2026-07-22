#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MaterialWeb v1.0 · 初始化数据库 + 种子数据
运行:python scripts/init_db.py
适用:首次部署 / 清空 DB 后重建
"""
import os
import sys
import sqlite3
import json
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent  # MaterialWeb-v1.0 根
DB_PATH  = BASE_DIR / 'db' / 'materials.db'
SCHEMA   = BASE_DIR / 'db' / 'init_schema.sql'


def init_db():
    """建表(读 init_schema.sql)"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.executescript(open(SCHEMA, encoding='utf-8').read())
    conn.commit()
    print(f"✓ 表结构已就绪: {DB_PATH}")
    return conn


def seed_materials(conn):
    """灌种子数据(示例,可后续更新)"""
    cats = {}
    for r in conn.execute('SELECT id, code FROM categories').fetchall():
        cats[r['code']] = r['id']

    rows = [
        # 花岗岩
        {
            'code': 'STONE_001', 'name_cn': '花岗岩', 'name_en': 'Granite',
            'category_id': cats.get('stone.granite'),
            'sub_category': '天然石材',
            'density': '2500~2800 kg/m³', 'strength': '抗压 100~250MPa',
            'thermal_cond': '2.0~3.5 W/(m·K)', 'water_absorp': '≤0.5%',
            'fire_rating': 'A1', 'fire_note': '不燃材料,达最高防火等级',
            'env_grade': '天然材料,无甲醛释放', 'std_code': 'GB/T 18601',
            'eco_cert': '绿色建材',
            'unit_price': 300, 'labor_cost': 200, 'loss_factor': 1.08,
            'cost_tier': '中', 'unit': '元/m²',
            'texture': '光面~细荔枝', 'color_series': '灰/白/黑/红/麻系',
            'specs': '600×600 / 800×800,厚 25~30mm(干挂)',
            'patterns': '光面/火烧面/荔枝面/天然面',
            'visual_desc': '天然石材纹理不重复,颗粒感强,适合庄重和高档项目',
            'structure_notes': '高层建议干挂;钢托+铝合金挂件;留 6~8mm 缝,做防水密封',
            'durability': '优', 'lifespan_years': '50~100年', 'maintenance': '5~10年一次防护处理',
            'applications_json': json.dumps(['商业幕墙', '高档住宅', '公共建筑', '室内地面'], ensure_ascii=False),
            'suppliers_json': json.dumps([1]),
            'exam_weight': 0.15,
            'remark': '参考:facade-materials-catalog.md 第 1 章',
        },
        # GRC
        {
            'code': 'GRC_001', 'name_cn': 'GRC 板', 'name_en': 'Glassfiber Reinforced Concrete',
            'category_id': cats.get('finishing.concrete'),
            'sub_category': '装饰混凝土',
            'density': '1800~2000 kg/m³', 'strength': '抗弯 8~15MPa',
            'thermal_cond': '0.5~1.0 W/(m·K)', 'water_absorp': '≤5%',
            'fire_rating': 'A1',
            'unit_price': 380, 'labor_cost': 150, 'loss_factor': 1.05,
            'cost_tier': '中', 'unit': '元/m²',
            'texture': '光面/肌理', 'color_series': '白/灰/彩',
            'specs': '厚度 8~15mm,大板可达 2×4m',
            'visual_desc': '轻质高强,可做复杂肌理,适合异形立面',
            'structure_notes': '背附钢龙骨,预留伸缩缝',
            'durability': '良', 'lifespan_years': '30~50年',
            'applications_json': json.dumps(['异形幕墙', '商业综合体', '文化建筑'], ensure_ascii=False),
            'exam_weight': 0.08,
        },
        # UHPC
        {
            'code': 'UHPC_001', 'name_cn': 'UHPC 超高性能混凝土', 'name_en': 'Ultra-High Performance Concrete',
            'category_id': cats.get('concrete.hpc'),
            'sub_category': '高性能混凝土',
            'density': '2400~2600 kg/m³', 'strength': '抗压 150~250MPa',
            'fire_rating': 'A1',
            'unit_price': 2500, 'labor_cost': 400, 'loss_factor': 1.05,
            'cost_tier': '高', 'unit': '元/m²',
            'texture': '光面/肌理', 'color_series': '白/灰/彩',
            'specs': '厚度 15~50mm',
            'visual_desc': '极致强度与极薄尺寸,适合地标性建筑',
            'structure_notes': '工厂预制,现场吊装',
            'durability': '优', 'lifespan_years': '100年以上',
            'applications_json': json.dumps(['地标幕墙', '桥梁', '公共空间'], ensure_ascii=False),
            'exam_weight': 0.10,
        },
        # Low-E 玻璃
        {
            'code': 'GLASS_001', 'name_cn': 'Low-E 中空玻璃', 'name_en': 'Low-E Insulating Glass',
            'category_id': cats.get('glass.low_e'),
            'sub_category': '节能玻璃',
            'density': '2500~2700 kg/m³', 'strength': '抗风压依厚度',
            'thermal_cond': '1.6~2.0 W/(m²·K)', 'fire_rating': 'A1',
            'unit_price': 480, 'labor_cost': 120, 'loss_factor': 1.03,
            'cost_tier': '中', 'unit': '元/m²',
            'texture': '透明', 'color_series': '蓝/灰/金',
            'specs': '6+12A+6 / 8+12A+8,常见厚度 24~32mm',
            'visual_desc': '高透光低辐射,节能指标强',
            'structure_notes': '铝合金幕墙系统,中空充氩气',
            'durability': '优', 'lifespan_years': '20~25年',
            'applications_json': json.dumps(['办公塔楼', '商业综合体', '住宅'], ensure_ascii=False),
            'exam_weight': 0.18,
        },
    ]

    for m in rows:
        # 已有就跳过
        ex = conn.execute('SELECT 1 FROM materials WHERE code = ?', [m['code']]).fetchone()
        if ex: continue
        cols = ', '.join(m.keys())
        placeholders = ', '.join(['?'] * len(m))
        conn.execute(
            f'INSERT INTO materials ({cols}) VALUES ({placeholders})',
            list(m.values())
        )
    conn.commit()
    print(f"✓ 灌入 {len(rows)} 条示例材料")


def seed_suppliers(conn):
    rows = [
        {
            'name': '环球石材', 'name_en': 'Universal Stone',
            'type': '国产头部', 'products': '花岗岩,大理石,砂岩',
            'price_level': '高', 'features': '品类全,工程经验多',
            'applicable': '商业,公共建筑', 'origin': '中国', 'website': 'https://www.universal-stone.com',
        },
        {
            'name': '康利石材', 'name_en': 'Kangli Stone',
            'type': '国产头部', 'products': '大理石,花岗岩',
            'price_level': '高', 'features': '高端项目经验',
            'applicable': '高端住宅,酒店', 'origin': '中国',
        },
        {
            'name': '意大利 Salvatori',
            'type': '进口品牌', 'products': '大理石,装饰石材',
            'price_level': '高', 'features': '设计与品质',
            'applicable': '豪宅,精品酒店', 'origin': '意大利',
            'china_channel': '北京/上海展厅',
        },
    ]
    for s in rows:
        ex = conn.execute('SELECT 1 FROM suppliers WHERE name = ?', [s['name']]).fetchone()
        if ex: continue
        cols = ', '.join(s.keys())
        placeholders = ', '.join(['?'] * len(s))
        conn.execute(
            f'INSERT INTO suppliers ({cols}) VALUES ({placeholders})',
            list(s.values())
        )
    conn.commit()
    print(f"✓ 灌入 {len(rows)} 条示例供应商")


def main():
    print(f"DB:   {DB_PATH}")
    print(f"SCHEMA: {SCHEMA}")
    if not SCHEMA.exists():
        print(f"❌ 找不到 schema: {SCHEMA}")
        sys.exit(1)
    conn = init_db()
    seed_suppliers(conn)
    seed_materials(conn)
    conn.close()
    print(f"✅ 完成")


if __name__ == '__main__':
    main()
