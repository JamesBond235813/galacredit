import { onBeforeUnmount } from 'vue'

/**
 * 创建可去重、可销毁的恢复任务执行器。
 *
 * :param callback: 页面刷新函数，可返回 Promise
 * :param options: 合并窗口和时钟配置
 * :return: 包含 run 和 dispose 的控制器
 */
export function createResumeRunner(callback, { minIntervalMs = 500, now = () => Date.now() } = {}) {
  let disposed = false
  let running = false
  let lastStartedAt = Number.NEGATIVE_INFINITY

  return {
    run() {
      const currentTime = Number(now())
      if (disposed || running || typeof callback !== 'function' || currentTime - lastStartedAt < minIntervalMs) return Promise.resolve(false)
      running = true
      lastStartedAt = currentTime
      return Promise.resolve()
        .then(() => callback())
        .then(() => true)
        .finally(() => { running = false })
    },
    dispose() { disposed = true }
  }
}

/**
 * 页面回到前台时触发一次可去重的数据刷新。
 *
 * :param callback: 页面刷新函数，可返回 Promise
 * :return: 无
 */
export function usePageResume(callback) {
  const runner = createResumeRunner(callback)
  const run = () => {
    runner.run()
      .catch(() => {
        // 页面自己的 load 函数负责展示错误；这里仅防止恢复事件产生未处理 Promise。
      })
  }

  const onVisibilityChange = () => {
    if (typeof document === 'undefined' || document.visibilityState === 'visible') run()
  }

  if (typeof document !== 'undefined') document.addEventListener('visibilitychange', onVisibilityChange)
  if (typeof window !== 'undefined') window.addEventListener('galacredit:resume', run)
  onBeforeUnmount(() => {
    runner.dispose()
    if (typeof document !== 'undefined') document.removeEventListener('visibilitychange', onVisibilityChange)
    if (typeof window !== 'undefined') window.removeEventListener('galacredit:resume', run)
  })
}
