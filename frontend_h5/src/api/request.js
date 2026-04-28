import axios from 'axios';
import { showToast } from 'vant';

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL;
if (!apiBaseUrl) {
  throw new Error('Missing required env: VITE_API_BASE_URL');
}
const clientId = import.meta.env.VITE_CLIENT_ID;
if (!clientId) {
  throw new Error('Missing required env: VITE_CLIENT_ID');
}

const request = axios.create({
  baseURL: apiBaseUrl,
  timeout: 60000
});

let isRedirectingToLogin = false;

// 请求拦截器
request.interceptors.request.use(
  config => {
    config.headers = config.headers || {};
    config.headers['client-id'] = clientId;

    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  error => Promise.reject(error)
);

// 响应拦截器
request.interceptors.response.use(
  response => response.data,
  error => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');

      if (!isRedirectingToLogin) {
        isRedirectingToLogin = true;
        showToast('登录已失效，请重新登录');
        window.setTimeout(() => {
          window.location.replace('/login');
        }, 120);
      }
    } else {
      showToast(error.response?.data?.detail || '网络异常');
    }
    return Promise.reject(error);
  }
);

export default request;
