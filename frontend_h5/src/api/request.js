import axios from 'axios';
import { showToast } from 'vant';

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || '/api';
const clientId = import.meta.env.VITE_CLIENT_ID || 'h5-web';

const request = axios.create({
  baseURL: apiBaseUrl,
  timeout: 60000
});

let isRedirectingToLogin = false;

const pageTitleMap = {
  '/home': '我的授信',
  '/profile': '个人中心',
  '/ocr': '实名认证',
  '/face': '人脸识别',
  '/face-mismatch': '人脸识别结果',
  '/application-form': '补充资料',
  '/review': '授信审核中',
  '/withdraw': '信用下单',
  '/bill': '付款账单',
  '/support': '客服帮助',
  '/orders': '我的订单',
  '/change-password': '修改密码',
  '/agreement': '用户协议',
  '/personal-info-authorization': '个人信息授权协议'
};

const actionMap = {
  'GET /user/info': ['页面初始化', '读取用户基础资料'],
  'POST /user/location': ['位置风控', '提交当前位置授权'],
  'POST /user/ocr': ['身份证上传区', '提交身份证正反面识别'],
  'POST /user/face-auth': ['人脸识别区', '提交人脸照片核验'],
  'POST /user/application': ['亲友联系人表单', '提交补充资料并申请授信'],
  'POST /user/channel-bind': ['渠道入口区', '绑定/识别专属渠道'],
  'POST /user/change-password': ['密码表单', '修改登录密码'],
  'GET /loan/status': ['额度状态区', '查看当前申请/账单状态'],
  'GET /loan/products': ['商品列表区', '查看可选商品'],
  'POST /loan/order-sms-code': ['下单确认区', '获取下单验证码'],
  'POST /loan/withdraw': ['下单确认区', '提交信用下单'],
  'GET /loan/bill': ['账单详情区', '查看还款账单'],
  'POST /loan/repay-attempt': ['还款操作区', '点击已还款/还款反馈'],
  'GET /loan/ecard-secret': ['E卡信息区', '查看E卡卡密']
};

const resolveAuditContext = (config) => {
  const pagePath = window.location.pathname || '/';
  const pageTitle = pageTitleMap[pagePath] || document.title || '前端页面';
  const urlPath = String(config.url || '').split('?')[0];
  const key = `${String(config.method || 'GET').toUpperCase()} ${urlPath}`;
  const [space, action] = actionMap[key] || ['服务请求', '访问服务接口'];
  return { pagePath, pageTitle, space, action };
};

const encodeAuditHeader = (value) => encodeURIComponent(String(value || ''));

// 请求拦截器
request.interceptors.request.use(
  config => {
    config.headers = config.headers || {};
    config.headers['client-id'] = clientId;
    const auditContext = resolveAuditContext(config);
    config.headers['x-xhb-page-path'] = encodeAuditHeader(auditContext.pagePath);
    config.headers['x-xhb-page-title'] = encodeAuditHeader(auditContext.pageTitle);
    config.headers['x-xhb-action-space'] = encodeAuditHeader(auditContext.space);
    config.headers['x-xhb-action-name'] = encodeAuditHeader(auditContext.action);

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
