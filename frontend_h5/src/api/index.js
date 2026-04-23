import request from './request';

// Auth API
export const sendCode = (data) => request.post('/auth/send-code', data);
export const login = (data) => request.post('/auth/login', data);
export const getChannelEntryInfo = (channelName) => request.get(`/auth/channels/${channelName}`);

// User API
export const getUserInfo = () => request.get('/user/info');
export const bindUserChannel = (data) => request.post('/user/channel-bind', data);
export const submitOCR = (data) => request.post('/user/ocr', data, {headers: {'Content-Type': 'multipart/form-data'}});
export const submitFaceAuth = (data) => request.post('/user/face-auth', data, {headers: {'Content-Type': 'multipart/form-data'}});
export const submitApplication = (data) => request.post('/user/application', data);
export const submitUserLocation = (data) => request.post('/user/location', data);

// Loan API
export const getLoanStatus = () => request.get('/loan/status');
export const applyLimit = () => request.post('/loan/apply');
export const getProducts = () => request.get('/loan/products');
export const withdraw = (data) => request.post('/loan/withdraw', data);
export const getBill = () => request.get('/loan/bill');
export const registerRepayAttempt = () => request.post('/loan/repay-attempt');
export const getEcardSecret = (field) => request.get('/loan/ecard-secret', { params: { field } });
