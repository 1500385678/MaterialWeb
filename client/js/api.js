// api.js · 所有 /api/* 封装(单一入口)
// 任何模块都不能直接 fetch(...),都过这里
import { state } from './core/state.js';
import { toast } from './core/toast.js';

const BASE = '/api';

async function req(path, opts = {}) {
  try {
    const r = await fetch(BASE + path, {
      headers: { 'Content-Type': 'application/json', ...(opts.headers || {}) },
      ...opts,
    });
    const txt = await r.text();
    let data;
    try { data = JSON.parse(txt); } catch { data = { error: txt }; }
    if (!r.ok) {
      const msg = (data && data.error) || `HTTP ${r.status}`;
      toast(msg, 'error');
      throw new Error(msg);
    }
    return data;
  } catch (e) {
    if (!String(e.message).includes('HTTP')) toast('请求失败: ' + e.message, 'error');
    throw e;
  }
}

// ---- materials ----
export const materials = {
  list:  (q = {}) => {
    const s = new URLSearchParams(q).toString();
    return req('/materials' + (s ? '?' + s : ''));
  },
  search:(q)       => req('/materials/search?q=' + encodeURIComponent(q)),
  detail:(id)      => req('/materials/' + id),
  qr:    (id)      => fetch(BASE + '/materials/' + id + '/qr').then(r => r.blob()),
};

// ---- categories / suppliers / exam ----
export const categories = () => req('/categories');
export const suppliers  = () => req('/suppliers');

// ---- prices(跨库:价格库 MaterialWebPrices 的查询) ----
export const prices = {
  byMaterial: (id) => req('/material_price/' + id),
  search:     (q)  => req('/prices?q=' + encodeURIComponent(q)),
  stats:      ()   => req('/prices/stats'),
};
export const exam       = {
  all:          () => req('/exam'),
  byChapter:    (c) => req('/exam/chapter/' + encodeURIComponent(c)),
};

// ---- projects ----
export const projects = {
  list:    () => req('/projects'),
  create:  (data) => req('/projects', { method: 'POST', body: JSON.stringify(data) }),
  detail:  (id) => req('/projects/' + id),
  addMat:  (pid, data) => req(`/projects/${pid}/materials`, { method: 'POST', body: JSON.stringify(data) }),
  delMat:  (pid, pmid) => req(`/projects/${pid}/materials/${pmid}`, { method: 'DELETE' }),
  cost:    (pid) => req(`/projects/${pid}/cost-summary`),
  exportData: (pid) => req(`/projects/${pid}/export/docx`),
};

// ---- media ----
export const media = {
  imageUrl:  (fn) => `/api/media/images/${fn}`,
  cadUrl:    (fn) => `/api/media/cad/${fn}`,
  uploadUrl: (fn) => `/uploads/${fn}`,
  list:      (mid) => req('/media/list/' + mid),
};

// ---- AI ----
export const ai = {
  testModel:    (cfg) => req('/test_model', { method: 'POST', body: JSON.stringify(cfg) }),
  // analyze 是 multipart,要传 FormData
  analyze:      async (formData) => {
    const r = await fetch(BASE + '/analyze_image', { method: 'POST', body: formData });
    const data = await r.json();
    if (!r.ok) { toast(data.error || '分析失败', 'error'); throw new Error(data.error); }
    return data;
  },
  searchBy:     (payload) => req('/search_by_analysis', { method: 'POST', body: JSON.stringify(payload) }),
  saveScheme:   (payload) => req('/save_scheme', { method: 'POST', body: JSON.stringify(payload) }),
  listSchemes:  () => req('/schemes'),
  getScheme:    (id) => req('/schemes/' + id),
  delScheme:    (id) => req('/schemes/' + id, { method: 'DELETE' }),
  reloadScheme: (id) => req('/schemes/' + id + '/reload'),
  exportPdfUrl: (id) => BASE + '/schemes/' + id + '/export/pdf',
  // 异步导出(P0 修 2026-08-09 夜间迭代批 3):doc.build 不再阻塞 Flask 主线程
  submitExportPdf: (id) => req('/schemes/' + id + '/export/pdf', { method: 'POST' }),
  pollExportStatus: (id, taskId) => req('/schemes/' + id + '/export/pdf/status/' + taskId),
  downloadExportPdfUrl: (id, taskId) => BASE + '/schemes/' + id + '/export/pdf/download/' + taskId,
};
