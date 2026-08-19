import './styles.css';
import { api, getToken } from './api.js';
import {
  compactPhone,
  formatCurrency,
  formatDate,
  formatDateTime,
  getPaymentSummary,
  getRiskSummary,
  getRiskTags,
  resolveLoanAmount,
  resolveUserId,
  getStatusText,
  getStatusTone,
} from './format.js';
import { TABS, buildQuery, buildSummaryCards, getActionForm, getAvailableActions, getTab } from './viewModel.js';

const app = document.querySelector('#app');

const state = {
  token: getToken(),
  admin: null,
  activeTab: 'profiles',
  segmentScope: 'REPAYMENTS',
  keyword: '',
  stats: {},
  repaymentStats: {},
  list: [],
  total: 0,
  loading: false,
  message: '',
  selected: null,
  activeAction: '',
  sheetHistory: false,
  logoutConfirm: false,
};

function html(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;');
}

function moneyCardValue(card) {
  return card.label.includes('额') || card.label.includes('回款') ? formatCurrency(card.value) : html(card.value);
}

function render() {
  app.innerHTML = state.token ? renderShell() : renderLogin();
  bindEvents();
}

function renderLogin() {
  return `
    <main class="login-page">
      <section class="login-hero">
        <img src="/logo.svg" alt="GalaCredit" class="login-icon" />
        <h1>GalaCredit Mobile Workspace</h1>
      </section>
      <form class="login-card" id="loginForm">
        <label>账号<input name="username" autocomplete="username" /></label>
        <label>密码<input name="password" type="password" autocomplete="current-password" /></label>
        <button class="primary-button" type="submit">登录</button>
        ${state.message ? `<p class="form-error">${html(state.message)}</p>` : ''}
      </form>
    </main>
  `;
}

function renderShell() {
  const tab = getTab(state.activeTab);
  const summaryCards = buildSummaryCards(tab.key, state.stats, state.total, state.repaymentStats);
  return `
    <main class="phone-shell">
      <header class="top-bar">
        <div>
          <span class="label">GalaCredit</span>
          <h1>${html(tab.title)}</h1>
        </div>
        <div class="top-actions">
          <button class="icon-button" id="refreshBtn" aria-label="刷新">↻</button>
          <button class="avatar-button" id="logoutBtn" aria-label="退出">${html((state.admin?.username || '管').slice(0, 1))}</button>
        </div>
      </header>

      <section class="summary-strip">
        ${summaryCards.map((card) => `
          <article class="metric-card">
            <span>${html(card.label)}</span>
            <strong>${moneyCardValue(card)}</strong>
            <p>${html(card.tip)}</p>
          </article>
        `).join('')}
      </section>

      <section class="toolbar-card">
        <input id="keywordInput" placeholder="搜索手机号 / 姓名 / 身份证" value="${html(state.keyword)}" />
        <button id="searchBtn">查询</button>
      </section>

      ${tab.segments ? renderSegments(tab) : ''}

      <section class="content-list">
        ${state.loading ? '<div class="empty-card">加载中...</div>' : renderList(tab)}
      </section>

      ${renderBottomNav()}
      ${state.selected ? renderSheet(tab, state.selected) : ''}
      ${state.logoutConfirm ? renderLogoutConfirm() : ''}
      ${state.message ? `<div class="toast">${html(state.message)}</div>` : ''}
    </main>
  `;
}

function renderLogoutConfirm() {
  return `
    <div class="confirm-mask" id="logoutCancelBackdrop"></div>
    <section class="confirm-dialog" role="dialog" aria-modal="true" aria-labelledby="logoutConfirmTitle">
      <h2 id="logoutConfirmTitle">退出当前账号？</h2>
      <div class="confirm-actions">
        <button class="danger-button" id="confirmLogoutBtn" type="button">登出</button>
        <button class="ghost-button" id="cancelLogoutBtn" type="button">取消</button>
      </div>
    </section>
  `;
}

function renderSegments(tab) {
  return `
    <nav class="segment-row">
      ${tab.segments.map((item) => `
        <button class="${state.segmentScope === item.scope ? 'active' : ''}" data-segment="${item.scope}">
          ${html(item.label)}
        </button>
      `).join('')}
    </nav>
  `;
}

function renderList(tab) {
  if (!state.list.length) {
    return '<div class="empty-card">暂无数据</div>';
  }
  return state.list.map((item) => (tab.key === 'profiles' ? renderUserCard(item) : renderLoanCard(item, tab))).join('');
}

