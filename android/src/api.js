const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api';
const TOKEN_KEY = 'xhb_android_admin_token';

export function getToken() {
  return localStorage.getItem(TOKEN_KEY) || '';
}

export function setToken(token) {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token);
  } else {
    localStorage.removeItem(TOKEN_KEY);
  }
}

export function buildRequestUrl(path, params, apiBase = API_BASE, origin = window.location.origin) {
  const url = new URL(`${apiBase}${path}`, origin);
  Object.entries(params || {}).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      url.searchParams.set(key, value);
    }
  });
  return /^https?:\/\//i.test(apiBase) ? url.toString() : `${url.pathname}${url.search}`;
}

function buildAbsoluteUrl(path) {
  if (!path) {
    return '';
  }
  if (/^https?:\/\//i.test(path)) {
    return path;
  }
  const base = /^https?:\/\//i.test(API_BASE) ? API_BASE : window.location.origin;
  return new URL(path, base).toString();
}

async function request(path, options = {}) {
  const token = getToken();
  const headers = {
    ...(options.body ? { 'Content-Type': 'application/json' } : {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers || {}),
  };
  const response = await fetch(buildRequestUrl(path, options.params), {
    method: options.method || 'GET',
    headers,
    body: options.body ? JSON.stringify(options.body) : undefined,
  });
  const text = await response.text();
  const data = text ? JSON.parse(text) : null;
  if (!response.ok) {
    const message = data?.detail || data?.msg || `请求失败：${response.status}`;
    const error = new Error(message);
    error.status = response.status;
    throw error;
  }
  return data;
}

export const api = {
  async login(username, password) {
    const result = await request('/admin/login', {
      method: 'POST',
      body: { username, password, client_type: 'MOBILE' },
    });
    setToken(result.access_token);
    return result;
  },
  logout() {
    setToken('');
  },
  me: () => request('/admin/me'),
  stats: () => request('/admin/stats'),
  repaymentStats: () => request('/admin/repayment-stats'),
  users: (params) => request('/admin/users', { params }),
  userDetail: (id) => request(`/admin/users/${id}`),
  userIpAudit: (id) => request(`/admin/users/${id}/ip-audit`),
  unlockLocationRisk: (id) => request(`/admin/users/${id}/location-risk/unlock`, { method: 'POST' }),
  blacklistUser: (id, body) => request(`/admin/users/${id}/blacklist`, { method: 'POST', body }),
  removeBlacklistUser: (id, body) => request(`/admin/users/${id}/blacklist/remove`, { method: 'POST', body }),
  loans: (params) => request('/admin/loans', { params }),
  updateLoan: (id, body) => request(`/admin/loans/${id}`, { method: 'PATCH', body }),
  reviewLoan: (id, body) => request(`/admin/loans/${id}/review`, { method: 'POST', body }),
  disburseLoan: (id, body) => request(`/admin/loans/${id}/disburse`, { method: 'POST', body }),
  rejectCardLoan: (id, body) => request(`/admin/loans/${id}/reject-card`, { method: 'POST', body }),
  reissueCardLoan: (id) => request(`/admin/loans/${id}/reissue-card`, { method: 'POST' }),
  closeCardReissue: (id) => request(`/admin/loans/${id}/close-card-reissue`, { method: 'POST' }),
  extendLoan: (id, body) => request(`/admin/loans/${id}/extend`, { method: 'POST', body }),
  adjustAvailableCredit: (id, body) => request(`/admin/loans/${id}/available-credit/adjust`, { method: 'POST', body }),
  setApprovedCreditLimit: (id, body) => request(`/admin/loans/${id}/approved-credit/set`, { method: 'POST', body }),
  updateOverdueDisplay: (id, body) => request(`/admin/loans/${id}/overdue-display`, { method: 'POST', body }),
  remindLoan: (id, body) => request(`/admin/loans/${id}/remind`, { method: 'POST', body }),
  collectLoan: (id, body) => request(`/admin/loans/${id}/collect`, { method: 'POST', body }),
  financeReconcileLoan: (id, body) => request(`/admin/loans/${id}/finance-reconcile`, { method: 'POST', body }),
  settleLoan: (id) => request(`/admin/loans/${id}/settle`, { method: 'POST' }),
  ackRepayAttempt: (id) => request(`/admin/loans/${id}/ack-repay-attempt`, { method: 'POST' }),
  mediaUrl: buildAbsoluteUrl,
};
