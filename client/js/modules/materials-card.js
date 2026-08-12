// modules/materials-card.js · 材料卡片渲染 (grid + 单卡)
// 从 materials.js 拆出 (R327 P0 · 8-12 23:21 · 超铁律 #1 单文件 ≤250 行)
// 依赖: dom.el, media.imageUrl
import { el } from '../core/dom.js';
import { media } from './media.js';

// code 前缀 → 占位 emoji(无图时)
const CATEGORY_ICON = {
  metal: '🔩', concrete: '🧱', masonry: '🧱', wood: '🪵', glass: '🪟',
  stone: '🪨', membrane: '⛺', insulation: '🛡', finishing: '🎨', composite: '🧬',
  flex: '🧊', grg: '🎭', grc: '🏛', uhpc: '💎', gfrc: '🏛',
};

export const materialsCard = {
  // 空态渲染
  renderEmpty(grid) {
    grid.innerHTML = '<div class="empty" style="grid-column:1/-1;"><div class="empty-icon">📭</div><p>没有匹配的材料。试试重置筛选或换个关键词。</p></div>';
  },

  renderGrid(list) {
    const grid = document.getElementById('materialsGrid');
    if (!grid) return;
    if (!list.length) { this.renderEmpty(grid); return; }
    grid.innerHTML = '';
    for (const m of list) grid.appendChild(this.makeCard(m));
  },

  // D5 Works:4:3 大图 + 类型 tag + 名称 + 价格 + 防火/造价 chip
  makeCard(m) {
    const card = el('div', { class: 'mat-card' });
    const imgBox = el('div', { class: 'mat-card-img' });

    // 首图(后端解析好的 images 数组)
    const firstImg = (m.images && m.images[0]) || null;
    if (firstImg) {
      const img = el('img', { src: media.imageUrl(firstImg), loading: 'lazy', alt: m.name_cn || m.code });
      img.onerror = () => { img.style.display = 'none'; };
      imgBox.appendChild(img);
    } else {
      // 占位:code 前缀映射 emoji
      const prefix = (m.code || '').split('_')[0]?.toLowerCase();
      imgBox.appendChild(el('div', { class: 'ph' }, CATEGORY_ICON[prefix] || '🧱'));
    }
    // 类型 tag: code 前缀 (STONE_001 → STONE)
    const tag = (m.code || '').split('_')[0] || 'MAT';
    imgBox.appendChild(el('div', { class: 'mat-card-tag' }, tag));
    // 语言 tag (取前 2 个,作为卡片上的小 chip)
    if (Array.isArray(m.material_language) && m.material_language.length) {
      imgBox.appendChild(el('div', { class: 'mat-card-lang' }, m.material_language.slice(0, 2).join(' · ')));
    }
    card.appendChild(imgBox);

    const body = el('div', { class: 'mat-card-body' });
    body.appendChild(el('div', { class: 'mat-card-name' }, m.name_cn || m.code));
    body.appendChild(el('div', { class: 'mat-card-sub' }, m.sub_category || m.category_name || ''));
    body.appendChild(el('div', { class: 'mat-card-price' }, `¥${m.unit_price || 0} / ${m.unit || 'm²'}`));
    const badges = el('div', { class: 'mat-card-badges' });
    if (m.fire_rating) badges.appendChild(el('span', { class: 'mat-badge fire-' + m.fire_rating }, m.fire_rating));
    if (m.cost_tier)   badges.appendChild(el('span', { class: 'mat-badge' }, m.cost_tier + '端'));
    body.appendChild(badges);
    card.appendChild(body);

    return card;
  },
};
