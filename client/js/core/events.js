// core/events.js · 极简事件总线(模块间通信,避免循环 import)
const _h = new Map();
export const bus = {
  on(ev, fn)  { (_h.get(ev) || _h.set(ev, new Set()).get(ev)).add(fn); return () => bus.off(ev, fn); },
  off(ev, fn) { _h.get(ev)?.delete(fn); },
  emit(ev, ...args) { for (const fn of (_h.get(ev) || [])) try { fn(...args); } catch (e) { console.error(e); } },
};
