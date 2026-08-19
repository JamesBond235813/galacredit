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
  '/home': 'My Credit',
  '/profile': 'My Account',
  '/ocr': 'Identity Verification',
  '/face': 'Face Verification',
  '/face-mismatch': 'Verification Result',
  '/application-form': 'Additional Information',
  '/review': 'Application Review',
  '/withdraw': 'Loan Application',
  '/bill': 'Repayment Bill',
  '/support': 'Customer Support',
  '/orders': 'My Applications',
  '/change-password': 'Change Password',
  '/agreement': 'User Agreement',
  '/personal-info-authorization': 'Personal Data Authorization'
};

const actionMap = {
  'GET /user/info': ['Page setup', 'Load customer profile'],
  'POST /user/location': ['Location check', 'Submit location permission'],
  'POST /user/ocr': ['ID upload', 'Submit identity documents'],
  'POST /user/face-auth': ['Face verification', 'Submit face image'],
  'POST /user/application': ['Contact form', 'Submit credit application'],
  'POST /user/channel-bind': ['Invitation access', 'Bind invitation channel'],
  'POST /user/change-password': ['Password form', 'Change sign-in password'],
  'GET /loan/status': ['Credit status', 'View application or bill status'],
  'GET /loan/products': ['Loan options', 'View available loan products'],
  'POST /loan/order-sms-code': ['Application confirmation', 'Request confirmation code'],
  'POST /loan/withdraw': ['Application confirmation', 'Submit loan application'],
  'GET /loan/bill': ['Bill details', 'View repayment bill'],
  'POST /loan/repay-attempt': ['Repayment action', 'Request repayment support'],
  'GET /loan/ecard-secret': ['Legacy e-card', 'View legacy e-card details']
};

const resolveAuditContext = (config) => {
  const pagePath = window.location.pathname || '/';
  const pageTitle = pageTitleMap[pagePath] || document.title || 'Customer page';
  const urlPath = String(config.url || '').split('?')[0];
  const key = `${String(config.method || 'GET').toUpperCase()} ${urlPath}`;
  const [space, action] = actionMap[key] || ['Service request', 'Access service API'];
  return { pagePath, pageTitle, space, action };
};

const encodeAuditHeader = (value) => encodeURIComponent(String(value || ''));

// Request interceptor
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

// Response interceptor
request.interceptors.response.use(
  response => response.data,
  error => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');

      if (!isRedirectingToLogin) {
        isRedirectingToLogin = true;
        showToast('Your session has expired. Please sign in again.');
        window.setTimeout(() => {
          window.location.replace('/login');
        }, 120);
      }
    } else {
      showToast(error.response?.data?.msg || 'Request failed. Please try again.');
    }
    return Promise.reject(error);
  }
);

export default request;
