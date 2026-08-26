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
    monitoring: '运营监控', messageCenter: '消息中心', kycReview: 'KYC复核', auditLog: '操作审计', riskStrategy: '风控策略', contentConfig: '运营配置',
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
    window.dispatchEvent(new CustomEvent('gala-locale-change', { detail: locale }));
    // 重新挂载页面，确保动态接口文案和属性占位符从原始语言重新渲染。
    window.setTimeout(() => window.location.reload(), 0);
  }
};

export const t = (key) => messages[adminLocale.value]?.[key] || messages['zh-CN'][key] || key;

export const tr = (chineseText, englishText) => adminLocale.value === 'en-GH' ? englishText : chineseText;
export const translateText = (value) => {
  if (adminLocale.value !== 'en-GH' || value === null || value === undefined) return value;
  const source = String(value);
  const core = source.trim();
  if (!core) return source;
  const target = englishFallback[core];
  if (!target) return source;
  const prefix = source.slice(0, source.indexOf(core));
  const suffix = source.slice(source.indexOf(core) + core.length);
  return `${prefix}${target}${suffix}`;
};

export const getMenuLabel = (key) => t(key);

export const getPageTitle = (key) => t(key);

export const getElementLocale = () => adminLocale.value === 'en-GH' ? 'en-US' : 'zh-CN';

const englishFallback = {
'搜索':'Search','查询':'Search','重置':'Reset','确认':'Confirm','取消':'Cancel','保存':'Save','编辑':'Edit','删除':'Delete','新增':'Add','操作':'Actions','状态':'Status','全部':'All','启用':'Active','停用':'Inactive','登录系统':'Sign in','账号':'Username','密码':'Password','请输入管理员账号':'Enter admin username','请输入密码':'Enter password','登录成功':'Signed in successfully','客户':'Borrower','用户':'Borrower','订单':'Loan','订单号':'Loan ID','姓名':'Name','手机号':'Phone','身份证号':'National ID','备注':'Note','日期':'Date','更新时间':'Updated','暂无数据':'No data','暂无记录':'No records','加载中':'Loading','详情':'Details','提交':'Submit','下载':'Download','导出':'Export','刷新':'Refresh','开始日期':'Start date','结束日期':'End date','未实名':'Unverified','黑名单':'Blacklisted','首购':'First loan','已结清':'Settled','部分支付':'Partially paid','待支付':'Pending payment','逾期':'Overdue','到期':'Due','今日':'Today','明日':'Tomorrow','类型':'Type','金额':'Amount','总额':'Total','余额':'Balance','成功':'Success','失败':'Failed','跟进处理':'Follow up','一键拉黑':'Blacklist','重新放款':'Retry disbursement','上传名单':'Upload blacklist','上传黑名单':'Upload blacklist','下载模板':'Download template','后台用户列表':'Admin user list','账号信息':'Account','当前登录':'Current session','页面权限':'Page permissions','角色配置':'Role configuration','角色映射权限':'Mapped permissions','请选择角色后自动展示权限':'Select roles to preview permissions','登录历史':'Login history','客户端':'Client','结果':'Result','原因':'Reason','日对账汇总':'Daily reconciliation summary','交易笔数':'Transaction count','交易金额':'Transaction amount','差异单':'Difference orders','待对账':'Pending reconciliation','流水ID':'Transaction ID','订单ID':'Loan ID','财务处理':'Finance processing','账单概览':'Loan overview','账单台账':'Loan ledger','财务登记':'Finance entry','登记收款':'Recorded payment','额外收款':'Additional payment','实际还款日':'Actual repayment date','选择实际还款日':'Select actual repayment date','提交财务登记':'Submit finance entry','已平账':'Reconciled','关闭':'Close','变更历史':'Change history','版本记录':'Version history','产品已复制':'Product copied','渠道已复制':'Channel copied','启用中':'Active','已停用':'Inactive','已过期':'Expired'};

