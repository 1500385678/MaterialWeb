// modules/materials.js · 材料库 · 列表 + 大图卡片 + 详情弹窗 + 入口卡
// 参考 D5 Works:4:3 大图 + 类型 tag + 名称 + 价格
import { $, el } from '../core/dom.js';
import { state } from '../core/state.js';
import { bus } from '../core/events.js';
import { toast } from '../core/toast.js';
import { materials as api, prices as pricesApi } from '../api.js';
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
    this.initTabs();
    await this.search();
  },

  // 详情 modal 内 tab 切换(没现成 listener,这里补)
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
    this.renderLanguage(d);
    await this.renderPrice(id);
    await this.renderReferences(id);
    const sn = $('#structureNotes');
    if (sn) sn.textContent = d.structure_notes || '暂无';
    bus.emit('material:opened', d);
    utils.openModal('materialModal');
  },

  // 渲染"语言" tab 内容
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

  // 渲染"价格" tab 内容(跨 db 查价格库)
  async renderPrice(materialId) {
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

  // 渲染"参考" tab 内容(异步拉 references)
  async renderReferences(materialId) {
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
