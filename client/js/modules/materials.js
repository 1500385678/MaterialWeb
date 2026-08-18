// modules/materials.js · 材料库 orchestrator (init + search + jumpEntry + openDetail)
// 重构自 267 行 (R327 P0 · 8-12 23:21 · 超铁律 #1 单文件 ≤250 行)
// 拆出 4 子模块: materials-card / materials-detail / materials-price / materials-references
// 卡片渲染 → ./materials-card.js
// 详情弹窗 (modal + 4 tab) → ./materials-detail.js
// 价格 tab → ./materials-price.js
// 参考 tab → ./materials-references.js
// 入口卡 onclick="materials.jumpEntry('xxx')" 走 window.materials 全局 (index.html:117/124/131)
import { state } from '../core/state.js';
import { toast } from '../core/toast.js';
import { materials as api } from '../api.js';
import { filters } from './filters.js';
import { materialsCard } from './materials-card.js';
import { materialsDetail } from './materials-detail.js';

export const materials = {
  async init() {
    materialsDetail.initTabs();  // modal 内 4-tab 切换
    await this.search();
  },

  async search() {
    const f = filters.get();
    const list = await api.list(f);
    state.materials = list;
    materialsCard.renderGrid(list);
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
      materialsCard.renderGrid(list);
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

  // 卡片点击 → 详情弹窗 (委托给 materials-detail 子模块)
  async openDetail(id) {
    await materialsDetail.open(id);
  },
};

// 暴露到 window 以支持 HTML 内联 onclick (index.html mat-entry)
// 与 media/modelSettings/qrPanel/utils/aiSchemes 保持一致
window.materials = materials;
