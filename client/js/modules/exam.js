// modules/exam.js · 考试学习(章节列表 + 知识点卡片)
import { $, el } from '../core/dom.js';
import { state } from '../core/state.js';
import { exam as api } from '../api.js';

export const exam = {
  async init() {
    $('#filterExamChapter')?.addEventListener('change', e => {
      state.examChapter = e.target.value;
      this.load();
    });
    await this.load();
  },

  async load() {
    const r = await api.byChapter(state.examChapter);
    state.exam = r.items || [];
    this.render();
  },

  render() {
    const root = $('#examGrid');
    if (!root) return;
    if (!state.exam.length) {
      root.innerHTML = '<div class="empty"><div class="empty-icon">📚</div><p>本章暂无知识点。</p></div>';
      return;
    }
    root.innerHTML = '';
    for (const k of state.exam) {
      const card = el('div', { class: 'exam-card' });
      card.appendChild(el('h3', { style: { fontSize: '15px', marginBottom: '6px' } },
        `${k.chapter}.${k.section || ''} ${k.topic}`));
      if (k.difficulty || k.exam_freq) {
        card.appendChild(el('div', { style: { fontSize: '12px', color: 'var(--text-muted)', marginBottom: '8px' } },
          `难度:${k.difficulty || '中'} · 频率:${k.exam_freq || '中'}`));
      }
      const p = el('p', { style: { fontSize: '13px', lineHeight: '1.6', color: 'var(--text)' } });
      p.textContent = (k.content || '').slice(0, 200) + ((k.content || '').length > 200 ? '...' : '');
      card.appendChild(p);
      if (k.key_point) {
        const tip = el('div', { style: { marginTop: '8px', padding: '8px', background: '#2a2a2a',
          borderRadius: '4px', fontSize: '12px', color: 'var(--primary)' } }, '💡 ' + k.key_point);
        card.appendChild(tip);
      }
      root.appendChild(card);
    }
  },
};
