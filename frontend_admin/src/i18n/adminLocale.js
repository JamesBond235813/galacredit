import { ref } from 'vue';

const STORAGE_KEY = 'galacredit_admin_locale';
const supportedLocales = ['zh-CN', 'en-GH'];
const initialLocale = typeof window !== 'undefined' && supportedLocales.includes(window.localStorage.getItem(STORAGE_KEY))
  ? window.localStorage.getItem(STORAGE_KEY)
  : 'zh-CN';

export const adminLocale = ref(initialLocale);

const messages = {
  'zh-CN': {
    chinese: '中文', english: 'English', language: '语言',
    brandSubtitle: 'Ghana cash loan',
    overview: '洞察看板', users: '用户档案', applications: '申请审批', disbursements: '待MoMo放款', 'disbursement-failures': '放款失败客户',
    repayments: '还款管理', collections: '催收管理', financials: '财务平账', riskSingleQuery: '风控报告单查',
    monitoring: '运营监控', messageCenter: '消息中心', kycReview: 'KYC复核', auditLog: '操作审计', riskStrategy: '风控策略预留', contentConfig: '运营配置',
    blacklist: '黑名单', overdueConfig: '逾期配置', products: '贷款产品', ecardPool: '历史卡池兼容',
    channels: '渠道管理', exclusiveLinks: '专属链接', adminUsers: '后台用户',
    operations: '运营总览', customerRisk: '客户与风控', loanOperations: '贷款运营',
    repaymentCollections: '还款与催收', productsChannels: '产品与渠道', system: '系统管理',
    'risk-single-query': '风控报告单查', 'overdue-config': '逾期配置', 'ecard-pool': '历史卡池兼容', 'exclusive-links': '专属链接', 'admin-users': '后台用户',
    defaultSubtitle: '同步查看 H5 用户资料、审批、MoMo 放款、还款提醒和催收进度',
    changePassword: '修改密码', logout: '退出登录', oldPassword: '原密码', newPassword: '新密码', confirmPassword: '确认新密码',
    cancel: '取消', confirm: '确认', save: '保存',
    productSearch: '贷款产品名称', all: '全部', active: '上架', inactive: '下架', search: '查询', reset: '重置',
    addLoanProduct: '新增贷款产品', loanProduct: '贷款产品', type: '类型', cashLoan: '现金贷', legacy: '历史兼容',
    nominalPrincipal: '名义本金', upfrontFee: '上扣费用', momoDisbursement: 'MoMo到账', term: '期限', installments: '分期',
    status: '状态', updatedAt: '更新时间', edit: '编辑', legacyRights: '历史权益',
    productName: '产品名称', businessType: '业务类型', upfrontFeeRate: '上扣费用率', feeTotal: '费用总额',
    auditFee: '审核费用', riskControlFee: '风控费用', systemFee: '系统费用', interest: '利息',
    feeBreakdownTotal: '费用分项合计', expectedMomo: '预计MoMo到账', interestStartDay: '起息日', dueDay: '到期日',
    installmentCount: '分期期数', installmentRatios: '每期比例', dailyOverdueFee: '每日逾期费', activeSwitch: '是否上架',
    productCreated: '贷款产品已创建', productUpdated: '贷款产品已更新', actions: '操作',
    legacyRightsConfig: '历史 E-card 权益兼容配置', legacyRightsHint: '仅用于存量 E-card 订单查询，不参与新的现金贷产品与 MoMo 放款流程。',
    selectLegacyProductHint: '请先在上方商品列表中点击“配置权益”'
  },
  'en-GH': {
    chinese: '中文', english: 'English', language: 'Language',
    brandSubtitle: 'Ghana cash loan',
    overview: 'Insights', users: 'Borrowers', applications: 'Applications', disbursements: 'MoMo Disbursement', 'disbursement-failures': 'Failed Disbursements',
    repayments: 'Repayments', collections: 'Collections', financials: 'Finance Reconciliation', riskSingleQuery: 'Risk Lookup',
    monitoring: 'Monitoring', messageCenter: 'Messages', kycReview: 'KYC Review', auditLog: 'Audit Logs', riskStrategy: 'Risk Strategy', contentConfig: 'Ops Config',
    blacklist: 'Blacklist', overdueConfig: 'Overdue Rules', products: 'Loan Products', ecardPool: 'Legacy Card Pool',
    channels: 'Channels', exclusiveLinks: 'Exclusive Links', adminUsers: 'Admin Users',
    operations: 'Operations', customerRisk: 'Borrowers & Risk', loanOperations: 'Loan Operations',
    repaymentCollections: 'Repayments & Collections', productsChannels: 'Products & Channels', system: 'System',
    'risk-single-query': 'Risk Lookup', 'overdue-config': 'Overdue Rules', 'ecard-pool': 'Legacy Card Pool', 'exclusive-links': 'Exclusive Links', 'admin-users': 'Admin Users',
    defaultSubtitle: 'Review borrower profiles, approvals, MoMo disbursement, repayments and collections',
    changePassword: 'Change password', logout: 'Sign out', oldPassword: 'Current password', newPassword: 'New password', confirmPassword: 'Confirm password',
    cancel: 'Cancel', confirm: 'Confirm', save: 'Save',
    productSearch: 'Loan product name', all: 'All', active: 'Active', inactive: 'Inactive', search: 'Search', reset: 'Reset',
    addLoanProduct: 'Add loan product', loanProduct: 'Loan product', type: 'Type', cashLoan: 'Cash loan', legacy: 'Legacy',
    nominalPrincipal: 'Nominal principal', upfrontFee: 'Upfront fee', momoDisbursement: 'MoMo received', term: 'Term', installments: 'Installments',
    status: 'Status', updatedAt: 'Updated', edit: 'Edit', legacyRights: 'Legacy rights',
    productName: 'Product name', businessType: 'Business type', upfrontFeeRate: 'Upfront fee rate', feeTotal: 'Fee total',
    auditFee: 'Review fee', riskControlFee: 'Risk control fee', systemFee: 'System fee', interest: 'Interest',
    feeBreakdownTotal: 'Fee breakdown total', expectedMomo: 'Expected MoMo received', interestStartDay: 'Interest starts', dueDay: 'Due day',
    installmentCount: 'Installment count', installmentRatios: 'Installment ratios', dailyOverdueFee: 'Daily overdue fee', activeSwitch: 'Active',
    productCreated: 'Loan product created', productUpdated: 'Loan product updated', actions: 'Actions',
    legacyRightsConfig: 'Legacy E-card rights compatibility', legacyRightsHint: 'For historical E-card orders only. It is not part of the new cash-loan or MoMo flow.',
    selectLegacyProductHint: 'Select a legacy product above to configure rights'
  }
};

