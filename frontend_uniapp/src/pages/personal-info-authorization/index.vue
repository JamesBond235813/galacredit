<script setup>
import { computed, onMounted, ref } from 'vue'
import PageHeader from '../../components/PageHeader.vue'

const loading = ref(true)
const content = ref('')
const fallback = `GALACREDIT PERSONAL DATA AUTHORIZATION\n\nLast updated: 5 September 2026\n\nPlease read this authorization before submitting identity documents or a credit application.\n\n1. DATA WE MAY COLLECT\n\nGalaCredit may process your identity, phone, application, device, location, emergency contact, MoMo and repayment information for account security, identity verification, credit assessment, servicing and legal obligations.\n\n2. YOUR CHOICES AND RIGHTS\n\nYou may request access to or correction of your personal data, raise a complaint through Customer Support and decline optional SMS review. Identity and risk checks required for a credit decision must still be completed.\n\n3. AUTHORIZATION\n\nBy submitting your information, you confirm that it is accurate and authorise GalaCredit and approved service providers to process it for the purposes described above, subject to applicable law.`
const paragraphs = computed(() => String(content.value || '').split(/\n\s*\n/g).map((item) => item.replace(/\n/g, ' ').trim()).filter(Boolean))

async function load() {
  try {
    if (typeof fetch === 'function') {
      const response = await fetch('/personal-info-authorization.txt', { cache: 'no-cache' })
      if (response.ok) content.value = await response.text()
    }
  } catch { /* App-Plus 或离线环境使用内置的同版条款摘要。 */ }
  if (!content.value) content.value = fallback
  loading.value = false
}

onMounted(load)
</script>

<template>
  <view class="gc-page authorization-page">
    <PageHeader title="Personal Data Authorization" :back="true" />
    <view class="gc-card authorization-card"><text class="authorization-title">Personal Data Authorization</text><text class="tip">The latest version of the authorization terms is shown below.</text><text v-if="loading" class="copy">Loading authorization…</text><view v-else class="authorization-content"><text v-for="(item, index) in paragraphs" :key="index" class="copy">{{ item }}</text></view></view>
  </view>
</template>

<style scoped>
.authorization-page { width:min(100%,430px); min-height:100vh; margin:0 auto; padding:calc(24px + env(safe-area-inset-top)) 10px calc(32px + env(safe-area-inset-bottom)); }
.authorization-card { padding:16px 14px 18px; }
.authorization-title { display:block; font-size:22px; line-height:1.2; font-weight:700; }
.tip,.copy { display:block; color:var(--gc-muted); font-size:12px; line-height:1.72; }
.tip { margin-top:8px; margin-bottom:12px; }
.authorization-content { display:flex; flex-direction:column; gap:10px; margin-top:0; }
.authorization-content .copy { color:var(--gc-ink); font-size:13px; text-align:justify; }
</style>
