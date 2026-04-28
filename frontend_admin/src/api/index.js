import request from './request';

// Admin API
export const login = (data) => request.post('/admin/login', data);
export const getAdminInfo = () => request.get('/admin/me');
export const getAdminStats = () => request.get('/admin/stats');
export const getRepaymentStats = () => request.get('/admin/repayment-stats');
export const getProjectCashInsights = () => request.get('/admin/project-cash-insights');
export const getChannels = (params) => request.get('/admin/channels', { params });
export const createChannel = (data) => request.post('/admin/channels', data);
export const updateChannel = (id, data) => request.patch(`/admin/channels/${id}`, data);
export const getProducts = (params) => request.get('/admin/products', { params });
export const createProduct = (data) => request.post('/admin/products', data);
export const updateProduct = (id, data) => request.patch(`/admin/products/${id}`, data);
export const getEcardPool = (params) => request.get('/admin/ecard-pool', { params });
export const createEcardPoolItem = (data) => request.post('/admin/ecard-pool', data);
export const updateEcardPoolItem = (id, data) => request.patch(`/admin/ecard-pool/${id}`, data);
export const uploadEcardPoolExcel = (formData) => request.post('/admin/ecard-pool/batch-upload', formData);
export const downloadEcardPoolTemplate = () => request.get('/admin/ecard-pool/template', { responseType: 'blob' });
export const getAdminUsers = (params) => request.get('/admin/admin-users', { params });
export const createAdminUser = (data) => request.post('/admin/admin-users', data);
export const updateAdminUser = (id, data) => request.patch(`/admin/admin-users/${id}`, data);
export const deleteAdminUser = (id) => request.delete(`/admin/admin-users/${id}`);

// User API for Admin
export const getUsers = (params) => request.get('/admin/users', { params });
export const getUserDetail = (id) => request.get(`/admin/users/${id}`);
export const createFrontUser = (data) => request.post('/admin/users', data);
export const resetFrontUserPassword = (id, data) => request.post(`/admin/users/${id}/reset-password`, data);
export const getRiskReportByUser = (data) => request.post('/admin/risk/report', data);

// Loan API for Admin
export const getLoans = (params) => request.get('/admin/loans', { params });
export const getLoanLedger = (id) => request.get(`/admin/loans/${id}/ledger`);
export const reviewLoan = (id, data) => request.post(`/admin/loans/${id}/review`, data);
export const updateLoan = (id, data) => request.patch(`/admin/loans/${id}`, data);
export const disburseLoan = (id, data) => request.post(`/admin/loans/${id}/disburse`, data);
export const settleLoan = (id) => request.post(`/admin/loans/${id}/settle`);
export const remindLoan = (id, data) => request.post(`/admin/loans/${id}/remind`, data);
export const collectLoan = (id, data) => request.post(`/admin/loans/${id}/collect`, data);
export const financeReconcileLoan = (id, data) => request.post(`/admin/loans/${id}/finance-reconcile`, data);
export const ackRepayAttempt = (id) => request.post(`/admin/loans/${id}/ack-repay-attempt`);
export const getLoanAssignees = (params) => request.get('/admin/loan-assignees', { params });
export const assignLoan = (id, data) => request.post(`/admin/loans/${id}/assign`, data);
