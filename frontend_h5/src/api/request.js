import axios from 'axios';
import { showToast } from 'vant';

const request = axios.create({
  baseURL: '/api', // 借助 Vite proxy 转发解决局域网手机访问跨域报错问题
  timeout: 60000
});

let isRedirectingToLogin = false;

// 请求拦截器
request.interceptors.request.use(
  config => {
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
