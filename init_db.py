#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化数据库并填充种子数据
运行: python init_db.py
"""

import os
import sqlite3
import json
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent
DB_PATH  = BASE_DIR / 'materials.db'
SCHEMA   = BASE_DIR / 'init_schema.sql'

def init_db():
    """初始化数据库表结构"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.executescript(open(SCHEMA, encoding='utf-8').read())
    conn.commit()
    print(f"✅ 表结构创建完成: {DB_PATH}")
    return conn

def seed_materials(conn):
    """填充材料种子数据（示例数据，可后续更新）"""

    # 先获取分类 ID
    cats = {}
    rows = conn.execute('SELECT id, code FROM categories').fetchall()
    for r in rows:
        cats[r['code']] = r['id']

    materials = [
        # ── 石材 ──
        {
            'code': 'STONE_001', 'name_cn': '花岗岩', 'name_en': 'Granite',
            'category_id': cats.get('stone.granite'),
            'sub_category': '天然石材',
            'density': '2500~2800 kg/m³', 'strength': '抗压 100~250MPa',
            'thermal_cond': '2.0~3.5 W/(m·K)', 'water_absorp': '≤0.5%',
            'fire_rating': 'A1', 'fire_note': '不燃材料，防火等级最高',
            'env_grade': '天然材料，无甲醛释放', 'std_code': 'GB/T 18601',
            'eco_cert': '绿色建材',
            'unit_price': 300, 'labor_cost': 200, 'loss_factor': 1.08,
            'cost_tier': '中', 'unit': '元/m²',
            'texture': '粗粝~细腻可选', 'color_series': '灰/白/黑/红/绿系',
            'specs': '600×600 / 800×800，厚25~30mm（干挂）',
            'patterns': '光面/火烧面/荔枝面/自然劈裂面',
            'visual_desc': '天然石材纹理不可复制，光面产生高级反射，适合庄重恒久感项目',
            'structure_notes': '高层必须干挂：钢龙骨+铝合金挂件，缝宽6~8mm；低层可湿贴',
            'durability': '优', 'lifespan_years': '50~100年', 'maintenance': '5~10年做一次防护处理',
            'applications_json': json.dumps(['商业幕墙', '高端住宅', '公共建筑', '景观地面']),
            'suppliers_json': json.dumps([1]),
            'exam_weight': 0.15, 'exam_points': json.dumps(['Q235用于一般结构', 'Q345/Q390用于重要结构']),
            'exam_cases': '上海中心（低辐射镀膜玻璃）',
            'remark': '参考: facade-materials-catalog.md 第1节',
        },
        {
            'code': 'STONE_002', 'name_cn': '大理石', 'name_en': 'Marble',
            'category_id': cats.get('stone.marble'),
            'sub_category': '天然石材',
            'density': '2600~2700 kg/m³', 'strength': '抗压 50~150MPa',
            'thermal_cond': '2.5~3.2 W/(m·K)', 'water_absorp': '≤0.5%',
            'fire_rating': 'A1',
            'env_grade': '天然材料', 'std_code': 'GB/T 19766',
            'unit_price': 600, 'labor_cost': 250, 'loss_factor': 1.1,
            'cost_tier': '高', 'unit': '元/m²',
            'texture': '温润光泽，天然纹理', 'color_series': '白/灰/米/黑系带纹理',
            'specs': '600×600~800×800，厚20~25mm',
            'patterns': '光面（抛光）为主',
            'visual_desc': '纹理丰富有层次，适合高端室内地面和墙裙',
            'structure_notes': '地面需做六面防护，幕墙必须干挂',
            'durability': '良', 'lifespan_years': '30~50年', 'maintenance': '注意酸雨区变色',
            'applications_json': json.dumps(['酒店大堂', '高端住宅', '室内墙地面']),
            'suppliers_json': json.dumps([2]),
            'exam_weight': 0.1,
            'remark': '硬度低于花岗岩，不适合高频地面',
        },
        # ── 金属板 ──
        {
            'code': 'METAL_001', 'name_cn': '铝单板', 'name_en': 'Aluminum Panel',
            'category_id': cats.get('metal.aluminum'),
            'sub_category': '铝合金',
            'density': '2700 kg/m³', 'strength': '抗拉 ≥130MPa',
            'thermal_cond': '237 W/(m·K)', 'water_absorp': '0%',
            'fire_rating': 'A1',
            'env_grade': '可回收，回收率>90%', 'std_code': 'GB/T 23443',
            'eco_cert': '绿色建材',
            'unit_price': 250, 'labor_cost': 180, 'loss_factor': 1.05,
            'cost_tier': '中', 'unit': '元/m²',
            'texture': '平整光洁', 'color_series': '任意RAL色+仿木纹/仿石纹',
            'specs': '1200×2400~1500×4000mm，厚2.0~3.0mm',
            'patterns': '粉末喷涂/氟碳喷涂/穿孔板/波纹板/拉丝面',
            'visual_desc': '现代建筑最灵活的表皮语言，穿孔铝板制造虚实渐变',
            'structure_notes': '铝合金龙骨+角码挂接，缝宽12~20mm开缝式',
            'durability': '优', 'lifespan_years': '25~40年', 'maintenance': '5~8年清洗一次',
            'applications_json': json.dumps(['商业幕墙', '办公建筑', '室内吊顶']),
            'suppliers_json': json.dumps([3]),
            'exam_weight': 0.12,
            'exam_points': json.dumps(['Low-E玻璃U值可至1.0 W/m²K', '氟碳喷涂耐候最佳']),
            'remark': '参考: facade-materials-catalog.md 第2节',
        },
        {
            'code': 'METAL_002', 'name_cn': '锌板', 'name_en': 'Zinc Sheet',
            'category_id': cats.get('metal.copper'),
            'sub_category': '铜/钛/锌',
            'density': '7100 kg/m³', 'strength': '抗拉 ≥150MPa',
            'thermal_cond': '116 W/(m·K)', 'water_absorp': '0%',
            'fire_rating': 'A1',
            'env_grade': '可回收，自修复氧化层', 'std_code': '',
            'unit_price': 600, 'labor_cost': 350, 'loss_factor': 1.05,
            'cost_tier': '高', 'unit': '元/m²',
            'texture': '银灰→深灰渐变', 'color_series': '银色系，随时间氧化加深',
            'specs': '卷材宽1000~1200mm，厚0.7~1.2mm',
            'patterns': '咬合式/立边咬合',
            'visual_desc': '赋予建筑时间沉淀感，随氧化过程产生独特的深浅变化',
            'structure_notes': '咬合式系统，雨水自排，最小坡度5°',
            'durability': '优', 'lifespan_years': '50~100年', 'maintenance': '基本免维护',
            'applications_json': json.dumps(['文化建筑', '高端住宅', '旧改项目']),
            'suppliers_json': json.dumps([4]),
            'exam_weight': 0.05,
            'remark': '进口品牌为主，交期长',
        },
        {
            'code': 'METAL_003', 'name_cn': '铜板', 'name_en': 'Copper Sheet',
            'category_id': cats.get('metal.copper'),
            'sub_category': '铜/钛/锌',
            'density': '8900 kg/m³', 'strength': '高',
            'thermal_cond': '401 W/(m·K)', 'water_absorp': '0%',
            'fire_rating': 'A1',
            'env_grade': '可回收，铜绿保护层', 'std_code': '',
            'unit_price': 900, 'labor_cost': 400, 'loss_factor': 1.05,
            'cost_tier': '高', 'unit': '元/m²',
            'texture': '金→棕→绿锈渐变', 'color_series': '铜金色→棕褐→铜绿',
            'specs': '卷材，厚度0.5~1.5mm',
            'visual_desc': '铜绿让建筑呈现独特的艺术气质，常用于地标建筑局部点缀',
            'structure_notes': '需做龙骨系统，端头密封处理',
            'durability': '优', 'lifespan_years': '80~100年', 'maintenance': '基本免维护',
            'applications_json': json.dumps(['地标建筑', '文化建筑', '雕塑/装饰']),
            'suppliers_json': json.dumps([4]),
            'exam_weight': 0.03,
        },
        {
            'code': 'METAL_004', 'name_cn': '锈蚀钢板', 'name_en': 'Weathering Steel',
            'category_id': cats.get('metal.steel'),
            'sub_category': '建筑钢材',
            'density': '7850 kg/m³', 'strength': '高强',
            'thermal_cond': '50 W/(m·K)', 'water_absorp': '0%',
            'fire_rating': 'A1',
            'env_grade': '可回收', 'std_code': '',
            'unit_price': 350, 'labor_cost': 200, 'loss_factor': 1.05,
            'cost_tier': '中', 'unit': '元/m²',
            'texture': '锈红/锈棕，粗粝', 'color_series': '锈红/棕褐色系',
            'specs': '按项目定制，厚度3~20mm',
            'patterns': '自然锈蚀/稳定化处理',
            'visual_desc': '用"不完美"制造视觉张力，工业风/粗野主义代表材料',
            'structure_notes': '需稳定化处理防止过渡锈蚀，与龙骨绝缘处理',
            'durability': '一般', 'lifespan_years': '30~50年', 'maintenance': '稳定化处理后基本免维护',
            'applications_json': json.dumps(['工业风建筑', '旧厂改造', '景观小品']),
            'suppliers_json': json.dumps([5]),
            'exam_weight': 0.08,
            'exam_cases': '鸟巢（Q460钢）',
        },
        # ── 陶板 ──
        {
            'code': 'CERAMIC_001', 'name_cn': '陶板', 'name_en': 'Terracotta Panel',
            'category_id': cats.get('stone.artificial'),
            'sub_category': '陶板',
            'density': '1900~2200 kg/m³', 'strength': '抗折 ≥14MPa',
            'thermal_cond': '0.6~1.0 W/(m·K)', 'water_absorp': '3~6%',
            'fire_rating': 'A1',
            'env_grade': '天然黏土烧结，无有害释放', 'std_code': 'GB/T 32981',
            'eco_cert': '绿色建材',
            'unit_price': 350, 'labor_cost': 200, 'loss_factor': 1.05,
            'cost_tier': '中', 'unit': '元/m²',
            'texture': '自然泥土质感，哑光温润', 'color_series': '红陶/灰陶/黄陶/棕陶/白陶（暖色系，约30种）',
            'specs': '300×600~600×1200mm，厚18~30mm',
            'patterns': '自然面（微凹凸）/拉丝面/光滑面/木纹面',
            'visual_desc': '兼具厚重感与精致感，温暖泥土色让建筑有"长在地上"的归属感',
            'structure_notes': '铝合金龙骨+专用挂件，上下搭接开口截面，雨水自排；背腔通风20~40mm',
            'durability': '优', 'lifespan_years': '50年以上', 'maintenance': '基本免维护，2~3年清水冲洗',
            'applications_json': json.dumps(['文化建筑', '高端住宅', '商业幕墙']),
            'suppliers_json': json.dumps([6]),
            'exam_weight': 0.1,
            'exam_points': json.dumps(['陶板为A1防火', '背腔通风构造']),
        },
        # ── 玻璃 ──
        {
            'code': 'GLASS_001', 'name_cn': 'Low-E中空玻璃', 'name_en': 'Low-E Insulating Glass',
            'category_id': cats.get('glass.low_e'),
            'sub_category': 'Low-E中空',
            'density': '2500 kg/m³', 'strength': '钢化抗弯 ≥90MPa',
            'thermal_cond': 'U值 1.1~2.5 W/(m²·K)', 'water_absorp': '0%',
            'fire_rating': 'A1', 'fire_note': '单片6mm防火极限仅30min，防火玻璃可达60~120min',
            'env_grade': '不可降解但可回收', 'std_code': 'GB/T 11944 / JGJ 102',
            'unit_price': 350, 'labor_cost': 300, 'loss_factor': 1.03,
            'cost_tier': '中高', 'unit': '元/m²',
            'texture': '通透/反射/半透明', 'color_series': '超白/白玻/灰/蓝/绿镀膜',
            'specs': '6Low-E+12A+6mm，板面最大约2500×4500mm',
            'patterns': 'Low-E反射/彩釉丝印/磨砂/热弯弧面',
            'visual_desc': 'Low-E镀膜让建筑呈现镜面反射的冷峻气质，是现代高层幕墙标配',
            'structure_notes': '明框/隐框/点式幕墙；中空需充氩气防结露；结构胶需定期检测',
            'durability': '优', 'lifespan_years': '25~40年', 'maintenance': '半年~1年清洗，结构胶10年检测',
            'applications_json': json.dumps(['幕墙', '门窗', '采光顶']),
            'suppliers_json': json.dumps([7]),
            'exam_weight': 0.2,
            'exam_points': json.dumps(['Low-E中空U值可至1.0 W/m²K', '中空玻璃充氩气', '结构胶寿命约25年']),
            'exam_cases': '上海中心（低辐射镀膜玻璃）',
        },
        {
            'code': 'GLASS_002', 'name_cn': '夹层玻璃', 'name_en': 'Laminated Glass',
            'category_id': cats.get('glass.laminated'),
            'sub_category': '夹层玻璃',
            'density': '2500 kg/m³', 'strength': '优于同厚度钢化玻璃',
            'thermal_cond': '与中空组合后 1.1~2.0 W/(m²·K)', 'water_absorp': '0%',
            'fire_rating': 'A1',
            'env_grade': '可回收', 'std_code': 'GB 15763.3',
            'unit_price': 450, 'labor_cost': 300, 'loss_factor': 1.03,
            'cost_tier': '中高', 'unit': '元/m²',
            'texture': '通透', 'color_series': '白玻/超白/彩色PVB',
            'specs': '6+1.52PVB+6mm（标准），可定制',
            'patterns': '透明/彩釉/磨砂',
            'visual_desc': 'PVB夹层提供安全性，破碎时碎片不脱落，常用于玻璃栏河和天窗',
            'structure_notes': '需用结构胶或机械夹具固定',
            'durability': '优', 'lifespan_years': '30~50年', 'maintenance': '定期检查密封性',
            'applications_json': json.dumps(['玻璃栏河', '阳光房', '幕墙', '天窗外层']),
            'suppliers_json': json.dumps([7]),
            'exam_weight': 0.08,
            'exam_points': json.dumps(['PVB夹层安全性', '破碎不脱落']),
        },
        # ── 清水混凝土 ──
        {
            'code': 'CONCRETE_001', 'name_cn': '清水混凝土', 'name_en': 'Fair-Face Concrete',
            'category_id': cats.get('concrete.fairface'),
            'sub_category': '清水混凝土',
            'density': '2300~2500 kg/m³', 'strength': 'C30~C50',
            'thermal_cond': '1.5~2.0 W/(m·K)', 'water_absorp': '3~5%（需憎水处理）',
            'fire_rating': 'A1',
            'env_grade': '无有害释放', 'std_code': 'JGJ 169',
            'eco_cert': '绿色建材',
            'unit_price': 0,  # 混凝土本身价格低，贵在模板
            'labor_cost': 0,
            'loss_factor': 1.0,
            'cost_tier': '高', 'unit': '元/m²（综合造价）',
            'remark': '综合造价 1500~3500元/m²（含模板+浇筑+保护剂），不按材料本身计价',
            'texture': '模板天然纹理，素朴禅意', 'color_series': '灰白~深灰，可调色',
            'specs': '无固定规格，由模板决定，常见分格1200×2400~1800×3600mm',
            'patterns': '光面（镜面模板）/木纹（木模板）/竖向条纹/螺栓孔',
            'visual_desc': '用最诚实的材料表达结构之美，安藤忠雄标志性的光滑清水面',
            'structure_notes': '大型钢模板或定制木模板；蝉缝4~6mm/明缝10~15mm；保护剂2~3道；一次浇筑成型不可修补',
            'durability': '良', 'lifespan_years': '50年以上（保护剂5~10年补涂）', 'maintenance': '5~8年检查保护剂',
            'applications_json': json.dumps(['美术馆', '住宅', '办公', '公共建筑']),
            'suppliers_json': json.dumps([]),
            'exam_weight': 0.1,
            'exam_points': json.dumps(['C30是基础标号', 'JGJ 169规范', '保护剂使用']),
            'exam_cases': '安藤忠雄系列项目',
        },
        # ── GRC / UHPC ──
        {
            'code': 'GRC_001', 'name_cn': 'GRC板', 'name_en': 'GFRC Panel',
            'category_id': cats.get('composite'),
            'sub_category': 'GRC',
            'density': '1800~2200 kg/m³', 'strength': '抗折 ≥8MPa',
            'thermal_cond': '0.8~1.5 W/(m·K)', 'water_absorp': '≤10%',
            'fire_rating': 'A1',
            'env_grade': '无有害释放', 'std_code': 'JG/T 564.1',
            'unit_price': 300, 'labor_cost': 200, 'loss_factor': 1.08,
            'cost_tier': '中', 'unit': '元/m²',
            'texture': '可仿石材/仿木纹/自由造型', 'color_series': '灰色系/白色（白水泥基）',
            'specs': '600×1200~1200×2400mm，厚15~25mm',
            'patterns': '光滑面/喷砂面/露骨料面/穿孔/格栅',
            'visual_desc': 'GRC是建筑师的造型自由材料，可仿石材可做弧面异形，轻了70%',
            'structure_notes': '背附钢框+挂件，缝宽8~12mm开缝；可做双曲面造型',
            'durability': '良', 'lifespan_years': '30~50年', 'maintenance': '3~5年检查表面防护',
            'applications_json': json.dumps(['文化建筑', '商业幕墙', '雕塑装饰']),
            'suppliers_json': json.dumps([8]),
            'exam_weight': 0.08,
            'exam_points': json.dumps(['GRC可仿石材', '轻质高强']),
        },
        {
            'code': 'UHPC_001', 'name_cn': 'UHPC板', 'name_en': 'UHPC Panel',
            'category_id': cats.get('composite'),
            'sub_category': 'UHPC',
            'density': '2400~2600 kg/m³', 'strength': '抗压 ≥120MPa，抗折 ≥15MPa',
            'thermal_cond': '~1.5 W/(m·K)', 'water_absorp': '≤2%',
            'fire_rating': 'A1',
            'env_grade': '无有害释放', 'std_code': 'T/CECS 752',
            'eco_cert': '绿色建材',
            'unit_price': 800, 'labor_cost': 350, 'loss_factor': 1.05,
            'cost_tier': '高', 'unit': '元/m²',
            'texture': '高密度细腻质感，可达石材级精致', 'color_series': '灰色系/可调色/可掺骨料',
            'specs': '1200×2400~1500×3000mm，厚12~25mm',
            'patterns': '光滑面/喷砂面/露骨料/超细线条/超薄穿孔',
            'visual_desc': '极致密实让表面如石材般精致，但比石材轻70%；超细线条肋宽可至30mm',
            'structure_notes': '预埋不锈钢连接件；超薄大板（12mm）；超细线条和超薄穿孔',
            'durability': '优', 'lifespan_years': '50~100年', 'maintenance': '基本免维护',
            'applications_json': json.dumps(['地标建筑', '高端幕墙', '桥梁装饰']),
            'suppliers_json': json.dumps([9]),
            'exam_weight': 0.05,
            'exam_points': json.dumps(['UHPC强度远超普通混凝土', '可超薄大板']),
        },
        # ── 木饰面 ──
        {
            'code': 'WOOD_001', 'name_cn': '外墙木饰面', 'name_en': 'Exterior Wood Cladding',
            'category_id': cats.get('wood'),
            'sub_category': '木材',
            'density': '400~700 kg/m³（软木）/ 700~1000 kg/m³（硬木）',
            'strength': '抗弯 30~100MPa（视木种）',
            'thermal_cond': '0.10~0.20 W/(m·K)', 'water_absorp': '12~30%（需防腐涂层）',
            'fire_rating': 'B2', 'fire_note': '外墙木饰面需满足当地消防要求',
            'env_grade': 'FSC认证木材为优选', 'std_code': 'GB 50016（防火）',
            'unit_price': 200, 'labor_cost': 150, 'loss_factor': 1.1,
            'cost_tier': '中', 'unit': '元/m²',
            'texture': '天然木纹温润', 'color_series': '松木（浅黄~金棕）/ 红雪松 / 柚木（深金~深棕）',
            'specs': '木板宽100~150mm，厚18~25mm；木格栅40×40~60×60mm',
            'patterns': '平面上漆/原木清漆/碳化处理/火烧处理',
            'visual_desc': '唯一让建筑看起来有温度的立面材料，随时间自然银化融入环境',
            'structure_notes': '通风雨幕系统（20~30mm空腔）；防腐处理必须（CCA/ACQ）；端头刷防腐漆不可朝上',
            'durability': '一般', 'lifespan_years': '15~30年（防腐软木）/ 30~50年（耐久硬木）',
            'maintenance': '2~3年检查保护漆，5~8年重涂',
            'applications_json': json.dumps(['住宅', '文旅项目', '木格栅立面']),
            'suppliers_json': json.dumps([10]),
            'exam_weight': 0.05,
            'exam_points': json.dumps(['B2防火等级', '必须防腐处理', '通风雨幕构造']),
        },
        # ── 涂料 ──
        {
            'code': 'PAINT_001', 'name_cn': '外墙真石漆', 'name_en': 'Stone Paint',
            'category_id': cats.get('finishing.paint'),
            'sub_category': '涂料',
            'fire_rating': 'B1', 'env_grade': '需符合 GB 24408',
            'std_code': 'JG/T 24 / GB/T 9755',
            'unit_price': 80, 'labor_cost': 50, 'loss_factor': 1.05,
            'cost_tier': '低', 'unit': '元/m²',
            'texture': '仿石材颗粒感', 'color_series': '石材色系（灰/黄/红棕）',
            'specs': '整体涂装，分格尺寸常见600×900~1200×1500mm',
            'patterns': '喷砂颗粒，多层喷涂',
            'visual_desc': '以1/3价格达到石材90%视觉效果，远看几乎乱真',
            'structure_notes': '基层处理（含水率≤10%）；底漆+中涂+面漆三层体系；分格缝8~12mm',
            'durability': '良', 'lifespan_years': '10~15年', 'maintenance': '5~8年局部修补',
            'applications_json': json.dumps(['住宅外墙', '商业裙房', '经济型项目']),
            'suppliers_json': json.dumps([11]),
            'exam_weight': 0.1,
            'exam_points': json.dumps(['防火等级B1', '分格缝防开裂']),
        },
        {
            'code': 'PAINT_002', 'name_cn': '外墙氟碳涂料', 'name_en': 'Fluorocarbon Paint',
            'category_id': cats.get('finishing.paint'),
            'sub_category': '涂料',
            'fire_rating': 'B1', 'env_grade': '低VOC', 'std_code': 'GB/T 9755',
            'unit_price': 250, 'labor_cost': 80, 'loss_factor': 1.03,
            'cost_tier': '中高', 'unit': '元/m²',
            'texture': '平整光滑/哑光', 'color_series': '任意色（标准色卡）',
            'specs': '整体涂装，氟碳面漆耐候最佳',
            'visual_desc': '氟碳涂料15年以上保色，是高端外墙涂料首选',
            'durability': '优', 'lifespan_years': '15~20年', 'maintenance': '基本免维护',
            'applications_json': json.dumps(['高端幕墙铝板面漆', '超高层外墙', '重要公建']),
            'suppliers_json': json.dumps([11]),
            'exam_weight': 0.08,
            'exam_points': json.dumps(['氟碳涂料耐候最佳', '保色15年以上']),
        },
        # ── 室内材料 ──
        {
            'code': 'INT_001', 'name_cn': '实木地板', 'name_en': 'Solid Wood Flooring',
            'category_id': cats.get('wood'),
            'sub_category': '木材-室内',
            'fire_rating': 'B2', 'env_grade': 'E0/E1', 'std_code': 'GB 18580',
            'unit_price': 450, 'labor_cost': 100, 'loss_factor': 1.05,
            'cost_tier': '中高', 'unit': '元/m²',
            'texture': '天然木纹温润', 'color_series': '浅色（白橡）/ 中色（橡木）/ 深色（黑胡桃）',
            'specs': '910×122×18mm（标准条）',
            'patterns': '平面（油漆/UV漆）/ 手刮面 / 拉丝',
            'structure_notes': '木龙骨@300~400mm + 防潮垫 + 地板钉；与瓷砖交接用不锈钢收口条',
            'durability': '优', 'lifespan_years': '30~50年',
            'applications_json': json.dumps(['住宅客厅/卧室', '高端公寓']),
            'suppliers_json': json.dumps([12]),
            'exam_weight': 0.05,
        },
        {
            'code': 'INT_002', 'name_cn': '岩板', 'name_en': 'Sintered Stone Slab',
            'category_id': cats.get('stone.artificial'),
            'sub_category': '瓷砖-室内',
            'fire_rating': 'A1', 'env_grade': '无有害释放',
            'unit_price': 400, 'labor_cost': 150, 'loss_factor': 1.08,
            'cost_tier': '中高', 'unit': '元/m²',
            'texture': '兼具石材质感与大规格', 'color_series': '全色系，仿石材/仿木纹/仿水泥',
            'specs': '1200×2400~1600×3200mm，厚6~12mm',
            'patterns': '光面/哑光/连纹大面',
            'visual_desc': '大规格通铺实现无缝效果，是中高端住宅热门选择',
            'structure_notes': '需专用吸盘安装，瓷砖胶+背网加固；薄贴法',
            'durability': '优', 'lifespan_years': '50年以上',
            'applications_json': json.dumps(['室内墙地面', '厨房台面', '浴室墙面']),
            'suppliers_json': json.dumps([13]),
            'exam_weight': 0.08,
            'exam_points': json.dumps(['岩板吸水率极低', '切割需专用工具']),
        },
    ]

    for m in materials:
        try:
            cols = ', '.join(m.keys())
            ph   = ', '.join(['?'] * len(m))
            vals = list(m.values())
            conn.execute(f'INSERT OR REPLACE INTO materials ({cols}) VALUES ({ph})', vals)
        except Exception as e:
            print(f"  ⚠️  材料 {m.get('code')} 插入失败: {e}")

    conn.commit()
    print(f"✅ 填充 {len(materials)} 条材料数据")

