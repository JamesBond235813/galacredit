/**
 * 判断滑块事件是否已经达到一次性提交条件。
 *
 * :param value: 当前滑块值
 * :param options: 当前弹窗、请求和挑战状态
 * :return: 允许发起一次验证时返回 true
 */
export function canVerifySlider(value, { busy = false, visible = true, hasCaptcha = true, submitted = false } = {}) {
  return Number(value) >= 100 && visible && hasCaptcha && !busy && !submitted
}
