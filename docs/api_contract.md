# docs/api_contract.md · API 契约(所有端点)

> 改 API 必读 · 加端点同步本文件 · 减端点会破 v0(5188)前端,禁!

---

## 0. 基础

- **Base URL**: `http://127.0.0.1:8086`
- **前缀**: `/api/`
- **Content-Type**: `application/json`(multipart 除外)
- **响应格式**: `JSON`
- **错误**: `{"error": "msg"}` + 4xx/5xx 状态码
- **CORS**: `*`(本地开发用)
- **静态防缓存**: HTML/CSS/JS 全部 no-store

---

## 1. materials(材料)

### `GET /api/materials`
列表,支持过滤。

| Query | 说明 | 示例 |
|---|---|---|
| `category`    | 分类 code(前缀匹配) | `stone` |
| `fire_rating` | 防火等级 | `A1` / `B1` / `B2` |
| `cost_tier`   | 造价档 | `低` / `中` / `高` |
| `keyword`     | 关键词(中英文) | `花岗岩` |

### `GET /api/materials/search?q=<kw>`
关键词搜索,limit 50。

### `GET /api/materials/<id>`
详情(自动补 suppliers 列表)。

### `GET /api/materials/<id>/qr`
返回二维码 PNG(`mavis://material/<code>` 协议)。

---

## 2. categories(分类)

### `GET /api/categories`
全部分类(平铺,parent_code 关系自建树)。返 `{items: [...], count: N}`。

---

## 3. suppliers(供应商)

### `GET /api/suppliers`
全部供应商。返 `{items: [...], count: N}`。

---

## 4. exam(考试知识)

### `GET /api/exam`
全部知识点(按 chapter, section 排序)。返 `{items: [...], count: N}`。

### `GET /api/exam/chapter/<chapter>`
按章节取(如 `4.1`)。返 `{items: [...], count: N}`。

---

## 5. projects(项目)

### `GET /api/projects`
项目列表(按 created_at DESC)。返 `{items: [...], count: N}`。

### `POST /api/projects`
创建项目。

**Body**: `{name, type, area}`
**返**: `{id, code}`(201)

### `GET /api/projects/<id>`
项目详情(自动含 materials + total_cost)。

### `POST /api/projects/<id>/materials`
向项目添加材料。

**Body**: `{material_id, quantity, location, unit_cost?}`
**返**: `{id}`(201)

### `DELETE /api/projects/<id>/materials/<pm_id>`
移除项目材料。返 `{ok: true}`。

### `GET /api/projects/<id>/cost-summary`
造价汇总(按 category + unit 分组)。

**返**: `{items, grand_total, area, cost_per_sqm}`

### `GET /api/projects/<id>/export/docx`
返回项目结构化数据(供前端生成 docx;v1.0 是 JSON,后续接 docx 库)。

---

## 6. media(媒体)

### `GET /api/media/images/<file>`
材料配图。

### `GET /api/media/cad/<file>`
CAD 文件下载(DWG/SKP/PDF/DXF,as_attachment)。

### `GET /uploads/<file>`
AI 上传的图片(供前端预览)。

### `GET /api/media/list/<material_id>`
列出某材料的全部媒体文件。

**返**: `{images: [...], cad_files: [...]}`

---

## 7. AI 视觉

### `POST /api/test_model`
测试 OpenAI 兼容视觉模型连通性(不传图)。

**Body**: `{api_url, api_key, model_name}`
**返**: `{ok: bool, message?, sample?, model?, error?, detail?}`

### `POST /api/analyze_image`
接收图片 + 可选上下文,返回结构化分析。

**Multipart**:
- `image`: 文件(必)
- `context`: JSON 字符串(选)
- `api_url` / `api_key` / `model_name`: 自定义模型(选)

**返**:
```json
{
  "analysis": {
    "scene_description": "...",
    "context": "外墙",
    "style": "现代",
    "identified_materials": [
      {"name": "...", "category_hint": "...", "color": "...",
       "texture": "...", "location_in_image": "...", "confidence": 0.9}
    ],
    "search_keywords": ["石材", "幕墙", ...]
  },
  "image_url": "/uploads/ai_xxx.jpg",
  "image_filename": "ai_xxx.jpg",
  "engine": "matrix MCP" / "自定义"
}
```

---

## 8. AI 检索

### `POST /api/search_by_analysis`
按视觉分析结果,在 materials 表里多字段打分排序。

**Body**: `{identified_materials?, search_keywords?, filters?}`
- `filters`: `{cost_tier?, fire_rating?, category_id?}`

**返**: `{count, items: [...], query_keywords: [...]}`
- 每项含 `score`, `matched_fields`, `matched_keywords`

---

## 9. schemes(方案)

### `POST /api/save_scheme`
保存选材方案(含 AI 会话上下文)。

**Body**:
```json
{
  "name": "...",
  "description": "...",
  "project_id": 1,
  "materials": [
    {"material_id": 1, "score": 8.5, "score_reason": "name_cn", "is_selected": 1}
  ],
  "image_filename": "ai_xxx.jpg",
  "analysis": {...},
  "search_results": [...],
  "selected_ids": [1, 2, 3]
}
```

**返**: `{scheme_id, name, material_count, image_url}`

### `GET /api/schemes`
方案列表(按 updated_at DESC)。返 `{count, items}`。

### `GET /api/schemes/<id>`
方案详情(含 materials + session 上下文)。

### `DELETE /api/schemes/<id>`
删除方案。返 `{deleted, image_filename}`。

### `GET /api/schemes/<id>/reload`
返回会话状态(分析 + 搜索结果 + 选中),供前端跳到 AI 流程任意步。

### `GET /api/schemes/<id>/export/pdf`
导出 PDF(中文 + 缩略图 + 命中详情)。

---

## 10. 错误码

| 状态 | 含义 |
|---|---|
| 200 | OK |
| 201 | Created |
| 400 | 参数错 |
| 404 | 不存在 |
| 500 | 服务端错 |
| 502 | 上游不通(AI 模型) |
| 503 | 并发超限 |
| 504 | 超时 |

---

## 11. 字段命名规范

- 全 `snake_case`
- 数组字段后缀 `_json`(`suppliers_json`, `applications_json`)
- 时间字段:`created_at`, `updated_at`(TEXT, `datetime('now', 'localtime')`)

---

## 12. 关联文档

-  · 主程序 vs 支程序
-  · AI 协作者硬约束
