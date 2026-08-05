// modules/projects.js · 我的项目(列表 + 创建 + 详情 + 添加材料 + 成本汇总)
import { $, el } from '../core/dom.js';
import { state } from '../core/state.js';
import { toast } from '../core/toast.js';
import { projects as api, materials as matApi } from '../api.js';
import { utils } from './utils.js';

export const projects = {
  async init() { await this.refresh(); },

  async refresh() {
    const r = await api.list();
    state.projects = r.items || [];
    this.renderList();
  },

  renderList() {
    const root = $('#projectList');
    if (!root) return;
    if (!state.projects.length) {
      root.innerHTML = '<div class="empty"><div class="empty-icon">📁</div><p>暂无项目,点上方"+ 新建项目"创建。</p></div>';
      return;
    }
    root.innerHTML = '';
    for (const p of state.projects) {
      const card = el('div', { class: 'project-card' });
      card.appendChild(el('h3', { style: { fontSize: '16px', marginBottom: '6px' } }, `${p.code} · ${p.name}`));
      card.appendChild(el('p', { style: { color: 'var(--text-muted)', fontSize: '13px' } },
        `${p.type || '—'} · ${p.area || 0} m² · ${p.status || 'designing'}`));
      card.addEventListener('click', () => this.openDetail(p.id));
      root.appendChild(card);
    }
  },

  showNewForm() { $('#newProjectForm').style.display = 'block'; },
  hideNewForm() { $('#newProjectForm').style.display = 'none'; },

  async create() {
    const name = $('#newProjectName').value.trim();
    const type = $('#newProjectType').value;
    const area = parseFloat($('#newProjectArea').value) || 0;
    if (!name) { toast('请输入项目名', 'error'); return; }
    await api.create({ name, type, area });
    toast('项目已创建 ✓', 'success');
    this.hideNewForm();
    await this.refresh();
  },

  async openDetail(id) {
    const d = await api.detail(id);
    state.currentProject = d;
    $('#projectModalTitle').textContent = `${d.code} · ${d.name}`;
    this.renderCostSummary(d);
    this.renderMaterialList(d.materials || []);
    await this.loadAddMatOptions();
    utils.openModal('projectModal');
  },

  renderCostSummary(d) {
    const total = d.total_cost || 0;
    const area  = d.area || 1;
    const per   = (total / Math.max(area, 1)).toFixed(2);
    $('#projectCostSummary').innerHTML = `
      <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:12px;">
        <div class="stat-item"><div class="stat-label">项目类型</div><div>${d.type || '—'}</div></div>
        <div class="stat-item"><div class="stat-label">建筑面积</div><div>${d.area || 0} m²</div></div>
        <div class="stat-item"><div class="stat-label">总造价</div><div style="color:var(--primary);font-size:18px;font-weight:600;">¥${total.toLocaleString()}</div></div>
        <div class="stat-item"><div class="stat-label">单方造价</div><div style="color:var(--primary);">¥${per}/m²</div></div>
      </div>
    `;
  },

  renderMaterialList(mats) {
    const root = $('#projectMaterialList');
    if (!root) return;
    if (!mats.length) {
      root.innerHTML = '<div class="empty"><div class="empty-icon">📋</div><p>暂无材料,下方添加。</p></div>';
      return;
    }
    root.innerHTML = '';
    for (const pm of mats) {
      const row = el('div', { class: 'material-row' }, [
        el('div', {}, pm.name_cn + (pm.category_name ? ` (${pm.category_name})` : '')),
        el('div', {}, `${pm.quantity} ${pm.unit || ''}`),
        el('div', {}, pm.location || '—'),
        el('div', {}, `¥${(pm.unit_cost * pm.quantity).toFixed(2)}`),
        el('button', { class: 'btn btn-outline btn-sm', onclick: () => this.remove(pm.id) }, '×'),
      ]);
      root.appendChild(row);
    }
  },

  async loadAddMatOptions() {
    const sel = $('#addMatSelect');
    if (!sel) return;
    const list = await matApi.list({});
    sel.innerHTML = '<option value="">-- 选择材料 --</option>' +
      list.map(m => `<option value="${m.id}" data-price="${m.unit_price}">${m.name_cn} (${m.code})</option>`).join('');
  },

  async addMaterial() {
    const pid = state.currentProject?.id;
    const mid = parseInt($('#addMatSelect').value);
    if (!mid) { toast('请选择材料', 'error'); return; }
    await api.addMat(pid, {
      material_id: mid,
      quantity:    parseFloat($('#addMatQty').value) || 0,
      location:    $('#addMatLoc').value,
    });
    toast('已添加 ✓', 'success');
    await this.openDetail(pid);
  },

  async remove(pmid) {
    const pid = state.currentProject?.id;
    await api.delMat(pid, pmid);
    toast('已移除', 'success');
    await this.openDetail(pid);
  },

  async exportDocx() {
    const pid = state.currentProject?.id;
    if (!pid) return;
    const data = await api.exportData(pid);
    // TODO: 接 docx 库生成 .docx;v1.0 先把 JSON 弹给用户,后续接 docx 库
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `${data.project.code}_材料清单.json`;
    a.click();
    toast('已下载 JSON(后续接 docx 库)', 'success');
  },
};