function renderUserCard(user) {
  const latestLoan = user.latest_loan || {};
  return `
    <article class="data-card" data-id="${user.id}">
      <div class="card-head">
        <div>
          <h2 class="name-with-tags"><span>${html(user.name || '未实名')}</span>${renderRiskTags(user)}</h2>
          <p>${compactPhone(user.phone)} · ${html(user.source_channel_name || user.source_channel_sales_name || '自然流量')}</p>
        </div>
        <span class="status-pill ${getStatusTone(latestLoan.status)}">${getStatusText(latestLoan.status || user.face_auth_status)}</span>
      </div>
      <div class="card-grid">
        <span><b>${formatCurrency(user.approved_limit || latestLoan.approved_credit_limit || 0)}</b><em>授信额度</em></span>
        <span><b>${formatDate(user.created_at)}</b><em>注册时间</em></span>
      </div>
    </article>
  `;
}

function renderLoanCard(loan, tab) {
  const amount = resolveLoanAmount(loan);
  return `
    <article class="data-card" data-id="${loan.id}">
      <div class="card-head">
        <div>
          <h2 class="name-with-tags"><span>${html(loan.user_name || '未实名')}</span>${renderRiskTags(loan)}</h2>
          <p>${compactPhone(loan.user_phone)} · ${html(loan.relend_label || '初借')}</p>
        </div>
        <span class="status-pill ${getStatusTone(loan.status)}">${getStatusText(loan.status)}</span>
      </div>
      <div class="card-grid">
        <span><b>${formatCurrency(amount)}</b><em>${tab.key === 'cards' ? '订单支付' : '待处理金额'}</em></span>
        <span><b>${formatDate(loan.due_date || loan.application_submitted_at || loan.created_at)}</b><em>${loan.due_date ? '还款日' : '提交时间'}</em></span>
      </div>
      <p class="card-note">${html(loan.product_name || loan.review_note || loan.collection_note || '点击查看处理动作')}</p>
    </article>
  `;
}

function renderRiskTags(row) {
  const tags = getRiskTags(row);
  if (!tags.length) {
    return '';
  }
  return `
    <div class="risk-tag-row">
      ${tags.map((tag) => `
        <span class="risk-tag ${tag.tone}" title="${html(tag.detail)}">${html(tag.label)}</span>
      `).join('')}
    </div>
  `;
}

function renderBottomNav() {
  return `
    <nav class="bottom-nav">
      ${TABS.map((tab) => `
        <button class="${state.activeTab === tab.key ? 'active' : ''}" data-tab="${tab.key}">
          <span class="nav-icon">${renderNavIcon(tab.icon)}</span>
          <em>${html(tab.label)}</em>
        </button>
      `).join('')}
    </nav>
  `;
}

function renderNavIcon(name) {
  const icons = {
    folder: '<path d="M4 7.5h6l1.5 2H20v8.5H4z" /><path d="M4 7.5V6h5.5l1.2 1.5" />',
    clipboard: '<rect x="6" y="5.5" width="12" height="15" rx="2" /><path d="M9.5 5.5a2.5 2.5 0 0 1 5 0" /><path d="M9 11h6" /><path d="M9 15h4" />',
    card: '<rect x="4" y="6.5" width="16" height="11" rx="2" /><path d="M4 10h16" /><path d="M7 14.5h4" />',
    repay: '<path d="M7 8.5h8a4 4 0 0 1 0 8H8" /><path d="M7 8.5l3-3" /><path d="M7 8.5l3 3" /><path d="M17 15.5l-3 3" /><path d="M17 15.5l-3-3" />',
    ledger: '<rect x="5" y="5" width="14" height="16" rx="2" /><path d="M9 5v16" /><path d="M12 9h4" /><path d="M12 13h4" /><path d="M12 17h3" />',
  };
  return `
    <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
      ${icons[name] || icons.folder}
    </svg>
  `;
}

function renderSheet(tab, item) {
  return `
    <div class="sheet-mask" id="sheetMask"></div>
    <section class="action-sheet detail-sheet">
      <div class="sheet-handle"></div>
      <div class="sheet-title-row">
        <button class="back-button" id="closeSheetBtn" aria-label="返回">‹</button>
        <div>
          <h2 class="name-with-tags"><span>${html(tab.key === 'profiles' ? item.name || '客户档案' : item.user_name || '业务详情')}</span>${renderRiskTags(item)}</h2>
          <p>${tab.key === 'profiles' ? compactPhone(item.phone) : `${compactPhone(item.user_phone)} · ${html(item.relend_label || '初借')}`}</p>
        </div>
      </div>
      ${renderIdentityPhotos(item)}
      ${renderDetailSections(tab, item)}
      ${state.activeAction ? renderActionForm(state.activeAction, item) : renderActionDock(tab, item)}
    </section>
  `;
}

