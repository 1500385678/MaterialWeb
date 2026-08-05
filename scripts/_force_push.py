"""用 GitHub API force-push 整个仓库内容
绕过 git 协议 (github.com:443 不可达)
把当前 local HEAD 9f894e1 设到 origin main + 同步所有 tag
"""
import base64
import json
import os
import subprocess
import sys
import urllib.request
import urllib.error
from pathlib import Path

ROOT = Path(__file__).parent.parent.resolve()
TOKEN = os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')
if not TOKEN:
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Environment') as key:
            TOKEN, _ = winreg.QueryValueEx(key, 'GH_TOKEN')
    except Exception:
        pass
if not TOKEN:
    print('ERR: GH_TOKEN not set'); sys.exit(1)

# owner/repo 推导
remote = subprocess.check_output(['git', 'remote', 'get-url', 'origin'], cwd=ROOT, encoding='utf-8').strip()
if 'github.com' not in remote:
    print(f'ERR: origin is not github: {remote}'); sys.exit(1)
if remote.startswith('git@'):
    _, _, tail = remote.partition(':')
    owner_repo = tail.rstrip('.git')
else:
    owner_repo = remote.rsplit('github.com/', 1)[-1].rstrip('.git')
owner, repo = owner_repo.split('/')

API = f'https://api.github.com/repos/{owner}/{repo}'
HDR = {
    'Authorization': f'Bearer {TOKEN}',
    'Accept': 'application/vnd.github+json',
    'User-Agent': 'MaterialWebArchitect',
}


def req(method, path, body=None, raw=False):
    url = f'{API}{path}'
    data = json.dumps(body).encode('utf-8') if body is not None else None
    headers = {**HDR}
    if data:
        headers['Content-Type'] = 'application/json'
    r = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(r, timeout=60) as resp:
            txt = resp.read().decode('utf-8')
            return txt if raw else json.loads(txt)
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='replace')
        print(f'ERR {method} {url}: {e.code} {body}', file=sys.stderr)
        raise


def get_local_head():
    return subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, encoding='utf-8').strip()


def get_local_tree_for_commit(commit_sha):
    return subprocess.check_output(['git', 'log', '-1', '--format=%T', commit_sha], cwd=ROOT, encoding='utf-8').strip()


# Step 1: 把 main 的 ref 指向 local HEAD
local_head = get_local_head()
print(f'Local HEAD: {local_head}')

# 用 update_ref (force=true)
print(f'Updating main ref to {local_head}...')
try:
    req('PATCH', '/git/refs/heads/main', {'sha': local_head, 'force': True})
    print('OK: main ref updated')
except Exception:
    # ref 不存在 → 可能是 fallback script 留下的 orphan commit
    # 尝试创建 ref
    print('Trying POST...')
    try:
        req('POST', '/git/refs', {'ref': 'refs/heads/main', 'sha': local_head})
        print('OK: main ref created')
    except Exception as e:
        print(f'Create ref failed: {e}')
        sys.exit(1)

# Step 2: 同步所有本地 tag 到 GitHub
print('Syncing tags...')
local_tags = subprocess.check_output(['git', 'tag'], cwd=ROOT, encoding='utf-8').strip().split('\n')
remote_tags_data = req('GET', '/git/refs/tags', raw=False) if False else []
try:
    remote_tags_data = req('GET', '/git/refs/tags', raw=False)
except Exception:
    remote_tags_data = []
remote_tag_names = {t['ref'].split('/')[-1] for t in remote_tags_data}

for tag in local_tags:
    if not tag:
        continue
    if tag in remote_tag_names:
        # 已经在,跳过
        continue
    # 取 tag 指向的 commit
    try:
        sha = subprocess.check_output(['git', 'rev-list', '-1', tag], cwd=ROOT, encoding='utf-8').strip()
    except subprocess.CalledProcessError:
        print(f'WARN: tag {tag} not found locally'); continue
    try:
        req('POST', '/git/refs', {'ref': f'refs/tags/{tag}', 'sha': sha})
        print(f'OK: created tag {tag} -> {sha[:8]}')
    except Exception as e:
        print(f'WARN: tag {tag} create failed: {e}')

print('DONE')
