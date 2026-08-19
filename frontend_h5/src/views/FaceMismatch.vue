<template>
  <div class="page-shell mismatch-page">
    <van-nav-bar left-arrow title="Verification Result" @click-left="goBack" />

    <div class="page-inner mismatch-inner">
      <section class="page-card mismatch-card">
        <div class="icon-wrap">!</div>
        <h1 class="title">Verification Unsuccessful</h1>
        <p class="desc">Your face image did not match your identity document. Please try again.</p>
        <p v-if="reasonText" class="reason">{{ reasonText }}</p>
        <van-button block type="primary" class="primary-action retry-btn" @click="goBack">
          Try Face Verification Again
        </van-button>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';

const router = useRouter();
const route = useRoute();

const reasonText = computed(() => {
  const reason = String(route.query.reason || '').trim();
  return reason ? `Reason: ${reason}` : '';
});

const goBack = () => {
  router.replace('/face');
};
</script>

<style scoped>
.mismatch-page {
  min-height: 100vh;
}

.mismatch-inner {
  padding-top: calc(env(safe-area-inset-top, 0px) + 10px);
}

.mismatch-card {
  margin-top: 10px;
  text-align: center;
  padding: 28px 18px 20px;
}

.icon-wrap {
  width: 54px;
  height: 54px;
  margin: 0 auto 10px;
  border-radius: 50%;
  background: rgba(243, 84, 96, 0.12);
  color: #e64858;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  font-weight: 700;
}

.title {
  margin: 0;
  font-size: 22px;
  color: var(--app-text);
  font-weight: 800;
}

.desc {
  margin: 10px 0 0;
  font-size: 14px;
  line-height: 1.7;
  color: var(--app-text-soft);
}

.reason {
  margin: 12px 0 0;
  padding: 10px 12px;
  background: rgba(255, 255, 255, 0.76);
  border: 1px solid rgba(243, 84, 96, 0.16);
  border-radius: 12px;
  font-size: 12px;
  line-height: 1.6;
  color: #7a869e;
  text-align: left;
}

.retry-btn {
  margin-top: 16px;
}
</style>