def seed_suppliers(conn):
    """填充供应商种子数据"""
    suppliers = [
        {'name': '环球石材', 'type': '国产头部', 'products': '花岗岩/大理石', 'price_level': '中高',
         'features': '大型矿山，加工能力强', 'applicable': '高端商业/酒店', 'id': 1},
        {'name': '康利石材', 'type': '国产头部', 'products': '花岗岩/大理石', 'price_level': '中',
         'features': '华南龙头，出口品质', 'applicable': '各类项目', 'id': 2},
        {'name': '金边铝业', 'type': '国产头部', 'products': '铝单板', 'price_level': '中高',
         'features': '深圳上市企业，品质稳定', 'applicable': '高端商业/公共建筑', 'id': 3},
        {'name': 'VMZINC（维尔赛斯）', 'type': '进口品牌', 'products': '锌板/铜板', 'price_level': '高',
         'features': '全球锌板龙头，上海有公司', 'applicable': '高端文化/商业',
         'origin': '法国', 'china_channel': '上海公司直供', 'id': 4},
        {'name': '蓝天铝业', 'type': '国产', 'products': '穿孔铝板/装饰板', 'price_level': '中',
         'features': '穿孔板/波纹板专业', 'applicable': '各类装饰项目', 'id': 5},
        {'name': '瑞高陶板', 'type': '国产头部', 'products': '陶板/陶棍', 'price_level': '中',
         'features': '国产陶板头部品牌', 'applicable': '文化/商业/住宅', 'id': 6},
        {'name': '南玻集团', 'type': '国产头部', 'products': '原片/加工玻璃/Low-E', 'price_level': '中高',
         'features': '全产业链，上市企业', 'applicable': '高端幕墙', 'id': 7},
        {'name': '旭建GRC', 'type': '国产头部', 'products': 'GRC板/异形', 'price_level': '中',
         'features': 'GRC行业龙头，标准板+异形', 'applicable': '各类项目', 'id': 8},
        {'name': '倍立达', 'type': '国产头部', 'products': 'UHPC/GRC', 'price_level': '中高',
         'features': 'UHPC幕墙板领军企业', 'applicable': '高端幕墙/地标', 'id': 9},
        {'name': '大自然木业', 'type': '国产', 'products': '户外木/防腐木', 'price_level': '中',
         'features': '品种齐全，全国渠道', 'applicable': '住宅/文旅', 'id': 10},
        {'name': '三棵树', 'type': '国产头部', 'products': '真石漆/仿石漆/氟碳涂料', 'price_level': '中',
         'features': '上市企业，外墙涂料市占率高', 'applicable': '住宅/商业外墙', 'id': 11},
        {'name': '久盛地板', 'type': '国产头部', 'products': '实木地板', 'price_level': '中高',
         'features': '实木专业品牌', 'applicable': '高端住宅', 'id': 12},
        {'name': '东鹏瓷砖', 'type': '国产头部', 'products': '瓷砖/岩板', 'price_level': '中高',
         'features': '上市企业，岩板品类全', 'applicable': '高端住宅/商业', 'id': 13},
    ]

    for s in suppliers:
        sid = s.pop('id')
        cols = ', '.join(s.keys())
        ph   = ', '.join(['?'] * len(s))
        conn.execute(f'INSERT OR REPLACE INTO suppliers (id, {cols}) VALUES ({sid}, {ph})',
                      list(s.values()))

    conn.commit()
    print(f"✅ 填充 {len(suppliers)} 条供应商数据")

