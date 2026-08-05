// modules/qr-panel.js · 二维码弹窗
import { $ } from '../core/dom.js';
import { bus } from '../core/events.js';
import { materials as api } from '../api.js';

export const qrPanel = {
  init() {
    bus.on('material:opened', d => {
      const btn = $('#btnQR');
      if (btn) btn.onclick = () => this.show(d.id, d.name_cn);
    });
  },

  async show(id, name) {
    const modal = $('#qrModal');
    modal.style.display = 'flex';
    $('#qrName').textContent = name || '';
    const img = $('#qrImg');
    img.src = '';
    try {
      const blob = await api.qr(id);
      img.src = URL.createObjectURL(blob);
    } catch (e) {
      img.alt = '生成失败';
    }
  },

  close() { $('#qrModal').style.display = 'none'; },
};
window.qrPanel = qrPanel;
