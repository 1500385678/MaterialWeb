// modules/materials.js · 材料库 · 列表 + 卡片 + 详情弹窗
import { $, el } from '../core/dom.js';
import { state } from '../core/state.js';
import { bus } from '../core/events.js';
import { toast } from '../core/toast.js';
import { materials as api } from '../api.js';
import { filters } from './filters.js';
import { qrPanel } from './qr-panel.js';
import { media } from './media.js';
import { utils } from './utils.js';

const CACHE = new Map(); // id -> 详情

export const materials = {
  async init() {
    await this.search();
  },

  async search() {
    const f = filters.get();
    const list = await api.list(f);
    state.materials = list;
    this.renderGrid(list);
  },

  renderGrid(list) {
    const grid = $('#materialsGrid');
    if (!grid) return;
    if (!list.length) {
      grid.innerHTML = '<div class="empty"><div class="empty-icon">📭</div><p>没有匹配的材料。</p></div>';
      return;
    }
    grid.innerHTML = '';
    for (const m of list) grid.appendChild(this.makeCard(m));
  },

  makeCard(m) {
    const card = el('div', { class: 'material-card' });
    card.appendChild(el('div', { class: 'card-bg' }));
    card.appendChild(el('div', { class: 'card-mask' }));
    const header = el('div', { class: 'card-header' }, [
      el('div', { class: 'card-title' }, m.name_cn || m.code),
      el('div', { class: 'card-code' }, m.code),
    ]);
    card.appendChild(header);
    if (m.category_name) card.appendChild(el('div', { class: 'card-category' }, m.category_name));
    const tags = el('div', { class: 'card-tags' });
    if (m.fire_rating) tags.appendChild(el('span', { class: 'tag tag-fire-' + m.fire_rating }, m.fire_rating));
    if (m.cost_tier)   tags.appendChild(el('span', { class: 'tag tag-cost-' + (m.cost_tier === '低' ? 'low' : m.cost_tier === '高' ? 'high' : 'mid') }, m.cost_tier));
    card.appendChild(tags);
    const stats = el('div', { class: 'card-stats' });
    stats.appendChild(el('div', { class: 'stat-item' }, [
      el('div', { class: 'stat-label' }, '单价'),
      el('div', {}, `¥${m.unit_price || 0}/${m.unit || 'm²'}`),
    ]));
    stats.appendChild(el('div', { class: 'stat-item' }, [
      el('div', { class: 'stat-label' }, '损耗'),
      el('div', {}, `${m.loss_factor || 1.0}`),
    ]));
    card.appendChild(stats);
    card.addEventListener('click', () => this.openDetail(m.id));
    return card;
  },

  async openDetail(id) {
    let d = CACHE.get(id);
    if (!d) {
      try { d = await api.detail(id); CACHE.set(id, d); }
      catch { return; }
    }
    $('#modalTitle').textContent = d.name_cn || d.code;
    const basic = $('#basicInfo');
    if (basic) basic.innerHTML = this.renderBasic(d);
    const sn = $('#structureNotes');
    if (sn) sn.textContent = d.structure_notes || '暂无';
    // 供应商 / 考试 / 图片 / CAD 由对应 module 接管
    bus.emit('material:opened', d);
    utils.openModal('materialModal');
  },

  renderBasic(d) {
    const rows = [
      ['编号',   d.code], ['英文名', d.name_en], ['子分类', d.sub_category],
      ['分类',   d.category_name], ['防火', d.fire_rating], ['防火补充', d.fire_note],
      ['环保',   d.env_grade], ['执行标准', d.std_code], ['认证', d.eco_cert],
      ['密度',   d.density], ['强度', d.strength], ['导热', d.thermal_cond],
      ['吸水率', d.water_absorp], ['单价', `¥${d.unit_price || 0}/${d.unit || 'm²'}`],
      ['施工费', `¥${d.labor_cost || 0}/${d.unit || 'm²'}`], ['损耗系数', d.loss_factor],
      ['造价',   d.cost_tier], ['质感', d.texture], ['色系', d.color_series],
      ['规格',   d.specs], ['样式', d.patterns], ['视觉效果', d.visual_desc],
      ['耐久性', d.durability], ['寿命', d.lifespan_years], ['维护', d.maintenance],
    ];
    return rows.filter(([_, v]) => v != null && v !== '').map(([k, v]) =>
      `<div class="item"><div class="item-label">${k}</div><div class="item-value">${v}</div></div>`
    ).join('');
  },
};
