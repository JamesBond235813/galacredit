export const MONTHLY_INTEREST_RATE = 0.02;

const roundAmount = (value) => Math.round(Number(value || 0) * 100) / 100;

export const calculateInterestDays = (termDays, interestStartDay = 1, repaymentDueDay = termDays) => {
  const start = Math.max(Number(interestStartDay || 1), 1);
  const due = Math.max(Number(repaymentDueDay || termDays || 0), 0);
  return Math.max(Math.floor(due - start + 1), 0);
};

export const resolveInterestRate = (loan) => {
  const components = loan?.fee_components_json;
  let parsed = components;
  if (typeof components === 'string') {
    try { parsed = JSON.parse(components); } catch { parsed = null; }
  }
  const rate = parsed?.interest_rate;
  return Number(rate ?? loan?.interest_rate ?? MONTHLY_INTEREST_RATE);
};

export const calculateInterestAmount = (creditLimit, termDays, interestStartDay = 1, repaymentDueDay = termDays, interestRate = MONTHLY_INTEREST_RATE) => {
  const principal = Number(creditLimit || 0);
  const days = calculateInterestDays(termDays, interestStartDay, repaymentDueDay);

  if (!principal || !days) {
    return 0;
  }

  return roundAmount(principal * Number(interestRate || 0) * days / 30);
};

export const calculateGuaranteeFeeAmount = (totalFeeAmount, creditLimit, termDays, interestStartDay = 1, repaymentDueDay = termDays, interestRate = MONTHLY_INTEREST_RATE) =>
  roundAmount(Math.max(Number(totalFeeAmount || 0) - calculateInterestAmount(creditLimit, termDays, interestStartDay, repaymentDueDay, interestRate), 0));

export const resolveInterestAmount = (loan) => {
  if (loan?.interest_amount !== undefined && loan?.interest_amount !== null) {
    return Number(loan.interest_amount || 0);
  }

  return calculateInterestAmount(loan?.credit_limit, loan?.term_days, loan?.interest_start_day, loan?.repayment_due_day, resolveInterestRate(loan));
};

export const resolveGuaranteeFeeAmount = (loan) => {
  if (loan?.guarantee_fee_amount !== undefined && loan?.guarantee_fee_amount !== null) {
    return Number(loan.guarantee_fee_amount || 0);
  }

  return calculateGuaranteeFeeAmount(loan?.fee_amount, loan?.credit_limit, loan?.term_days, loan?.interest_start_day, loan?.repayment_due_day, resolveInterestRate(loan));
};
