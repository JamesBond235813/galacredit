export const TABS = [
  {
    key: 'profiles',
    label: '档案',
    icon: 'folder',
    title: '客户档案',
    subtitle: '实名资料、渠道来源与授信状态',
    endpoint: 'users',
  },
  {
    key: 'applications',
    label: '申请',
    icon: 'clipboard',
    title: '申请审批',
    subtitle: '按移动端卡片核对资料并处理额度',
    endpoint: 'loans',
    query: { scope: 'REVIEWING', status: 'REVIEWING' },
  },
  {
    key: 'cards',
    label: '发卡',
    icon: 'card',
    title: '待发卡',
    subtitle: '核对商品、账期和卡池库存',
    endpoint: 'loans',
    query: { scope: 'WITHDRAWING' },
  },
  {
    key: 'repayments',
    label: '回款',
    icon: 'repay',
    title: '回款管理',
    subtitle: '当日还款与逾期催收集中跟进',
    endpoint: 'loans',
    query: { scope: 'REPAYMENTS', due_date_preset: 'TODAY' },
    segments: [
      { label: '当日还款', scope: 'REPAYMENTS', due_date_preset: 'TODAY' },
      { label: '逾期催收', scope: 'OVERDUE', due_date_preset: undefined },
    ],
  },
  {
    key: 'finance',
    label: '平账',
    icon: 'ledger',
    title: '财务平账',
    subtitle: '登记收款、减免与结清状态',
    endpoint: 'loans',
    query: { scope: 'FINANCE' },
  },
];

export const ACTIONS = {
  profiles: [
    { key: 'refresh-profile', label: '刷新档案', tone: 'primary' },
    { key: 'unlock-location', label: '解除位置风控', tone: 'ghost', visible: (item) => item.location_risk_blocked && item.can_unlock_location_risk },
    { key: 'blacklist-user', label: '一键拉黑', tone: 'danger', visible: (item) => !item.blacklist_hit },
    { key: 'remove-blacklist', label: '移出黑名单', tone: 'ghost', visible: (item) => item.blacklist_hit },
    { key: 'reissue-card', label: '开启二次发卡', tone: 'ghost', visible: (item) => Boolean(item.current_loan_id) },
    { key: 'close-reissue', label: '退回待下单', tone: 'ghost', visible: (item) => Boolean(item.current_loan_id) },
  ],
  applications: [
    { key: 'approve', label: '审批通过', tone: 'primary' },
    { key: 'reject', label: '审批拒绝', tone: 'danger' },
    { key: 'set-credit', label: '调整授信', tone: 'ghost' },
    { key: 'adjust-credit', label: '增加可用额度', tone: 'ghost' },
    { key: 'blacklist-user', label: '一键拉黑', tone: 'danger', visible: (item) => !item.user_blacklist_hit },
  ],
  cards: [
    { key: 'disburse', label: '确认发卡', tone: 'primary' },
    { key: 'reject-card', label: '拒绝发卡', tone: 'danger' },
    { key: 'close-reissue', label: '退回待下单', tone: 'ghost' },
    { key: 'save-note', label: '保存备注', tone: 'ghost' },
    { key: 'blacklist-user', label: '一键拉黑', tone: 'danger', visible: (item) => !item.user_blacklist_hit },
  ],
  repayments: [
    { key: 'remind', label: '登记提醒', tone: 'primary', visible: (_item, state) => state.segmentScope !== 'OVERDUE' },
    { key: 'collect', label: '登记催收', tone: 'primary', visible: (_item, state) => state.segmentScope === 'OVERDUE' },
    { key: 'ack', label: '确认还款申请', tone: 'ghost' },
    { key: 'extend', label: '账单展期', tone: 'ghost' },
    { key: 'adjust-credit', label: '增加可用额度', tone: 'ghost' },
    { key: 'blacklist-user', label: '一键拉黑', tone: 'danger', visible: (item) => !item.user_blacklist_hit },
  ],
  finance: [
    { key: 'reconcile', label: '登记平账', tone: 'primary' },
    { key: 'settle', label: '确认结清', tone: 'ghost' },
    { key: 'extend', label: '账单展期', tone: 'ghost' },
  ],
};

export function getTab(key) {
  return TABS.find((item) => item.key === key) || TABS[0];
}

export function buildQuery(tab, keyword, segmentScope) {
  const query = { ...(tab.query || {}), skip: 0, limit: 20 };
  const segment = tab.segments?.find((item) => item.scope === segmentScope);
  const normalizedKeyword = String(keyword || '').trim();
  if (segment) {
    query.scope = segment.scope;
    query.due_date_preset = segment.due_date_preset;
  }
  if (normalizedKeyword) {
    query[tab.key === 'profiles' ? 'keyword' : 'phone'] = normalizedKeyword;
  }
  return query;
}

export function buildSummaryCards(tabKey, stats = {}, listTotal = 0, repaymentStats = {}) {
  if (tabKey === 'profiles') {
    return [
      { label: '总档案', value: stats.total_users || 0, tip: '全部注册客户' },
      { label: '今日新增', value: stats.today_new_users || 0, tip: '今天进入系统' },
    ];
  }
  if (tabKey === 'applications') {
    return [
      { label: '待审批', value: stats.reviewing_loans || listTotal, tip: '需要核验资料' },
      { label: '今日申请', value: stats.today_applications || 0, tip: '当天提交' },
    ];
  }
  if (tabKey === 'cards') {
    return [
      { label: '待发卡', value: stats.withdrawing_loans || listTotal, tip: '等待卡池匹配' },
      { label: '今日发卡额', value: stats.today_disbursed_amount || 0, tip: '已发放面值' },
    ];
  }
  if (tabKey === 'repayments') {
    return [
      { label: '今日到期', value: stats.due_today_loans || 0, tip: '当日应跟进' },
      { label: '逾期订单', value: stats.overdue_loans || 0, tip: '催收优先处理' },
    ];
  }
  return [
    { label: '列表订单', value: listTotal, tip: '可财务处理' },
    { label: '已收金额', value: repaymentStats.received_amount || 0, tip: `其他费用 ${repaymentStats.other_fee_amount || 0}` },
  ];
}

