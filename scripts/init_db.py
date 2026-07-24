#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MaterialWeb v1.0 · 初始化数据库 + 种子数据
运行:python scripts/init_db.py
适用:首次部署 / 清空 DB 后重建 / 增量补 language + references

v1.1 增量更新:
  - 加 material_language / language_notes 列(try/except 兼容已存在 DB)
  - 加 material_references 表 + 6 条 demo
  - 18 种主流材料 language 种子
"""
import os
import sys
import sqlite3
import json
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent  # 项目根
DB_PATH  = BASE_DIR / 'db' / 'materials.db'
SCHEMA   = BASE_DIR / 'db' / 'init_schema.sql'


# ============================================================
# Language 词库(统一词表,所有材料用同一组词便于组合搜索)
# ============================================================
LANG_VOCAB = [
    # 时间感
    '现代', '后现代', '当代', '古朴', '古典', '未来',
    # 性格
    '冷峻', '温润', '厚重', '轻盈', '沉稳', '灵动',
    # 质感
    '精致', '粗野', '光滑', '肌理', '哑光', '镜面', '磨砂',
    # 气质
    '工业', '自然', '极简', '奢华', '通透',
    # 温度
    '温暖', '冰冷',
    # 风格
    '高技派', '极简主义', '新中式', '工业风', '侘寂',
    # 空间感
    '曲面', '直线', '永恒', '时光',
]


# ============================================================
# 18 种主流材料的空间语言(建筑师视角的"用上去什么感觉")
# ============================================================
MATERIAL_LANGUAGE = {
    'STONE_001': {  # 花岗岩
        'tags': ['厚重', '沉稳', '永恒', '自然'],
        'notes': '天然颗粒肌理,色彩沉稳,大尺度幕墙/基座首选',
    },
    'STONE_002': {  # 大理石
        'tags': ['奢华', '精致', '古典', '温润'],
        'notes': '纹理温润,光泽优雅,适合大堂/室内/高端住宅',
    },
    'GRC_001': {  # GRC 板
        'tags': ['精致', '现代', '曲面', '高技派', '肌理'],
        'notes': '轻质高强可异形,曲面/肌理立面表现力强,商业综合体常用',
    },
    'UHPC_001': {  # UHPC
        'tags': ['极致', '现代', '冷峻', '精密', '高技派', '轻盈'],
        'notes': '极致强度+极薄尺寸,适合地标性建筑/参数化立面/桥梁',
    },
    'GLASS_001': {  # Low-E 中空
        'tags': ['通透', '现代', '冷峻', '轻盈', '极简'],
        'notes': '高透光低辐射,塔楼/办公/商业幕墙主流',
    },
    'GLASS_002': {  # 夹层玻璃
        'tags': ['通透', '现代', '精致', '安全'],
        'notes': '安全+透明,采光顶/雨棚/楼梯栏板常用',
    },
    'CONCRETE_001': {  # 清水混凝土
        'tags': ['极简', '工业', '冷峻', '粗野', '现代', '侘寂'],
        'notes': '一次浇筑成型,模板即装饰,粗野/极简风地标',
    },
    'METAL_001': {  # 铝单板
        'tags': ['现代', '工业', '冷峻', '轻盈', '极简'],
        'notes': '轻量可塑,氟碳喷涂,商业塔楼/综合体幕墙主力',
    },
    'METAL_002': {  # 锌板
        'tags': ['冷峻', '精密', '现代', '高技派', '时光'],
        'notes': '自修复氧化层,岁月包浆,博物馆/精品建筑',
    },
    'METAL_003': {  # 铜板
        'tags': ['古朴', '温润', '时光', '工业', '厚重'],
        'notes': '从亮铜渐变到铜绿,时光感极强,文化建筑/高端',
    },
    'METAL_004': {  # 锈蚀钢板
        'tags': ['工业', '古朴', '粗野', '厚重', '冷峻'],
        'notes': '耐候钢锈层稳定,工业风/粗野风,景观/办公外立面',
    },
    'CERAMIC_001': {  # 陶板
        'tags': ['温润', '自然', '现代', '工业', '肌理'],
        'notes': '陶土烧结,色彩温润耐久,办公/住宅外墙',
    },
    'FLEX_001': {  # 软瓷片
        'tags': ['温润', '现代', '轻盈', '经济', '肌理'],
        'notes': '柔性饰面,旧改/经济型项目常用,仿石材/木/砖',
    },
    'WOOD_001': {  # 外墙木饰面
        'tags': ['温润', '自然', '古朴', '休闲', '温暖'],
        'notes': '度假/低层/商业街,需注意防腐/防火',
    },
    'INT_001': {  # 实木地板
        'tags': ['温润', '自然', '古朴', '精致', '温暖'],
        'notes': '室内地面,触感温润,显高级感',
    },
    'INT_002': {  # 岩板
        'tags': ['精致', '现代', '极简', '光滑', '镜面'],
        'notes': '大尺寸薄板,室内墙面/台面/地面,极简风',
    },
    'PAINT_001': {  # 外墙真石漆
        'tags': ['自然', '粗野', '经济', '温暖'],
        'notes': '仿石效果,经济型外墙,住宅/旧改常用',
    },
    'PAINT_002': {  # 外墙氟碳涂料
        'tags': ['现代', '精致', '轻盈', '极简'],
        'notes': '金属感/纯色,高端商业/办公外墙',
    },
}


# ============================================================
# 6 条真实工程参考 demo(每条字段齐全,图占位待补)
# ============================================================
MATERIAL_REFERENCES = [
    {
        'code': 'CONCRETE_001', 'project_name': '鹿野苑石刻博物馆', 'designer': '刘家琨',
        'city': '成都', 'year': 2002, 'part': '外墙/屋面',
        'comment': '粗野主义代表作,模板即装饰,一次浇筑成型,缝隙即韵律',
    },
    {
        'code': 'CONCRETE_001', 'project_name': 'Tadao Ando 住吉的长屋', 'designer': '安藤忠雄',
        'city': '大阪', 'year': 1976, 'part': '外墙/室内',
        'comment': '极简+侘寂,光在清水混凝土上的诗意',
    },
    {
        'code': 'GRC_001', 'project_name': '上海当代艺术博物馆', 'designer': '原作设计',
        'city': '上海', 'year': 2012, 'part': '外墙',
        'comment': '南市电厂改造,粗大烟囱与 GRC 板对比,工业记忆',
    },
    {
        'code': 'UHPC_001', 'project_name': '法国 Fondation Louis Vuitton', 'designer': 'Frank Gehry',
        'city': '巴黎', 'year': 2014, 'part': '幕墙曲面',
        'comment': 'UHPC 弧形板实现风帆造型,曲面精度毫米级',
    },
    {
        'code': 'STONE_001', 'project_name': '中国国家大剧院', 'designer': '保罗·安德鲁',
        'city': '北京', 'year': 2007, 'part': '外壳/幕墙',
        'comment': '钛金属 + 花岗岩基座,沉稳与现代对话',
    },
    {
        'code': 'GLASS_001', 'project_name': 'CCTV 大楼', 'designer': 'Rem Koolhaas / OMA',
        'city': '北京', 'year': 2012, 'part': '幕墙',
        'comment': 'Low-E 玻璃 + 不规则网格,极高难度幕墙工程',
    },
    {
        'code': 'METAL_001', 'project_name': '北京大兴机场', 'designer': '扎哈·哈迪德',
        'city': '北京', 'year': 2019, 'part': '屋面/幕墙',
        'comment': '铝单板 + 自由曲面,参数化设计落地典范',
    },
    {
        'code': 'METAL_003', 'project_name': '哥本哈根证券交易所', 'designer': '修复/3XN',
        'city': '哥本哈根', 'year': 2024, 'part': '屋面',
        'comment': '铜板 + 屋面曲线,200 年铜绿文化重塑',
    },
]


# ============================================================
# DB 初始化
# ============================================================
def init_db():
    """建表(读 init_schema.sql)"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.executescript(open(SCHEMA, encoding='utf-8').read())
    conn.commit()
    print(f'[ok] 表结构已就绪: {DB_PATH}')
    return conn


