import axios from 'axios';
import { ElMessage } from 'element-plus';
import { clearStoredAdminAuth } from '../constants/adminPages';
import { adminLocale, translateText } from '../i18n/adminLocale';

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || '/api';

const request = axios.create({
  baseURL: apiBaseUrl,
  timeout: 10000
});

let isRedirectingToLogin = false;

request.interceptors.request.use(
  config => {
    const token = localStorage.getItem('admin_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    config.headers['Accept-Language'] = adminLocale.value;
    return config;
  },
  error => Promise.reject(error)
);

request.interceptors.response.use(
  response => response.data,
  error => {
    if (error.response?.status === 401) {
      clearStoredAdminAuth();

      if (!isRedirectingToLogin) {
        isRedirectingToLogin = true;
        ElMessage.error('登录失效请重新登录');
        window.setTimeout(() => {
          window.location.replace('/login');
        }, 120);
      }
    } else {
      ElMessage.error(translateText(error.response?.data?.detail || '网络异常') || 'Network error');
    }
    return Promise.reject(error);
  }
);

export default request;
