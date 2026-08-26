export const ADMIN_PAGE_OPTIONS = [
  { key: 'overview', label: '洞察看板', route: '/overview', iconKey: 'overview' },
  { key: 'monitoring', label: '运营监控', route: '/monitoring', iconKey: 'monitoring' },
  { key: 'message-center', label: '消息中心', route: '/message-center', iconKey: 'messageCenter' },
  { key: 'users', label: '用户档案', route: '/users', iconKey: 'users' },
  { key: 'kyc-review', label: 'KYC复核', route: '/kyc-review', iconKey: 'kycReview' },
  { key: 'applications', label: '申请审批', route: '/applications', iconKey: 'applications' },
  { key: 'disbursements', label: '待MoMo放款', route: '/disbursements', iconKey: 'disbursements' },
  { key: 'disbursement-failures', label: '放款失败客户', route: '/disbursement-failures', iconKey: 'disbursementFailures' },
  { key: 'repayments', label: '还款管理', route: '/repayments', iconKey: 'repayments' },
  { key: 'collections', label: '催收管理', route: '/collections', iconKey: 'collections' },
  { key: 'financials', label: '财务平账', route: '/financials', iconKey: 'financials' },
  { key: 'audit-log', label: '操作审计', route: '/audit-log', iconKey: 'auditLog' },
  { key: 'risk-single-query', label: '风控报告单查', route: '/risk-single-query', iconKey: 'riskSingleQuery' },
  { key: 'risk-strategy', label: '风控策略', route: '/risk-strategy', iconKey: 'riskStrategy' },
  { key: 'blacklist', label: '黑名单', route: '/blacklist', iconKey: 'users' },
  { key: 'overdue-config', label: '逾期配置', route: '/overdue-config', iconKey: 'overdueConfig' },
  { key: 'content-config', label: '运营配置', route: '/content-config', iconKey: 'contentConfig' },
  { key: 'products', label: '贷款产品', route: '/products', iconKey: 'products' },
  { key: 'ecard-pool', label: '历史卡池兼容', route: '/ecard-pool', iconKey: 'ecardPool' },
  { key: 'channels', label: '渠道管理', route: '/channels', iconKey: 'channels' },
  { key: 'exclusive-links', label: '专属链接', route: '/exclusive-links', iconKey: 'channels' },
  { key: 'admin-users', label: '后台用户', route: '/admin-users', iconKey: 'adminUsers' }
];

export const ADMIN_MENU_GROUPS = [
  { key: 'operations', iconKey: 'overview', itemKeys: ['overview', 'monitoring', 'message-center'] },
  { key: 'customerRisk', iconKey: 'users', itemKeys: ['users', 'kyc-review', 'risk-single-query', 'audit-log', 'blacklist'] },
  { key: 'loanOperations', iconKey: 'applications', itemKeys: ['applications', 'disbursements', 'disbursement-failures'] },
  { key: 'repaymentCollections', iconKey: 'repayments', itemKeys: ['repayments', 'collections', 'financials'] },
  { key: 'productsChannels', iconKey: 'products', itemKeys: ['products', 'overdue-config', 'content-config', 'channels', 'exclusive-links', 'ecard-pool'] },
  { key: 'riskStrategy', iconKey: 'riskSingleQuery', itemKeys: ['risk-strategy'] },
  { key: 'system', iconKey: 'adminUsers', itemKeys: ['admin-users'] }
];

export const ADMIN_DEFAULT_ROUTE = ADMIN_PAGE_OPTIONS[0].route;
export const ADMIN_PAGE_PERMISSION_KEYS = ADMIN_PAGE_OPTIONS.map((item) => item.key);
export const ADMIN_ACTION_PERMISSION_OPTIONS = [
  { key: 'user-location-risk-unlock', label: '解除位置风控' },
  { key: 'loan-review-takeover', label: '审核转入自己' }
];
export const ADMIN_ACTION_PERMISSION_KEYS = ADMIN_ACTION_PERMISSION_OPTIONS.map((item) => item.key);
export const ALL_ADMIN_PERMISSION_KEYS = [...ADMIN_PAGE_PERMISSION_KEYS, ...ADMIN_ACTION_PERMISSION_KEYS];

export const ADMIN_ROLE_OPTIONS = [
  { key: 'ADMIN', label: '管理员', description: '所有页面与操作权限' },
  { key: 'REVIEW', label: '审核', description: '用户档案、KYC复核、申请审批、还款管理' },
  { key: 'FINANCE', label: '财务', description: 'MoMo放款、财务平账、消息中心、贷款产品、历史卡池兼容' },
  { key: 'COLLECTION', label: '催收', description: '催收管理、消息中心' },
  { key: 'BUSINESS_CONSULTANT', label: '业务顾问', description: '用户档案、专属链接页面' }
];