export function getAvailableActions(tabKey, item = {}, state = {}) {
  return (ACTIONS[tabKey] || []).filter((action) => !action.visible || action.visible(item, state));
}

export function getActionForm(action, item = {}) {
  const remaining = Number(item.remaining_repayment_amount || 0);
  const credit = Number(item.approved_credit_limit || item.credit_limit || 1000);
  const termDays = Number(item.product_term_days || item.term_days || 7);
  const forms = {
    approve: {
      title: '审批通过',
      fields: [
        { name: 'credit_limit', label: '授信额度', type: 'number', value: credit, min: 0, step: 100 },
        { name: 'approval_discount_amount', label: '减免额度', type: 'number', value: Number(item.approval_discount_amount || 0), min: 0, step: 100 },
        { name: 'term_days', label: '期限天数', type: 'number', value: termDays, min: 1, max: 364, step: 1 },
        { name: 'review_note', label: '审批备注', type: 'textarea', value: item.review_note || '安卓端审批通过' },
      ],
    },
    reject: {
      title: '审批拒绝',
      fields: [{ name: 'review_note', label: '拒绝原因', type: 'textarea', value: item.review_note || '资料不符合要求' }],
    },
    'set-credit': {
      title: '调整授信',
      fields: [
        { name: 'credit_limit', label: '新授信额度', type: 'number', value: credit, min: 0, step: 100 },
        { name: 'note', label: '调整说明', type: 'textarea', value: '安卓端调减授信额度' },
      ],
    },
    'adjust-credit': {
      title: '增加可用额度',
      fields: [
        { name: 'amount', label: '增加金额', type: 'number', value: 100, min: 1, step: 100 },
        { name: 'note', label: '调整说明', type: 'textarea', value: '安卓端增加可用额度' },
      ],
    },
    disburse: {
      title: '确认发卡',
      fields: [{ name: 'term_days', label: '账期天数', type: 'number', value: termDays, min: 1, max: 364, step: 1 }],
    },
    'reject-card': {
      title: '拒绝发卡',
      fields: [{ name: 'note', label: '拒绝原因', type: 'textarea', value: '安卓端拒绝发卡' }],
    },
    remind: {
      title: '登记提醒',
      fields: [{ name: 'note', label: '提醒记录', type: 'textarea', value: '安卓端登记提醒' }],
    },
    collect: {
      title: '登记催收',
      fields: [{ name: 'note', label: '催收记录', type: 'textarea', value: '安卓端登记催收' }],
    },
    reconcile: {
      title: '登记平账',
      fields: [
        { name: 'received_amount', label: '收款金额', type: 'number', value: remaining, min: 0, step: 1 },
        { name: 'reduction_amount', label: '减免金额', type: 'number', value: 0, min: 0, step: 1 },
        { name: 'other_fee_amount', label: '其他费用', type: 'number', value: 0, min: 0, step: 1 },
        { name: 'note', label: '平账说明', type: 'textarea', value: '安卓端登记平账' },
      ],
    },
    extend: {
      title: '账单展期',
      fields: [
        { name: 'extension_type', label: '展期类型', type: 'select', value: 'FREE', options: [['FREE', '免费展期'], ['FEE', '收费展期']] },
        { name: 'days', label: '展期天数', type: 'number', value: 3, min: 1, max: 365, step: 1 },
        { name: 'reduction_amount', label: '减免金额', type: 'number', value: 0, min: 0, step: 1 },
        { name: 'note', label: '展期说明', type: 'textarea', value: '安卓端账单展期' },
      ],
    },
    'blacklist-user': {
      title: '一键拉黑',
      fields: [{ name: 'note', label: '拉黑原因', type: 'textarea', value: '安卓端一键拉黑' }],
    },
    'remove-blacklist': {
      title: '移出黑名单',
      fields: [{ name: 'note', label: '移出原因', type: 'textarea', value: '安卓端移出黑名单' }],
    },
    'unlock-location': {
      title: '解除位置风控',
      fields: [{ name: 'confirm_note', label: '处理说明', type: 'textarea', value: '安卓端解除位置风控' }],
    },
    'save-note': {
      title: '保存备注',
      fields: [{ name: 'review_note', label: '订单备注', type: 'textarea', value: item.review_note || '' }],
    },
    'close-reissue': {
      title: '退回待下单',
      fields: [{ name: 'confirm_note', label: '处理说明', type: 'textarea', value: '安卓端退回待下单' }],
    },
    'reissue-card': {
      title: '开启二次发卡',
      fields: [{ name: 'confirm_note', label: '处理说明', type: 'textarea', value: '安卓端开启二次发卡' }],
    },
    ack: { title: '确认还款申请', fields: [] },
    settle: { title: '确认结清', fields: [] },
    'refresh-profile': { title: '刷新档案', fields: [] },
  };
  return forms[action] || { title: '业务处理', fields: [] };
}
