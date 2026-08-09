// modules/ai-schemes.js · 已保存方案(列表 + 详情 + 删除 + PDF 导出 + 重载)
import { $, el } from '../core/dom.js';
import { state } from '../core/state.js';
import { toast } from '../core/toast.js';
import { ai as api } from '../api.js';
import { aiFlow } from './ai-flow.js';
import { utils } from './utils.js';

export const aiSchemes = {
  async show() {
    utils.openModal('ai-schemes-modal');
    const root = $('#ai-schemes-list');
    root.innerHTML = '<div class="empty"><div class="empty-icon">⏳</div><p>加载中...</p></div>';
    try {
      const r = await api.listSchemes();
      if (!r.items.length) {
        root.innerHTML = '<div class="empty"><div class="empty-icon">📂</div><p>还没有方案。</p></div>';
        return;
      }
      root.innerHTML = '';
      for (const s of r.items) root.appendChild(this.makeItem(s));
    } catch (e) { toast('加载失败: ' + e.message, 'error'); }
  },

  makeItem(s) {
    const item = el('div', { class: 'ai-scheme-item' });
    const img = s.image_url
      ? el('img', { src: s.image_url, class: 'ai-scheme-thumb' })
      : el('div', { class: 'ai-scheme-thumb' });
    item.appendChild(img);
    item.appendChild(el('div', { class: 'ai-scheme-info' }, [
      el('h4', {}, s.name),
      el('p', {}, `${s.material_count} 项材质 · ${s.project_name || '未关联项目'} · ${s.created_at || ''}`),
    ]));
    const actions = el('div', { class: 'ai-scheme-actions' });
    actions.appendChild(el('button', { class: 'btn btn-outline btn-sm', onclick: e => { e.stopPropagation(); this.view(s.id); } }, '查看'));
    actions.appendChild(el('button', { class: 'btn btn-outline btn-sm', onclick: e => { e.stopPropagation(); this.reload(s.id); } }, '重载'));
    actions.appendChild(el('button', { class: 'btn btn-primary btn-sm', onclick: e => { e.stopPropagation(); this.exportPdf(s.id); } }, 'PDF'));
    actions.appendChild(el('button', { class: 'btn btn-danger btn-sm',  onclick: e => { e.stopPropagation(); this.del(s.id); } }, '删'));
    item.appendChild(actions);
    return item;
  },

  async view(id) {
    const s = await api.getScheme(id);
    $('#sd-title').textContent = s.name;
    $('#sd-body').innerHTML = `
      ${s.image_url ? `<div style="text-align:center;margin-bottom:12px;"><img src="${s.image_url}" style="max-width:300px;border-radius:6px;"/></div>` : ''}
      ${s.description ? `<p style="color:var(--text-muted);margin-bottom:12px;">${s.description}</p>` : ''}
      <h3 style="font-size:14px;margin:12px 0 8px;color:var(--text-muted);">材质清单 (${(s.materials || []).length})</h3>
      <div class="ai-results-list">
        ${(s.materials || []).map(m => `
          <div class="ai-result${m.is_selected ? ' selected' : ''}">
            <div class="ai-result-info">
              <h4>${m.name_cn} <span style="color:var(--text-muted);font-weight:400;">${m.code}</span></h4>
              <p>${m.category_name || ''} · ¥${m.unit_price || 0}/${m.unit || 'm²'}</p>
              <p style="font-size:12px;">${m.visual_desc || ''}</p>
            </div>
            <div class="ai-result-score">${m.score || 0}</div>
          </div>
        `).join('')}
      </div>
    `;
    utils.openModal('scheme-detail-modal');
  },

  closeDetail() { utils.closeModal('scheme-detail-modal'); },

  async del(id) {
    if (!confirm('确认删除这个方案?')) return;
    try { await api.delScheme(id); toast('已删除', 'success'); this.show(); }
    catch (e) { toast('删除失败: ' + e.message, 'error'); }
  },

  // 异步 PDF 导出(P0 修 2026-08-09 夜间迭代批 3):doc.build 改到后端线程池,
  // 前端 POST 拿 task_id → 每 1s 轮询 status → done 后下载,期间不阻塞 UI
  async exportPdf(id) {
    let task;
    try {
      task = await api.submitExportPdf(id);
      toast(`PDF 生成中(task=${task.task_id})...`);
    } catch (e) {
      // 异步端点失败时回退到旧的 GET 同步端点(保底)
      toast('异步提交失败,回退到同步导出...', 'error');
      window.open(api.exportPdfUrl(id), '_blank');
      return;
    }
    const taskId = task.task_id;
    const startedAt = Date.now();
    const TIMEOUT_MS = 90_000;  // 90s 上限
    const POLL_MS    = 1_000;
    while (Date.now() - startedAt < TIMEOUT_MS) {
      await new Promise(r => setTimeout(r, POLL_MS));
      let st;
      try { st = await api.pollExportStatus(id, taskId); }
      catch (_) { continue; }
      if (st.status === 'done') {
        toast('PDF 已就绪,开始下载', 'success');
        window.location.href = api.downloadExportPdfUrl(id, taskId);
        return;
      }
      if (st.status === 'error') {
        toast('PDF 生成失败: ' + (st.error || '未知错误'), 'error');
        return;
      }
      // pending 继续轮询
    }
    toast('PDF 生成超时(>90s),请稍后重试或查看 server 日志', 'error');
  },

  async reload(id) {
    const s = await api.reloadScheme(id);
    utils.closeModal('ai-schemes-modal');
    aiFlow.reset();
    if (s.session) {
      state.ai.analysis      = s.session.analysis || null;
      state.ai.materials     = JSON.parse(JSON.stringify(s.session.analysis?.identified_materials || []));
      state.ai.keywords      = [...(s.session.analysis?.search_keywords || [])];
      state.ai.searchResults = s.session.search_results || [];
      state.ai.selectedIds   = new Set(s.session.selected_ids || []);
      state.ai.imageFilename = s.image_filename || '';
      state.ai.imageUrl      = s.image_url || '';
    }
    utils.tabs?.switch?.('ai');
    if (state.ai.analysis) aiFlow.gotoStep(3);
    toast('已重载到方案 #' + id, 'success');
  },
};
window.aiSchemes = aiSchemes;