Object.assign(englishFallback, {
  '模板总数': 'Total templates', '启用模板': 'Active templates', '历史触达': 'Historical sends',
  '待提醒订单': 'Loans to remind', '提醒队列': 'Reminder queue', '模板库': 'Template library',
  '服务端模板版本': 'Server template versions', '新建模板版本': 'New template version',
  '模板标识': 'Template key', '版本': 'Version', '标题': 'Title', '内容': 'Content',
  '发送时间': 'Sent at', '发送提醒': 'Send reminder', '编辑新版本': 'Edit version',
  '消息模板版本': 'Message template version', '保存新版本': 'Save new version',
  '调度与运行状态': 'Scheduling and runtime status', '任务ID': 'Job ID', '下一次执行': 'Next run',
  '调度器': 'Scheduler', '待执行': 'Pending', '正常': 'Healthy', '暂无明细': 'No details',
  '操作者类型': 'Operator type', '管理员': 'Administrator', '系统': 'System',
  '事件类型': 'Event type', '对象类型': 'Object type', '对象': 'Object', '操作者': 'Operator',
  '事件': 'Event', '导出CSV': 'Export CSV', '如 KYC_APPROVE': 'e.g. KYC_APPROVE',
  '风险标签': 'Risk flags', '渠道': 'Channel', '提交时间': 'Submitted at',
  '通过': 'Approve', '拒绝': 'Reject', '查看档案': 'View profile', '处理备注': 'Processing note',
  '渠道名称 / 业务员': 'Channel name / advisor', '新增渠道': 'Add channel',
  '渠道 / 业务员': 'Channel / advisor', '专属链接': 'Exclusive link', '复制链接': 'Copy link',
  '二维码': 'QR code', '放款方式': 'Disbursement mode', '审核方式': 'Review mode',
  '归属用户': 'Attributed borrowers', '申请量': 'Applications', '放款表现': 'Disbursement performance',
  '逾期表现': 'Overdue performance', '最近进件 / 放款': 'Latest application / disbursement',
  '查看': 'View', '自动审核': 'Automatic review', '人工审核': 'Manual review',
  '自动放款': 'Automatic disbursement', '人工放款': 'Manual disbursement', '历史': 'History',
  '渠道配置': 'Channel configuration', '业务员': 'Advisor', '填写业务员姓名': 'Enter advisor name',
  '渠道名称': 'Channel name', '邀请码': 'Invitation code', '渠道状态': 'Channel status',
  '业务顾问': 'Business advisor', '输入用户ID或用户名搜索业务顾问': 'Search advisor by user ID or username',
  '填写渠道说明、投放场景或业务员备注': 'Enter channel, campaign or advisor notes',
  '专属链接预览': 'Exclusive link preview', '业绩快照': 'Performance snapshot', '放款金额': 'Disbursed amount',
  '逾期率': 'Overdue rate', '新建后台用户': 'Create admin user', '编辑后台用户': 'Edit admin user',
  '后台用户名': 'Admin username', '登录密码': 'Login password',
  '登录密码（留空则不修改）': 'Login password (leave blank to keep current)',
  '如需修改密码请重新输入': 'Enter a new password to change it',
  '请输入登录密码，至少 6 位': 'Enter a password of at least 6 characters',
  '创建账号': 'Create account', '保存修改': 'Save changes', '角色': 'Role',
  '创建时间': 'Created at', '账号已启用': 'Account enabled', '账号已禁用': 'Account disabled',
  '应还款时间': 'Due date', '实际还款时间': 'Actual repayment time', '复购次数': 'Repeat loans',
  '历史账单': 'Loan history', '总还款额': 'Total repayment', '已还款额': 'Paid amount',
  '减免金额': 'Waived amount', '其他费用': 'Other fees', '剩余还款额': 'Remaining repayment',
  '订单状态': 'Loan status', '平账后已还款额': 'Paid after reconciliation',
  '平账后减免金额': 'Waiver after reconciliation', '本次冲抵逾期费': 'Penalty offset',
  '平账后其他费用': 'Other fees after reconciliation', '当前待补逾期费': 'Pending penalty',
  '平账后剩余还款额': 'Remaining after reconciliation',
  '收款金额与减免金额累计不能超过总还款额': 'Payment and waiver cannot exceed total repayment',
  '未结清订单': 'Open loans', '应收总额': 'Total receivable', '实收金额': 'Amount received',
  '账单外额外收款单独统计': 'Additional payments outside bills are tracked separately',
  '财务登记后会自动回写账单余额': 'The loan balance is updated after finance entry',
  '贷款产品': 'Loan product', '产品名称': 'Product name', '复制': 'Copy',
  '产品变更历史': 'Product change history', '渠道变更历史': 'Channel change history',
  '最近一次正常结清账单': 'Most recent settled loan', '借款人': 'Borrower',
  '账期': 'Term', '名义本金': 'Nominal principal', '上扣费用': 'Upfront fee',
  'MoMo到账': 'MoMo received', '实际结清额': 'Actual settlement', '放款时间': 'Disbursed at',
  '还款日': 'Repayment date', '暂无历史结清账单': 'No settled loan history'
  , '洞察看板': 'Insights', '运营监控': 'Monitoring', '消息中心': 'Messages',
  '用户档案': 'Borrowers', 'KYC复核': 'KYC review', '申请审批': 'Applications',
  '待MoMo放款': 'Pending MoMo disbursement', '放款失败客户': 'Failed disbursements',
  '还款管理': 'Repayments', '催收管理': 'Collections', '财务平账': 'Finance reconciliation',
  '操作审计': 'Audit logs', '风控报告单查': 'Risk lookup', '风控策略': 'Risk strategy',
  '逾期配置': 'Overdue rules', '运营配置': 'Operations config', '历史卡池兼容': 'Legacy card pool',
  '渠道管理': 'Channels', '后台用户': 'Admin users', '解除位置风控': 'Clear location risk',
  '审核转入自己': 'Take over review', '审核': 'Reviewer', '财务': 'Finance', '催收': 'Collections',
  '业务顾问': 'Business advisor', '所有页面与操作权限': 'All pages and actions',
  '用户档案、KYC复核、申请审批、还款管理': 'Borrowers, KYC review, applications and repayments',
  'MoMo放款、财务平账、消息中心、贷款产品、历史卡池兼容': 'MoMo disbursement, finance, messages, products and legacy card pool',
  '催收管理、消息中心': 'Collections and messages', '用户档案、专属链接页面': 'Borrowers and exclusive links'
  , '信用额度': 'Credit limit', '审批额度': 'Approved limit', '授信额度': 'Credit limit',
  '用户信息': 'Borrower', '客户信息': 'Borrower', '申请单号': 'Application ID', '审核员': 'Reviewer',
  '风控查询': 'Risk lookup', '报告查询': 'Report lookup', '黑名单': 'Blacklist', '命中': 'Matched',
  '未命中': 'Not matched', '审批备注': 'Review note', '申请时间': 'Application time',
  '资料提交': 'Profile submission', '审批结果': 'Review result', '待下单': 'Awaiting confirmation',
  '审核中': 'Under review', '未通过': 'Rejected', '可转入': 'Available for takeover',
  '位置风控': 'Location risk', '风控状态': 'Risk status', '风控原因': 'Risk reason',
  '风控时间': 'Risk time', 'GPS坐标': 'GPS coordinates', 'IP地址': 'IP address',
  '住址': 'Address', '定位地址': 'Location address', '定位时间': 'Located at', '定位来源': 'Location source',
  '省市区': 'Region', '行政区划': 'Administrative area', '经度': 'Longitude', '纬度': 'Latitude',
  '精度(米)': 'Accuracy (m)', '最近登录': 'Latest login', '最近渠道访问': 'Latest channel visit',
  '提醒记录': 'Reminder records', '提醒次数': 'Reminder count', '提醒备注': 'Reminder note',
  '催收记录': 'Collection records', '催收员': 'Collector', '催收备注': 'Collection note',
  '跟进日志': 'Follow-up log', '催收日志': 'Collection log', '暂无日志': 'No logs',
  '暂无跟进记录': 'No follow-up records', '暂无操作记录': 'No action records', '无补充说明': 'No additional notes',
  '账单进度': 'Loan progress', '还款状态': 'Repayment status', '每期应还': 'Installment due',
  '总应还': 'Total due', '逾期天数': 'Overdue days', '逾期费用': 'Overdue fee',
  '违约金': 'Penalty', '逾期费口径': 'Overdue fee basis', '展期天数': 'Extension days',
  '展期类型': 'Extension type', '账单展期': 'Loan extension', '跟进处理': 'Follow up',
  '还款跟进': 'Repayment follow-up', '逾期催收处理': 'Overdue collection',
  '可用额度': 'Available credit', '增加额度': 'Increase limit', '减免额度': 'Reduce limit',
  '调整后额度': 'Adjusted limit', '调整备注': 'Adjustment note', '调减备注': 'Reduction note',
  '下单商品': 'Selected product', '下单时间': 'Order time', '预计付款日': 'Expected due date',
  '待MoMo放款处理': 'Pending MoMo disbursement', '最近操作轨迹': 'Recent actions',
  '产品默认逾期费': 'Default product overdue fee', '期限': 'Term', '利率': 'Interest rate',
  '总费率': 'Total fee rate', '系统服务费率': 'System service fee rate', '封控费率': 'Risk control fee rate',
  '通道费率': 'Channel fee rate', '适用用户': 'Eligible borrowers', 'E卡面值': 'E-card face value',
  '旅游权益金额': 'Travel benefit amount', '旅游权益标题': 'Travel benefit title',
  '旅游权益说明': 'Travel benefit description', '图片': 'Images', '文字介绍': 'Description',
  '客服电话': 'Customer service phone', '现金贷合规参数': 'Cash-loan compliance parameters',
  '规则名称': 'Rule name', '最大上扣费用率': 'Maximum upfront fee rate',
  '最低实际到账比例': 'Minimum actual disbursement rate', '最大折算年化费率': 'Maximum effective APR',
  '最大每日逾期费': 'Maximum daily overdue fee', '最大贷款期限（天）': 'Maximum loan term (days)',
  '最大分期期数': 'Maximum installment count', '生效时间': 'Effective at',
  '请输入后台用户名': 'Enter admin username', '姓名 / 手机号': 'Name / phone',
  '姓名 / 手机号 / 身份证号': 'Name / phone / National ID',
  '手机号 / 姓名 / 身份证号': 'Phone / name / National ID',
  '姓名 / 手机号 / 订单号 / 备注': 'Name / phone / loan ID / note',
  '开始日期': 'Start date', '结束日期': 'End date', '选择日期': 'Select date',
  '选择审核员': 'Select reviewer', '选择催收员': 'Select collector', '选择还款状态': 'Select repayment status',
  '批量上传历史卡密': 'Bulk upload legacy card credentials', '新增卡池记录': 'Add card-pool record',
  '编辑卡池记录': 'Edit card-pool record', '新增用户': 'Add borrower', '用户档案详情': 'Borrower profile',
  '申请审批处理': 'Application review', '重置密码': 'Reset password', '新增逾期配置': 'Add overdue rule'
});

