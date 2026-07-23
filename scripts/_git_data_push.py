"""
_git_data_push.py · 走 GitHub Git Data API 推 commit(绕过 git 协议)
场景:github.com 端口 443 不可达但 api.github.com 可达时,用这个推 commit
用法:python scripts\_git_data_push.py "commit message" [files...]
     不传 files 则推所有 git status --porcelain 列出的文件
依赖:GH_TOKEN (User-scope 环境变量)
"""
import base64
import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent.parent.resolve()
TOKEN = os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')
if not TOKEN:
    # 读 User-scope env (Windows)
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Environment') as key:
            TOKEN, _ = winreg.QueryValueEx(key, 'GH_TOKEN')
    except Exception:
        pass
if not TOKEN:
    print('ERR: GH_TOKEN not set', file=sys.stderr); sys.exit(1)

# 仓库推导
remote = subprocess.check_output(['git', 'remote', 'get-url', 'origin'], cwd=ROOT, encoding='utf-8').strip()
if 'github.com' not in remote:
    print(f'ERR: origin is not github: {remote}', file=sys.stderr); sys.exit(1)
# 解析 owner/repo (兼容 https://...git  和 git@github.com:...git)
if remote.startswith('git@'):
    _, _, tail = remote.partition(':')
    owner_repo = tail.rstrip('.git')
else:
    owner_repo = remote.rsplit('github.com/', 1)[-1].rstrip('.git')
owner, repo = owner_repo.split('/')

API = f'https://api.github.com/repos/{owner}/{repo}'
HDR = {'Authorization': f'Bearer {TOKEN}', 'Accept': 'application/vnd.github+json', 'User-Agent': 'MaterialWebArchitect'}


def req(method, path, body=None):
    url = f'{API}{path}'
    data = json.dumps(body).encode('utf-8') if body is not None else None
    r = urllib.request.Request(url, data=data, method=method, headers={**HDR, 'Content-Type': 'application/json'} if data else HDR)
    try:
        with urllib.request.urlopen(r, timeout=30) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='ignore')
        print(f'ERR {method} {url}\n  status={e.code}\n  body={body[:500]}', file=sys.stderr); sys.exit(1)


def get_ref():
    return req('GET', '/git/refs/heads/main')


def get_commit(sha):
    return req('GET', f'/git/commits/{sha}')


def create_blob(content_bytes):
    return req('POST', '/git/blobs', {'content': base64.b64encode(content_bytes).decode('ascii'), 'encoding': 'base64'})


def create_tree(base_tree_sha, entries):
    return req('POST', '/git/trees', {
        'base_tree': base_tree_sha,
        'tree': entries,
    })


def create_commit(message, tree_sha, parent_sha):
    return req('POST', '/git/commits', {
        'message': message, 'tree': tree_sha, 'parents': [parent_sha],
    })


def update_ref(sha):
    return req('PATCH', '/git/refs/heads/main', {'sha': sha, 'force': False})


def list_changed_files():
    """git diff --name-only HEAD + untracked (in repo)"""
    out = subprocess.check_output(['git', 'diff', '--name-only', 'HEAD'], cwd=ROOT, encoding='utf-8')
    files = [l for l in out.splitlines() if l]
    # untracked
    out2 = subprocess.check_output(['git', 'ls-files', '--others', '--exclude-standard'], cwd=ROOT, encoding='utf-8')
    files += [l for l in out2.splitlines() if l]
    return sorted(set(files))


def main():
    msg = sys.argv[1] if len(sys.argv) > 1 else 'auto: update via Git Data API'
    args_files = sys.argv[2:]
    if args_files:
        files = args_files
    else:
        files = list_changed_files()
    if not files:
        print('无改动,跳过'); return

    print(f'[git_data_push] owner={owner} repo={repo} files={len(files)}')

    # 1. base ref
    ref = get_ref()
    base_sha = ref['object']['sha']
    print(f'[git_data_push] base_sha={base_sha[:7]}')

    # 2. base tree
    base_commit = get_commit(base_sha)
    base_tree = base_commit['tree']['sha']

    # 3. blobs
    entries = []
    for rel in files:
        p = ROOT / rel
        if not p.exists():
            print(f'  skip (not exist): {rel}'); continue
        if p.is_dir():
            continue
        content = p.read_bytes()
        blob = create_blob(content)
        entries.append({
            'path': rel.replace('\\', '/'),
            'mode': '100644',
            'type': 'blob',
            'sha': blob['sha'],
        })
        print(f'  blob: {rel} ({len(content)} bytes)')

    if not entries:
        print('no valid files to push'); return

    # 4. tree
    tree = create_tree(base_tree, entries)
    print(f'[git_data_push] tree_sha={tree["sha"][:7]}')

    # 5. commit
    commit = create_commit(msg, tree['sha'], base_sha)
    print(f'[git_data_push] commit_sha={commit["sha"][:7]}')

    # 6. update ref
    update_ref(commit['sha'])
    print(f'[git_data_push] OK · {commit["sha"]} pushed to main')


if __name__ == '__main__':
    main()
