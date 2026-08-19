import { adminLocale } from '../i18n/adminLocale';

export const statusTextMap = {
  'zh-CN': {
    INIT: '待补资料', REVIEWING: '审核中', APPROVED: '待下单', REJECTED: '未通过',
    WITHDRAWING: '待MoMo放款', DISBURSED: '已放款', FIRST_BORROW: '首借',
    SETTLED: '已结清', OVERDUE: '已逾期', CARD_REJECTED: '审批退回'
  },
  'en-GH': {
    INIT: 'Profile incomplete', REVIEWING: 'Under review', APPROVED: 'Awaiting confirmation', REJECTED: 'Rejected',
    WITHDRAWING: 'Pending MoMo disbursement', DISBURSED: 'Disbursed', FIRST_BORROW: 'First loan',
    SETTLED: 'Settled', OVERDUE: 'Overdue', CARD_REJECTED: 'Returned by approval'
  }
};

export const statusTagMap = {
  INIT: 'info',
  REVIEWING: 'warning',
  APPROVED: 'primary',
  REJECTED: 'danger',
  WITHDRAWING: 'warning',
  DISBURSED: 'success',
  FIRST_BORROW: 'success',
  SETTLED: 'info',
  OVERDUE: 'danger',
  CARD_REJECTED: 'danger'
};

export const getStatusText = (status) => statusTextMap[adminLocale.value]?.[status] || status || '--';
export const getStatusTagType = (status) => statusTagMap[status] || 'info';

export const formatCurrency = (value) => {
  const amount = Number(value || 0);
  return `GHS ${amount.toLocaleString('en-GH', {
    minimumFractionDigits: amount % 1 === 0 ? 0 : 2,
    maximumFractionDigits: 2
  })}`;
};

export const formatPhone = (value) => {
  const phone = String(value || '').trim();
  if (/^233\d{9}$/.test(phone)) {
    return `+233 ${phone.slice(3, 5)} ${phone.slice(5)}`;
  }
  return phone || '--';
};

export const formatRate = (value) => `${(Number(value || 0) * 100).toFixed(0)}%`;

export const formatDateTime = (value) => {
  if (!value) {
    return '--';
  }

  return new Date(value).toLocaleString(adminLocale.value, { hour12: false });
};

export const formatDate = (value) => {
  if (!value) {
    return '--';
  }

  return new Date(value).toLocaleDateString(adminLocale.value);
};

export const formatTime = (value) => {
  if (!value) {
    return '--';
  }

  return new Date(value).toLocaleTimeString(adminLocale.value, { hour12: false });
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
