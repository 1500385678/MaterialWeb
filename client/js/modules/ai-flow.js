// modules/ai-flow.js · AI 选材 5 步流程
// 1 上传图 → 2 分析中 → 3 确认信息 → 4 选材料 → 5 保存方案
import { $, el } from '../core/dom.js';
import { state, hasModel } from '../core/state.js';
import { toast } from '../core/toast.js';
import { ai as api } from '../api.js';
import { utils } from './utils.js';

export const aiFlow = {
  init() {
    // Step 1 — 上传
    $('#ai-file-input')?.addEventListener('change', e => this.onFile(e));
    const dropZone = $('#ai-upload-area');
    if (dropZone) {
      dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.style.borderColor = 'var(--primary)'; });
      dropZone.addEventListener('dragleave', () => dropZone.style.borderColor = '');
      dropZone.addEventListener('drop', e => {
        e.preventDefault();
        dropZone.style.borderColor = '';
        if (e.dataTransfer.files[0]) this.setFile(e.dataTransfer.files[0]);
      });
    }
    // 上下文输入
    ['ai-ctx-type', 'ai-ctx-location', 'ai-ctx-cost', 'ai-ctx-style'].forEach(id => {
      $('#' + id)?.addEventListener('change', () => this.collectCtx());
    });
    $('#ai-ctx-note')?.addEventListener('input', () => this.collectCtx());
  },

  collectCtx() {
    state.ai.context = {
      type:     $('#ai-ctx-type')?.value || '',
      location: $('#ai-ctx-location')?.value || '',
      cost:     $('#ai-ctx-cost')?.value || '',
      style:    $('#ai-ctx-style')?.value || '',
      note:     $('#ai-ctx-note')?.value || '',
    };
  },

  setFile(f) {
    if (!f.type.startsWith('image/')) { toast('请选择图片文件', 'error'); return; }
    state.ai.file = f;
    if (state.ai.previewUrl) URL.revokeObjectURL(state.ai.previewUrl);
    state.ai.previewUrl = URL.createObjectURL(f);
    const wrap = $('#ai-preview-wrap');
    wrap.innerHTML = `<div style="text-align:center;margin-top:14px;">
      <img src="${state.ai.previewUrl}" style="max-width:300px;max-height:200px;border-radius:6px;"/>
      <p style="margin-top:8px;font-size:13px;color:var(--text-muted);">${f.name} · ${(f.size/1024).toFixed(0)}KB</p>
    </div>`;
    wrap.style.display = 'block';
    const btn = $('#ai-start-btn');
    if (btn) btn.disabled = false;
  },

  onFile(e) { if (e.target.files[0]) this.setFile(e.target.files[0]); },

  gotoStep(n) {
    state.ai.step = n;
    document.querySelectorAll('.ai-step').forEach(s =>
      s.classList.toggle('active', parseInt(s.dataset.step) <= n));
    for (let i = 1; i <= 5; i++) {
      const p = $('#ai-step-' + i + '-panel');
      if (p) p.style.display = (i === n ? 'block' : 'none');
    }
  },

  async startAnalysis() {
    if (!state.ai.file) { toast('请先选择图片', 'error'); return; }
    if (!hasModel()) toast('提示:未配置自定义模型,使用系统默认 matrix MCP', 'success');
    this.gotoStep(2);
    try {
      const fd = new FormData();
      fd.append('image', state.ai.file);
      this.collectCtx();
      const ctxClean = Object.fromEntries(Object.entries(state.ai.context).filter(([_, v]) => v));
      fd.append('context', JSON.stringify(ctxClean));
      if (hasModel()) {
        fd.append('api_url',   state.model.api_url);
        fd.append('api_key',   state.model.api_key);
        fd.append('model_name', state.model.model_name);
      }
      const r = await api.analyze(fd);
      state.ai.analysis       = r.analysis;
      state.ai.imageUrl       = r.image_url;
      state.ai.imageFilename  = r.image_filename;
      state.ai.materials      = JSON.parse(JSON.stringify(r.analysis.identified_materials || []));
      state.ai.keywords       = [...(r.analysis.search_keywords || [])];
      this.renderConfirm();
      this.gotoStep(3);
    } catch (e) {
      toast('分析失败: ' + e.message, 'error');
      this.gotoStep(1);
    }
  },

  renderConfirm() {
    const a = state.ai.analysis;
    $('#ai-confirm-image').innerHTML = state.ai.imageUrl
      ? `<img src="${state.ai.imageUrl}" style="max-width:240px;max-height:180px;border-radius:6px;"/>`
      : '';
    $('#ai-confirm-desc').value   = a.scene_description || '';
    $('#ai-confirm-context').value = a.context || '';
    $('#ai-confirm-style').value   = a.style || '';
    $('#ai-confirm-keywords').value = state.ai.keywords.join(', ');
    this.renderChips();
  },

  renderChips() {
    const root = $('#ai-mat-chips');
    if (!root) return;
    root.innerHTML = '';
    state.ai.materials.forEach((m, idx) => {
      const chip = el('div', { class: 'ai-mat-chip' }, [
        el('input', { type: 'text', value: m.name || '', oninput: e => { m.name = e.target.value; } }),
        el('select', { onchange: e => { m.category_hint = e.target.value; } },
          ['金属', '石材', '木材', '玻璃', '混凝土', '涂料', '砖', '陶瓷', '其他']
            .map(c => el('option', { value: c, selected: m.category_hint === c }, c))),
        el('input', { type: 'text', value: m.color || '', placeholder: '颜色', oninput: e => { m.color = e.target.value; } }),
        el('input', { type: 'text', value: m.texture || '', placeholder: '质感', oninput: e => { m.texture = e.target.value; } }),
        el('button', { onclick: () => { state.ai.materials.splice(idx, 1); this.renderChips(); } }, '删'),
      ]);
      root.appendChild(chip);
    });
  },

  addChip() {
    state.ai.materials.push({ name: '', category_hint: '其他', color: '', texture: '', confidence: 0.5 });
    this.renderChips();
  },

  async searchMaterials() {
    state.ai.keywords = $('#ai-confirm-keywords').value.split(/[,，\s]+/).filter(Boolean);
    if (!state.ai.materials.length && !state.ai.keywords.length) {
      toast('请至少识别一个材质或填写关键词', 'error'); return;
    }
    this.gotoStep(4);
    const r = await api.searchBy({
      identified_materials: state.ai.materials,
      search_keywords:      state.ai.keywords,
    });
    state.ai.searchResults = r.items || [];
    state.ai.selectedIds.clear();
    this.renderResults();
  },

  renderResults() {
    const root = $('#ai-results-list');
    $('#ai-result-summary').textContent = `共 ${state.ai.searchResults.length} 个匹配`;
    if (!state.ai.searchResults.length) {
      root.innerHTML = '<div class="empty"><div class="empty-icon">🔍</div><p>没找到匹配材料,改关键词再试。</p></div>';
      $('#ai-selected-count').textContent = '0';
      return;
    }
    root.innerHTML = '';
    state.ai.searchResults.forEach(m => {
      const div = el('div', { class: 'ai-result' + (state.ai.selectedIds.has(m.id) ? ' selected' : '') }, [
        el('div', { class: 'ai-result-info' }, [
          el('h4', {}, `${m.name_cn} (${m.code})`),
          el('p', {}, `${m.category_name || ''} · ¥${m.unit_price || 0}/${m.unit || 'm²'} · 匹配 ${m.matched_keywords.join('/') || '—'}`),
        ]),
        el('div', { class: 'ai-result-score' }, m.score),
      ]);
      div.addEventListener('click', () => {
        if (state.ai.selectedIds.has(m.id)) state.ai.selectedIds.delete(m.id);
        else state.ai.selectedIds.add(m.id);
        div.classList.toggle('selected');
        $('#ai-selected-count').textContent = state.ai.selectedIds.size;
      });
      root.appendChild(div);
    });
    $('#ai-selected-count').textContent = state.ai.selectedIds.size;
  },

  gotoSave() {
    if (state.ai.selectedIds.size === 0) { toast('请至少选一个材料', 'error'); return; }
    this.gotoStep(5);
    const sel = $('#ai-scheme-project');
    if (sel) {
      sel.innerHTML = '<option value="">不关联</option>' +
        (window.state?.projects || []).map(p => `<option value="${p.id}">${p.code} · ${p.name}</option>`).join('');
    }
    const list = $('#ai-save-list');
    const chosen = state.ai.searchResults.filter(m => state.ai.selectedIds.has(m.id));
    list.innerHTML = chosen.map(m => `<div>· ${m.name_cn} (¥${m.unit_price}/${m.unit || 'm²'})</div>`).join('');
    $('#ai-save-count').textContent = chosen.length;
  },

  async saveScheme() {
    const name = $('#ai-scheme-name').value.trim() || `AI方案-${utils.nowStr()}`;
    const desc = $('#ai-scheme-desc').value.trim();
    const project_id = parseInt($('#ai-scheme-project').value) || null;
    const chosen = state.ai.searchResults
      .filter(m => state.ai.selectedIds.has(m.id))
      .map(m => ({
        material_id:  m.id,
        score:        m.score,
        score_reason: (m.matched_fields || []).join(', '),
        is_selected:  1,
      }));
    if (!chosen.length) { toast('没选材料', 'error'); return; }
    try {
      const r = await api.saveScheme({
        name, description: desc, project_id,
        materials:       chosen,
        image_filename:  state.ai.imageFilename,
        analysis:        state.ai.analysis,
        search_results:  state.ai.searchResults,
        selected_ids:    [...state.ai.selectedIds],
      });
      toast(`方案已保存 #${r.scheme_id}`, 'success');
      setTimeout(() => { this.reset(); utils.tabs?.switch?.('materials'); }, 1500);
    } catch (e) { toast('保存失败: ' + e.message, 'error'); }
  },

  reset() {
    state.ai = {
      step: 1, file: null, previewUrl: '', imageFilename: '',
      analysis: null, imageUrl: '',
      materials: [], keywords: [], context: { type: '', location: '', cost: '', style: '', note: '' },
      searchResults: [], selectedIds: new Set(),
    };
    const wrap = $('#ai-preview-wrap');
    if (wrap) { wrap.innerHTML = ''; wrap.style.display = 'none'; }
    const fi = $('#ai-file-input'); if (fi) fi.value = '';
    const btn = $('#ai-start-btn'); if (btn) btn.disabled = true;
    this.gotoStep(1);
  },
};
