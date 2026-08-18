"""检查 GitHub 是否需要重推"""
import subprocess
local = subprocess.run(['git', 'rev-parse', 'HEAD'], capture_output=True, text=True, encoding='utf-8').stdout.strip()
remote = subprocess.run(['git', 'ls-remote', 'origin', 'main'], capture_output=True, text=True, encoding='utf-8').stdout.strip()
print(f'Local HEAD:  {local}')
print(f'Remote main: {remote or "FAILED"}')
print(f'In sync:     {local == remote[:40] if remote else False}')
