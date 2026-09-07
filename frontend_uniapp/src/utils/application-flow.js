/**
 * 根据当前借款状态返回用户应继续处理的页面。
 *
 * :param status: 后端借款状态
 * :return: UniApp 页面路径
 */
export function applicationNextPage(status) {
  const value = String(status || 'INIT').toUpperCase()
  if (['INIT', 'REJECTED', 'SETTLED'].includes(value)) return '/pages/verification/index'
  if (value === 'REVIEWING') return '/pages/review/index'
  if (value === 'APPROVED') return '/pages/withdraw/index'
  if (['WITHDRAWING', 'DISBURSED', 'OVERDUE'].includes(value)) return '/pages/bill/index'
  return '/pages/home/index'
}

/**
 * 判断状态是否需要重新开始身份与申请流程。
 *
 * :param status: 后端借款状态
 * :return: 是否需要身份流程
 */
export function needsApplicationStart(status) {
  return ['INIT', 'REJECTED', 'SETTLED'].includes(String(status || 'INIT').toUpperCase())
}
