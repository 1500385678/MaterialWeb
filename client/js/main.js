// main.js · 入口 — import + init 所有模块
// 改这里 = 加新模块,顺序无所谓
import { state } from './core/state.js';
import { $ } from './core/dom.js';
import { tabs } from './modules/tabs.js';
import { filters } from './modules/filters.js';
import { materials } from './modules/materials.js';
import { projects } from './modules/projects.js';
import { exam } from './modules/exam.js';
import { modelSettings } from './modules/model-settings.js';
import { aiFlow } from './modules/ai-flow.js';
import { aiSchemes } from './modules/ai-schemes.js';
import { media } from './modules/media.js';
import { qrPanel } from './modules/qr-panel.js';
import { utils } from './modules/utils.js';

// 全局暴露(给 inline onclick 调用,逐步去掉)
window.state = state;
window.aiFlow = aiFlow;
window.aiSchemes = aiSchemes;
window.modelSettings = modelSettings;
window.utils = utils;
window.tabs = tabs;

async function init() {
  // 基础 UI
  tabs.init();
  modelSettings.init();
  media.init();
  qrPanel.init();
  utils.init();

  // 业务模块
  filters.init();
  materials.init();
  projects.init();
  exam.init();
  aiFlow.init();
  aiSchemes.init();

  // 默认打开材料库 tab
  tabs.switch('materials');

  // 模型状态灯
  modelSettings.refreshStatus();

  console.log('[MaterialWeb] v1.0 · 13 modules loaded');
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
