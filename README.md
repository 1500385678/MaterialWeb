# MaterialWeb v1.0 · 小白入门 README

> **这份用大白话写**,技术细节看 [[MAIN]]、[[docs/README]]、[[docs/AGENTS]]、[[docs/FILE_GUIDE]]、[[docs/api_contract]]。
> 参考 CanvasWeb-v2.5 框架:主程序 vs 支程序 + 单文件 ≤250 行。

---

## 0. 一句话说明

**网页版的建筑材料数据库 + AI 选材工具** —— 看材料库、创建项目、用 AI 识别图片选材料、保存方案、导出 PDF。

跑起来后打开浏览器到 `http://127.0.0.1:8086/` 就能用。

---

## 0.5 📍 当前状态快照(2026-07-13)

| 项 | 状态 | 备注 |
|---|---|---|
| 服务 | 🟢 在跑 | 端口 8086 · 8/8 smoke endpoints OK |
| 规模 | ~3700 行 | Py 1850 + JS 1600 + HTML/CSS 450 |
| 框架 | v2.5 风格 | 主程序 vs 支程序 · 单文件 ≤250 行 |
| 依赖 | Flask + qrcode + reportlab | v1.0 保留,见 § 6 偏离声明 |
| 数据 | 已迁移 | materials.db 160KB + 11 张 AI 图 + 4 个 QR |

**今天做了什么(2026-07-13)**:
- ✅ 把原 MaterialDb(后端 1231 行 monolith)+ MaterialWeb(前端 1902 行 monolith)拆成 35 个文件
- ✅ 端口 5188 → 8086(顺延 CanvasWeb 8085)
- ✅ 备份旧目录 `_archive_2026-07-13_MaterialWeb/`
- ✅ 启动 + 8/8 smoke 通过

---

## 1. 怎么启动(3 步 · Mac / Windows 双平台)

### 🍎 Mac (本机默认)

```bash
# 第 1 步:打开 Terminal,切到这个文件夹
cd /Users/aaron/Mac/WorkTeam/05_Space/03_Architect/Defense/06-Material/_ArchiDefenseMaterial/MaterialWeb/

# 第 2 步:启动后台服务(关掉窗口也不会停)
python3 scripts/daemon.py

# 第 3 步:打开浏览器
#    http://127.0.0.1:8086/
```

> **Mac 用 `source` 替 `powershell`**(没有 venv 就 `python3` 直接跑,跟下面 Linux 通用)。

### 🪟 Windows (PowerShell)

```powershell
# 第 1 步:打开 PowerShell,切到这个文件夹
#    Windows 路径仅作历史参考 — 实际开发在 Mac mini 上
#    如需在 Windows 跑,先 git clone 同步本仓,再按本机实际路径改 cd

# 第 2 步:启动后台服务
python scripts\daemon.py

# 第 3 步:打开浏览器
#    http://127.0.0.1:8086/
```

**怎么知道启动成功了?**
最后一行:`[daemon] OK · http://127.0.0.1:8086/`

**怎么知道有没有坏?**
`python3 tests/smoke.py` → `✅ 8/8 endpoints OK` 就对了。

**想看实时日志?** 前台模式:
```bash
python3 -X utf8 -u -m server
```

---

## 2. 怎么用(基本操作)

1. **顶部 4 个 tab** — 材料库 / 我的项目 / 考试学习 / 🤖 AI 选材
2. **材料库** — 顶部 4 个下拉(分类/防火/造价)+ 搜索框;点击卡片看详情
3. **我的项目** — 新建项目 → 打开 → 添加材料 → 看造价汇总 → 导出文档
4. **考试学习** — 章节下拉 + 知识点卡片
5. **AI 选材** — 5 步流程:上传图 → AI 识图 → 确认信息 → 选材料 → 保存方案
6. **右上角"模型设置"** — 配置自定义 OpenAI 兼容视觉模型

---

## 3. 文件夹地图(逐个解释)

### 3.1 顶层文件

| 文件 | 它是什么 |
|---|---|
| `MAIN.md` | **地图 + 红线**。哪些是骨架,哪些是支程序。改之前必看。 |
| `README.md` | **这份文件**(小白入门版)。 |
| `CONTROL.md` | **5 分钟接手文档**(下一个 agent 必读)。 |
| `db/materials.db` | **SQLite 数据库**(所有材料/项目/方案数据)。 |
| `data/uploads/` | AI 上传的图。 |
| `data/qr_codes/` | 生成的二维码 PNG。 |
| `data/media/images/` | 材料配图。 |
| `data/media/cad/` | CAD 文件(DWG/SKP/PDF)。 |
| `server.out` / `server.err` | 服务日志。 |
| `daemon.out` / `daemon.err` | 启动器日志。 |

### 3.2 `server/` 后端(Python + Flask)

| 文件 | 它在做什么 |
|---|---|
| `__init__.py` | 包标识 + 顶层 API 暴露 |
| `__main__.py` | 入口 + 启动 |
| `config.py` | 路径/端口/常量 |
| `core.py` | Flask app + DB 连接 + row 转换 + CORS |
| `routes.py` | 路由注册表 |
| `handlers/materials.py` | 材料 CRUD + 搜索 |
| `handlers/categories.py` | 分类 |
| `handlers/suppliers.py` | 供应商 |
| `handlers/exam.py` | 考试 |
| `handlers/projects.py` | 项目 + 关联材料 + 成本汇总 |
| `handlers/qr.py` | 二维码生成 |
| `handlers/media.py` | 媒体(图/CAD/uploads) |
| `handlers/vision.py` | AI 视觉分析 + 模型测试 |
| `handlers/search_by.py` | 关键词检索评分 |
| `handlers/schemes.py` | 方案 CRUD + reload |
| `handlers/pdf_export.py` | PDF 导出(reportlab) |