function renderIdentityPhotos(item) {
  const photos = [
    ['身份证正面', item.id_card_front_image_url],
    ['身份证反面', item.id_card_back_image_url],
    ['人脸照', item.face_image_url],
  ];
  return `
    <section class="sheet-section">
      <h3>认证照片</h3>
      <div class="identity-photo-grid">
        ${photos.map(([label, url]) => `
          <figure class="identity-photo">
            ${url ? `<img src="${html(api.mediaUrl(url))}" alt="${html(label)}" />` : '<div class="photo-empty">暂无</div>'}
            <figcaption>${html(label)}</figcaption>
          </figure>
        `).join('')}
      </div>
    </section>
  `;
}

function renderDetailSections(tab, item) {
  const profileRows = tab.key === 'profiles'
    ? [
        ['手机号', compactPhone(item.phone)],
        ['身份证', item.id_card_num || '--'],
        ['渠道', item.source_channel_name || item.source_channel_sales_name || '--'],
        ['最新状态', getStatusText(item.latest_loan?.status || item.face_auth_status)],
        ['授信额度', formatCurrency(item.approved_limit || item.latest_loan?.approved_credit_limit || 0)],
        ['注册时间', formatDateTime(item.created_at)],
        ['位置风控', item.location_risk_blocked ? item.location_risk_reason || '已锁定' : '未锁定'],
        ['风险校验', getRiskSummary(item)],
      ]
    : [
        ['状态', getStatusText(item.status)],
        ['手机号', compactPhone(item.user_phone)],
        ['身份证', item.user_id_card_num || '--'],
        ['渠道', item.user_source_channel_name || item.user_source_channel_sales_name || '--'],
        ['复购', item.relend_label || '初借'],
        ['提交时间', formatDateTime(item.application_submitted_at || item.created_at)],
        ['风险校验', getRiskSummary(item)],
      ];
  const orderRows = tab.key === 'profiles' ? [] : [
    ['商品', item.product_name || '--'],
    ['订单金额', formatCurrency(item.product_total_price || item.total_repayment_amount || item.credit_limit || 0)],
    ['还款进度', getPaymentSummary(item)],
    ['剩余应还', formatCurrency(item.remaining_repayment_amount || 0)],
    ['还款日', formatDateTime(item.due_date)],
    ['审批备注', item.review_note || '--'],
    ['催收备注', item.collection_note || '--'],
  ];
  return `
    ${renderInfoSection('核心信息', profileRows)}
    ${orderRows.length ? renderInfoSection('订单信息', orderRows) : ''}
  `;
}

function renderInfoSection(title, rows) {
  return `
    <section class="sheet-section">
      <h3>${html(title)}</h3>
      <div class="profile-grid">
        ${rows.map(([label, value]) => `<div><span>${html(label)}</span><strong>${html(value)}</strong></div>`).join('')}
      </div>
    </section>
  `;
}

function renderActionDock(tab, item) {
  const actions = getAvailableActions(tab.key, item, state);
  return `
    <section class="sheet-section action-dock">
      <h3>可执行操作</h3>
      <div class="sheet-actions action-grid">
        ${actions.map((action) => `<button class="${action.tone === 'danger' ? 'danger-button' : action.tone === 'primary' ? 'primary-button' : 'ghost-button'}" data-action="${html(action.key)}">${html(action.label)}</button>`).join('')}
      </div>
    </section>
  `;
}

function renderActionForm(action, item) {
  const form = getActionForm(action, item);
  return `
    <section class="sheet-section action-panel">
      <h3>${html(form.title)}</h3>
      <form class="mobile-action-form" id="actionForm">
        ${form.fields.map(renderActionField).join('')}
        ${form.fields.length ? '' : '<p class="confirm-text">确认执行该操作？</p>'}
        <div class="sheet-actions">
          <button class="primary-button" type="submit">提交</button>
          <button class="ghost-button" type="button" id="cancelActionBtn">取消</button>
        </div>
      </form>
    </section>
  `;
}

