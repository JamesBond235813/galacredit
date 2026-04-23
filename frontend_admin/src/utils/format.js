export const statusTextMap = {
  INIT: '待补资料',
  REVIEWING: '审核中',
  APPROVED: '待下单',
  REJECTED: '未通过',
  WITHDRAWING: '待发卡',
  DISBURSED: '待付款',
  SETTLED: '已结清',
  OVERDUE: '已逾期'
};

export const statusTagMap = {
  INIT: 'info',
  REVIEWING: 'warning',
  APPROVED: 'primary',
  REJECTED: 'danger',
  WITHDRAWING: 'warning',
  DISBURSED: 'success',
  SETTLED: 'info',
  OVERDUE: 'danger'
};

export const getStatusText = (status) => statusTextMap[status] || status || '--';
export const getStatusTagType = (status) => statusTagMap[status] || 'info';

export const formatCurrency = (value) => {
  const amount = Number(value || 0);
  return `￥${amount.toLocaleString('zh-CN', {
    minimumFractionDigits: amount % 1 === 0 ? 0 : 2,
    maximumFractionDigits: 2
  })}`;
};

export const formatRate = (value) => `${(Number(value || 0) * 100).toFixed(0)}%`;

export const formatDateTime = (value) => {
  if (!value) {
    return '--';
  }

  return new Date(value).toLocaleString('zh-CN', { hour12: false });
};

export const formatDate = (value) => {
  if (!value) {
    return '--';
  }

  return new Date(value).toLocaleDateString('zh-CN');
};

export const formatTime = (value) => {
  if (!value) {
    return '--';
  }

  return new Date(value).toLocaleTimeString('zh-CN', { hour12: false });
};

export const maskCard = (value) => {
  if (!value) {
    return '--';
  }

  if (value.length <= 8) {
    return value;
  }

  return `${value.slice(0, 4)} **** **** ${value.slice(-4)}`;
};
