import { describe, expect, it } from 'vitest';

import { buildQuery, getActionForm, getAvailableActions, getTab } from './viewModel.js';

describe('mobile console tab query mapping', () => {
  it('uses user keyword for profile tab', () => {
    expect(buildQuery(getTab('profiles'), '张三')).toMatchObject({
      keyword: '张三',
      skip: 0,
      limit: 20,
    });
  });

  it('maps repayment default segment to the web repayment scope', () => {
    expect(buildQuery(getTab('repayments'), '', 'REPAYMENTS')).toMatchObject({
      scope: 'REPAYMENTS',
      due_date_preset: 'TODAY',
      skip: 0,
      limit: 20,
    });
  });

  it('maps overdue segment to the web collection scope', () => {
    expect(buildQuery(getTab('repayments'), '', 'OVERDUE')).toMatchObject({
      scope: 'OVERDUE',
      skip: 0,
      limit: 20,
    });
  });

  it('maps finance tab to the existing web backend scope', () => {
    expect(buildQuery(getTab('finance'), '188')).toMatchObject({
      scope: 'FINANCE',
      phone: '188',
    });
  });

  it('exposes mobile card actions that match web admin operations', () => {
    const actions = getAvailableActions('cards', { user_blacklist_hit: false }).map((item) => item.key);
    expect(actions).toEqual(['disburse', 'reject-card', 'close-reissue', 'save-note', 'blacklist-user']);
  });

  it('hides location unlock when the current admin cannot unlock', () => {
    const actions = getAvailableActions('profiles', { location_risk_blocked: true, can_unlock_location_risk: false }).map((item) => item.key);
    expect(actions).not.toContain('unlock-location');
  });

  it('builds finance reconcile form using backend field names', () => {
    const form = getActionForm('reconcile', { remaining_repayment_amount: 123 });
    expect(form.fields.map((item) => item.name)).toEqual(['received_amount', 'reduction_amount', 'other_fee_amount', 'note']);
    expect(form.fields[0].value).toBe(123);
  });
});
