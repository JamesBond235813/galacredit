<script setup>
import { ref } from 'vue'
import PageHeader from '../../components/PageHeader.vue'
import { bindUserChannel } from '../../api/index.js'
import { errorMessage, requireSession } from '../../utils/app.js'
const code = ref('')
const busy = ref(false)
async function bind() {
  if (!requireSession() || busy.value) return
  const value = code.value.trim().toLowerCase()
  if (!/^[a-z0-9]{24,32}$/.test(value)) return uni.showToast({ title: 'Enter a valid invitation code.', icon: 'none' })
  busy.value = true
  try { await bindUserChannel({ invite_code: value }); uni.showToast({ title: 'Invitation linked', icon: 'none' }); code.value = '' }
  catch (error) { uni.showToast({ title: errorMessage(error, 'Unable to link this invitation.'), icon: 'none' }) }
  finally { busy.value = false }
}
</script>

<template><view class="gc-page"><PageHeader title="Invitation access" subtitle="If a partner invited you, enter their code once." :back="true" /><view class="gc-card"><input v-model="code" class="gc-field" maxlength="32" placeholder="Invitation code" /><button class="gc-button" :loading="busy" :disabled="busy" @click="bind">{{ busy ? 'Linking…' : 'Link invitation' }}</button><view class="gc-safe-note">Only use a code from a trusted GalaCredit partner.</view></view></view></template>
