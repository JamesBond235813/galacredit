/**
 * GalaCredit 轻量 SVG 图标路径集合，避免关键导航依赖系统字体符号。
 *
 * :return: 图标名称到 SVG path 数据的映射
 */
export const ICON_PATHS = Object.freeze({
  home: ['M3 10.5 12 3l9 7.5', 'M5.5 9.5V21h13V9.5', 'M9.5 21v-6h5v6'],
  applications: ['M7 3h7l4 4v14H7z', 'M14 3v5h4', 'M10 12h5', 'M10 16h5'],
  account: ['M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8Z', 'M4.5 21a7.5 7.5 0 0 1 15 0'],
  'shield-check': ['M12 3 20 6v5c0 5.2-3.3 8.8-8 10-4.7-1.2-8-4.8-8-10V6z', 'm8.5 12 2.2 2.2 4.8-5'],
  plus: ['M12 5v14', 'M5 12h14'],
  help: ['M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18Z', 'M9.7 9a2.4 2.4 0 1 1 4.3 1.5c-.8 1-2 1.3-2 2.7', 'M12 17h.01'],
  'chevron-left': ['m14.5 5-7 7 7 7'],
  'chevron-right': ['m9.5 5 7 7-7 7']
})
