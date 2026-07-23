"""MaterialWeb v1.0 启动器 · 清旧进程 + 端口健康检查 + detached 启动
用法:
  python scripts/daemon.py            # 后台启动(关窗口不退出)
  python scripts/daemon.py foreground # 前台启动(调试)
被谁调用:人工 / start.ps1
"""
import os
import sys
import subprocess
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent.parent.resolve()  # MaterialWeb-v1.0 根
PORT = 8093
HOST = '127.0.0.1'


def kill_old():
    """清掉占着 PORT 的旧 python 进程(只杀本项目的)"""
    if sys.platform == 'win32':
        try:
            out = subprocess.check_output(
                ['netstat', '-ano', '-p', 'TCP'],
                encoding='gbk', errors='ignore',
            )
            for line in out.splitlines():
                if f':{PORT}' in line and 'LISTENING' in line:
                    pid = line.strip().split()[-1]
                    if pid.isdigit():
                        print(f'[daemon] 杀掉占着 {PORT} 的 PID={pid}', flush=True)
                        subprocess.run(['taskkill', '/F', '/PID', pid],
                                       capture_output=True)
        except Exception as e:
            print(f'[daemon] 端口检查失败: {e}', flush=True)
    else:
        try:
            out = subprocess.check_output(['lsof', '-ti', f':{PORT}'], encoding='utf-8')
            for pid in out.strip().splitlines():
                print(f'[daemon] 杀掉占着 {PORT} 的 PID={pid}', flush=True)
                subprocess.run(['kill', '-9', pid], capture_output=True)
        except Exception:
            pass


def wait_ready(timeout=15):
    """等 /api/categories 返回 200"""
    url = f'http://{HOST}:{PORT}/api/categories'
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as r:
                if r.status == 200:
                    return True
        except Exception:
            time.sleep(0.3)
    return False


def start_detached():
    """detached 后台启动"""
    if sys.platform == 'win32':
        DETACHED_PROCESS = 0x00000008
        CREATE_NEW_PROCESS_GROUP = 0x00000200
        flags = DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
        log_out = open(ROOT / 'server.out', 'a', encoding='utf-8')
        log_err = open(ROOT / 'server.err', 'a', encoding='utf-8')
        subprocess.Popen(
            [sys.executable, '-X', 'utf8', '-u', '-m', 'server'],
            cwd=str(ROOT),
            stdout=log_out, stderr=log_err,
            creationflags=flags,
            close_fds=True,
        )
    else:
        log_out = open(ROOT / 'server.out', 'a', encoding='utf-8')
        log_err = open(ROOT / 'server.err', 'a', encoding='utf-8')
        subprocess.Popen(
            [sys.executable, '-u', '-m', 'server'],
            cwd=str(ROOT),
            stdout=log_out, stderr=log_err,
            start_new_session=True,
        )


def main():
    if 'foreground' in sys.argv:
        print('[daemon] 前台模式启动', flush=True)
        os.chdir(ROOT)
        from server import __main__ as _  # noqa
        return

    print(f'[daemon] 端口 {PORT} · 清旧进程', flush=True)
    kill_old()
    print(f'[daemon] 启动 MaterialWeb-v1.0 (detached)', flush=True)
    start_detached()
    if wait_ready(15):
        print(f'[daemon] OK · http://{HOST}:{PORT}/', flush=True)
    else:
        print(f'[daemon] 启动超时 · 看 server.err', flush=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
