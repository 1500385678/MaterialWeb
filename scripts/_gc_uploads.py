#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""scripts/_gc_uploads.py · 上传目录回收器

MaterialWeb v1.1 · P2 Verifier row 18 改
夜间迭代批 2 (01:00)

清理目标(config.UPLOAD_DIR):
  1. _req_*.json  — matrix MCP 请求临时文件,7 天前 mtime 即删
  2. ai_*.{jpg,png,...}  — 失败上传遗留图,analyze_image finally 已处理;
     此处兜底清 7 天前 mtime 的孤儿(analyze_image 漏掉的,如 daemon 强杀)

设计:幂等可重入,可放 cron(每天 03:00 跑);也可手动 `python scripts/_gc_uploads.py`
退出码:
  0  正常
  1  配置错误(UPLOAD_DIR 不存在)
  2  部分文件 unlink 失败(继续清理,汇总打印)
"""
import argparse
import os
import sys
import time
from pathlib import Path

# 项目根 → config.UPLOAD_DIR
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from server import config  # noqa: E402


def _scan_and_clean(upload_dir: Path, days: int, dry_run: bool = False) -> tuple:
    """扫描 upload_dir,删 mtime > days 天的临时文件(_req_*.json + ai_*.img)

    返回 (deleted_count, failed_count, total_size_bytes)
    """
    if not upload_dir.exists():
        print(f'[ERR] UPLOAD_DIR 不存在: {upload_dir}', file=sys.stderr)
        return 0, 0, 0

    cutoff = time.time() - days * 86400
    deleted = 0
    failed  = 0
    total_sz = 0
    patterns = ('_req_*.json', 'ai_*.jpg', 'ai_*.jpeg', 'ai_*.png', 'ai_*.webp')

    for pat in patterns:
        for fp in upload_dir.glob(pat):
            try:
                mtime = fp.stat().st_mtime
            except OSError as exc:
                print(f'  [!] stat 失败 {fp.name}: {exc}', file=sys.stderr)
                failed += 1
                continue
            if mtime > cutoff:
                continue  # 还没到保留期
            size = fp.stat().st_size
            if dry_run:
                print(f'  [dry-run] {fp.name} ({size}B, mtime={time.strftime("%Y-%m-%d", time.localtime(mtime))})')
                deleted += 1
                total_sz += size
                continue
            try:
                fp.unlink()
                deleted += 1
                total_sz += size
                print(f'  [ok] {fp.name} ({size}B)')
            except OSError as exc:
                print(f'  [!] unlink 失败 {fp.name}: {exc}', file=sys.stderr)
                failed += 1

    return deleted, failed, total_sz


def main():
    ap = argparse.ArgumentParser(
        description='MaterialWeb uploads/ 临时文件回收器 · 删 7 天前 _req_*.json / ai_*.img'
    )
    ap.add_argument('--days', type=int, default=7, help='保留天数(默认 7)')
    ap.add_argument('--dry-run', action='store_true', help='只列不删')
    ap.add_argument('--upload-dir', type=Path, default=None,
                    help=f'上传目录路径(默认走 config.UPLOAD_DIR = {config.UPLOAD_DIR})')
    args = ap.parse_args()

    upload_dir = args.upload_dir or config.UPLOAD_DIR
    print(f'UPLOAD_DIR = {upload_dir}')
    print(f'保留天数   = {args.days}')
    print(f'dry-run    = {args.dry_run}')
    print('---')

    deleted, failed, total_sz = _scan_and_clean(
        upload_dir, args.days, dry_run=args.dry_run
    )
    print('---')
    print(f'删除: {deleted} 个,共 {total_sz:,} 字节 ({total_sz/1024:.1f} KB)')
    if failed:
        print(f'失败: {failed} 个', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
