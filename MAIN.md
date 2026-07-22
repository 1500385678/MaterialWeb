# MAIN.md · 主程序 vs 支程序 · 边界声明

> **改之前先看这个**。明确告诉你哪些是"系统骨架"(改要谨慎),哪些是"业务模块"(可独立替换)。
> 参考 CanvasWeb-v2.5 框架。

---

## 0. 核心原则

**主程序 = 改之前要三思。**
**支程序 = 可独立替换 / 删 / 改,不影响主程序。**

判断标准:**改它会不会让整个项目"启动不起来"或"路由错乱"?**
- ✅ 会 → 主程序
- ❌ 不会 → 支程序

---

## 1. 主程序(改之前三思)

### 后端骨架 · 6 文件
```
server/__init__.py        v1.0.0 包标识 + 顶层 API 暴露
server/__main__.py        启动入口
server/config.py          路径/端口/常量(改 → 同步 scripts/daemon.py + docs/api_contract.md)
server/core.py            Flask app + DB 连接 + row 转换 + CORS
server/routes.py          路由表(加/移端点改这里)
db/init_schema.sql        表结构(改 → 同步 scripts/init_db.py 种子数据)
```

### 前端骨架 · 5 文件
```
client/index.html          主页入口 HTML
client/css/common.css      全部样式(整合)
client/js/main.js          入口(import + init)
client/js/api.js           所有 /api/* 封装(单一事实源)
client/js/core/state.js    全局状态(其他都 import 它)
```

---

## 2. 支程序(可独立替换 · 大胆改)

### 后端业务端点 · 11 文件
```
server/handlers/materials.py    材料 CRUD + search
server/handlers/categories.py   分类
server/handlers/suppliers.py    供应商
server/handlers/exam.py         考试知识
server/handlers/projects.py     项目 + 关联材料 + 造价 + docx
server/handlers/qr.py           二维码
server/handlers/media.py        媒体(图/CAD/uploads)
server/handlers/vision.py       AI 视觉分析 + 模型测试
server/handlers/search_by.py    关键词检索评分
server/handlers/schemes.py      方案 CRUD + reload
server/handlers/pdf_export.py   PDF 导出
```
> **删了某个** → 那个功能消失,其它不受影响
> **加新文件** → 在 `server/routes.py` import + `mod.register(app)` 一行

### 前端业务模块 · 11 文件
```
client/js/modules/tabs.js          tab 切换
client/js/modules/filters.js       分类/防火/造价 过滤
client/js/modules/materials.js     材料库
client/js/modules/projects.js      我的项目
client/js/modules/exam.js          考试学习
client/js/modules/ai-flow.js       AI 5 步流程
client/js/modules/ai-schemes.js    已保存方案
client/js/modules/model-settings.js  AI 模型设置
client/js/modules/qr-panel.js      二维码弹窗
client/js/modules/media.js         图片库 + CAD + 灯箱
client/js/modules/utils.js         通用工具
```

### 核心共享 · 3 文件
```
client/js/core/dom.js          DOM 工具 / el() / $() / debounce
client/js/core/events.js       极简事件总线 bus
client/js/core/toast.js        toast 提示
```

---

## 3. 辅助(改了不影响功能)

```
docs/         7 份文档 · 改了不影响代码
tests/        smoke + e2e
scripts/      daemon + start + init_db
data/         用户数据(uploads / qr_codes / media)
.Log/         变更日志
```

---

## 4. 模块依赖图(简化)

```
main.js  ─┬─→  api.js  ──→  /api/* (后端)
          ├─→  core/state.js  ← 共享状态
          ├─→  core/dom.js    ← DOM 工具
          ├─→  core/events.js ← 事件总线
          ├─→  core/toast.js  ← toast
          └─→  modules/*  (11 个支程序模块)

server/__main__.py  ─┬─→  routes.py  ──→  handlers/* (11 支程序)
                     ├─→  config.py  ──→  所有模块
                     ├─→  core.py    ← Flask app
                     └─→  db/materials.db  (SQLite)
```

**关键事实:**
- 主程序**不直接调用支程序的具体实现**,只通过 routes / import 间接
- 支程序**只能依赖主程序**,不能反向
- 模块间通过 `bus.emit` 通信,避免循环 import

---

## 5. 改前 1 句话自检

| 我想改... | 这是主/支? | 我要做 |
|---|---|---|
| 加一个 API 端点 | 支(handlers) | 写新 handler → `routes.py` 注册 → `docs/api_contract.md` 同步 |
| 加一个 UI 模块 | 支(modules) | 写新 module → `main.js` import + init |
| 改端口 / 路径 | **主** | 改 `config.py` + `scripts/daemon.py` |
| 改 BaseHandler | **主** | 改 `core.py` → 检查所有 handler 兼容 |
| 改字段 | **主** | 改 `init_schema.sql` → 备份 DB 后重灌 |
| 调样式 | 支(css) | 改 `common.css` |
| 改某模块逻辑 | 支(modules) | 改对应 module |

---

> 变更记录
> - 2026-07-13 · 初版 · 由 03_Architect 创建,从 MaterialDb+MaterialWeb 单文件重构
