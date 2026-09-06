<script setup>
import { computed, onMounted, ref } from 'vue'

const loading = ref(true)
const content = ref('')
const fallback = `GALACREDIT USER AGREEMENT\n\nLast updated: 5 September 2026\n\nPlease read this agreement before using GalaCredit services.\n\n1. ELIGIBILITY AND ACCOUNT\n\nYou must provide accurate information and keep your account credentials secure.\n\n2. CREDIT SERVICES\n\nApplications are assessed using the information and checks described in the application flow. Approval, amount and repayment terms are subject to the result of that assessment.\n\n3. CONTACT\n\nYou may contact Customer Support for questions, corrections or complaints.`
const paragraphs = computed(() => String(content.value || '').split(/\n\s*\n/g).map((item) => item.replace(/\n/g, ' ').trim()).filter(Boolean))

/** 加载与 H5 共用的用户协议文本。
 *
 * :return: Promise<void>
 */
async function load() {
  try {
    // app-plus 原生渲染没有浏览器 fetch；优先读取 H5 静态文件，失败时使用同版内置条款保证页面可用。
    if (typeof fetch === 'function') {
      const response = await fetch('/user-agreement.txt', { cache: 'no-cache' })
      if (response.ok) content.value = await response.text()
    }
  } catch {
    // 离线或 app-plus 资源路径不可用时继续使用内置内容。
  }
  if (!content.value) content.value = fallback
  loading.value = false
}

onMounted(load)
</script>

<template>
  <view class="gc-page agreement-page">
    <view class="gc-card agreement-card"><text class="agreement-title">User Agreement</text><text class="agreement-tip">The latest version of the platform agreement is shown below.</text><text v-if="loading" class="agreement-loading">Loading agreement...</text><view v-else class="agreement-content"><text v-for="(item, index) in paragraphs" :key="index" class="agreement-paragraph">{{ item }}</text></view></view>
  </view>
</template>

<style scoped>
.agreement-page { width:min(100%,430px); min-height:100vh; margin:0 auto; padding:calc(40px + env(safe-area-inset-top)) 10px calc(32px + env(safe-area-inset-bottom)); }
.agreement-card { padding:16px 14px 18px; }
.agreement-title { display:block; color:var(--gc-ink); font-size:22px; line-height:1.2; font-weight:700; }
.agreement-tip { display:block; margin:8px 0 12px; color:var(--gc-muted); font-size:12px; line-height:1.4; }
.agreement-loading { display:block; color:var(--gc-muted); font-size:14px; }
.agreement-content { display:flex; flex-direction:column; gap:10px; }
.agreement-paragraph { display:block; color:var(--gc-ink); font-size:13px; line-height:1.72; text-align:justify; word-break:break-word; }
</style>