def seed_exam(conn):
    """填充考试知识种子数据（章节4.1）"""
    cats = {}
    rows = conn.execute('SELECT id, code FROM categories').fetchall()
    for r in rows:
        cats[r['code']] = r['id']

    knowledge = [
        {'chapter': '4.1', 'section': '4.1.1', 'topic': '钢材分类与选用',
         'content': 'Q235用于一般结构，Q345/Q390用于重要结构，Q460用于特殊大跨度钢结构',
         'difficulty': '易', 'exam_freq': '高',
         'key_point': '记住强度等级对应的应用场景',
         'case_example': '鸟巢使用Q460钢4.2万吨',
         'category_id': cats.get('metal.steel')},
        {'chapter': '4.1', 'section': '4.1.2', 'topic': '混凝土标号',
         'content': 'C30是基础标号；高性能混凝土HPC强度等级更高；自密实混凝土SCC无需振捣',
         'difficulty': '易', 'exam_freq': '高',
         'key_point': 'C30是所有混凝土的基础，必须记住',
         'category_id': cats.get('concrete.normal')},
        {'chapter': '4.1', 'section': '4.1.3', 'topic': '石材分类与性能',
         'content': '花岗岩（优，50~100年）/大理石（良，30~50年）/砂岩（一般，需防护）',
         'difficulty': '中', 'exam_freq': '高',
         'key_point': '花岗岩是外墙首选石材，记住吸水率差异',
         'category_id': cats.get('stone.granite')},
        {'chapter': '4.1', 'section': '4.1.4', 'topic': 'Low-E玻璃性能',
         'content': 'Low-E中空玻璃U值可至1.0 W/(m²·K)，远优于普通玻璃',
         'difficulty': '中', 'exam_freq': '高',
         'key_point': 'U值越低保温越好，Low-E是节能幕墙首选',
         'case_example': '上海中心双层幕墙使用低辐射镀膜玻璃',
         'category_id': cats.get('glass.low_e')},
        {'chapter': '4.1', 'section': '4.1.5', 'topic': '建筑材料防火等级',
         'content': 'A1级（不燃）：石材/金属/混凝土/玻璃/陶板/清水混凝土；B1级（难燃）：阻燃处理木材/阻燃涂料；B2级（可燃）：普通木材/普通涂料',
         'difficulty': '中', 'exam_freq': '高',
         'key_point': '高层建筑外墙必须使用A级材料（重要考点）',
         'category_id': cats.get('stone')},
        {'chapter': '4.1', 'section': '4.1.6', 'topic': 'ETFE膜材',
         'content': 'ETFE透光率可达90%，自洁轻质，常用于膜结构幕墙和屋面',
         'difficulty': '中', 'exam_freq': '中',
         'key_point': 'ETFE是透光性最好的建筑膜材',
         'case_example': '水立方使用ETFE膜4万m²',
         'category_id': cats.get('membrane')},
    ]

    for k in knowledge:
        k.pop('category_id', None)
        cols = ', '.join(k.keys())
        ph   = ', '.join(['?'] * len(k))
        conn.execute(f'INSERT OR IGNORE INTO exam_knowledge ({cols}) VALUES ({ph})',
                      list(k.values()))

    conn.commit()
    print(f"✅ 填充 {len(knowledge)} 条考试知识点")

# ============================================================
# 主程序
# ============================================================
if __name__ == '__main__':
    print("=" * 50)
    print("建筑材料数据库 - 初始化")
    print(f"数据库路径: {DB_PATH}")
    print("=" * 50)

    conn = init_db()
    seed_materials(conn)
    seed_suppliers(conn)
    seed_exam(conn)

    # 验证数据
    mat_count = conn.execute('SELECT COUNT(*) FROM materials').fetchone()[0]
    sup_count = conn.execute('SELECT COUNT(*) FROM suppliers').fetchone()[0]
    ek_count  = conn.execute('SELECT COUNT(*) FROM exam_knowledge').fetchone()[0]
    cat_count = conn.execute('SELECT COUNT(*) FROM categories').fetchone()[0]

    print()
    print("📊 数据统计:")
    print(f"   分类: {cat_count}")
    print(f"   材料: {mat_count}")
    print(f"   供应商: {sup_count}")
    print(f"   考试知识点: {ek_count}")
    print()
    print(f"✅ 数据库初始化完成!")
    print(f"   运行 python api_server.py 启动服务")
