"""AI 视觉分析 · /api/test_model + /api/analyze_image
支持自定义 OpenAI 兼容视觉模型,或 fallback 到 matrix MCP
"""
import base64
import json
import os
import re
import subprocess
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from flask import Blueprint, request, jsonify
from .. import config
from ..core import create_app  # noqa  (kept for future hooks)

bp = Blueprint('vision', __name__)

ANALYZE_PROMPT = """请仔细分析这张建筑相关图片,按以下 JSON 格式输出(**只输出 JSON**,不要其他文字,不要 markdown 标记):

{{
  "scene_description": "整体场景的简短中文描述",
  "context": "建筑场景判断(外墙/室内/景观/屋顶/幕墙/其他之一)",
  "style": "建筑风格(现代/极简/新中式/欧式/工业/其他之一)",
  "identified_materials": [
    {{
      "name": "材质名称(中文,2-6字)",
      "category_hint": "材质大类(金属/石材/木材/玻璃/混凝土/涂料/砖/陶瓷/其他之一)",
      "color": "颜色",
      "texture": "质感",
      "location_in_image": "位置",
      "confidence": 0.0 到 1.0 之间的浮点数
    }}
  ],
  "search_keywords": ["用于数据库搜索的中文关键词数组"]
}}

{user_context}

要求:
1. identified_materials 至少 1 个,最多 8 个,按重要程度排序
2. search_keywords 是去重后的中文关键词列表,3-10 个
3. 严格 JSON,不要 ``` 标记,不要解释
"""


