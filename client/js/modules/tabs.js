// modules/tabs.js · 顶部 4 个 tab 切换
import { $ } from '../core/dom.js';

export const tabs = {
  init() {
    document.querySelectorAll('.nav-tabs a').forEach(a => {
      a.addEventListener('click', e => {
        e.preventDefault();
        const t = a.dataset.tab || a.textContent.trim();
        // 智能识别 tab 名
        const m = a.textContent.match(/[材料|项目|考试|AI]/);
        const tabName = a.dataset.tab || (
          m ? ({ '材料': 'materials', '项目': 'projects', '考试': 'exam', 'AI': 'ai' }[m[0]] || 'materials') : 'materials'
        );
        this.switch(tabName);
      });
    });
  },
  switch(name) {
    document.querySelectorAll('.nav-tabs a').forEach(a => {
      a.classList.toggle('active', (a.dataset.tab || a.textContent).includes(name) || (a.textContent.includes('AI') && name === 'ai'));
    });
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    const page = document.getElementById('page-' + name);
    if (page) page.classList.add('active');
  }
};
