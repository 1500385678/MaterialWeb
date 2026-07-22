// core/state.js · 全局状态(模块间共享)
// 所有模块从这里读 / 改;刷新页面 = 全部丢失
export const state = {
  // 材料库
  materials:   [],
  categories:  [],         // 列表 + 树
  categoryMap: {},         // code → 详情
  filters:     { category: '', fire_rating: '', cost_tier: '', keyword: '' },

  // 项目
  projects:    [],
  currentProject: null,     // 当前打开的项目详情

  // 考试
  exam:        [],
  examChapter: '4.1',

  // AI 流程(4 步)
  ai: {
    step: 1,                // 1..5
    file: null,             // File 对象
    previewUrl: '',
    imageFilename: '',
    analysis: null,         // vision 返回的 analysis 对象
    imageUrl: '',
    materials: [],          // identified_materials (可编辑)
    keywords: [],           // search_keywords (可编辑)
    context:  { type: '', location: '', cost: '', style: '', note: '' },
    searchResults: [],      // search_by_analysis 返回
    selectedIds: new Set(), // 选中的 material.id
  },

  // 模型设置(localStorage 持久化)
  model: loadModel(),
};

function loadModel() {
  try { return JSON.parse(localStorage.getItem('materialweb_model') || 'null') || {}; }
  catch { return {}; }
}

export function saveModel(s) {
  state.model = s || {};
  try { localStorage.setItem('materialweb_model', JSON.stringify(state.model)); } catch {}
}
export function hasModel() { return !!(state.model.api_url && state.model.api_key && state.model.model_name); }
