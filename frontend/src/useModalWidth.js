import { ref, onMounted, onUnmounted } from 'vue'

/**
 * 弹窗自适应宽度 composable：
 * 宽度 = min(max, max(min, window.innerWidth - 48))，随窗口变化实时更新。
 * @param {number} min 最小宽度
 * @param {number} max 最大宽度
 */
export function useModalWidth(min = 420, max = 720) {
  const modalW = ref(calc())
  function calc() {
    return Math.min(max, Math.max(min, (window.innerWidth || 1024) - 48))
  }
  function onResize() { modalW.value = calc() }
  onMounted(() => window.addEventListener('resize', onResize))
  onUnmounted(() => window.removeEventListener('resize', onResize))
  return { modalW }
}