### 3.3 `client/` 前端(原生 ES Modules)

| 文件 | 它在做什么 |
|---|---|
| `index.html` | 主页(瘦)。4 tab + 4 弹窗。 |
| `css/common.css` | 全部样式。 |
| `js/main.js` | 入口。import + init 11 个 module。 |
| `js/api.js` | 所有 /api/* 封装(单一入口)。 |
| `js/core/state.js` | 全局状态。 |
| `js/core/dom.js` | DOM 工具 / el() / debounce。 |
| `js/core/events.js` | 极简事件总线。 |
| `js/core/toast.js` | 顶部 toast。 |
| `js/modules/*.js` | 11 个业务模块(材料/项目/AI 等)。 |

### 3.4 `db/` 数据库

| 文件 | 它是什么 |
|---|---|
| `materials.db` | SQLite 数据文件(自动生成) |
| `init_schema.sql` | 表结构(改这里要重新建表) |

### 3.5 `scripts/` 启动器

| 文件 | 它在做什么 |
|---|---|
| `daemon.py` | **大开关**。清旧进程 + 后台启动 + 健康检查 |
| `start.ps1` | Windows 启动按钮 |
| `init_db.py` | 首次部署 / 重建数据库(建表 + 灌种子) |

### 3.6 `tests/`

| 文件 | 它在做什么 |
|---|---|
| `smoke.py` | 8 项 API 快检 |

### 3.7 `docs/` 7 份

| 文件 | 它在讲什么 |
|---|---|
| `docs/README.md` | 上手 3 步(技术版) |
| `docs/AGENTS.md` | AI 协作者硬约束 |
| `docs/api_contract.md` | 所有 API 端点契约 |
| `docs/WORKFLOWS.md` | 8 阶段工作流 |
| `docs/STYLE.md` | 写作风格 + 反 AI 味 |
| `docs/CHEATSHEET.md` | 1 行/文件速查 |
| `docs/FILE_GUIDE.md` | 每个文件 3-5 行详释 |

### 3.8 `data/` 用户数据

| 文件 | 它在做什么 |
|---|---|
| `uploads/` | AI 上传图片 |
| `qr_codes/` | 二维码 PNG |
| `media/images/` | 材料配图 |
| `media/cad/` | CAD 文件 |

### 3.9 `.Log/` 流水

`YYYY-MM-DD-干了什么.md` 格式,每日一篇。

---

## 4. 数据存在哪(一张表)

| 数据 | 放在哪 | 重要程度 |
|---|---|---|
| 材料/项目/方案/方案详情 | `db/materials.db` | ★★★ 重要 |
| AI 上传图 | `data/uploads/` | ★★ 可重建 |
| 二维码 | `data/qr_codes/` | ★★ 可重建 |
| 材料配图 | `data/media/images/` | ★★ |
| CAD 文件 | `data/media/cad/` | ★★ |
| 兄弟图库 | `_ArchitectLib/PictureDb/PictureDb.db` | ★★★ 重要(不动) |

---

## 5. 哪里找什么帮助

| 你想... | 看哪 |
|---|---|
| 第一次接触项目 | 这份 [[README]] |
| 知道怎么启动 | [[docs/README]] 上手 3 步 |
| 知道每个文件干啥 | [[docs/FILE_GUIDE]] 3-5 行/文件 |
| 1 行速查每个文件 | [[docs/CHEATSHEET]] |
| AI 改这个项目 | [[docs/AGENTS]] |
| 看 API 长啥样 | [[docs/api_contract]] |
| 代码怎么写(命名/风格/禁词) | [[docs/STYLE]] |
| 主程序 vs 支程序边界 | [[MAIN]] |
| 出问题了 | 翻 `server.err` 和 `daemon.err` |

---

## 6. 项目铁律(不能踩)

- **每个文件不超过 250 行**(画布/复杂模块例外 ≤ 400 行,v1.1 拆)
- **端口 8086**(改它要同步改 3 个地方:`config.py` + `daemon.py` + 文档)
- **API 路径只加不减**(减了会让旧前端失效)
- **API 响应字段只加不删,可以重命名**
- **HTML/CSS/JS 不缓存**(改了立刻生效)
- **写权限限本机 IP**(dev 默认 127.0.0.1,生产严禁 0.0.0.0;需 LAN 临时开 `MW_HOST=0.0.0.0 MW_ALLOWED_LAN_IPS=<ip1,ip2>`)
- **同时最多 20 人用**(超出返 503)

### 6.1 ⚠️ v1.0 偏离 v2.5 铁律

| 偏离项 | 理由 | 何时回归 |
|---|---|---|
| 保留 Flask 依赖(非 stdlib) | PDF 导出(reportlab)+ 二维码(qrcode)需要 | v1.1 看是否换 HTML→PDF |

完整铁律见 `docs/AGENTS.md` § 3。

---

## 7. 变更记录

| 日期 | 变更 | 触发 |
|---|---|---|
| 2026-07-13 | **v1.0 重构** · 35 个文件 · 8/8 smoke OK · 端口 8086 | 用户"单个文件不能太大,方便后面开发" |

---

## 关联文档

- [[MAIN]] · 主程序 vs 支程序边界
- [[CONTROL]] · 5 分钟接手文档
- [[docs/AGENTS]] · AI 协作者硬约束
- [[docs/api_contract]] · API 契约
