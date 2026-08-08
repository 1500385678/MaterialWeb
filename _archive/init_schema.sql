-- ============================================================
-- 建筑材料数据库 Schema
-- MaterialDb/materials.db
-- ============================================================

-- 根目录：C:\Users\yongzhang\.mavis\agents\verifier\workspace\
-- 数据库文件：D:\Mac\Mac\workteam\05_space\03_architect\_ArchitectLib\MaterialDb\materials.db

-- ----------------------------------------------------------
-- 1. 材料分类表
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS categories (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    code            TEXT    NOT NULL UNIQUE,     -- 'metal.steel'
    name            TEXT    NOT NULL,             -- '建筑钢材'
    parent_code     TEXT    DEFAULT NULL,         -- 父级分类，NULL 为顶级
    exam_chapter    TEXT    DEFAULT NULL,         -- 考试章节号 '4.1'
    sort_order      INTEGER DEFAULT 0,
    remark          TEXT    DEFAULT NULL,
    created_at      TEXT    DEFAULT (datetime('now', 'localtime')),
    updated_at      TEXT    DEFAULT (datetime('now', 'localtime'))
);

-- ----------------------------------------------------------
-- 2. 供应商表
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS suppliers (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT    NOT NULL,             -- '环球石材'
    name_en         TEXT    DEFAULT NULL,
    type            TEXT    NOT NULL,             -- '国产头部' / '进口品牌' / '性价比'
    products        TEXT    NOT NULL,             -- 主营产品（逗号分隔）
    price_level     TEXT    NOT NULL,             -- '高' / '中' / '低'
    features        TEXT    DEFAULT NULL,         -- 特点描述
    applicable      TEXT    DEFAULT NULL,         -- 适用项目类型
    origin          TEXT    DEFAULT NULL,         -- 原产国（进口品牌）
    china_channel   TEXT    DEFAULT NULL,         -- 中国代理/渠道
    website         TEXT    DEFAULT NULL,
    contact         TEXT    DEFAULT NULL,
    remark          TEXT    DEFAULT NULL,
    created_at      TEXT    DEFAULT (datetime('now', 'localtime')),
    updated_at      TEXT    DEFAULT (datetime('now', 'localtime'))
);

-- ----------------------------------------------------------
-- 3. 考试知识表
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS exam_knowledge (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id     INTEGER REFERENCES categories(id),
    chapter         TEXT    NOT NULL,             -- '4.1'
    section         TEXT    DEFAULT NULL,         -- '4.1.2'
    topic           TEXT    NOT NULL,              -- 知识点标题
    content         TEXT    NOT NULL,             -- 知识点内容
    difficulty      TEXT    DEFAULT '中',          -- '易' / '中' / '难'
    exam_freq       TEXT    DEFAULT '中',          -- 出题频率 '高' / '中' / '低'
    key_point       TEXT    DEFAULT NULL,         -- 答题要点/套路
    case_example    TEXT    DEFAULT NULL,         -- 案例关联
    created_at      TEXT    DEFAULT (datetime('now', 'localtime')),
    updated_at      TEXT    DEFAULT (datetime('now', 'localtime'))
);

