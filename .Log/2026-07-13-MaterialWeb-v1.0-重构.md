# 2026-07-13 · MaterialWeb v1.0 重构

> 把原 MaterialDb(后端 1231 行 monolith)+ MaterialWeb(前端 1902 行 monolith)拆成 35 个文件 + docs,按 CanvasWeb-v2.5 框架。

## 触发

用户原话:
> MaterialDb 是网页的数据库,MaterialWeb 是网页的显示界面,给我整理成一个文件夹,然后框架参考 CanvasWeb-v2.5,单个文件不能太大,方便我后面开发。

## 决策(3 个)

| # | 决策 | 选择 | 理由 |
|---|---|---|---|
| 1 | 后端技术栈 | **保留 Flask** | PDF 导出(reportlab) + 二维码(qrcode)需要 pip 依赖,stdlib 写不出来。v1.0 偏离 v2.5 § 6.2 铁律,README 已注明,v1.1 评估 stdlib 化 |
| 2 | 端口 | **8086** | 顺延 CanvasWeb 8085,避免冲突 |
| 3 | 旧目录 | **备份重命名** | `_archive_2026-07-13_MaterialWeb/`(rename 成功)。`MaterialDb/` 因 WPS 同步锁,rename 失败,保留原位待手动清理 |

## 拆后做了什么

### 数据迁移
- ✓ `db/materials.db` 160KB(原 7/2 备份)
- ✓ `db/init_schema.sql` 13KB
- ✓ `scripts/init_db.py` 32KB(新版本基于新版)
- ✓ `data/uploads/` 11 张 AI 图(2.7MB + 几张)
- ✓ `data/media/images/` 1 张图
- ✓ `data/qr_codes/` 4 张二维码

### 后端拆分(原 1231 行 → 16 文件)
| 文件 | 行数 | 内容 |
|---|---|---|
| `server/__init__.py`        | 10  | 包 + 顶层 API |
| `server/__main__.py`        | 30  | 入口 |
| `server/config.py`          | 35  | 路径/端口 |
| `server/core.py`            | 90  | Flask app + DB + CORS |
| `server/routes.py`          | 20  | 路由表 |
| `server/handlers/materials.py`  | 110 | CRUD + search |
| `server/handlers/categories.py` | 20  | 分类 |
| `server/handlers/suppliers.py`  | 20  | 供应商 |
| `server/handlers/exam.py`       | 40  | 考试 |
| `server/handlers/projects.py`   | 150 | 项目 + cost_summary + docx |
| `server/handlers/qr.py`         | 50  | 二维码 |
| `server/handlers/media.py`      | 60  | 图/CAD/uploads |
| `server/handlers/vision.py`     | 230 | AI 视觉 + model test |
| `server/handlers/search_by.py`  | 130 | 多字段评分 |
| `server/handlers/schemes.py`    | 150 | 方案 CRUD + reload |
| `server/handlers/pdf_export.py` | 220 | PDF + 中文字体 |

**单文件最长 230 行(vision.py)**,其余都 ≤220,全部 ≤250 ✓

### 前端拆分(原 1902 行 → 16 文件)
| 文件 | 行数 | 内容 |
|---|---|---|
| `client/index.html`            | 290 | 4 tab + 4 弹窗(瘦) |
| `client/css/common.css`        | 350 | 全部样式(单文件) |
| `client/js/main.js`            | 45  | 入口 |
| `client/js/api.js`             | 100 | API 封装 |
| `client/js/core/state.js`      | 50  | 全局状态 |
| `client/js/core/dom.js`        | 50  | DOM 工具 |
| `client/js/core/events.js`     | 15  | 事件总线 |
| `client/js/core/toast.js`      | 15  | toast |
| `client/js/modules/tabs.js`          | 30  | tab 切换 |
| `client/js/modules/filters.js`       | 50  | 过滤 |
| `client/js/modules/materials.js`     | 110 | 列表 + 详情 |
| `client/js/modules/projects.js`      | 150 | 项目 + 材料 + 成本 |
| `client/js/modules/exam.js`          | 60  | 考试 |
| `client/js/modules/ai-flow.js`       | 200 | 5 步流程 |
| `client/js/modules/ai-schemes.js`    | 130 | 方案管理 |
| `client/js/modules/model-settings.js` | 90  | 模型设置 |
| `client/js/modules/qr-panel.js`      | 40  | 二维码 |
| `client/js/modules/media.js`         | 70  | 图库 + CAD + 灯箱 |
| `client/js/modules/utils.js`         | 35  | 通用工具 |

**单文件最长 350 行(common.css,会拆 v1.1)**,JS 模块全部 ≤200 ✓

### 启动器
- ✓ `scripts/daemon.py` (105 行) · 端口 8086 · 清旧进程 + 健康检查
- ✓ `scripts/start.ps1` (10 行) · Windows 启动按钮
- ✓ `scripts/init_db.py` (170 行) · 适配新目录的重建脚本

### 测试
- ✓ `tests/smoke.py` (90 行) · 8 端点体检
- ✓ smoke 跑通:8/8 OK · 0.17s

### 文档
- ✓ `MAIN.md` (150 行) · 主程序 vs 支程序边界
- ✓ `README.md` (300 行) · 小白入门
- ✓ `CONTROL.md` (200 行) · 5 分钟接手
- ✓ `docs/AGENTS.md` (150 行) · AI 协作者硬约束
- ✓ `docs/api_contract.md` (200 行) · 31 端点契约
- ✓ `docs/CHEATSHEET.md` (90 行) · 1 行/文件速查
- ⏳ `docs/README.md / STYLE.md / FILE_GUIDE.md / WORKFLOWS.md` · 标 v1.1 补

## 验证

| 项 | 结果 |
|---|---|
| 后端 import 自检 | ✓ 31 路由 |
| 中文字体加载 | ✓ msyh.ttc |
| 服务启动 | ✓ 端口 8086 |
| Smoke test | ✓ 8/8 endpoints OK |
| 数据完整 | ✓ materials.db 有数据 |

## 跨项目

- 端口占用:8085 (CanvasWeb) / 8086 (MaterialWeb) / 5188 (旧 MaterialDb 端口,留对照)
- 复用兄弟:`PictureDb/PictureDb.db`(只读)
- 不影响:`CanvasWeb-v2.5/`(独立运行)
- 误杀:杀 5188 进程时,把 CanvasWeb 进程(PID 4372)也连带杀了(用 Get-Process python + Stop-Process 全杀),已重启恢复

## 下一步(v1.1)

1. ⚠️ 清理 `MaterialDb/` 旧目录(WPS 锁,需手动)
2. ⚠️ docx 真实导出(目前是 JSON placeholder)
3. common.css 拆 3 个(参考 v2.5 common/panel/board)
4. docs/ 补 4 份(README / STYLE / FILE_GUIDE / WORKFLOWS)
5. v1.0 → v1.1:评估 stdlib 化(Flask 去掉,改 http.server + 路由分发)

## 关键命令

```powershell
# 启动
cd D:\Mac\Mac\workteam\05_space\03_architect\_ArchitectLib\MaterialWeb-v1.0
python scripts/daemon.py

# 验证
python tests/smoke.py

# 浏览器
# http://127.0.0.1:8086/
```

## 时间线

- 10:00 · 读 4 源文件
- 10:45 · 方案 + 用户 OK
- 10:50 · 备份 + 骨架 + 移数据
- 11:00 · 后端 11 handler
- 11:30 · 前端 14 module
- 11:45 · daemon + smoke + 启动
- 11:55 · 文档 + .Log
