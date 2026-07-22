// modules/media.js · 图片库 / CAD / 灯箱
import { $, el } from '../core/dom.js';
import { bus } from '../core/events.js';
import { media as api } from '../api.js';
import { toast } from '../core/toast.js';

export const media = {
  init() {
    bus.on('material:opened', d => {
      this.loadImageGallery(d.id, d.image_urls || []);
      this.loadCADList(d.id, d.cad_files || []);
    });
  },

  async loadImageGallery(mid, urls) {
    const root = $('#imageGallery');
    if (!root) return;
    if (!urls.length) {
      root.innerHTML = '<div class="image-empty"><div class="empty-icon">🖼</div><p>暂无图片<br><small style="font-size:12px;color:#94a3b8;">把图片放到 data/media/images/ 然后在 DB 的 image_urls 字段写文件名</small></p></div>';
      return;
    }
    root.innerHTML = '';
    urls.forEach(fn => {
      const img = el('img', {
        src: api.imageUrl(fn), loading: 'lazy',
        onerror: e => { e.target.style.background = '#fee2e2'; e.target.alt = '图片缺失'; },
        onclick: () => this.openLightbox(api.imageUrl(fn)),
      });
      root.appendChild(img);
    });
  },

  async loadCADList(mid, files) {
    const root = $('#cadList');
    if (!root) return;
    if (!files.length) {
      root.innerHTML = '<div class="image-empty"><div class="empty-icon">📐</div><p>暂无 CAD 文件<br><small style="font-size:12px;color:#94a3b8;">把 DWG/SKP/PDF 放到 data/media/cad/ 然后在 DB 的 cad_files 字段写文件名</small></p></div>';
      return;
    }
    root.innerHTML = '';
    files.forEach(fn => {
      const item = el('div', { class: 'cad-item' }, [
        el('span', {}, fn),
        el('a', { href: api.cadUrl(fn), class: 'btn btn-outline btn-sm', download: fn }, '下载'),
      ]);
      root.appendChild(item);
    });
  },

  openLightbox(url) {
    const lb = $('#lightbox');
    $('#lightboxImg').src = url;
    lb.style.display = 'flex';
  },
  closeLightbox() {
    $('#lightbox').style.display = 'none';
    $('#lightboxImg').src = '';
  },
};
window.media = media;
