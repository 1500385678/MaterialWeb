// modules/utils.js · 通用工具(弹窗打开关闭 / 时间 / 模式 tab)
import { $ } from '../core/dom.js';
import { tabs } from './tabs.js';

export const utils = {
  init() {
    // 弹窗外点关闭
    document.querySelectorAll('.modal-overlay').forEach(m => {
      m.addEventListener('click', e => {
        if (e.target === m && m.id) this.closeModal(m.id);
      });
    });
    // lightbox 关闭
    const lb = $('#lightbox');
    if (lb) lb.addEventListener('click', e => {
      if (e.target === lb || e.target.tagName === 'IMG') this.media?.closeLightbox();
    });
  },

  openModal(id)  { const m = $('#' + id); if (m) m.style.display = 'flex'; },
  closeModal(id) { const m = $('#' + id); if (m) m.style.display = 'none'; },

  nowStr() {
    const d = new Date();
    return `${d.getFullYear()}${String(d.getMonth()+1).padStart(2,'0')}${String(d.getDate()).padStart(2,'0')}-${String(d.getHours()).padStart(2,'0')}${String(d.getMinutes()).padStart(2,'0')}`;
  },

  // 暴露给 ai-flow 等调用 tab 切换
  tabs,
};
window.utils = utils;