function renderActionField(field) {
  if (field.type === 'textarea') {
    return `<label class="full-field"><span>${html(field.label)}</span><textarea name="${html(field.name)}" rows="3" maxlength="255">${html(field.value || '')}</textarea></label>`;
  }
  if (field.type === 'select') {
    return `<label><span>${html(field.label)}</span><select name="${html(field.name)}">${field.options.map(([value, label]) => `<option value="${html(value)}" ${field.value === value ? 'selected' : ''}>${html(label)}</option>`).join('')}</select></label>`;
  }
  return `<label><span>${html(field.label)}</span><input name="${html(field.name)}" type="${html(field.type || 'text')}" min="${html(field.min ?? '')}" max="${html(field.max ?? '')}" step="${html(field.step ?? '')}" value="${html(field.value ?? '')}" /></label>`;
}

function bindEvents() {
  document.querySelector('#loginForm')?.addEventListener('submit', onLogin);
  document.querySelector('#logoutBtn')?.addEventListener('click', () => {
    state.logoutConfirm = true;
    render();
  });
  document.querySelector('#confirmLogoutBtn')?.addEventListener('click', () => {
    api.logout();
    state.token = '';
    state.admin = null;
    state.logoutConfirm = false;
    render();
  });
  document.querySelector('#cancelLogoutBtn')?.addEventListener('click', closeLogoutConfirm);
  document.querySelector('#logoutCancelBackdrop')?.addEventListener('click', closeLogoutConfirm);
  document.querySelector('#refreshBtn')?.addEventListener('click', loadData);
  document.querySelector('#searchBtn')?.addEventListener('click', () => {
    state.keyword = document.querySelector('#keywordInput')?.value || '';
    loadData();
  });
  document.querySelectorAll('[data-tab]').forEach((node) => {
    node.addEventListener('click', () => {
      state.activeTab = node.dataset.tab;
      state.selected = null;
      state.activeAction = '';
      state.segmentScope = state.activeTab === 'repayments' ? 'REPAYMENTS' : state.segmentScope;
      loadData();
    });
  });
  document.querySelectorAll('[data-segment]').forEach((node) => {
    node.addEventListener('click', () => {
      state.segmentScope = node.dataset.segment;
      loadData();
    });
  });
  document.querySelectorAll('.data-card').forEach((node) => {
    node.addEventListener('click', () => {
      openDetail(state.list.find((item) => String(item.id) === node.dataset.id));
    });
  });
  document.querySelector('#sheetMask')?.addEventListener('click', closeSheet);
  document.querySelector('#closeSheetBtn')?.addEventListener('click', closeSheet);
  document.querySelector('#cancelActionBtn')?.addEventListener('click', () => {
    state.activeAction = '';
    render();
  });
  document.querySelector('#actionForm')?.addEventListener('submit', submitActionForm);
  document.querySelectorAll('[data-action]').forEach((node) => node.addEventListener('click', () => openAction(node.dataset.action)));
}

function closeLogoutConfirm() {
  state.logoutConfirm = false;
  render();
}

function openAction(action) {
  state.activeAction = action;
  render();
}

async function onLogin(event) {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  try {
    await api.login(form.get('username'), form.get('password'));
    state.token = getToken();
    state.message = '';
    await initialize();
  } catch (error) {
    state.message = error.message;
    render();
  }
}

function closeSheet() {
  if (state.sheetHistory) {
    state.sheetHistory = false;
    window.history.back();
    return;
  }
  state.selected = null;
  state.activeAction = '';
  render();
}

function openDetail(item) {
  if (!item) {
    return;
  }
  if (!state.selected) {
    window.history.pushState({ mobileDetail: true }, '');
    state.sheetHistory = true;
  }
  state.selected = item;
  state.activeAction = '';
  render();
}

window.addEventListener('popstate', () => {
  if (state.selected) {
    state.selected = null;
    state.activeAction = '';
    state.sheetHistory = false;
    render();
  }
});

async function initialize() {
  if (!state.token) {
    render();
    return;
  }
  try {
    state.admin = await api.me();
  } catch (error) {
    api.logout();
    state.token = '';
    state.message = error.message;
    render();
    return;
  }
  await loadData();
}

