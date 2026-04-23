<template>
  <div class="page-shell support-page">
    <van-nav-bar left-arrow title="客服帮助" @click-left="router.back()" />

    <div class="page-inner support-inner">
      <section class="page-card hero-card">
        <div class="hero-icon">
          <van-icon name="service-o" />
        </div>
        <div class="hero-copy">
          <h1 class="hero-title">客服帮助</h1>
          <p class="hero-desc">为您提供常见问题说明、订单查询入口和客服协助指引。</p>
        </div>
      </section>

      <section class="page-card quick-card">
        <h2 class="page-section-title">快捷入口</h2>
        <div class="quick-actions">
          <button type="button" class="quick-action" @click="router.push('/orders')">
            <span class="quick-icon">
              <van-icon name="orders-o" />
            </span>
            <span class="quick-copy">
              <span class="quick-title">查看我的订单</span>
              <span class="quick-desc">查看申请记录、审核进度与账单状态</span>
            </span>
            <van-icon name="arrow" class="quick-arrow" />
          </button>

          <button type="button" class="quick-action" @click="refreshStatus">
            <span class="quick-icon quick-icon-refresh">
              <van-icon name="replay" />
            </span>
            <span class="quick-copy">
              <span class="quick-title">刷新业务状态</span>
              <span class="quick-desc">同步最新审核、下单、发卡和付款信息</span>
            </span>
            <van-icon name="arrow" class="quick-arrow" />
          </button>
        </div>
      </section>

      <section class="page-card faq-card">
        <h2 class="page-section-title">常见问题</h2>
        <div class="faq-list">
          <div class="faq-item" v-for="item in faqs" :key="item.question">
            <p class="faq-question">{{ item.question }}</p>
            <p class="faq-answer">{{ item.answer }}</p>
          </div>
        </div>
      </section>

      <section class="page-card service-card">
        <h2 class="page-section-title">服务时间</h2>
        <p class="page-section-desc">工作日 09:00 - 18:00。非工作时间提交的问题会在下一个服务时段内处理。</p>
      </section>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router';
import { showToast } from 'vant';

const router = useRouter();

const faqs = [
  {
    question: '如何继续申请额度？',
    answer: '进入首页点击“立即申请”，按流程完成实名认证和人脸识别后即可提交申请。'
  },
  {
    question: '订单为什么一直在审核中？',
    answer: '审核会根据资料完整度和业务规则自动处理，您可以在“我的订单”中查看最新状态。'
  },
  {
    question: '如何查看还款信息？',
    answer: '如果订单已进入待发卡、待付款或逾期阶段，可在“我的订单”页点击按钮进入账单页面查看。'
  }
];

const refreshStatus = () => {
  showToast('状态已刷新，请前往我的订单查看');
  router.push('/orders');
};
</script>

<style scoped>
.hero-card,
.quick-card,
.faq-card,
.service-card {
  padding: 18px;
}

.quick-card,
.faq-card,
.service-card {
  margin-top: 16px;
}

.hero-card {
  display: flex;
  align-items: center;
  gap: 14px;
}

.hero-icon {
  width: 56px;
  height: 56px;
  flex-shrink: 0;
  border-radius: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(47, 126, 247, 0.12);
  color: var(--app-primary-deep);
  font-size: 28px;
}

.hero-copy {
  min-width: 0;
}

.hero-title {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
  color: var(--app-text);
}

.hero-desc {
  margin: 8px 0 0;
  font-size: 13px;
  line-height: 1.7;
  color: var(--app-text-soft);
}

.quick-actions {
  margin-top: 16px;
}

.quick-action {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 0;
  color: inherit;
}

.quick-action + .quick-action {
  border-top: 1px solid #eef3fb;
}

.quick-icon {
  width: 40px;
  height: 40px;
  flex-shrink: 0;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(47, 126, 247, 0.12);
  color: var(--app-primary-deep);
  font-size: 20px;
}

.quick-icon-refresh {
  background: rgba(48, 215, 169, 0.14);
  color: #0daa79;
}

.quick-copy {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
  text-align: left;
}

.quick-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--app-text);
}

.quick-desc {
  font-size: 12px;
  line-height: 1.6;
  color: var(--app-text-soft);
}

.quick-arrow {
  color: var(--app-text-faint);
  font-size: 18px;
}

.faq-list {
  margin-top: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.faq-item + .faq-item {
  padding-top: 16px;
  border-top: 1px solid #eef3fb;
}

.faq-question {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: var(--app-text);
}

.faq-answer {
  margin: 8px 0 0;
  font-size: 13px;
  line-height: 1.7;
  color: var(--app-text-soft);
}
</style>
