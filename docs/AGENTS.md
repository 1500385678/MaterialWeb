# docs/AGENTS.md · AI 协作者硬约束

> 给 AI agent 改这个项目必读。

---

## 1. 项目元信息

- **名称**: MaterialWeb v1.0 · 建筑材料数据库 + AI 选材
- **端口**: 8086(v0 = 5188 留对照)
- **数据**: SQLite `db/materials.db`
- **体量**: ~3700 行 · 35 个文件
- **依赖**: Flask + qrcode + reportlab(v1.0 偏离 v2.5 § 6.2 铁律)

---

## 2. 启动顺序(必读)

1. 读  · 主程序 vs 支程序
2. 读本文件 · 硬约束
3. 读  · 现有 API 端点
4. 跑 `python scripts/daemon.py` · 启动
5. 跑 `python tests/smoke.py` · 验证 8 端点

合计 20 分钟。

---

## 3. 铁律(违反就崩)

| # | 铁律 | 违反后果 |
|---|---|---|
| 1 | **单文件 ≤ 250 行** | 已超的标 v1.1 必拆 |
| 2 | **Python 允许 pip 依赖**(Flask + qrcode + reportlab) | v1.0 偏离 v2.5 铁律,v1.1 评估 stdlib 化 |
| 3 | **零 npm 依赖** | 任何 package.json 必先讨论 |
| 4 | **端口 8086** | 改 → 同步 config.py + daemon.py + 文档 |
| 5 | **API 路径只加不删** | 删字段会让 v0(5188)前端失效 |
| 6 | **API 响应字段只加不删,可以重命名** | 同上 |
| 7 | **HTML/CSS/JS 全部 no-store** | 否则 AI 改完不生效 |
| 8 | **写权限限本机 IP** | 其他 403 |
| 9 | **并发上限 20** | 超出 503 |
| 10 | **用 bus 跨模块,别直接 import 内部变量** | 循环依赖 |

---

## 4. 加新功能的标准流程

### 4.1 加一个 API 端点(支程序)

```
1. 在 server/handlers/ 下新建(或改)对应模块
   例:加一个 /api/foo/bar 端点
   → server/handlers/foo.py:bp.get('/api/foo/bar')(...)

2. 在 server/routes.py 加 import + register
   from .handlers import foo
   在 register_blueprints 内加 mod.register(app)

3. 在 client/js/api.js 加封装
   export const foo = { bar: () => req('/foo/bar') }

4. 在 docs/api_contract.md 同步端点列表

5. python tests/smoke.py 验证

6. 在 .Log/ 写一条日志
```

### 4.2 加一个 UI 模块(支程序)

```
1. 在 client/js/modules/ 下新建 .js
   例:加一个 "settings" 模块
   → client/js/modules/settings.js:export const settings = { init() {...} }

2. 在 client/js/main.js 加 import + 调用
   import { settings } from './modules/settings.js';
   async function init() {
     ...
     settings.init();
   }

3. 在 client/index.html 写对应 DOM
   <div id="settings-modal">...</div>

4. 跑 daemon + 浏览器硬刷(已 no-store)

5. 在 .Log/ 写一条日志
```

### 4.3 改主程序(改之前三思)

```
1. 先问:这个改动会让服务"启动不起来"或"路由错乱"吗?
   - 是 → 主程序 → 改前先看  § 5 自检表
   - 否 → 支程序 → 按 4.1 / 4.2 流程

2. 改主程序前:在 .Log/ 写"为什么改"和"风险评估"

3. 改完跑 smoke + 浏览器端到端验证

4. 同步更新  § 1 主程序清单
```

---

## 5. 命名规范

### 5.1 文件 / 目录
- 项目根:大写驼峰 `MaterialWeb-v1.0/`
- 源代码:小写 `server/`, `client/`, `handlers/`
- 模块:小写连字符 `ai-flow.js`, `qr-panel.js`
- 日志:`YYYY-MM-DD-干了什么.md`
- 文档:`docs/{README,AGENTS,api_contract,STYLE,CHEATSHEET,FILE_GUIDE,WORKFLOWS}.md`

### 5.2 Python
- 模块:`snake_case.py`
- 类:`PascalCase`
- 函数/变量:`snake_case`
- 常量:`UPPER_SNAKE_CASE`(在 config.py)
- Blueprint:`bp = Blueprint('name', __name__)`
- Handler 入口函数:`def register(app): app.register_blueprint(bp)`

### 5.3 JavaScript
- 模块导出:`export const name = {...}`(小写连字符对象)
- 事件名:`namespace:action`(如 `material:opened`, `bus.emit(...)`)
- DOM id:`kebab-case`(`#filter-category`)
- CSS class:`kebab-case`(`.ai-step`)

### 5.4 数据库
- 表名:`snake_case` 复数(`materials`, `project_materials`)
- 字段:`snake_case`
- 主键:`id`(INTEGER AUTOINCREMENT)
- 业务编码:`MAT_001`, `PRJ_0001`

---

## 6. 编码风格

- **Python**:PEP 8,函数 docstring 1 行
- **JS**:ESM + 箭头函数优先,`const` 默认,`let` 必要才用,无 `var`
- **SQL**:大写关键字(`SELECT`, `FROM`, `WHERE`)
- **注释**:WHY > WHAT,代码自己能解释的就不写注释
- **错误处理**:统一 `try/except` + `toast('错误信息', 'error')`

完整反 AI 味 + 命名 + 排版见 。

---

## 7. 变更日志规范

每次改完在 `.Log/YYYY-MM-DD-干了什么.md` 加一段,格式:
```markdown
## [模块名] 改了什么
- 文件:xxx.py / xxx.js
- 原因:为什么改
- 风险:影响范围
- 验证:跑 smoke / 浏览器测试
```

---

## 8. 关联文档

-  · 主程序 vs 支程序边界
-  · API 契约
-  · 写作风格
-  · 1 行速查
