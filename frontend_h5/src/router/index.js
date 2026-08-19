import { createRouter, createWebHistory } from 'vue-router';

// Lazy-loaded pages
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
  { path: '/login', component: () => import('../views/Login.vue'), meta: { title: 'Sign In', public: true } },
  {
    path: '/',
    component: () => import('../views/Layout.vue'),
    children: [
      { path: '', redirect: '/home' },
      { path: 'home', component: () => import('../views/Home.vue'), meta: { title: 'My Credit', tab: 'home' } },
      { path: 'profile', component: () => import('../views/Profile.vue'), meta: { title: 'My Account', tab: 'profile' } },
      { path: 'ocr', component: () => import('../views/OCR.vue'), meta: { title: 'Identity Verification', tab: 'home' } },
      { path: 'face', component: () => import('../views/Face.vue'), meta: { title: 'Face Verification', tab: 'home' } },
      { path: 'face-mismatch', component: FaceMismatch, meta: { title: 'Verification Result', tab: 'home' } },
      { path: 'application-form', component: ApplicationForm, meta: { title: 'Additional Information', tab: 'home' } },
      { path: 'review', component: () => import('../views/Review.vue'), meta: { title: 'Application Review', tab: 'home' } },
      { path: 'withdraw', component: () => import('../views/Withdraw.vue'), meta: { title: 'Loan Application', tab: 'home' } },
      { path: 'bill', component: () => import('../views/Bill.vue'), meta: { title: 'Repayment Bill', tab: 'profile' } },
      { path: 'about', component: About, meta: { title: 'About Us', tab: 'profile' } },
      { path: 'support', component: Support, meta: { title: 'Customer Support', tab: 'profile' } },
      { path: 'change-password', component: ChangePassword, meta: { title: 'Change Password', tab: 'profile' } },
      { path: 'orders', component: Orders, meta: { title: 'My Applications', tab: 'profile' } },
      { path: 'agreement', component: UserAgreement, meta: { title: 'User Agreement', tab: 'profile' } },
      { path: 'personal-info-authorization', component: PersonalInfoAuthorization, meta: { title: 'Personal Data Authorization', tab: 'home' } }
    ]
  },
  {
    path: '/:inviteCode([a-z0-9]{16,24})',
    component: ChannelEntry,
    meta: { title: 'Invitation Access', public: true }
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

// Update page titles and enforce basic authentication.
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
