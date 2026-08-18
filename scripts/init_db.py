#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""scripts/init_db.py · 5 行 wrapper,转调 scripts/init_db/__init__.py:main()

MaterialWeb v1.1 · 拆 scripts/init_db/{__init__,schema,seed}.py 后
保留 CLI 入口 `python scripts/init_db.py` 兼容
夜间迭代批 2 (01:00) 改 · P1 Verifier row 16
"""
# 关键:python scripts/init_db.py 运行时,Python 会把 scripts/ 加到 sys.path
# 所以这里用包名 'init_db' 即可,不要 'scripts.init_db'
from init_db import main

if __name__ == '__main__':
    main()