-- ----------------------------------------------------------
-- 4. 材料主表
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS materials (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    code            TEXT    NOT NULL UNIQUE,     -- 'MAT_001'
    name_cn         TEXT    NOT NULL,             -- '花岗岩'
    name_en         TEXT    DEFAULT NULL,
    category_id     INTEGER REFERENCES categories(id),
    sub_category    TEXT    DEFAULT NULL,         -- 子分类 '天然石材'

    -- 物理性能
    density         TEXT    DEFAULT NULL,         -- '2500~2800 kg/m³'
    strength        TEXT    DEFAULT NULL,         -- '抗压 100~250MPa'
    thermal_cond    TEXT    DEFAULT NULL,         -- '2.0~3.5 W/(m·K)'
    water_absorp    TEXT    DEFAULT NULL,         -- '≤0.5%'
    fire_rating     TEXT    NOT NULL,             -- 'A1' 防火等级
    fire_note       TEXT    DEFAULT NULL,         -- 防火补充说明

    -- 环保与规范
    env_grade       TEXT    DEFAULT NULL,         -- 'E0/E1' / '无甲醛'
    std_code        TEXT    DEFAULT NULL,         -- 'GB/T 18601'
    eco_cert         TEXT    DEFAULT NULL,         -- '绿色建材认证' 等

    -- 经济属性
    unit_price      REAL    DEFAULT 0,            -- 材料单价（元/m²）
    unit_price_m3   REAL    DEFAULT 0,            -- 或 元/m³
    unit            TEXT    DEFAULT '元/m²',      -- 计量单位
    labor_cost      REAL    DEFAULT 0,            -- 施工费（元/m²）
    loss_factor     REAL    DEFAULT 1.05,          -- 损耗系数
    cost_tier       TEXT    DEFAULT '中',         -- '💰' ~ '💰💰💰💰'

    -- 供应商（JSON 数组：supplier_id 列表）
    suppliers_json  TEXT    DEFAULT '[]',

    -- 适用场景（JSON 数组）
    applications_json TEXT  DEFAULT '[]',

    -- 外观属性
    texture         TEXT    DEFAULT NULL,         -- '哑光/光泽/粗粝'
    color_series    TEXT    DEFAULT NULL,         -- '灰/白/黑/红系'
    specs           TEXT    DEFAULT NULL,         -- '600×600, 厚度25~30mm'
    patterns        TEXT    DEFAULT NULL,         -- '光面/火烧面/荔枝面'
    visual_desc     TEXT    DEFAULT NULL,         -- 视觉效果描述

    -- 构造要点
    structure_notes TEXT    DEFAULT NULL,         -- 构造节点要点

    -- 耐候耐久
    durability      TEXT    DEFAULT NULL,         -- '优/良/一般'
    lifespan_years  TEXT    DEFAULT NULL,         -- '50~100年'
    maintenance     TEXT    DEFAULT NULL,         -- 维护周期说明

    -- 考试关联
    exam_weight     REAL    DEFAULT 0,            -- 考试权重 0~1
    exam_points     TEXT    DEFAULT NULL,         -- 考试要点（JSON 数组）
    exam_cases      TEXT    DEFAULT NULL,         -- 关联案例

    -- 图片与二维码
    image_urls      TEXT    DEFAULT '[]',        -- 图片路径（JSON 数组）
    qr_code_path    TEXT    DEFAULT NULL,         -- 二维码图片路径
    qr_content      TEXT    DEFAULT NULL,         -- 二维码内容

    -- 状态与备注
    status          TEXT    DEFAULT 'active',     -- 'active' / 'deprecated'
    source_doc      TEXT    DEFAULT NULL,         -- 来源文档路径
    remark          TEXT    DEFAULT NULL,
    created_at      TEXT    DEFAULT (datetime('now', 'localtime')),
    updated_at      TEXT    DEFAULT (datetime('now', 'localtime'))
);

-- ----------------------------------------------------------
-- 5. 项目表
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS projects (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    code            TEXT    NOT NULL UNIQUE,     -- 'PRJ_001'
    name            TEXT    NOT NULL,
    type            TEXT    DEFAULT NULL,         -- '住宅' / '商业' / '办公'
    area            REAL    DEFAULT 0,            -- 建筑面积 m²
    location        TEXT    DEFAULT NULL,
    status          TEXT    DEFAULT 'designing',  -- 'designing' / 'tender' / 'constructed'
    created_at      TEXT    DEFAULT (datetime('now', 'localtime')),
    updated_at      TEXT    DEFAULT (datetime('now', 'localtime'))
);

-- ----------------------------------------------------------
-- 6. 项目材料清单表
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS project_materials (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      INTEGER NOT NULL REFERENCES projects(id),
    material_id     INTEGER NOT NULL REFERENCES materials(id),

    quantity        REAL    NOT NULL,            -- 用量（面积 m² 或 体积 m³）
    unit_cost       REAL    DEFAULT 0,            -- 实际采购单价
    location        TEXT    DEFAULT NULL,         -- 使用部位 '外墙' / '地面'
    position_desc   TEXT    DEFAULT NULL,         -- 位置描述
    spec_override   TEXT    DEFAULT NULL,         -- 规格覆盖（与标准规格不同的说明）

    remark          TEXT    DEFAULT NULL,
    created_at      TEXT    DEFAULT (datetime('now', 'localtime')),
    updated_at      TEXT    DEFAULT (datetime('now', 'localtime'))
);

