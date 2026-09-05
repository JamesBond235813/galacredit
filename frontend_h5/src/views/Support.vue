<template>
  <div class="page-shell support-page">
    <van-nav-bar left-arrow title="Customer Support" @click-left="router.back()" />

    <div class="page-inner support-inner">
      <section class="page-card hero-card">
        <div class="hero-icon">
          <van-icon name="service-o" />
        </div>
        <div class="hero-copy">
          <h1 class="hero-title">How Can We Help?</h1>
          <p class="hero-desc">Find answers, review your applications and contact support.</p>
        </div>
      </section>

      <section class="page-card quick-card">
        <h2 class="page-section-title">Quick Access</h2>
        <div class="quick-actions">
          <button type="button" class="quick-action" @click="router.push('/orders')">
            <span class="quick-icon">
              <van-icon name="orders-o" />
            </span>
            <span class="quick-copy">
              <span class="quick-title">View My Applications</span>
              <span class="quick-desc">Review applications, decisions and repayment status</span>
            </span>
            <van-icon name="arrow" class="quick-arrow" />
          </button>

          <button type="button" class="quick-action" @click="refreshStatus">
            <span class="quick-icon quick-icon-refresh">
              <van-icon name="replay" />
            </span>
            <span class="quick-copy">
              <span class="quick-title">Refresh Status</span>
              <span class="quick-desc">Load the latest review, disbursement and repayment information</span>
            </span>
            <van-icon name="arrow" class="quick-arrow" />
          </button>
        </div>
      </section>

      <section class="page-card faq-card">
        <h2 class="page-section-title">Frequently Asked Questions</h2>
        <div class="faq-list">
          <div class="faq-item" v-for="item in faqs" :key="item.question">
            <p class="faq-question">{{ item.question }}</p>
            <p class="faq-answer">{{ item.answer }}</p>
          </div>
        </div>
      </section>

      <section class="page-card service-card">
        <h2 class="page-section-title">Support Hours</h2>
        <p class="page-section-desc">Weekdays, 09:00 - 18:00. Requests submitted outside these hours will be handled during the next service period.</p>
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
    question: 'How do I apply for credit?',
    answer: 'Open the home page, select Apply Now, and complete identity and face verification.'
  },
  {
    question: 'Why is my application still under review?',
    answer: 'Review time depends on the completeness of your information and the applicable credit rules. Check My Applications for updates.'
  },
  {
    question: 'Where can I find repayment information?',
    answer: 'Open My Applications and select View Bill once your loan is disbursed or overdue.'
  }
];

const refreshStatus = () => {
  showToast('Status refreshed. Open My Applications to view the latest information.');
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
  background: rgba(234, 149, 24, 0.12);
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
  background: rgba(234, 149, 24, 0.12);
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
