export const ADMIN_PAGE_OPTIONS = [
  { key: 'overview', label: '洞察看板', route: '/overview', iconKey: 'overview' },
  { key: 'users', label: '用户档案', route: '/users', iconKey: 'users' },
  { key: 'applications', label: '申请审批', route: '/applications', iconKey: 'applications' },
  { key: 'disbursements', label: '待发卡', route: '/disbursements', iconKey: 'disbursements' },
  { key: 'repayments', label: '还款管理', route: '/repayments', iconKey: 'repayments' },
  { key: 'collections', label: '催收管理', route: '/collections', iconKey: 'collections' },
  { key: 'financials', label: '财务平账', route: '/financials', iconKey: 'financials' },
  { key: 'products', label: '商品管理', route: '/products', iconKey: 'products' },
  { key: 'ecard-pool', label: '卡池管理', route: '/ecard-pool', iconKey: 'ecardPool' },
  { key: 'channels', label: '渠道管理', route: '/channels', iconKey: 'channels' },
  { key: 'admin-users', label: '后台用户', route: '/admin-users', iconKey: 'adminUsers' }
];

export const ADMIN_DEFAULT_ROUTE = ADMIN_PAGE_OPTIONS[0].route;
export const ADMIN_PAGE_PERMISSION_KEYS = ADMIN_PAGE_OPTIONS.map((item) => item.key);

export const ADMIN_ROLE_OPTIONS = [
  { key: 'ADMIN', label: '管理员', description: '所有页面与操作权限' },
  { key: 'REVIEW', label: '审核', description: '用户档案、申请审批、还款管理' },
  { key: 'FINANCE', label: '财务', description: '待发卡、财务平账、商品管理、卡池管理' },
  { key: 'COLLECTION', label: '催收', description: '仅催收管理' }
];

export const ADMIN_ROLE_PERMISSION_MAP = {
  ADMIN: [...ADMIN_PAGE_PERMISSION_KEYS],
  REVIEW: ['users', 'applications', 'repayments'],
  FINANCE: ['disbursements', 'financials', 'products', 'ecard-pool'],
  COLLECTION: ['collections']
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
      if (ADMIN_PAGE_PERMISSION_KEYS.includes(item) && !merged.includes(item)) {
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
    if (ADMIN_PAGE_PERMISSION_KEYS.includes(key) && !uniqueKeys.includes(key)) {
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
      if (ADMIN_PAGE_PERMISSION_KEYS.includes(item) && !merged.includes(item)) {
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