export const installEnglishFallback = () => {
  if (typeof document === 'undefined' || window.__galaEnglishFallback) return;
  window.__galaEnglishFallback = true;
  const translateValue = (value) => translateText(value);
  const translate = (node) => {
    if (adminLocale.value !== 'en-GH' || !node.nodeValue?.trim()) return;
    const value = translateValue(node.nodeValue);
    if (value !== node.nodeValue) node.nodeValue = value;
  };
  const scan = (root) => {
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    let node; while ((node = walker.nextNode())) translate(node);
    if (root.querySelectorAll) root.querySelectorAll('input,textarea,[title],[aria-label]').forEach((element) => {
      ['placeholder','title','aria-label'].forEach((attribute) => {
        if (element.hasAttribute(attribute)) element.setAttribute(attribute, translateValue(element.getAttribute(attribute)));
      });
    });
  };
  window.addEventListener('gala-locale-change', () => scan(document.body));
  const observer = new MutationObserver((mutations) => mutations.forEach(({ addedNodes }) => addedNodes.forEach((node) => node.nodeType === Node.TEXT_NODE ? translate(node) : scan(node))));
  observer.observe(document.body, { childList: true, subtree: true });
  scan(document.body);
};

// Do not translate isolated Chinese characters: they can be part of a user name,
// message body or a longer phrase. Page components must use tr() for such labels.
['单', '次', '人', '天', '至', '当前', '风', '日志'].forEach((key) => delete englishFallback[key]);
