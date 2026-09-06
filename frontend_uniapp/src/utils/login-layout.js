/**
 * 计算表单避开键盘所需的最小上移距离。
 * :param buttonBottom: 当前按钮底部坐标
 * :param viewportHeight: 键盘上方可视高度
 * :param currentLift: 已应用的上移距离
 * :return: 保留 8px 间距所需的非负位移
 */
export function loginFormLift(buttonBottom, viewportHeight, currentLift = 0) {
  return Math.max(0, buttonBottom + currentLift + 8 - viewportHeight)
}
