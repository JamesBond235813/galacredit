import { createRouter, createWebHistory } from 'vue-router';
import {
  getFirstAccessibleRoute,
  getStoredAdminPermissions
} from '../constants/adminPages';

const Login = () => import('../views/Login.vue');
const Layout = () => import('../views/Layout.vue');
const Overview = () => import('../views/Overview.vue');
const Monitoring = () => import('../views/Monitoring.vue');
const MessageCenter = () => import('../views/MessageCenter.vue');
const Applications = () => import('../views/Applications.vue');
const Users = () => import('../views/Users.vue');
const KycReview = () => import('../views/KycReview.vue');
const Channels = () => import('../views/Channels.vue');
const ExclusiveLinks = () => import('../views/ExclusiveLinks.vue');
const Disbursements = () => import('../views/Disbursements.vue');
const DisbursementFailures = () => import('../views/DisbursementFailures.vue');
const Repayments = () => import('../views/Repayments.vue');
const Collections = () => import('../views/Collections.vue');
const FinancialReconciliation = () => import('../views/FinancialReconciliation.vue');
const AuditLog = () => import('../views/AuditLog.vue');
const RiskSingleQuery = () => import('../views/RiskSingleQuery.vue');
const RiskStrategy = () => import('../views/RiskStrategy.vue');
const Blacklist = () => import('../views/Blacklist.vue');
const OverdueConfig = () => import('../views/OverdueConfig.vue');
const ContentConfig = () => import('../views/ContentConfig.vue');
const Products = () => import('../views/Products.vue');
const EcardPool = () => import('../views/EcardPool.vue');
const AdminUsers = () => import('../views/AdminUsers.vue');

const routes = [
  { path: '/login', component: Login, meta: { title: '管理后台登录' } },
  {
    path: '/',
    component: Layout,
    redirect: () => getFirstAccessibleRoute(),
    children: [
      {
        path: 'overview',
        component: Overview,
        meta: {
          title: '洞察看板',
          description: '按项目卡片查看资金注入、提现回款以及各类收支净额',
          permission: 'overview'
        }
      },
      {
        path: 'monitoring',
        component: Monitoring,
        meta: {
          title: '运营监控',
          description: '聚合审计、KYC、消息、资金和调度任务状态',
          permission: 'monitoring'
        }
      },
      {
        path: 'message-center',
        component: MessageCenter,
        meta: {
          title: '消息中心',
          description: '管理到期提醒、逾期提醒和催收触达记录',
          permission: 'message-center'
        }
      },
      {
        path: 'users',
        component: Users,
        meta: {
          title: '用户档案',
          description: '按客户维度查看实名资料、收款信息、联系人和完整业务时间线',
          permission: 'users'
        }
      },
      {
        path: 'kyc-review',
        component: KycReview,
        meta: {
          title: 'KYC复核',
          description: '集中查看待复核用户、风险标签与建议处理动作',
          permission: 'kyc-review'
        }
      },
      {
        path: 'applications',
        component: Applications,
        meta: {
          title: '申请审批',
          description: '集中完成实名资料复核、额度授予、期限确认和现金贷费用配置审批',
          permission: 'applications'
        }
      },
      {
        path: 'disbursements',
        component: Disbursements,
        meta: {
          title: '待MoMo放款',
          description: '集中核对待放款订单和贷款快照，确认 MoMo 到账金额',
          permission: 'disbursements'
        }
      },
      {
        path: 'disbursement-failures',
        component: DisbursementFailures,
        meta: {
          title: '放款失败客户',
          description: '查看 MoMo 放款失败原因并重新处理可重试订单',
          permission: 'disbursement-failures'
        }
      },
      {
        path: 'repayments',
        component: Repayments,
        meta: {
          title: '还款管理',
          description: '处理正常在贷账单的到期提醒、分期应还和财务跳转',
          permission: 'repayments'
        }
      },
      {
        path: 'collections',
        component: Collections,
        meta: {
          title: '催收管理',
          description: '聚焦逾期订单的催收登记、逾期筛选与后续账务处理',
          permission: 'collections'
        }
      },
      {
        path: 'financials',
        component: FinancialReconciliation,
        meta: {
          title: '财务平账',
          description: '对未结清账单登记收款、减免金额，并自动完成平账结清',
          permission: 'financials'
        }
      },
      {
        path: 'audit-log',
        component: AuditLog,
        meta: {
          title: '操作审计',
          description: '查询管理员对用户、订单和资金动作的审计记录',
          permission: 'audit-log'
        }
      },
      {
        path: 'risk-single-query',
        component: RiskSingleQuery,
        meta: {
          title: '风控报告单查',
          description: '输入姓名、身份证号或手机号查询 GalaCredit 风险报告，并查看历史查询记录',
          permission: 'risk-single-query'
        }
      },
      {
        path: 'risk-strategy',
        component: RiskStrategy,
        meta: {
          title: '风控策略预留',
          description: '预留自动审核与风控策略配置入口，等待外部三方数据接入',
          permission: 'risk-strategy'
        }
      },
      {
        path: 'blacklist',
        component: Blacklist,
        meta: {
          title: '黑名单',
          description: '展示与上传黑名单，支持手机号和身份证号明文或MD5',
          permission: 'blacklist'
        }
      },
      {
        path: 'overdue-config',
        component: OverdueConfig,
        meta: {
          title: '逾期配置',
          description: '配置逾期费用标准，按生效日向后应用，不改变历史记录',
          permission: 'overdue-config'
        }
      },
      {
        path: 'content-config',
        component: ContentConfig,
        meta: {
          title: '运营配置',
          description: '维护消息模板、首页内容和运营位预案',
          permission: 'content-config'
        }
      },
      {
        path: 'products',
        component: Products,
        meta: {
          title: '贷款产品',
          description: '维护名义本金、上扣费用、MoMo 到账、期限和分期参数',
          permission: 'products'
        }
      },
      {
        path: 'ecard-pool',
        component: EcardPool,
        meta: {
          title: '历史卡池兼容',
          description: '保留历史 E-card 库存查询，不参与现金贷 MoMo 放款主流程',
          permission: 'ecard-pool'
        }
      },
      {
        path: 'channels',
        component: Channels,
        meta: {
          title: '渠道管理',
          description: '管理业务员专属链接并查看申请、放款、逾期等渠道业绩统计',
          permission: 'channels'
        }
      },
      {
        path: 'exclusive-links',
        component: ExclusiveLinks,
        meta: {
          title: '专属链接',
          description: '查看归属于当前业务顾问的渠道专属链接列表',
          permission: 'exclusive-links'
        }
      },
      {
        path: 'admin-users',
        component: AdminUsers,
        meta: {
          title: '后台用户',
          description: '创建、修改、删除后台使用人员，并按页面标签配置访问权限',
          permission: 'admin-users'
        }
      }
    ]
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

router.beforeEach((to) => {
  if (to.meta.title) document.title = to.meta.title;

  const token = localStorage.getItem('admin_token');
  if (to.path === '/login' && token) {
    return getFirstAccessibleRoute();
  }

  if (to.path !== '/login' && !token) {
    return '/login';
  }

  const permissions = getStoredAdminPermissions();
  if (
    to.meta.permission &&
    Array.isArray(permissions) &&
    permissions.length > 0 &&
    !permissions.includes(to.meta.permission)
  ) {
    return getFirstAccessibleRoute(permissions);
  }

  return true;
});

export default router;
