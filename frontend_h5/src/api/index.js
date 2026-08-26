import request from './request';

// Auth API
export const sendCode = (data) => request.post('/auth/send-code', data);
export const createSliderCaptcha = (data) => request.post('/auth/slider-captcha/create', data);
export const verifySliderCaptcha = (data) => request.post('/auth/slider-captcha/verify', data);
export const login = (data) => request.post('/auth/login', data);
export const smsLogin = (data) => request.post('/auth/sms-login', data);
export const logout = (data) => request.post('/auth/logout', data);

// User API
export const getUserInfo = () => request.get('/user/info');
export const bindUserChannel = (data) => request.post('/user/channel-bind', data);
export const submitOCR = (data) => request.post('/user/ocr', data, {headers: {'Content-Type': 'multipart/form-data'}});
export const submitFaceAuth = (data) => request.post('/user/face-auth', data, {headers: {'Content-Type': 'multipart/form-data'}});
export const submitApplication = (data) => request.post('/user/application', data);
export const submitUserLocation = (data) => request.post('/user/location', data);
export const submitRiskSignals = (data) => request.post('/user/risk-signals', data);
export const changePassword = (data) => request.post('/user/change-password', data);

// Loan API
export const getLoanStatus = () => request.get('/loan/status');
export const applyLimit = () => request.post('/loan/apply');
export const getProducts = (params) => request.get('/loan/products', { params });
export const previewPurchaseContract = (data) => request.post('/loan/purchase-contract/preview', data);
export const signPurchaseContract = (data) => request.post('/loan/purchase-contract/sign', data);
export const sendOrderSmsCode = () => request.post('/loan/order-sms-code');
export const withdraw = (data) => request.post('/loan/withdraw', data);
export const getBill = () => request.get('/loan/bill');
export const registerRepayAttempt = () => request.post('/loan/repay-attempt');
export const getEcardSecret = (field, params = {}) => request.get('/loan/ecard-secret', { params: { field, ...params } });