export const setAdminLocale = (locale) => {
  if (!supportedLocales.includes(locale)) {
    return;
  }
  adminLocale.value = locale;
  if (typeof window !== 'undefined') {
    window.localStorage.setItem(STORAGE_KEY, locale);
  }
};

export const t = (key) => messages[adminLocale.value]?.[key] || messages['zh-CN'][key] || key;

export const tr = (chineseText, englishText) => adminLocale.value === 'en-GH' ? englishText : chineseText;

export const getMenuLabel = (key) => t(key);

export const getPageTitle = (key) => t(key);

export const getElementLocale = () => adminLocale.value === 'en-GH' ? 'en-US' : 'zh-CN';

const englishFallback = {
  '搜索':'Search','查询':'Search','重置':'Reset','确认':'Confirm','取消':'Cancel','保存':'Save','编辑':'Edit','删除':'Delete','新增':'Add','操作':'Actions','状态':'Status','全部':'All','启用':'Active','停用':'Inactive','登录系统':'Sign in','账号':'Username','密码':'Password','请输入管理员账号':'Enter admin username','请输入密码':'Enter password','登录成功':'Signed in successfully','客户':'Borrower','用户':'Borrower','订单':'Loan','订单号':'Loan ID','姓名':'Name','手机号':'Phone','身份证号':'National ID','备注':'Note','日期':'Date','更新时间':'Updated','暂无数据':'No data','暂无记录':'No records','加载中':'Loading','详情':'Details','提交':'Submit','下载':'Download','导出':'Export','刷新':'Refresh','开始日期':'Start date','结束日期':'End date','未实名':'Unverified','黑名单':'Blacklisted','首购':'First loan','已结清':'Settled','部分支付':'Partially paid','待支付':'Pending payment','逾期':'Overdue','到期':'Due','今日':'Today','明日':'Tomorrow','类型':'Type','金额':'Amount','总额':'Total','余额':'Balance','成功':'Success','失败':'Failed','跟进处理':'Follow up','一键拉黑':'Blacklist','重新放款':'Retry disbursement'};

export const installEnglishFallback = () => {
  if (typeof document === 'undefined' || window.__galaEnglishFallback) return;
  window.__galaEnglishFallback = true;
  const translate = (node) => {
    if (adminLocale.value !== 'en-GH' || !node.nodeValue?.trim()) return;
    let value = node.nodeValue;
    Object.entries(englishFallback).forEach(([source, target]) => { value = value.replaceAll(source, target); });
    if (value !== node.nodeValue) node.nodeValue = value;
  };
  const scan = (root) => {
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    let node; while ((node = walker.nextNode())) translate(node);
  };
  const observer = new MutationObserver((mutations) => mutations.forEach(({ addedNodes }) => addedNodes.forEach((node) => node.nodeType === Node.TEXT_NODE ? translate(node) : scan(node))));
  observer.observe(document.body, { childList: true, subtree: true });
  scan(document.body);
};
