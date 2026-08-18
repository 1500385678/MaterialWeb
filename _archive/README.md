# _archive/ 根目录旧 monolith 归档

**生成时间**: 2026-08-09 01:00 · 夜间迭代批 2 (01:00)
**触发**: materialweb-coder · Verifier P1 意见 #4

## 7 个旧 monolith 移到此处

| 旧路径(根目录) | 替代路径(当前激活) | 备注 |
|---|---|---|
| `export_materials.py` | `scripts/seed_materials.py` | 旧 `D:\Mac\...` 硬编码路径,Win 时代残留 |
| `generate_template.py` | `_MaterialDb/generate_template.py` | 模板定义同源,迁到子仓 |
| `init_db.py` | `scripts/init_db.py` | 同一作者,旧版本(12.7KB → 13.3KB) |
| `init_schema.sql` | `db/init_schema.sql` | 表结构单点真源已迁到 `db/` |
| `materials.db` | `db/materials.db` | 数据文件已迁到 `db/`(`.gitignore`) |
| `requirements.txt` | (无 · 见 CONTROL.md 铁律:仅 flask/qrcode/reportlab) | 旧版没维护,直接 `pip install` |
| `verify_db.py` | (无 · 用 `tests/smoke.py` + `server/config.py` 健康检查) | 旧 `D:\Mac\...` 硬编码,Win 时代残留 |

## 原则

- **当前激活代码不引用此处任何文件** —— 已 `grep -rn` 验证零引用(除本身说明外)
- **保留可追溯**: 旧 `D:\Mac\...` 硬编码路径是 Win v1.0 时代的遗产,留作版本考古
- **不动 git 历史**: `git mv` 保留 blame 链,后续如需彻底删,可走 `git rm` 二次清理

## 关联

- `MAIN.md` 铁律: 根目录仅放 README/CONTROL/MAIN/_archive/_MaterialDb/client/data/db/docs/media/qr_codes/scripts/server/tests/uploads/.gitignore
- `CONTROL.md` §0 30 秒定位: 工作目录标准布局
- `db/init_schema.sql` 注释第 126 行: 字段迁移单点真源
