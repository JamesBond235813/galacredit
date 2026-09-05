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
  <view class="gc-page">
    <PageHeader title="Additional information" subtitle="Add two contacts so we can support you responsibly." :back="true" />
    <AsyncState :loading="state.loading" :error="state.error" :empty="false" @retry="load">
      <view v-for="(contact, index) in contacts" :key="contact.category" class="gc-card contact-card">
        <view class="gc-row"><text class="gc-section-title">Emergency contact {{ index + 1 }}</text><text class="gc-badge">{{ contact.category === 'FAMILY' ? 'Family' : 'Social' }}</text></view>
        <picker mode="selector" :range="contact.category === 'FAMILY' ? familyRelations : socialRelations" :value="Math.max((contact.category === 'FAMILY' ? familyRelations : socialRelations).indexOf(contact.relation), 0)" @change="contact.relation = (contact.category === 'FAMILY' ? familyRelations : socialRelations)[$event.detail.value]">
          <view class="gc-field picker-field">{{ contact.relation || 'Select relationship' }} <text>⌄</text></view>
        </picker>
        <button class="gc-button gc-button--secondary" :disabled="busy" @click="pick(index)">{{ contact.name ? 'Change contact' : 'Choose from address book' }}</button>
        <view v-if="contact.name" class="selected-contact"><text class="selected-contact__name">{{ contact.name }}</text><text class="selected-contact__phone">{{ contact.phone }}</text></view>
      </view>
      <view class="gc-safe-note">We only use these details to contact you about your application or account support. We do not upload your full address book.</view>
      <button class="gc-button" :loading="busy" :disabled="busy" @click="submit">{{ busy ? 'Saving…' : 'Save and continue' }}</button>
    </AsyncState>
  </view>
</template>

<style scoped>
.contact-card { margin-top:20rpx; }
.contact-card .gc-section-title { margin:0; }
.picker-field { display:flex; align-items:center; justify-content:space-between; color:var(--gc-muted); line-height:94rpx; }
.gc-button--secondary { margin-top:18rpx; }
.selected-contact { margin-top:18rpx; padding:20rpx; border-radius:18rpx; background:#f7f9fc; }
.selected-contact__name,.selected-contact__phone { display:block; }
.selected-contact__name { font-size:28rpx; font-weight:700; }
.selected-contact__phone { margin-top:6rpx; color:var(--gc-muted); font-size:24rpx; }
</style>