async function loadData() {
  const tab = getTab(state.activeTab);
  state.loading = true;
  state.message = '';
  render();
  try {
    const shouldLoadRepaymentStats = tab.key === 'repayments' || tab.key === 'finance';
    const [stats, repaymentStats, page] = await Promise.all([
      api.stats(),
      shouldLoadRepaymentStats ? api.repaymentStats() : Promise.resolve({}),
      tab.endpoint === 'users'
        ? api.users(buildQuery(tab, state.keyword))
        : api.loans(buildQuery(tab, state.keyword, tab.key === 'repayments' ? state.segmentScope : undefined)),
    ]);
    state.stats = stats || {};
    state.repaymentStats = repaymentStats || {};
    state.list = page?.items || [];
    state.total = page?.total || state.list.length;
  } catch (error) {
    state.message = error.message;
    if (error.status === 401) {
      api.logout();
      state.token = '';
    }
  } finally {
    state.loading = false;
    state.selected = null;
    render();
  }
}

async function submitActionForm(event) {
  event.preventDefault();
  await runAction(state.activeAction, readActionFormPayload());
}

async function runAction(action, payload = {}) {
  const item = state.selected;
  if (!item) {
    return;
  }
  try {
    if (action === 'approve') {
      const credit = Number(payload.credit_limit || 0);
      if (!credit) return;
      await api.reviewLoan(item.id, {
        approved: true,
        credit_limit: credit,
        approval_discount_amount: Number(payload.approval_discount_amount || 0),
        term_days: Number(payload.term_days || 7),
        review_note: payload.review_note || '安卓端审批通过',
      });
    } else if (action === 'reject') {
      await api.reviewLoan(item.id, { approved: false, review_note: payload.review_note || '资料不符合要求' });
    } else if (action === 'set-credit') {
      await api.setApprovedCreditLimit(item.id, {
        credit_limit: Number(payload.credit_limit || 0),
        note: payload.note || '安卓端调整授信',
      });
    } else if (action === 'adjust-credit') {
      await api.adjustAvailableCredit(item.id, {
        amount: Number(payload.amount || 0),
        note: payload.note || '安卓端增加可用额度',
      });
    } else if (action === 'disburse') {
      await api.disburseLoan(item.id, { term_days: Number(payload.term_days || item.product_term_days || item.term_days || 7) });
    } else if (action === 'reject-card') {
      await api.rejectCardLoan(item.id, { note: payload.note || '安卓端拒绝发卡' });
    } else if (action === 'close-reissue') {
      await api.closeCardReissue(item.current_loan_id || item.id);
    } else if (action === 'reissue-card') {
      await api.reissueCardLoan(item.current_loan_id || item.id);
    } else if (action === 'save-note') {
      await api.updateLoan(item.id, { review_note: payload.review_note || '' });
    } else if (action === 'remind') {
      await api.remindLoan(item.id, { note: payload.note || '安卓端登记提醒' });
    } else if (action === 'collect') {
      await api.collectLoan(item.id, { note: payload.note || '安卓端登记催收' });
    } else if (action === 'ack') {
      await api.ackRepayAttempt(item.id);
    } else if (action === 'reconcile') {
      await api.financeReconcileLoan(item.id, {
        received_amount: Number(payload.received_amount || 0),
        reduction_amount: Number(payload.reduction_amount || 0),
        other_fee_amount: Number(payload.other_fee_amount || 0),
        note: payload.note || '安卓端登记平账',
      });
    } else if (action === 'settle') {
      await api.settleLoan(item.id);
    } else if (action === 'extend') {
      await api.extendLoan(item.id, {
        extension_type: payload.extension_type || 'FREE',
        days: Number(payload.days || 1),
        reduction_amount: Number(payload.reduction_amount || 0),
        note: payload.note || '安卓端账单展期',
      });
    } else if (action === 'blacklist-user') {
      await api.blacklistUser(resolveUserId(item), { note: payload.note || '安卓端一键拉黑' });
    } else if (action === 'remove-blacklist') {
      await api.removeBlacklistUser(resolveUserId(item), { note: payload.note || '安卓端移出黑名单' });
    } else if (action === 'unlock-location') {
      await api.unlockLocationRisk(resolveUserId(item));
    } else if (action === 'refresh-profile') {
      state.selected = await api.userDetail(item.id);
      state.activeAction = '';
      render();
      return;
    }
    state.message = '处理完成';
    await loadData();
  } catch (error) {
    state.message = error.message;
    render();
  }
}

function readActionFormPayload() {
  const form = document.querySelector('#actionForm');
  if (!form) {
    return {};
  }
  const data = new FormData(form);
  return Object.fromEntries([...data.entries()].map(([key, value]) => [key, String(value || '').trim()]));
}

initialize();
