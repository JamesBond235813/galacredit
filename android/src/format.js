export const statusTextMap = {
  INIT: '待补资料',
  REVIEWING: '审核中',
  APPROVED: '待下单',
  REJECTED: '未通过',
  WITHDRAWING: '待发卡',
  DISBURSED: '待付款',
  SETTLED: '已结清',
  OVERDUE: '已逾期',
  CARD_REJECTED: '拒发卡',
};

export const statusToneMap = {
  INIT: 'neutral',
  REVIEWING: 'warning',
  APPROVED: 'brand',
  REJECTED: 'danger',
  WITHDRAWING: 'warning',
  DISBURSED: 'success',
  SETTLED: 'neutral',
  OVERDUE: 'danger',
  CARD_REJECTED: 'danger',
};

export function getStatusText(status) {
  return statusTextMap[status] || status || '--';
}

export function getStatusTone(status) {
  return statusToneMap[status] || 'neutral';
}

export function formatCurrency(value) {
  const amount = Number(value || 0);
  return `¥${amount.toLocaleString('zh-CN', {
    minimumFractionDigits: amount % 1 === 0 ? 0 : 2,
    maximumFractionDigits: 2,
  })}`;
}

export function formatDateTime(value) {
  if (!value) {
    return '--';
  }
  return new Date(value).toLocaleString('zh-CN', { hour12: false });
}

export function formatDate(value) {
  if (!value) {
    return '--';
  }
  return new Date(value).toLocaleDateString('zh-CN');
}

export function compactPhone(value) {
  const phone = String(value || '');
  if (phone.length !== 11) {
    return phone || '--';
  }
  return `${phone.slice(0, 3)} ${phone.slice(3, 7)} ${phone.slice(7)}`;
}

export function pickMoney(row, keys) {
  const key = keys.find((item) => Number(row?.[item] || 0) > 0);
  return key ? row[key] : 0;
}

export function formatPercent(value) {
  const ratio = Number(value || 0);
  return `${(ratio * 100).toFixed(1)}%`;
}

export function resolveUserId(row = {}) {
  return row.user_id || row.owner_id || row.id;
}

export function resolveLoanAmount(row = {}) {
  return pickMoney(row, [
    'remaining_repayment_amount',
    'product_total_price',
    'total_repayment_amount',
    'approved_credit_limit',
    'credit_limit',
  ]);
}

export function getPaymentSummary(row = {}) {
  const total = Number(row.total_repayment_amount || row.product_total_price || 0);
  const remaining = Number(row.remaining_repayment_amount || 0);
  if (!total) {
    return '暂无账单';
  }
  const paid = Math.max(total - remaining, 0);
  return `${formatCurrency(paid)} / ${formatCurrency(total)}`;
}

export function getRoleLabels(admin = {}) {
  const labels = {
    ADMIN: '超管',
    REVIEWER: '审批',
    DISBURSEMENT: '发卡',
    REPAYMENT: '回款',
    COLLECTION: '催收',
    FINANCE: '财务',
    BUSINESS_CONSULTANT: '商务',
  };
  return (admin.roles || []).map((role) => labels[role] || role);
}

export function getRiskTags(row = {}) {
  const blacklistHit = Boolean(row.user_blacklist_hit ?? row.blacklist_hit ?? row.current_blacklist_hit);
  const riskListHit = Boolean(row.user_risk_list_hit ?? row.risk_list_hit ?? row.current_risk_list_hit);
  const locationRiskHit = Boolean(row.user_location_risk_hit ?? row.location_risk_blocked ?? row.location_risk_hit);
  return [
    {
      key: 'location',
      label: '风险区域',
      hit: locationRiskHit,
      detail: row.user_location_risk_detail || row.location_risk_reason || 'GPS或IP命中风险位置',
      tone: 'dark',
    },
    {
      key: 'risk-list',
      label: '风险名单',
      hit: riskListHit,
      detail: row.user_risk_list_reason || row.risk_list_reason || '命中风险名单',
      tone: 'danger',
    },
    {
      key: 'blacklist',
      label: '黑名单',
      hit: blacklistHit,
      detail: row.user_blacklist_reason || row.blacklist_reason || '命中黑名单',
      tone: 'danger',
    },
  ].filter((item) => item.hit);
}

export function getRiskSummary(row = {}) {
  const tags = getRiskTags(row);
  if (!tags.length) {
    return '未命中';
  }
  return tags.map((item) => item.label).join('、');
}
