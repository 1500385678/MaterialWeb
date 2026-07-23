// modules/filters.js · sidebar 筛选 (分类/防火/造价) + 搜索
// 单选式 sidebar:点一个激活一个,搜索框实时触发
import { $ } from '../core/dom.js';
import { state } from '../core/state.js';
import { categories as apiCategories } from '../api.js';
import { materials } from './materials.js';

const ALL_LIST = ['#matSidebarCategories', '#matSidebarFire', '#matSidebarCost'];

export const filters = {
  async init() {
    const { items } = await apiCategories();
    state.categories  = items;
    state.categoryMap = Object.fromEntries(items.map(c => [c.code, c]));

    this.renderCategories(items);
    this.bindEvents();
    // 默认激活"全部"分类
    const all = $('#matSidebarCategories .mat-sidebar-item[data-cat=""]');
    if (all) all.classList.add('active');
  },

  renderCategories(items) {
    const root = $('#matSidebarCategories');
    if (!root) return;
    const top = items.filter(c => !c.parent_code);
    const childMap = {};
    items.filter(c => c.parent_code).forEach(c => {
      (childMap[c.parent_code] = childMap[c.parent_code] || []).push(c);
    });
    let html = '';
    for (const t of top) {
      const kids = childMap[t.code] || [];
      html += `<li class="mat-sidebar-item" data-cat="${t.code}"><span class="icon">📦</span>${t.name}<span class="count">${kids.length || '-'}</span></li>`;
      if (kids.length) {
        html += '<li><ul class="mat-sidebar-children" style="display:flex;">';
        for (const k of kids) {
          html += `<li class="mat-sidebar-item" data-cat="${k.code}"><span class="icon">·</span>${k.name}</li>`;
        }
        html += '</ul></li>';
      }
    }
    // "全部" 放最前
    root.innerHTML = `<li class="mat-sidebar-item active" data-cat=""><span class="icon">🏷</span>全部<span class="count">${items.length}</span></li>` + html;
  },

  bindEvents() {
    $('#searchInput')?.addEventListener('input', () => materials.search());
    // 委托: 三个 sidebar 列表的 click
    ALL_LIST.forEach(sel => {
      $(sel)?.addEventListener('click', (e) => {
        const item = e.target.closest('.mat-sidebar-item');
        if (!item) return;
        // 同级去 active
        item.parentElement.querySelectorAll('.mat-sidebar-item').forEach(sib => sib.classList.remove('active'));
        item.classList.add('active');
        materials.search();
      });
    });
  },

  reset() {
    if ($('#searchInput')) $('#searchInput').value = '';
    ALL_LIST.forEach(sel => {
      $(sel)?.querySelectorAll('.mat-sidebar-item').forEach(s => s.classList.remove('active'));
    });
    const all = $('#matSidebarCategories .mat-sidebar-item[data-cat=""]');
    if (all) all.classList.add('active');
    materials.search();
  },

  get() {
    const catEl  = $('#matSidebarCategories')?.querySelector('.mat-sidebar-item.active');
    const fireEl = $('#matSidebarFire')?.querySelector('.mat-sidebar-item.active');
    const costEl = $('#matSidebarCost')?.querySelector('.mat-sidebar-item.active');
    return {
      keyword:     $('#searchInput')?.value.trim() || '',
      category:    catEl?.dataset.cat || '',
      fire_rating: fireEl?.dataset.fire || '',
      cost_tier:   costEl?.dataset.cost || '',
    };
  },
};