def add_columns_if_missing(conn):
    """增量加列(对已存在 DB 兼容)"""
    targets = [
        ('materials', 'material_language', "TEXT DEFAULT '[]'"),
        ('materials', 'language_notes',    "TEXT DEFAULT NULL"),
    ]
    for table, col, decl in targets:
        # 查已有列
        cur = conn.execute(f"PRAGMA table_info({table})")
        existing = {row['name'] for row in cur.fetchall()}
        if col in existing:
            continue
        try:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {decl}")
            print(f'  [ok] 加列 {table}.{col}')
        except sqlite3.OperationalError as e:
            print(f'  [!] 加列 {table}.{col} 失败: {e}')
    conn.commit()


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
        ex = conn.execute('SELECT 1 FROM materials WHERE code = ?', [m['code']]).fetchone()
        if ex: continue
        cols = ', '.join(m.keys())
        placeholders = ', '.join(['?'] * len(m))
        conn.execute(
            f'INSERT INTO materials ({cols}) VALUES ({placeholders})',
            list(m.values())
        )
    conn.commit()
    print(f'[ok] 灌入 {len(rows)} 条示例材料')


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
    print(f'[ok] 灌入 {len(rows)} 条示例供应商')


def seed_material_language(conn):
    """灌材料空间语言 tags"""
    count = 0
    for code, data in MATERIAL_LANGUAGE.items():
        ex = conn.execute('SELECT id FROM materials WHERE code = ?', [code]).fetchone()
        if not ex: continue
        mid = ex['id']
        tags_json = json.dumps(data['tags'], ensure_ascii=False)
        conn.execute(
            'UPDATE materials SET material_language = ?, language_notes = ? WHERE id = ?',
            [tags_json, data['notes'], mid]
        )
        count += 1
    conn.commit()
    print(f'[ok] 灌入 {count} 种材料的 language 标签')


