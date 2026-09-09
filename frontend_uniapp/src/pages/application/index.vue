<script setup>
import { onMounted, ref } from 'vue'
import PageHeader from '../../components/PageHeader.vue'
import AsyncState from '../../components/AsyncState.vue'
import { getUserInfo, submitApplication } from '../../api/index.js'
import { chooseContact } from '../../utils/platform.js'
import { errorMessage, requireSession } from '../../utils/app.js'
import { usePageResume } from '../../utils/page-resume.js'

const familyRelations = ['Parents', 'Brothers or sisters', 'Grandparents', 'Couple', 'Children']
const socialRelations = ['Friends', 'Classmates', 'Colleagues']
const state = ref({ loading: true, error: '', saved: null })
const contacts = ref([
  { category: 'FAMILY', relation: '', name: '', phone: '', source: '' },
  { category: 'SOCIAL', relation: '', name: '', phone: '', source: '' }
])
const busy = ref(false)

async function load() {
  if (!requireSession()) return
  try {
    const user = await getUserInfo()
    contacts.value[0] = { ...contacts.value[0], relation: familyRelations.includes(user.emergency_contact1_relation) ? user.emergency_contact1_relation : '', name: user.emergency_contact1_name || '', phone: user.emergency_contact1_phone || '', source: user.emergency_contact1_phone ? 'CONTACT_PICKER' : '' }
    contacts.value[1] = { ...contacts.value[1], relation: socialRelations.includes(user.emergency_contact2_relation) ? user.emergency_contact2_relation : '', name: user.emergency_contact2_name || '', phone: user.emergency_contact2_phone || '', source: user.emergency_contact2_phone ? 'CONTACT_PICKER' : '' }
    state.value.loading = false
  } catch (error) {
    state.value = { ...state.value, loading: false, error: errorMessage(error, 'Unable to load your saved contacts.') }
  }
}

async function pick(index) {
  if (busy.value) return
  busy.value = true
  try {
    const selected = await chooseContact()
    contacts.value[index] = { ...contacts.value[index], name: selected.name || '', phone: selected.phone || '', source: 'CONTACT_PICKER' }
  } catch (error) {
    uni.showToast({ title: errorMessage(error, 'Choose a contact from your address book.'), icon: 'none' })
  } finally { busy.value = false }
}

function validPhone(value) { return /^(?:233\d{9}|\d{11})$/.test(String(value || '').replace(/\D/g, '')) }
function displayLocalPhone(value) {
  const digits = String(value || '').replace(/\D/g, '')
  return digits.startsWith('233') && digits.length === 12 ? digits.slice(3) : digits
}

function validate() {
  const rows = contacts.value
  if (rows.some((item) => !item.name.trim() || !item.relation || !validPhone(item.phone) || item.source !== 'CONTACT_PICKER')) {
    uni.showToast({ title: 'Choose two valid contacts and relationships.', icon: 'none' })
    return false
  }
  if (rows[0].phone.replace(/\D/g, '') === rows[1].phone.replace(/\D/g, '')) {
    uni.showToast({ title: 'The two contacts must be different.', icon: 'none' })
    return false
  }
  return true
}

async function submit() {
  if (busy.value || !validate()) return
  busy.value = true
  try {
    await submitApplication({ emergency_contacts: contacts.value.map(({ category, relation, name, phone, source }) => ({ category, relation, name: name.trim(), phone: phone.replace(/\D/g, ''), source })) })
    state.value.saved = true
    uni.showToast({ title: 'Application details saved', icon: 'none' })
    setTimeout(() => uni.navigateTo({ url: '/pages/home/index' }), 700)
  } catch (error) {
    uni.showToast({ title: errorMessage(error, 'Unable to submit your application.'), icon: 'none' })
  } finally { busy.value = false }
}

onMounted(load)
usePageResume(() => { if (!busy.value) return load() })
</script>

