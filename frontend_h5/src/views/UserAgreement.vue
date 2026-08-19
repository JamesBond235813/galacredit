<template>
  <div class="page-shell agreement-page">
    <section class="page-card agreement-card">
      <h1 class="agreement-title">User Agreement</h1>
      <p class="agreement-tip">The latest version of the platform agreement is shown below.</p>
      <div v-if="loading" class="agreement-loading">Loading agreement...</div>
      <div v-else class="agreement-content">
        <p v-for="(item, index) in paragraphs" :key="index">{{ item }}</p>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';

const loading = ref(true);
const content = ref('');

const paragraphs = computed(() =>
  String(content.value || '')
    .split(/\n\s*\n/g)
    .map((item) => item.replace(/\n/g, ' ').trim())
    .filter(Boolean)
);

onMounted(async () => {
  try {
    const resp = await fetch('/user-agreement.txt', { cache: 'no-cache' });
    content.value = await resp.text();
  } catch (error) {
    content.value = 'The User Agreement could not be loaded. Please try again later.';
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
.agreement-page {
  min-height: calc(100vh - 88px);
  padding: calc(env(safe-area-inset-top, 0px) + 18px) 10px 24px;
  box-sizing: border-box;
}

.agreement-card {
  padding: 16px 14px 18px;
}

.agreement-title {
  margin: 0;
  font-size: 22px;
  color: var(--app-text);
  font-weight: 700;
}

.agreement-tip {
  margin: 8px 0 12px;
  font-size: 12px;
  color: var(--app-text-soft);
}

.agreement-loading {
  color: var(--app-text-soft);
  font-size: 14px;
}

.agreement-content {
  display: grid;
  gap: 10px;
}

.agreement-content p {
  margin: 0;
  color: var(--app-text);
  font-size: 13px;
  line-height: 1.72;
  text-align: justify;
  white-space: normal;
  word-break: break-word;
}
</style>
