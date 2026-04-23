export const MONTHLY_INTEREST_RATE = 0.02;
export const LOAN_PERIOD_DAYS = 7;

export const roundAmount = (value) => Math.round(Number(value || 0) * 100) / 100;

export const calculateTotalFeeAmount = (creditLimit, feeRate) =>
  roundAmount(Number(creditLimit || 0) * Number(feeRate || 0));

export const calculateInterestAmount = (creditLimit, termDays) => {
  const principal = Number(creditLimit || 0);
  const days = Number(termDays || 0);

  if (!principal || !days) {
    return 0;
  }

  return roundAmount(principal * MONTHLY_INTEREST_RATE * days / 30);
};

export const calculateGuaranteeFeeAmount = (totalFeeAmount, creditLimit, termDays) =>
  roundAmount(Math.max(Number(totalFeeAmount || 0) - calculateInterestAmount(creditLimit, termDays), 0));

export const calculateInstallmentPeriods = (termDays, periodDays = LOAN_PERIOD_DAYS) => {
  const days = Number(termDays || 0);
  if (!days || days < periodDays || days % periodDays !== 0) {
    return 0;
  }
  return days / periodDays;
};

export const buildLoanFeePreview = ({ creditLimit, feeRatePercentage, termDays }) => {
  const principal = Number(creditLimit || 0);
  const totalFeeAmount = calculateTotalFeeAmount(principal, Number(feeRatePercentage || 0) / 100);
  const interestAmount = calculateInterestAmount(principal, termDays);
  const guaranteeFeeAmount = calculateGuaranteeFeeAmount(totalFeeAmount, principal, termDays);
  const installmentPeriods = calculateInstallmentPeriods(termDays);
  const totalRepayment = roundAmount(principal + totalFeeAmount);
  const installmentAmount = installmentPeriods ? roundAmount(totalRepayment / installmentPeriods) : 0;

  return {
    principal,
    totalFeeAmount,
    interestAmount,
    guaranteeFeeAmount,
    totalRepayment,
    installmentPeriods,
    installmentAmount,
  };
};

export const resolveInterestAmount = (loan) => {
  if (loan?.interest_amount !== undefined && loan?.interest_amount !== null) {
    return Number(loan.interest_amount || 0);
  }

  return calculateInterestAmount(loan?.credit_limit, loan?.term_days);
};

export const resolveGuaranteeFeeAmount = (loan) => {
  if (loan?.guarantee_fee_amount !== undefined && loan?.guarantee_fee_amount !== null) {
    return Number(loan.guarantee_fee_amount || 0);
  }

  const totalFeeAmount = loan?.fee_amount !== undefined && loan?.fee_amount !== null
    ? Number(loan.fee_amount || 0)
    : calculateTotalFeeAmount(loan?.credit_limit, loan?.fee_rate);

  return calculateGuaranteeFeeAmount(totalFeeAmount, loan?.credit_limit, loan?.term_days);
};