def _allowed(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[-1].lower() in config.ALLOWED_EXTS


def _chat(api_url, api_key, model, messages, max_tokens=2000, timeout=120):
    url = api_url.rstrip('/')
    if not url.endswith('/chat/completions'):
        url = url + ('/v1/chat/completions' if '/v1' not in url else '/chat/completions')
    payload = {'model': model, 'messages': messages, 'max_tokens': max_tokens}
    headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {api_key}'}
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode('utf-8'),
        headers=headers, method='POST',
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = json.loads(resp.read().decode('utf-8'))
    return raw['choices'][0]['message']['content'], raw


def _openai_vision(api_url, api_key, model, image_path, prompt):
    with open(image_path, 'rb') as f:
        b64 = base64.b64encode(f.read()).decode('utf-8')
    ext = image_path.rsplit('.', 1)[-1].lower()
    mime = {'jpg': 'image/jpeg', 'jpeg': 'image/jpeg',
            'png': 'image/png', 'webp': 'image/webp', 'gif': 'image/gif'}.get(ext, 'image/png')
    messages = [{
        'role': 'user',
        'content': [
            {'type': 'text', 'text': prompt},
            {'type': 'image_url', 'image_url': {'url': f'data:{mime};base64,{b64}'}},
        ],
    }]
    return _chat(api_url, api_key, model, messages)[0]


@bp.post('/api/test_model')
def test_model():
    """测试视觉模型连通性(不传图)"""
    data = request.get_json() or {}
    api_url = (data.get('api_url') or '').strip()
    api_key = (data.get('api_key') or '').strip()
    model   = (data.get('model_name') or '').strip()
    if not (api_url and api_key and model):
        return jsonify({'ok': False, 'error': 'API URL、API Key、模型名都需填写'}), 400
    try:
        content, raw = _chat(
            api_url, api_key, model,
            messages=[{'role': 'user', 'content': 'reply with one word: pong'}],
            max_tokens=10, timeout=15,
        )
        return jsonify({
            'ok': True, 'message': '连接成功 ✓',
            'sample': (content or '').strip()[:80] or '(空响应)',
            'model': raw.get('model', model),
        })
    except urllib.error.HTTPError as e:
        body = ''
        try: body = e.read().decode('utf-8', errors='ignore')[:300]
        except: pass
        return jsonify({'ok': False, 'error': f'HTTP {e.code} {e.reason}', 'detail': body}), e.code
    except urllib.error.URLError as e:
        return jsonify({'ok': False, 'error': f'无法连接: {e.reason}'}), 502
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@bp.post('/api/analyze_image')
def analyze_image():
    """接收图片 + 可选上下文,返回结构化分析"""
    if 'image' not in request.files:
        return jsonify({'error': '未上传图片'}), 400
    f = request.files['image']
    if not f or not f.filename or not _allowed(f.filename):
        return jsonify({'error': f'仅支持 {", ".join(config.ALLOWED_EXTS)} 格式'}), 400

    # 1) 保存
    ext  = f.filename.rsplit('.', 1)[-1].lower()
    fname = f'ai_{uuid.uuid4().hex[:12]}.{ext}'
    config.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    fpath = config.UPLOAD_DIR / fname
    f.save(str(fpath))
    abs_path = str(fpath.resolve()).replace('\\', '/')

    # 2) 构造 prompt
    user_ctx_raw = (request.form.get('context') or '').strip()
    user_ctx = ''
    if user_ctx_raw:
        try:
            obj = json.loads(user_ctx_raw)
            lines = [f'- {k}: {v}' for k, v in obj.items() if v]
            if lines: user_ctx = '用户的额外上下文:\n' + '\n'.join(lines)
        except Exception:
            user_ctx = f'用户的额外上下文:{user_ctx_raw}'
    prompt = ANALYZE_PROMPT.format(user_context=user_ctx)

    # 3) 调模型
    custom_url   = (request.form.get('api_url') or '').strip()
    custom_key   = (request.form.get('api_key') or '').strip()
    custom_model = (request.form.get('model_name') or '').strip()
    use_custom   = bool(custom_url and custom_key and custom_model)
    engine       = '自定义' if use_custom else 'matrix MCP'

    try:
        if use_custom:
            try:
                stdout = _openai_vision(custom_url, custom_key, custom_model, abs_path, prompt)
            except urllib.error.HTTPError as e:
                body = ''
                try: body = e.read().decode('utf-8', errors='ignore')[:500]
                except: pass
                return jsonify({
                    'error': f'自定义模型 HTTP {e.code} {e.reason}', 'detail': body,
                }), e.code
        else:
            req_file = config.UPLOAD_DIR / f'_req_{uuid.uuid4().hex[:8]}.json'
            payload = {'image_info': [{'file': abs_path, 'prompt': prompt}]}
            req_file.write_text(
                json.dumps(payload, ensure_ascii=False), encoding='utf-8'
            )
            try:
                result = subprocess.run(
                    ['mavis', 'mcp', 'call', 'matrix', 'matrix_describe_images',
                     '--file', str(req_file)],
                    capture_output=True, text=True,
                    timeout=config.VISION_TIMEOUT, encoding='utf-8',
                )
                stdout = result.stdout or ''
            finally:
                try: req_file.unlink()
                except: pass

        # 解析 JSON
        m = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', stdout, re.DOTALL)
        if m:
            j = m.group(1)
        else:
            s, e = stdout.find('{'), stdout.rfind('}')
            j = stdout[s:e+1] if (s != -1 and e != -1 and e > s) else ''
        try:
            analysis = json.loads(j)
        except Exception as e:
            return jsonify({
                'error': f'{engine} 返回无法解析: {e}', 'raw': stdout[:2000],
            }), 500
    except Exception as e:
        return jsonify({'error': f'分析过程出错: {e}'}), 500

    # 4) 兜底字段
    analysis.setdefault('scene_description', '')
    analysis.setdefault('context', '其他')
    analysis.setdefault('style', '其他')
    if not isinstance(analysis.get('identified_materials'), list):
        analysis['identified_materials'] = []
    if not isinstance(analysis.get('search_keywords'), list):
        analysis['search_keywords'] = []

    return jsonify({
        'analysis': analysis,
        'image_url': f'/uploads/{fname}',
        'image_filename': fname,
        'engine': engine,
    })


def register(app): app.register_blueprint(bp)
