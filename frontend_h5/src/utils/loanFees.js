export const MONTHLY_INTEREST_RATE = 0.02;

const roundAmount = (value) => Math.round(Number(value || 0) * 100) / 100;

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

  return calculateGuaranteeFeeAmount(loan?.fee_amount, loan?.credit_limit, loan?.term_days);
};