def seed_material_references(conn):
    """灌真实工程参考 demo"""
    count = 0
    for ref in MATERIAL_REFERENCES:
        ex = conn.execute('SELECT id FROM materials WHERE code = ?', [ref['code']]).fetchone()
        if not ex:
            print(f'  [!] 找不到材料 {ref["code"]},跳过参考 {ref["project_name"]}')
            continue
        mid = ex['id']
        # 防重复
        dup = conn.execute(
            'SELECT 1 FROM material_references WHERE material_id = ? AND project_name = ?',
            [mid, ref['project_name']]
        ).fetchone()
        if dup: continue
        conn.execute(
            '''INSERT INTO material_references
               (material_id, project_name, designer, city, year, part, comment, sort_order)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            [mid, ref['project_name'], ref.get('designer'), ref.get('city'),
             ref.get('year'), ref.get('part'), ref.get('comment'), count]
        )
        count += 1
    conn.commit()
    print(f'[ok] 灌入 {count} 条真实工程参考 demo')


def main():
    # 兼容 Windows GBK PowerShell:让 print 走 UTF-8
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    print(f'DB:     {DB_PATH}')
    print(f'SCHEMA: {SCHEMA}')
    if not SCHEMA.exists():
        print(f'[ERR] 找不到 schema: {SCHEMA}')
        sys.exit(1)
    conn = init_db()
    add_columns_if_missing(conn)
    seed_suppliers(conn)
    seed_materials(conn)
    seed_material_language(conn)
    seed_material_references(conn)
    conn.close()
    print('[done]')


if __name__ == '__main__':
    main()