export const ADMIN_ROLE_PERMISSION_MAP = {
  ADMIN: [...ALL_ADMIN_PERMISSION_KEYS],
  REVIEW: ['users', 'applications', 'repayments', 'risk-single-query', 'blacklist', 'loan-review-takeover', 'kyc-review', 'audit-log', 'message-center', 'monitoring'],
  FINANCE: ['disbursements', 'disbursement-failures', 'financials', 'products', 'ecard-pool', 'blacklist', 'message-center', 'monitoring', 'content-config'],
  COLLECTION: ['collections', 'blacklist', 'message-center', 'audit-log'],
  BUSINESS_CONSULTANT: ['users', 'exclusive-links']
};

export const normalizeAdminRoles = (roles) => {
  if (!Array.isArray(roles)) {
    return [];
  }

  const roleKeys = ADMIN_ROLE_OPTIONS.map((item) => item.key);
  const normalized = [];
  roles.forEach((item) => {
    const key = String(item || '').trim().toUpperCase();
    if (roleKeys.includes(key) && !normalized.includes(key)) {
      normalized.push(key);
    }
  });
  return normalized;
};

export const buildPermissionsFromRoles = (roles) => {
  const normalizedRoles = normalizeAdminRoles(roles);
  const merged = [];
  normalizedRoles.forEach((role) => {
    (ADMIN_ROLE_PERMISSION_MAP[role] || []).forEach((item) => {
      if (ALL_ADMIN_PERMISSION_KEYS.includes(item) && !merged.includes(item)) {
        merged.push(item);
      }
    });
  });
  return merged;
};

export const normalizeAdminPermissions = (permissions) => {
  if (!Array.isArray(permissions)) {
    return [];
  }

  const uniqueKeys = [];
  permissions.forEach((item) => {
    const key = String(item || '').trim();
    if (ALL_ADMIN_PERMISSION_KEYS.includes(key) && !uniqueKeys.includes(key)) {
      uniqueKeys.push(key);
    }
  });
  return uniqueKeys;
};

export const readStoredAdminProfile = () => {
  if (typeof window === 'undefined') {
    return null;
  }

  const raw = window.localStorage.getItem('admin_profile');
  if (!raw) {
    return null;
  }

  try {
    return JSON.parse(raw);
  } catch (error) {
    window.localStorage.removeItem('admin_profile');
    return null;
  }
};

export const writeStoredAdminProfile = (profile) => {
  if (typeof window === 'undefined') {
    return;
  }
  window.localStorage.setItem('admin_profile', JSON.stringify(profile || {}));
};

export const clearStoredAdminAuth = () => {
  if (typeof window === 'undefined') {
    return;
  }
  window.localStorage.removeItem('admin_token');
  window.localStorage.removeItem('admin_profile');
};

export const getStoredAdminPermissions = () => {
  const profile = readStoredAdminProfile();
  if (!profile) {
    return null;
  }
  return resolvePermissions(profile);
};

const resolvePermissions = (permissions) => {
  if (permissions === undefined) {
    return getStoredAdminPermissions();
  }
  if (Array.isArray(permissions)) {
    return normalizeAdminPermissions(permissions);
  }
  if (permissions && typeof permissions === 'object') {
    const rolePermissions = buildPermissionsFromRoles(permissions.roles);
    const explicitPermissions = normalizeAdminPermissions(permissions.permissions);
    const merged = [];
    [...rolePermissions, ...explicitPermissions].forEach((item) => {
      if (ALL_ADMIN_PERMISSION_KEYS.includes(item) && !merged.includes(item)) {
        merged.push(item);
      }
    });
    if (merged.length) {
      return merged;
    }
    return normalizeAdminPermissions(permissions.permissions);
  }
  return [];
};

export const hasAdminPermission = (permissions, permissionKey) => {
  if (!permissionKey) {
    return true;
  }

  const normalized = resolvePermissions(permissions);
  if (normalized === null) {
    return true;
  }
  return normalized.includes(permissionKey);
};

export const getFirstAccessibleRoute = (permissions) => {
  const normalized = resolvePermissions(permissions);
  if (!Array.isArray(normalized) || !normalized.length) {
    return ADMIN_DEFAULT_ROUTE;
  }

  const firstMatchedPage = ADMIN_PAGE_OPTIONS.find((item) => normalized.includes(item.key));
  return firstMatchedPage?.route || ADMIN_DEFAULT_ROUTE;
};