-- ----------------------------------------------------------
-- 7. 材料对比方案表
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS material_schemes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      INTEGER NOT NULL REFERENCES projects(id),
    name            TEXT    NOT NULL,
    description     TEXT    DEFAULT NULL,
    status          TEXT    DEFAULT 'draft',      -- 'draft' / 'selected'
    created_at      TEXT    DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS scheme_materials (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    scheme_id       INTEGER NOT NULL REFERENCES material_schemes(id),
    material_id     INTEGER NOT NULL REFERENCES materials(id),
    score           REAL    DEFAULT 0,            -- 评分 0~10
    score_reason    TEXT    DEFAULT NULL,
    is_selected     INTEGER DEFAULT 0             -- 0=备选 1=选用
);

-- ============================================================
-- 索引
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_materials_category  ON materials(category_id);
CREATE INDEX IF NOT EXISTS idx_materials_code     ON materials(code);
CREATE INDEX IF NOT EXISTS idx_materials_fire     ON materials(fire_rating);
CREATE INDEX IF NOT EXISTS idx_materials_cost_tier ON materials(cost_tier);
CREATE INDEX IF NOT EXISTS idx_pm_project         ON project_materials(project_id);
CREATE INDEX IF NOT EXISTS idx_pm_material         ON project_materials(material_id);
CREATE INDEX IF NOT EXISTS idx_ek_category         ON exam_knowledge(category_id);
CREATE INDEX IF NOT EXISTS idx_sm_scheme           ON scheme_materials(scheme_id);

-- ============================================================
-- 初始数据：分类
-- ============================================================
INSERT OR IGNORE INTO categories (code, name, parent_code, sort_order) VALUES
    ('metal',        '金属材料',        NULL, 1),
    ('concrete',     '混凝土',         NULL, 2),
    ('masonry',      '砌体材料',       NULL, 3),
    ('wood',         '木材',           NULL, 4),
    ('glass',        '玻璃',           NULL, 5),
    ('stone',        '石材',           NULL, 6),
    ('membrane',     '膜材',           NULL, 7),
    ('insulation',   '保温/防水',      NULL, 8),
    ('finishing',    '装饰材料',       NULL, 9),
    ('composite',    '复合材料',       NULL, 10);

-- 金属材料子分类
INSERT OR IGNORE INTO categories (code, name, parent_code, sort_order) VALUES
    ('metal.steel',   '建筑钢材',       'metal',  11),
    ('metal.aluminum','铝合金',         'metal',  12),
    ('metal.copper',  '铜/钛/锌',       'metal',  13),
    ('metal.stainless','不锈钢',        'metal',  14);

-- 混凝土子分类
INSERT OR IGNORE INTO categories (code, name, parent_code, sort_order) VALUES
    ('concrete.normal',    '普通混凝土',   'concrete', 21),
    ('concrete.hpc',       '高性能混凝土', 'concrete', 22),
    ('concrete.scc',       '自密实混凝土', 'concrete', 23),
    ('concrete.fairface',  '清水混凝土',   'concrete', 24);

-- 玻璃子分类
INSERT OR IGNORE INTO categories (code, name, parent_code, sort_order) VALUES
    ('glass.float',    '浮法玻璃',       'glass', 51),
    ('glass.tempered', '钢化玻璃',       'glass', 52),
    ('glass.laminated', '夹层玻璃',      'glass', 53),
    ('glass.low_e',    'Low-E中空',      'glass', 54),
    ('glass.vacuum',   '真空玻璃',       'glass', 55);

-- 石材子分类
INSERT OR IGNORE INTO categories (code, name, parent_code, sort_order) VALUES
    ('stone.granite',  '花岗岩',         'stone', 61),
    ('stone.marble',   '大理石',         'stone', 62),
    ('stone.sandstone','砂岩',           'stone', 63),
    ('stone.artificial','人造石材',       'stone', 64);

-- 装饰材料子分类
INSERT OR IGNORE INTO categories (code, name, parent_code, sort_order) VALUES
    ('finishing.paint',   '涂料',        'finishing', 91),
    ('finishing.tile',    '瓷砖',        'finishing', 92),
    ('finishing.metal',   '金属板',      'finishing', 93),
    ('finishing.wood',    '木饰面',      'finishing', 94),
    ('finishing.glass',  '玻璃',        'finishing', 95);
