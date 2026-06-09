import { createRouter, createWebHistory } from 'vue-router';

// 懒加载页面
const Login = () => import('../views/Login.vue');
const Home = () => import('../views/Home.vue');
const OCR = () => import('../views/OCR.vue');
const Face = () => import('../views/Face.vue');
const FaceMismatch = () => import('../views/FaceMismatch.vue');
const ApplicationForm = () => import('../views/ApplicationForm.vue');
const Review = () => import('../views/Review.vue');
const Withdraw = () => import('../views/Withdraw.vue');
const Bill = () => import('../views/Bill.vue');
const About = () => import('../views/About.vue');
const Support = () => import('../views/Support.vue');
const ChangePassword = () => import('../views/ChangePassword.vue');
const Orders = () => import('../views/Orders.vue');
const UserAgreement = () => import('../views/UserAgreement.vue');
const PersonalInfoAuthorization = () => import('../views/PersonalInfoAuthorization.vue');
const ChannelEntry = () => import('../views/ChannelEntry.vue');

const routes = [
  { path: '/login', component: () => import('../views/Login.vue'), meta: { title: '登录', public: true } },
  {
    path: '/',
    component: () => import('../views/Layout.vue'),
    children: [
      { path: '', redirect: '/home' },
      { path: 'home', component: () => import('../views/Home.vue'), meta: { title: '我的授信', tab: 'home' } },
      { path: 'profile', component: () => import('../views/Profile.vue'), meta: { title: '个人中心', tab: 'profile' } },
      { path: 'ocr', component: () => import('../views/OCR.vue'), meta: { title: '实名认证', tab: 'home' } },
      { path: 'face', component: () => import('../views/Face.vue'), meta: { title: '人脸识别', tab: 'home' } },
      { path: 'face-mismatch', component: FaceMismatch, meta: { title: '人脸识别结果', tab: 'home' } },
      { path: 'application-form', component: ApplicationForm, meta: { title: '补充资料', tab: 'home' } },
      { path: 'review', component: () => import('../views/Review.vue'), meta: { title: '授信审核中', tab: 'home' } },
      { path: 'withdraw', component: () => import('../views/Withdraw.vue'), meta: { title: '信用下单', tab: 'home' } },
      { path: 'bill', component: () => import('../views/Bill.vue'), meta: { title: '付款账单', tab: 'profile' } },
      { path: 'about', component: About, meta: { title: '关于我们', tab: 'profile' } },
      { path: 'support', component: Support, meta: { title: '客服帮助', tab: 'profile' } },
      { path: 'change-password', component: ChangePassword, meta: { title: '修改密码', tab: 'profile' } },
      { path: 'orders', component: Orders, meta: { title: '我的订单', tab: 'profile' } },
      { path: 'agreement', component: UserAgreement, meta: { title: '用户协议', tab: 'profile' } },
      { path: 'personal-info-authorization', component: PersonalInfoAuthorization, meta: { title: '个人信息授权协议', tab: 'home' } }
    ]
  },
  {
    path: '/:inviteCode([a-z0-9]{16,24})',
    component: ChannelEntry,
    meta: { title: '专属入口', public: true }
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

// 路由守卫：更新标题和简易权限拦截
router.beforeEach((to) => {
  if (to.meta.title) {
    document.title = to.meta.title;
  }

  const token = localStorage.getItem('token');
  if (!to.meta.public && !token) {
    return '/login';
  }

  return true;
});

export default router;
