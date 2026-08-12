// modules/materials-detail.js · 材料详情弹窗 (modal + 4 tab)
// 从 materials.js 拆出 (R327 P0 · 8-12 23:21 · 超铁律 #1 单文件 ≤250 行)
// 依赖: dom, state, events.bus, utils.openModal, materialsPrice, materialsReferences, api.detail
import { $ } from '../core/dom.js';
import { bus } from '../core/events.js';
import { utils } from './utils.js';
import { materialsPrice } from './materials-price.js';
import { materialsReferences } from './materials-references.js';
import { materials as api } from '../api.js';

const CACHE = new Map(); // id -> 详情

export const materialsDetail = {
  // modal 内 4-tab 切换(没现成 listener,这里补)
  initTabs() {
    document.querySelectorAll('.tab-btn[data-mtab]').forEach(btn => {
      btn.addEventListener('click', () => {
        const tab = btn.dataset.mtab;
        const root = btn.closest('.modal') || document;
        root.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        root.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        btn.classList.add('active');
        const content = root.querySelector('#tab-' + tab);
        if (content) content.classList.add('active');
      });
    });
  },

  // 弹窗主入口(被 materials.openDetail 调用)
  async open(id) {
    let d = CACHE.get(id);
    if (!d) {
      try { d = await api.detail(id); CACHE.set(id, d); }
      catch { return; }
    }
    $('#modalTitle').textContent = d.name_cn || d.code;
    const basic = $('#basicInfo');
    if (basic) basic.innerHTML = this.renderBasic(d);
    this.renderLanguage(d);
    await materialsPrice.render(id);
    await materialsReferences.render(id);
    const sn = $('#structureNotes');
    if (sn) sn.textContent = d.structure_notes || '暂无';
    bus.emit('material:opened', d);
    utils.openModal('materialModal');
  },

  // "语言" tab 内容
  renderLanguage(d) {
    const panel = $('#languagePanel');
    if (!panel) return;
    const langs = Array.isArray(d.material_language) ? d.material_language : [];
    if (!langs.length && !d.language_notes) {
      panel.innerHTML = '<div class="empty"><p>暂无空间语言标签</p></div>';
      return;
    }
    let html = '';
    if (langs.length) {
      html += '<div class="lang-tags">' + langs.map(t =>
        `<span class="lang-tag">${t}</span>`
      ).join('') + '</div>';
    }
    if (d.language_notes) {
      html += `<p class="lang-notes">${d.language_notes}</p>`;
    }
    panel.innerHTML = html;
  },

  // "基本信息" 表 (key-value 列表)
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
