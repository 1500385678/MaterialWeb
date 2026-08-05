# docs/CHEATSHEET.md · 1 行/文件速查

> 找文件用这个最快。

---

## 后端(15 个 .py)

| 文件 | 一句话 |
|---|---|
| `server/__init__.py`        | 包标识 + 顶层 API 暴露(create_app, config) |
| `server/__main__.py`        | 入口,`python -m server` 启动 Flask |
| `server/config.py`          | 路径/端口/常量(改 → 同步 daemon.py) |
| `server/core.py`            | Flask app + DB 连接 + row_to_dict + CORS |
| `server/routes.py`          | 路由表,register_blueprints 把 11 个 handler 串起来 |
| `server/handlers/materials.py` | 材料 list / search / detail + QR(可选) |
| `server/handlers/categories.py` | 分类全表 |
| `server/handlers/suppliers.py`  | 供应商全表 |
| `server/handlers/exam.py`       | 考试知识点 all + by_chapter |
| `server/handlers/projects.py`   | 项目 CRUD + 关联材料 + 造价 + 导出 docx |
| `server/handlers/qr.py`         | 二维码生成 + 缓存 |
| `server/handlers/media.py`      | 静态图/CAD/uploads 服务 + 媒体列表 |
| `server/handlers/vision.py`     | OpenAI 兼容视觉 + matrix MCP fallback |
| `server/handlers/search_by.py`  | 多字段评分排序,top 30 |
| `server/handlers/schemes.py`    | 方案 CRUD + reload + 会话上下文 |
| `server/handlers/pdf_export.py` | reportlab PDF + 中文字体探测 |

## 前端(14 个 .js + 1 个 .css + 1 个 .html)

| 文件 | 一句话 |
|---|---|
| `client/index.html`           | 主页(瘦,4 tab + 4 弹窗,纯 markup) |
| `client/css/common.css`       | 全部样式(整合,单文件) |
| `client/js/main.js`           | 入口,import + init 11 个 module |
| `client/js/api.js`            | 所有 /api/* 封装 + multipart analyze |
| `client/js/core/state.js`     | 全局 state + model localStorage 持久化 |
| `client/js/core/dom.js`       | `$`/`el`/`on`/`debounce`/`fmt` |
| `client/js/core/events.js`    | 极简 bus(`on`/`off`/`emit`) |
| `client/js/core/toast.js`     | 顶部 toast |
| `client/js/modules/tabs.js`         | 4 tab 切换 |
| `client/js/modules/filters.js`      | 分类/防火/造价 + 搜索 |
| `client/js/modules/materials.js`    | 列表 + 卡片 + 详情弹窗(6 tab) |
| `client/js/modules/projects.js`     | 项目 CRUD + 添加材料 + 成本汇总 |
| `client/js/modules/exam.js`         | 章节列表 + 知识点卡片 |
| `client/js/modules/ai-flow.js`      | 5 步流程(上传 → 识图 → 确认 → 选 → 保存) |
| `client/js/modules/ai-schemes.js`   | 已保存方案(查看/重载/PDF/删) |
| `client/js/modules/model-settings.js` | AI 模型设置(localStorage) |
| `client/js/modules/qr-panel.js`     | 二维码弹窗 |
| `client/js/modules/media.js`        | 图片库 + CAD 列表 + 灯箱 |
| `client/js/modules/utils.js`        | 弹窗开关 + nowStr + 暴露 tabs |

## 数据 + 启动 + 测试(7 个)

| 文件 | 一句话 |
|---|---|
| `db/materials.db`     | SQLite 数据(自动生成) |
| `db/init_schema.sql`   | 6 张表 + 索引 + 初始分类 |
| `scripts/daemon.py`    | 清旧进程 + 后台启动 + 15s 健康检查 |
| `scripts/start.ps1`    | Windows 启动按钮 |
| `scripts/init_db.py`   | 重建 DB + 灌种子(4 材料 + 3 供应商) |
| `tests/smoke.py`       | 8 项 API 快检 |
| `data/uploads/`        | AI 上传图(11 张已迁移) |
| `data/qr_codes/`       | 生成的二维码(4 张已迁移) |
| `data/media/images/`   | 材料配图(1 张) |
| `data/media/cad/`      | CAD 文件 |

## 文档(3 入口 + 7 docs = 10)

| 文件 | 一句话 |
|---|---|
| `MAIN.md`              | 主程序 vs 支程序 · 改前必看 |
| `README.md`            | 小白入门(本目录) |
| `CONTROL.md`           | 5 分钟接手(下一个 agent 必读) |
| `docs/README.md`       | 上手 3 步(技术版) · v1.1 补 |
| `docs/AGENTS.md`       | AI 协作者硬约束 ✓ |
| `docs/api_contract.md` | 31 端点契约 ✓ |
| `docs/STYLE.md`        | 写作风格 · v1.1 补 |
| `docs/CHEATSHEET.md`   | 1 行/文件速查 ✓ (本文件) |
| `docs/FILE_GUIDE.md`   | 3-5 行/文件详释 · v1.1 补 |
| `docs/WORKFLOWS.md`    | 8 阶段工作流 · v1.1 补 |

> ✓ = v1.0 已写 · 其他 4 份标 v1.1 补(README 已有简版覆盖)

## 统计

- 后端 .py:16 个(含 `__init__` × 2)
- 前端 .js:14 个
- 前端 .html:1 个
- 前端 .css:1 个
- SQL/数据:2 个
- 脚本:3 个
- 测试:1 个
- 文档:10 个
- **总:48 个文件 · ~3700 行代码**
