import { createRouter, createWebHistory } from 'vue-router';
import {
  getFirstAccessibleRoute,
  getStoredAdminPermissions
} from '../constants/adminPages';

const Login = () => import('../views/Login.vue');
const Layout = () => import('../views/Layout.vue');
const Overview = () => import('../views/Overview.vue');
const Applications = () => import('../views/Applications.vue');
const Users = () => import('../views/Users.vue');
const Channels = () => import('../views/Channels.vue');
const Disbursements = () => import('../views/Disbursements.vue');
const Repayments = () => import('../views/Repayments.vue');
const Collections = () => import('../views/Collections.vue');
const FinancialReconciliation = () => import('../views/FinancialReconciliation.vue');
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
        path: 'users',
        component: Users,
        meta: {
          title: '用户档案',
          description: '按客户维度查看实名资料、收款信息、联系人和完整业务时间线',
          permission: 'users'
        }
      },
      {
        path: 'applications',
        component: Applications,
        meta: {
          title: '申请审批',
          description: '集中完成实名资料复核、额度授予、期限确认和总费率配置审批',
          permission: 'applications'
        }
      },
      {
        path: 'disbursements',
        component: Disbursements,
        meta: {
          title: '待发卡',
          description: '集中核对待发卡订单和商品配置，确认京东E卡发放',
          permission: 'disbursements'
        }
      },
      {
        path: 'repayments',
        component: Repayments,
        meta: {
          title: '还款管理',
          description: '处理正常在贷账单的到期提醒、跟进记录和财务跳转',
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
        path: 'products',
        component: Products,
        meta: {
          title: '商品管理',
          description: '维护京东E卡+旅游权益商品组合、账期与支付金额',
          permission: 'products'
        }
      },
      {
        path: 'ecard-pool',
        component: EcardPool,
        meta: {
          title: '卡池管理',
          description: '管理京东E卡库存，按面额和有效期支持后台发卡',
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
