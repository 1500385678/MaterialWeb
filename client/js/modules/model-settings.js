// modules/model-settings.js · AI 模型 API 设置(localStorage 持久化)
import { $, $$, el } from '../core/dom.js';
import { state, saveModel, hasModel } from '../core/state.js';
import { toast } from '../core/toast.js';
import { ai as api } from '../api.js';

const PRESETS = [
  { name: 'OpenAI',    url: 'https://api.openai.com' },
  { name: 'DeepSeek',  url: 'https://api.deepseek.com' },
  { name: 'Moonshot',  url: 'https://api.moonshot.cn' },
  { name: 'DashScope', url: 'https://dashscope.aliyuncs.com' },
];

export const modelSettings = {
  init() {
    // 渲染 preset 按钮
    const wrap = document.querySelector('.ms-presets');
    if (wrap) {
      wrap.innerHTML = '';
      PRESETS.forEach(p => {
        const s = el('span', { class: 'ms-preset', onclick: () => this.fillPreset(p.url) }, p.name);
        wrap.appendChild(s);
      });
    }
    // 填充当前值
    if (state.model.api_url)   $('#ms-api-url').value   = state.model.api_url;
    if (state.model.api_key)   $('#ms-api-key').value   = state.model.api_key;
    if (state.model.model_name)$('#ms-model-name').value = state.model.model_name;
  },

  fillPreset(url) { $('#ms-api-url').value = url; },

  open()  { $('#model-settings-modal').style.display = 'flex'; },
  close() { $('#model-settings-modal').style.display = 'none'; },

  refreshStatus() {
    const btn = $('#nav-model-btn');
    if (!btn) return;
    btn.classList.toggle('on', hasModel());
  },

  save() {
    const cfg = {
      api_url:    $('#ms-api-url').value.trim(),
      api_key:    $('#ms-api-key').value.trim(),
      model_name: $('#ms-model-name').value.trim(),
    };
    if (!cfg.api_url || !cfg.api_key || !cfg.model_name) {
      toast('三项都需填写', 'error'); return;
    }
    saveModel(cfg);
    toast('已保存 ✓', 'success');
    this.refreshStatus();
    this.close();
  },

  clear() {
    saveModel({});
    $('#ms-api-url').value = '';
    $('#ms-api-key').value = '';
    $('#ms-model-name').value = '';
    this.refreshStatus();
    toast('已清除,恢复默认 matrix MCP', 'success');
  },

  async test() {
    const cfg = {
      api_url:    $('#ms-api-url').value.trim(),
      api_key:    $('#ms-api-key').value.trim(),
      model_name: $('#ms-model-name').value.trim(),
    };
    if (!cfg.api_url || !cfg.api_key || !cfg.model_name) {
      toast('三项都需填写', 'error'); return;
    }
    const btn = $('#ms-test-btn');
    btn.disabled = true; btn.textContent = '测试中...';
    try {
      const r = await api.testModel(cfg);
      const s = $('#ms-status');
      s.className = 'ms-status on';
      s.innerHTML = `<span class="dot"></span><span>${r.message || '连接成功'}${r.sample ? ' · ' + r.sample : ''}</span>`;
      toast(r.message || '连接成功 ✓', 'success');
    } catch (e) {
      const s = $('#ms-status');
      s.className = 'ms-status err';
      s.innerHTML = `<span class="dot"></span><span>${e.message}</span>`;
    } finally {
      btn.disabled = false; btn.textContent = '测试连接';
    }
  },
};
window.modelSettings = modelSettings;
