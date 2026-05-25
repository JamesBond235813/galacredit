export const buildApplicationsQueryParams = (filters, isSuperAdmin) => {
  const payload = {
    scope: 'REVIEWING',
    phone: filters.phone || undefined,
    status: filters.status === 'ALL' ? undefined : filters.status,
    review_admin_id: isSuperAdmin && filters.reviewAdminId ? Number(filters.reviewAdminId) : undefined,
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