<template>
  <view class="gc-page application-page">
    <PageHeader title="Additional Information" :back="true" />
    <view class="application-heading"><text class="hero-chip">Step 3 of 4</text><text class="hero-title">Emergency Contacts</text><text class="hero-desc">Provide two emergency contacts from your address book.</text></view>
    <AsyncState :loading="state.loading" :error="state.error" :empty="false" @retry="load">
      <view class="contact-grid">
        <view v-for="(contact, index) in contacts" :key="contact.category" class="gc-card contact-card">
          <view class="contact-head"><text class="contact-index">Emergency contact {{ index + 1 }} ({{ contact.category === 'FAMILY' ? 'family' : 'friend' }})</text></view>
          <view class="contact-fields">
            <view class="contact-display-field contact-field">
              <text class="contact-display-label">Relatives</text>
              <picker class="relation-picker" mode="selector" :range="contact.category === 'FAMILY' ? familyRelations : socialRelations" :value="Math.max((contact.category === 'FAMILY' ? familyRelations : socialRelations).indexOf(contact.relation), 0)" @change="contact.relation = (contact.category === 'FAMILY' ? familyRelations : socialRelations)[$event.detail.value]">
                <view class="relation-trigger" :class="{ empty: !contact.relation }"><text>{{ contact.relation || 'Select relationship' }}</text><text>⌄</text></view>
              </picker>
            </view>
            <button class="contact-display-field contact-action-field" :disabled="busy" @click="pick(index)"><text class="contact-display-label">PhoneNumber</text><text class="contact-display-value" :class="{ empty: !contact.phone }">{{ displayLocalPhone(contact.phone) || 'Select contact' }}</text><text class="contact-display-arrow">›</text></button>
            <button class="contact-display-field contact-action-field" :disabled="busy" @click="pick(index)"><text class="contact-display-label">Full Name</text><text class="contact-display-value" :class="{ empty: !contact.name }">{{ contact.name || 'Select contact' }}</text><text class="contact-display-arrow">›</text></button>
          </view>
        </view>
      </view>
      <button class="gc-button submit-btn" :loading="busy" :disabled="busy" @click="submit">{{ busy ? 'Submitting…' : 'Submit Application' }}</button>
    </AsyncState>
  </view>
</template>

<style scoped>
.application-page { padding:calc(24px + env(safe-area-inset-top)) 12px calc(88px + env(safe-area-inset-bottom)); }
.application-page :deep(.gc-page-header) { margin:0 -12px 8px; }
.application-heading { display:flex; flex-direction:column; align-items:flex-start; width:100%; padding:0; }
.hero-chip { display:inline-flex; align-items:center; min-height:22px; padding:0 10px; border-radius:999px; color:var(--gc-brand-deep); background:rgba(234,149,24,.1); font-size:10px; font-weight:700; }
.hero-title { display:block; margin-top:10px; font-size:24px; line-height:1.16; font-weight:800; }
.hero-desc { display:block; margin-top:6px; color:var(--gc-muted); font-size:14px; line-height:1.4; }
.contact-grid { display:grid; grid-template-columns:1fr; gap:12px; margin-top:12px; }
.contact-card { margin-top:0; padding:14px 12px; overflow:visible; }
.contact-head { display:flex; align-items:flex-start; height:24px; margin-bottom:8px; }
.contact-index { display:inline-flex; align-items:center; max-width:100%; min-height:24px; padding:0 10px; border-radius:999px; color:var(--gc-brand-deep); background:rgba(234,149,24,.08); font-size:12px; line-height:1.3; font-weight:700; }
.contact-fields { display:grid; grid-template-columns:1fr; gap:8px; }
.contact-display-field { display:flex; align-items:center; gap:12px; width:100%; min-height:56px; padding:0 14px; border:1px solid #e8eef8; border-radius:12px; color:var(--gc-ink); background:#f7faff; text-align:left; }
.contact-display-field::after { border:0; }
.contact-display-label { width:104px; flex:none; color:#9aa4b3; font-size:14px; font-weight:600; }
.relation-picker { min-width:0; flex:1; }
.relation-trigger { display:flex; align-items:center; justify-content:space-between; gap:8px; width:100%; min-height:24px; color:var(--gc-ink); font-size:16px; font-weight:700; }
.empty { color:#b2bed0 !important; font-weight:600 !important; }
.contact-field { border-color:#d8e2f0; background:#fff; }
.contact-display-value { min-width:0; flex:1; overflow:hidden; color:var(--gc-ink); font-size:16px; font-weight:700; text-align:right; text-overflow:ellipsis; white-space:nowrap; }
.contact-display-arrow { flex:none; color:var(--gc-muted); font-size:22px; line-height:1; }
.submit-btn { width:100%; height:48px; min-height:48px; margin-top:12px; border-radius:14px; font-size:17px; }
</style>
