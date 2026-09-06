<script setup>
import { ref } from 'vue'
import { changePassword } from '../../api/index.js'
import { errorMessage, requireSession } from '../../utils/app.js'

const form = ref({ oldPassword: '', newPassword: '', confirmPassword: '' })
const busy = ref(false)

async function submit() {
  if (!requireSession() || busy.value) return
  if (form.value.oldPassword.length < 6) return uni.showToast({ title: 'Enter your current password.', icon: 'none' })
  if (form.value.newPassword.length < 6 || form.value.newPassword !== form.value.confirmPassword) return uni.showToast({ title: 'Use 6+ characters and confirm the same password.', icon: 'none' })
  busy.value = true
  try { await changePassword({ old_password: form.value.oldPassword, new_password: form.value.newPassword, confirm_password: form.value.confirmPassword }); uni.showToast({ title: 'Password changed', icon: 'none' }); form.value = { oldPassword: '', newPassword: '', confirmPassword: '' } }
  catch (error) { uni.showToast({ title: errorMessage(error, 'Unable to change password.'), icon: 'none' }) }
  finally { busy.value = false }
}
</script>

<template>
  <view class="gc-page password-page"><view class="gc-card form-card"><text class="section-title">Change Sign-in Password</text><input v-model="form.oldPassword" class="gc-field" password placeholder="Current password" /><input v-model="form.newPassword" class="gc-field" password placeholder="New password (at least 6 characters)" /><input v-model="form.confirmPassword" class="gc-field" password placeholder="Confirm new password" /><button class="gc-button" :loading="busy" :disabled="busy" @click="submit">{{ busy ? 'Saving…' : 'Update Password' }}</button></view></view></template>

<style scoped>
.password-page { width:min(100%,430px); min-height:100vh; margin:0 auto; padding:calc(40px + env(safe-area-inset-top)) 12px calc(32px + env(safe-area-inset-bottom)); }
.form-card { padding:16px 0 20px; }
.section-title { display:block; margin:0 16px 14px; color:var(--gc-ink); font-size:18px; line-height:1.3; font-weight:700; }
.form-card .gc-field { width:100%; height:56px; min-height:56px; margin:0; padding:16px 18px; border:0; border-bottom:1px solid #eef3fb; border-radius:0; background:transparent; color:var(--gc-ink); font-size:16px; line-height:24px; }
.form-card .gc-field::placeholder { color:#9aa4b3; }
.form-card .gc-button { width:calc(100% - 32px); height:44px; min-height:44px; margin-left:16px; margin-top:20px; border-radius:22px; font-size:14px; }
</style>
