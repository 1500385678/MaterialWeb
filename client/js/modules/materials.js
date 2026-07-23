// modules/materials.js · 材料库 · 列表 + 大图卡片 + 详情弹窗 + 入口卡
// 参考 D5 Works:4:3 大图 + 类型 tag + 名称 + 价格
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

// code 前缀 → 占位 emoji(无图时)
const CATEGORY_ICON = {
  metal: '🔩', concrete: '🧱', masonry: '🧱', wood: '🪵', glass: '🪟',
  stone: '🪨', membrane: '⛺', insulation: '🛡', finishing: '🎨', composite: '🧬',
  flex: '🧊', grg: '🎭', grc: '🏛', uhpc: '💎', gfrc: '🏛',
};

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
      grid.innerHTML = '<div class="empty" style="grid-column:1/-1;"><div class="empty-icon">📭</div><p>没有匹配的材料。试试重置筛选或换个关键词。</p></div>';
      return;
    }
    grid.innerHTML = '';
    for (const m of list) grid.appendChild(this.makeCard(m));
  },

  makeCard(m) {
    const card = el('div', { class: 'mat-card' });
    const imgBox = el('div', { class: 'mat-card-img' });

    // 取首图(后端解析好的 images 数组)
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

    card.addEventListener('click', () => this.openDetail(m.id));
    return card;
  },

  // 入口卡跳转:激活对应 sidebar 筛选 + 搜索 + 滚到网格
  async jumpEntry(key) {
    const map = {
      fire: { sel: '#matSidebarFire',  attr: 'fire',  val: 'A1' },
      high: { sel: '#matSidebarCost',  attr: 'cost',  val: '高' },
    };
    if (key === 'new') {
      // 本月新增:临时改用 order_by=created_at_desc,清掉其他筛选
      filters.reset();
      const list = await api.list({ order_by: 'created_at_desc', limit: 30 });
      state.materials = list;
      this.renderGrid(list);
      document.getElementById('materialsGrid')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      toast(`已加载最近 ${list.length} 条新材料`, 'success');
      return;
    }
    const cfg = map[key];
    if (!cfg) return;
    const target = document.querySelector(`${cfg.sel} [data-${cfg.attr}="${cfg.val}"]`);
    if (!target) return;
    // 分类/造价都清掉,只激活目标
    ['#matSidebarCategories', cfg.sel].forEach(sel => {
      document.querySelectorAll(`${sel} .mat-sidebar-item`).forEach(s => s.classList.remove('active'));
    });
    target.classList.add('active');
    await this.search();
    document.getElementById('materialsGrid')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
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
