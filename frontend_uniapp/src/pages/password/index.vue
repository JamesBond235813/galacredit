<script setup>
import { ref } from 'vue'
import PageHeader from '../../components/PageHeader.vue'
import { changePassword } from '../../api/index.js'
import { errorMessage, requireSession } from '../../utils/app.js'

const form = ref({ oldPassword: '', newPassword: '', confirmPassword: '' })
const busy = ref(false)

async function submit() {
  if (!requireSession() || busy.value) return
  if (form.value.newPassword.length < 6 || form.value.newPassword !== form.value.confirmPassword) return uni.showToast({ title: 'Use 6+ characters and confirm the same password.', icon: 'none' })
  busy.value = true
  try { await changePassword({ old_password: form.value.oldPassword, new_password: form.value.newPassword, confirm_password: form.value.confirmPassword }); uni.showToast({ title: 'Password changed', icon: 'none' }); form.value = { oldPassword: '', newPassword: '', confirmPassword: '' } }
  catch (error) { uni.showToast({ title: errorMessage(error, 'Unable to change password.'), icon: 'none' }) }
  finally { busy.value = false }
}
</script>

<template><view class="gc-page"><PageHeader title="Change password" subtitle="Keep your account protected." :back="true" /><view class="gc-card"><input v-model="form.oldPassword" class="gc-field" password placeholder="Current password" /><input v-model="form.newPassword" class="gc-field" password placeholder="New password" /><input v-model="form.confirmPassword" class="gc-field" password placeholder="Confirm new password" /><button class="gc-button" :loading="busy" :disabled="busy" @click="submit">{{ busy ? 'Saving…' : 'Save password' }}</button></view></view></template>
