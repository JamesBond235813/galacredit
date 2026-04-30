export const getDealColumnConfig = (isBusinessConsultant) => {
  if (isBusinessConsultant) {
    return {
      timeLabel: '成交时间',
      amountLabel: '成交金额',
      timeKey: 'first_disbursed_at',
      amountKey: 'first_deal_amount'
    };
  }

  return {
    timeLabel: '最近成交时间',
    amountLabel: '最近成交金额',
    timeKey: 'latest_disbursed_at',
    amountKey: 'latest_deal_amount'
  };
};
