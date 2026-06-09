export const buildUsersQueryParams = (filters, isBusinessConsultant) => {
  const payload = {
    keyword: filters.keyword || undefined,
    skip: (filters.page - 1) * filters.size,
    limit: filters.size
  };

  if (isBusinessConsultant && Array.isArray(filters.dealDateRange) && filters.dealDateRange.length === 2) {
    payload.deal_time_start = filters.dealDateRange[0] || undefined;
    payload.deal_time_end = filters.dealDateRange[1] || undefined;
  }

  return payload;
};
