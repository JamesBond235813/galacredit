export const buildApplicationsQueryParams = (filters, isSuperAdmin, canReviewTakeover = false) => {
  const isTakeoverStatus = filters.status === 'TAKEOVER';
  const shouldUseTakeoverPool = !isSuperAdmin
    && canReviewTakeover
    && (isTakeoverStatus || filters.takeoverPool)
    && (isTakeoverStatus || filters.status === 'REVIEWING');
  const payload = {
    scope: 'REVIEWING',
    phone: filters.phone || undefined,
    status: filters.status === 'ALL' ? undefined : (isTakeoverStatus ? 'REVIEWING' : filters.status),
    review_admin_id: isSuperAdmin && filters.reviewAdminId ? Number(filters.reviewAdminId) : undefined,
    takeover_pool: shouldUseTakeoverPool ? true : undefined,
    skip: (filters.page - 1) * filters.size,
    limit: filters.size
  };

  if (filters.relendFilter === '3_PLUS') {
    payload.relend_min_count = 3;
  } else if (filters.relendFilter !== 'ALL') {
    payload.relend_count = Number(filters.relendFilter);
  }

  return payload;
};
