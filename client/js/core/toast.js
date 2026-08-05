// core/toast.js · 顶部 toast 提示
import { $ } from './dom.js';

let _t;
export function toast(msg, type = '') {
  const t = $('#toast');
  if (!t) return;
  t.textContent = msg;
  t.className = 'toast show' + (type ? ' ' + type : '');
  clearTimeout(_t);
  _t = setTimeout(() => t.classList.remove('show'), 2400);
}
