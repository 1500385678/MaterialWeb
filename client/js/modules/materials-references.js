// modules/materials-references.js · 参考工程 tab (异步拉 references)
// 从 materials.js 拆出 (R327 P0 · 8-12 23:21 · 超铁律 #1 单文件 ≤250 行)
// 依赖: dom.$
import { $ } from '../core/dom.js';

export const materialsReferences = {
  // 渲染"参考" tab 内容(异步拉 references)
  async render(materialId) {
    const panel = $('#referencesPanel');
    if (!panel) return;
    panel.innerHTML = '<div class="empty"><p>加载中…</p></div>';
    try {
      const r = await fetch(`/api/materials/${materialId}/references`).then(r => r.json());
      if (!r.length) {
        panel.innerHTML = '<div class="empty"><p>暂无真实工程参考(可后续补充)</p></div>';
        return;
      }
      panel.innerHTML = r.map(ref => `
        <div class="ref-card">
          <div class="ref-head">
            <div class="ref-name">${ref.project_name}</div>
            <div class="ref-year">${ref.year || '?'}</div>
          </div>
          <div class="ref-meta">${[ref.designer, ref.city, ref.part].filter(Boolean).join(' · ')}</div>
          ${ref.comment ? `<div class="ref-comment">"${ref.comment}"</div>` : ''}
          ${ref.image_url ? `<div class="ref-img"><img src="${ref.image_url}" alt="${ref.project_name}" loading="lazy"></div>` : '<div class="ref-img ref-img-empty">配图待补</div>'}
        </div>
      `).join('');
    } catch (e) {
      panel.innerHTML = '<div class="empty"><p>加载失败</p></div>';
    }
  },
};
