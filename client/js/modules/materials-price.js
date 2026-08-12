// modules/materials-price.js · 价格 tab (跨 db 查价格库)
// 从 materials.js 拆出 (R327 P0 · 8-12 23:21 · 超铁律 #1 单文件 ≤250 行)
// 依赖: dom.$
import { $ } from '../core/dom.js';
import { prices as pricesApi } from '../api.js';

export const materialsPrice = {
  // 渲染"价格" tab 内容(跨 db 查价格库)
  async render(materialId) {
    const panel = $('#pricePanel');
    if (!panel) return;
    panel.innerHTML = '<div class="empty"><p>加载中…</p></div>';
    try {
      const r = await pricesApi.byMaterial(materialId);
      if (!r.latest) {
        panel.innerHTML = `<div class="empty"><p>${r.message || '价格库暂无对应条目'}</p><p style="font-size:12px;color:var(--text-muted);margin-top:6px;">关键词:${(r.keywords || []).join(' / ') || '无'}</p></div>`;
        return;
      }
      const L = r.latest;
      const tiers = r.tiers || [];
      panel.innerHTML = `
        <div class="price-headline">
          <div class="price-label">当前参考价</div>
          <div class="price-value">
            <span class="price-min">¥${L.unit_price_min ?? 0}</span>
            <span class="price-tilde">~</span>
            <span class="price-max">¥${L.unit_price_max ?? 0}</span>
            <span class="price-unit">/ ${L.unit || '元/m²'}</span>
          </div>
          <div class="price-meta">
            <span class="price-avg">均价 ¥${L.unit_price_avg ?? 0}</span>
            <span class="price-type">${L.price_type || ''}</span>
            <span class="price-fluct">${L.fluctuation || ''}</span>
            <span class="price-from">${L.valid_from || ''} 起</span>
          </div>
        </div>
        ${L.spec && L.spec !== L.material_name ? `<div class="price-spec">规格:${L.spec}</div>` : ''}
        <div class="price-source">来源:${L.source_doc || '?'}</div>

        <div class="price-tiers-title">所有价档 <span class="price-tiers-count">共 ${tiers.length} 条</span></div>
        <div class="price-tiers-list">
          ${tiers.map(t => `
            <div class="price-tier-row">
              <div class="price-tier-name">${t.material_name}</div>
              <div class="price-tier-tags">
                ${t.category ? `<span class="price-tag">${t.category}</span>` : ''}
                ${t.brand_tier ? `<span class="price-tag">${t.brand_tier}</span>` : ''}
                ${t.craft ? `<span class="price-tag">${t.craft}</span>` : ''}
                ${t.price_type ? `<span class="price-tag price-type-tag">${t.price_type}</span>` : ''}
              </div>
              <div class="price-tier-num">
                <span class="price-tier-min">¥${t.unit_price_min ?? 0}</span>~
                <span class="price-tier-max">¥${t.unit_price_max ?? 0}</span>
                <span class="price-tier-unit">/ ${t.unit || '元/m²'}</span>
              </div>
            </div>
          `).join('')}
        </div>
      `;
    } catch (e) {
      panel.innerHTML = '<div class="empty"><p>价格加载失败:' + (e.message || e) + '</p></div>';
    }
  },
};
