// modules/filters.js · 分类/防火/造价 三个下拉 + 搜索
import { $ } from '../core/dom.js';
import { state } from '../core/state.js';
import { categories as apiCategories } from '../api.js';
import { materials } from './materials.js';

export const filters = {
  async init() {
    const { items } = await apiCategories();
    state.categories  = items;
    state.categoryMap = Object.fromEntries(items.map(c => [c.code, c]));

    const sel = $('#filterCategory');
    if (sel) {
      sel.innerHTML = '<option value="">全部分类</option>' +
        items.filter(c => c.parent_code).map(c =>
          `<option value="${c.code}">${c.name}</option>`
        ).join('');
    }

    // 事件
    $('#searchInput')?.addEventListener('input', () => materials.search());
    $('#filterCategory')?.addEventListener('change', () => materials.search());
    $('#filterFire')?.addEventListener('change', () => materials.search());
    $('#filterCost')?.addEventListener('change', () => materials.search());
  },
  reset() {
    if ($('#searchInput'))   $('#searchInput').value = '';
    if ($('#filterCategory'))$('#filterCategory').value = '';
    if ($('#filterFire'))    $('#filterFire').value = '';
    if ($('#filterCost'))    $('#filterCost').value = '';
    materials.search();
  },
  get() {
    return {
      keyword:     $('#searchInput')?.value.trim() || '',
      category:    $('#filterCategory')?.value || '',
      fire_rating: $('#filterFire')?.value || '',
      cost_tier:   $('#filterCost')?.value || '',
    };
  },
};
