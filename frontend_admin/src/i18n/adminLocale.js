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
    window.dispatchEvent(new CustomEvent('gala-locale-change', { detail: locale }));
    // 重新挂载页面，确保动态接口文案和属性占位符从原始语言重新渲染。
    window.setTimeout(() => window.location.reload(), 0);
  }
};

export const t = (key) => messages[adminLocale.value]?.[key] || messages['zh-CN'][key] || key;

export const tr = (chineseText, englishText) => adminLocale.value === 'en-GH' ? englishText : chineseText;
export const translateText = (value) => {
  if (adminLocale.value !== 'en-GH' || !value) return value;
  return Object.entries(englishFallback).sort((a, b) => b[0].length - a[0].length).reduce((text, [source, target]) => text.replaceAll(source, target), String(value));
};

export const getMenuLabel = (key) => t(key);

export const getPageTitle = (key) => t(key);

export const getElementLocale = () => adminLocale.value === 'en-GH' ? 'en-US' : 'zh-CN';

const englishFallback = {
  '搜索':'Search','查询':'Search','重置':'Reset','确认':'Confirm','取消':'Cancel','保存':'Save','编辑':'Edit','删除':'Delete','新增':'Add','操作':'Actions','状态':'Status','全部':'All','启用':'Active','停用':'Inactive','登录系统':'Sign in','账号':'Username','密码':'Password','请输入管理员账号':'Enter admin username','请输入密码':'Enter password','登录成功':'Signed in successfully','客户':'Borrower','用户':'Borrower','订单':'Loan','订单号':'Loan ID','姓名':'Name','手机号':'Phone','身份证号':'National ID','备注':'Note','日期':'Date','更新时间':'Updated','暂无数据':'No data','暂无记录':'No records','加载中':'Loading','详情':'Details','提交':'Submit','下载':'Download','导出':'Export','刷新':'Refresh','开始日期':'Start date','结束日期':'End date','未实名':'Unverified','黑名单':'Blacklisted','首购':'First loan','已结清':'Settled','部分支付':'Partially paid','待支付':'Pending payment','逾期':'Overdue','到期':'Due','今日':'Today','明日':'Tomorrow','类型':'Type','金额':'Amount','总额':'Total','余额':'Balance','成功':'Success','失败':'Failed','跟进处理':'Follow up','一键拉黑':'Blacklist','重新放款':'Retry disbursement','模板总数':'Total templates','预设提醒模板数量':'Preset reminder templates','启用模板':'Active templates','当前可直接使用的模板':'Templates ready to use','历史触达':'Historical sends','已记录的提醒/催收动作':'Recorded reminder and collection actions','待提醒订单':'Loans to remind','今天先补足的触达队列':'Queue requiring attention today','提醒队列':'Reminder queue','模板库':'Template library','服务端模板版本':'Server template versions','新建模板版本':'New template version','模板标识':'Template key','版本':'Version','标题':'Title','内容':'Content','发送时间':'Sent at','消息模板版本':'Message template version','保存新版本':'Save new version','编辑新版本':'Edit version','发送提醒':'Send reminder','模板版本已保存':'Template version saved','模板状态已更新':'Template status updated','提醒已发送':'Reminder sent','Due日提醒':'Due date reminder','Overdue第一大提醒':'First overdue reminder','Overdue第二大提醒':'Second overdue reminder','您的还款今天Due，请尽快完成还款。':'Your repayment is due today. Please complete it as soon as possible.','您的账单已Overdue 1天，请尽快处理。':'Your loan is 1 day overdue. Please take action.','您的账单已Overdue 3天，请及时联系催收。':'Your loan is 3 days overdue. Please contact collections promptly.','基于当前到期和逾期订单生成可发送队列，发送动作会回写到现有业务事件里。':'A sendable queue based on due and overdue loans. Sends are recorded in business events.','当前先提供预设模板，后续接短信供应商与文案版本库时可直接切换为服务端配置。':'Preset templates can later be switched to provider-managed versions.','单':'loans','次':'times','人':'people','天':'days','至':'to','当前':'Current','可待回收':'Eligible for collection','速到金':'Expected cash','仅展示已进入催收阶段的账单':'Only loans that have entered collections','按后台催收登记次数统计':'Based on collection records','按当前筛选结果统计':'Based on current filters','用于判断优先催收账单':'Used to prioritize collection loans','Overdue天数':'Overdue days','OverdueLoan':'Overdue loans','Today已催收':'Collected today','当前应待回收':'Currently collectible','当前快速到金':'Fast cash now','减免Amount':'Waived amount','应还款时间':'Due date','实际还款时间':'Actual repayment date','复购次数':'Repeat loans','IP审查':'IP review','催收员':'Collector','总还款额':'Total repayment','已还款额':'Paid amount','减免金额':'Waived amount','剩余还款额':'Remaining repayment','违约金':'Penalty','逾期费口径':'Overdue fee basis','催收记录':'Collection records','日志':'Log','风':'Risk','快捷':'Quick filter','手机号 / 姓名 / 身份证号':'Phone / name / National ID','Overdue':'Overdue','今天':'Today','应还Loan':'Loans due','应还Borrower':'Borrowers due','实收Amount':'Collected amount','回款率':'Collection rate','账单进度':'Loan progress','提醒记录':'Reminder records','还款Status':'Repayment status','还款快捷':'Repayment quick filter','当前区间应还款额':'Amount due in current period','减免 GHS':'Waived GHS','其他费用 GHS':'Other fees GHS','应还Amount':'Amount due','Loan号':'Loan ID','审批员':'Reviewer','复购':'Repeat loan','选择审核员':'Select reviewer','放款金额':'Disbursement amount','实际到账':'Actual received','失败原因':'Failure reason','最近失败时间':'Last failure time','查看详情':'View details','申请审批':'Application review','审核通过':'Approve','审核拒绝':'Reject','通过':'Approve','拒绝':'Reject','待审核':'Pending review','处理中':'Processing','已完成':'Completed','创建时间':'Created at','操作人':'Operator','事件类型':'Event type','对象类型':'Object type','日期范围':'Date range','导出日志':'Export logs','导出成功':'Export completed','复制':'Copy','复制成功':'Copied','变更历史':'Change history','版本记录':'Version history','禁用':'Disabled','启用账号':'Enable account','禁用账号':'Disable account','重置密码':'Reset password','登录历史':'Login history','备注信息':'Notes','原因':'Reason','服务商':'Provider','发送结果':'Send result','回溯':'Trace back','暂无跟进记录':'No follow-up records','无补充说明':'No additional notes','例如':'For example','确认将':'Confirm that','加入黑名单':'Add to blacklist','移出黑名单':'Remove from blacklist','已加入黑名单':'Added to blacklist','退回待下单':'Return to pending order','预览':'Preview','关闭':'Close','放款':'Disburse','到账':'Received','上扣费用':'Upfront fee','名义本金':'Nominal principal','可用额度':'Available credit','调整备注':'Adjustment note','增加额度':'Increase limit','渠道名称':'Channel name','业务员':'Advisor','归属用户':'Assigned borrower','复制链接':'Copy link','面额':'Face value','卡号':'Card number','有效期':'Validity period','通用':'General','文件':'File','图片组':'Image group','地址':'Address','时间':'Time','历史':'History','启用中':'Active','已停用':'Inactive','已过期':'Expired','今日':'Today'};

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
