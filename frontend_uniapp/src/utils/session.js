import { getStorage } from './platform.js'

/**
 * 判断当前是否存在登录令牌。
 *
 * :return: 是否已登录
 */
export function isSignedIn() { return Boolean(getStorage('token')) }
