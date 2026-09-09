<script setup>
import { computed, onMounted, ref } from 'vue'
import PageHeader from '../../components/PageHeader.vue'
import AsyncState from '../../components/AsyncState.vue'
import Icon from '../../components/Icon.vue'
import { getUserInfo, submitOCR } from '../../api/index.js'
import { errorMessage, requireSession } from '../../utils/app.js'
import { usePageResume } from '../../utils/page-resume.js'

const state = ref({ loading: true, error: '', user: null })
const busy = ref(false)
const agreed = ref(false)
const activeType = ref('')
const documentsReady = computed(() => Boolean(state.value.user?.id_card_front_image_url || state.value.user?.id_card_verified || state.value.user?.ocr_status === 'PASSED'))

function continueToFace() {
  uni.navigateTo({ url: '/pages/face/index' })
}

async function load() {
  if (!requireSession()) return
  try { state.value = { loading: false, error: '', user: await getUserInfo() } }
  catch (error) { state.value = { loading: false, error: errorMessage(error), user: null } }
}

/**
 * 选择并上传 Ghana Card 图片，后端负责 OCR 处理。
 *
 * :param side: front 或 back
 * :return: 无
 */
function chooseCaptureSource() {
  if (busy.value) return
  uni.showActionSheet({
    itemList: ['Take photo', 'Choose from gallery'],
    success: ({ tapIndex }) => uploadDocuments(tapIndex === 0 ? 'camera' : 'album')
  })
}

async function uploadDocuments(source = 'album') {
  if (busy.value) return
  busy.value = true
  activeType.value = 'documents'
  try {
    const result = await submitOCR({ source: 'uniapp' }, { sourceType: [source] })
    state.value.user = { ...state.value.user, ...result }
    uni.showToast({ title: 'Document uploaded', icon: 'none' })
    setTimeout(() => uni.navigateTo({ url: '/pages/face/index' }), 500)
  } catch (error) { uni.showToast({ title: errorMessage(error, 'Unable to upload your document.'), icon: 'none' }) }
  finally { busy.value = false; activeType.value = '' }
}

onMounted(load)
usePageResume(() => { if (!busy.value) return load() })
</script>

<template>
  <view class="gc-page verification-page">
    <PageHeader title="ID Verification" :back="true" />
    <view class="document-heading"><text>Capture both sides of your</text><text class="document-heading__strong">Ghana Card</text><text class="document-heading__hint">First capture the front, then the back when prompted.</text></view>
    <AsyncState :loading="state.loading" :error="state.error" :empty="false" @retry="load">
      <view v-for="side in ['front','back']" :key="side" class="capture-panel">
        <text class="capture-label">{{ side === 'front' ? 'Front of your Ghana Card' : 'Back of your Ghana Card' }}</text>
        <view class="viewfinder">
          <view class="finder-corner top-left" /><view class="finder-corner top-right" /><view class="finder-corner bottom-left" /><view class="finder-corner bottom-right" />
          <view class="ghana-card-placeholder"><view class="ghana-card-topline"><text class="ghana-seal">GH</text><view><text>ECOWAS IDENTITY CARD</text><text>REPUBLIC OF GHANA</text></view><view class="ghana-flag"><text /><text /><text /></view></view><view class="ghana-card-body"><view class="ghana-chip" /><view class="ghana-lines"><text /><text /><text /><text /></view><view class="ghana-portrait"><text /></view></view></view>
          <button class="upload-button" :disabled="busy" @click="chooseCaptureSource"><Icon name="camera" :size="18" /><text>{{ activeType === 'documents' ? 'Uploading…' : 'Add photo' }}</text></button>
        </view>
      </view>
      <view class="note-section"><text class="note-title">Note:</text><text class="note-copy">Submitting a clear, valid Ghana Card scan can help you get a higher credit limit.</text></view>
      <view class="reject-section"><view class="reject-title"><view class="reject-icon">×</view><text>Photos that would be rejected</text></view><view class="reject-grid"><view class="reject-item"><view class="reject-shot selfie-shot" /><text>Selfie</text></view><view class="reject-item"><view class="reject-shot blur-shot"><view class="blur-card"><text>GHANA CARD</text><text /><text /><text /></view></view><text>Blurred photos or incomplete ID photos</text></view><view class="reject-item"><view class="reject-shot scenery-shot" /><text>Scenery or items</text></view></view></view>
    </AsyncState>
    <view class="verification-footer"><label class="agreement-row" @click="agreed = !agreed"><view :class="['agreement-check', { checked: agreed }]">{{ agreed ? '✓' : '' }}</view><text>I have read and agree to the <text class="agreement-link" @click.stop="uni.navigateTo({ url: '/pages/personal-info-authorization/index' })">Personal Data Authorization</text></text></label><button class="gc-button submit-btn" :disabled="!documentsReady || !agreed || busy" @click="documentsReady ? continueToFace() : chooseCaptureSource()">{{ busy ? 'Uploading…' : 'Submit Identity Information' }}</button></view>
  </view>
</template>

<style scoped>
.verification-page { padding:calc(24px + env(safe-area-inset-top)) 16px calc(150px + 88px + env(safe-area-inset-bottom)); background:#fffaf2; }
.verification-page :deep(.gc-page-header) { margin:0 -16px 18px; }
.document-heading { display:flex; flex-direction:column; gap:6px; margin:0 2px 16px; color:var(--gc-ink); font-size:14px; line-height:1.45; }
.document-heading__strong { display:block; color:var(--gc-brand-deep); font-size:24px; line-height:1.15; font-weight:800; }
.document-heading__hint { color:var(--gc-muted); font-size:12px; }
.capture-panel { padding:14px; margin-top:12px; border:1px solid #e7ebf1; border-radius:20px; background:#fff; box-shadow:0 10px 24px rgba(23,32,51,.06); }.capture-panel:first-child { margin-top:0; }.capture-label { display:flex; align-items:center; gap:8px; margin:0 0 10px; color:var(--gc-ink); font-size:15px; font-weight:750; }.capture-label::before { content:''; display:inline-block; width:8px; height:8px; border-radius:50%; background:var(--gc-brand); box-shadow:0 0 0 4px rgba(234,149,24,.12); }
.viewfinder { position:relative; aspect-ratio:2.18 / 1; overflow:hidden; border:1px solid #e7edf6; border-radius:16px; background:linear-gradient(180deg,#fbfdff 0%,#f4f7fc 100%); }
.finder-corner { position:absolute; z-index:2; width:16px; height:16px; border:2px solid rgba(234,149,24,.9); }
.top-left { top:12px; left:12px; border-right:0; border-bottom:0; }.top-right { top:12px; right:12px; border-left:0; border-bottom:0; }.bottom-left { bottom:12px; left:12px; border-right:0; border-top:0; }.bottom-right { right:12px; bottom:12px; border-left:0; border-top:0; }
.ghana-card-placeholder { position:absolute; inset:18% 12%; padding:10px; border-radius:10px; opacity:.55; background:linear-gradient(145deg,#f4f8ff 0%,#e4edfb 100%); box-shadow:0 8px 20px rgba(34,63,95,.08); color:#6b82a2; }
.ghana-card-topline { display:flex; align-items:center; gap:7px; font-size:7px; text-align:center; }.ghana-card-topline > view:nth-child(2) { flex:1; }.ghana-card-topline > view:nth-child(2) text { display:block; line-height:1.25; }.ghana-seal { display:flex; align-items:center; justify-content:center; width:24px; height:24px; border:2px solid #d1a141; border-radius:50%; color:#317360; font-size:8px; font-weight:800; }.ghana-flag { display:flex; width:30px; flex-direction:column; }.ghana-flag text { height:6px; background:#d94a48; }.ghana-flag text:nth-child(2) { background:#e5c34d; }.ghana-flag text:nth-child(3) { background:#3b9868; }
.ghana-card-body { display:grid; grid-template-columns:42px 1fr 54px; align-items:center; gap:8px; margin-top:12px; }.ghana-chip { height:34px; border-radius:6px; background:linear-gradient(135deg,#e7c675,#b88f3e); }.ghana-lines { display:flex; flex-direction:column; gap:7px; }.ghana-lines text { width:90%; height:4px; border-radius:4px; background:rgba(88,115,143,.28); }.ghana-lines text:nth-child(2) { width:68%; }.ghana-lines text:nth-child(4) { width:78%; }.ghana-portrait { height:66px; border-radius:6px; background:rgba(204,218,228,.9); overflow:hidden; }.ghana-portrait text { display:block; width:42px; height:58px; margin:12px auto 0; border-radius:50% 50% 35% 35%; background:#9fb1c4; }
.upload-button { position:absolute; left:50%; top:50%; z-index:4; display:flex; flex-direction:column; align-items:center; justify-content:center; gap:2px; width:56px; height:56px; transform:translate(-50%,-50%); border:3px solid rgba(255,255,255,.78); border-radius:50%; color:#fff; background:var(--gc-brand-deep); box-shadow:0 8px 18px rgba(201,111,12,.25); font-size:11px; font-weight:750; }.upload-button::after { border:0; }
.note-section { margin:16px 2px 0; padding:12px 14px; border-radius:14px; background:#fff8ed; }
.note-title { display:block; color:var(--gc-brand-deep); font-size:13px; font-weight:750; }
.note-copy { display:block; margin-top:4px; color:#7d6c55; font-size:12px; line-height:1.5; }
.reject-section { margin:22px 2px 0; }
.reject-title { display:flex; align-items:center; gap:8px; height:22px; margin-bottom:10px; color:var(--gc-ink); font-size:14px; font-weight:700; }
.reject-icon { display:flex; align-items:center; justify-content:center; width:20px; height:20px; border:2px solid #e44b42; border-radius:50%; color:#e44b42; font-size:16px; line-height:16px; }
.reject-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:10px; }
.reject-item { min-width:0; text-align:center; }
.reject-shot { position:relative; height:72px; border:1px solid #e4e9f1; border-radius:7px; background:#eef3f8; overflow:hidden; }
.reject-item > text { display:block; margin-top:7px; color:#9aa4b3; font-size:10px; line-height:1.3; }
.selfie-shot { background:#eef3f8; }.selfie-shot::after { content:''; position:absolute; left:25px; right:25px; bottom:0; height:52px; border-radius:50% 50% 0 0; background:#8eb4d6; }.selfie-shot::before { content:''; position:absolute; z-index:1; left:50%; top:9px; width:28px; height:28px; transform:translateX(-50%); border-radius:50%; background:#506f91; }
.blur-shot { background:#eef3f8; }.blur-card { position:absolute; inset:12px 8px; padding:8px; border-radius:5px; background:#e8f1ed; filter:blur(1.7px); text-align:left; }.blur-card text { display:block; font-size:7px; }.blur-card text + text { width:70%; height:3px; margin-top:6px; background:#91a5b5; }.scenery-shot { background:linear-gradient(#b9dcf2 0 48%,#d5c178 49%); }.scenery-shot::before,.scenery-shot::after { position:absolute; bottom:27px; content:''; border-style:solid; border-width:0 30px 24px; border-color:transparent transparent #819e88; }.scenery-shot::before { left:-8px; }.scenery-shot::after { right:-12px; border-bottom-color:#76917c; }
.verification-footer { position:fixed; left:50%; bottom:calc(88px + env(safe-area-inset-bottom)); z-index:10; width:min(430px,100%); transform:translateX(-50%); padding:10px 16px 12px; background:linear-gradient(180deg,rgba(247,251,255,0) 0%,rgba(250,252,255,.9) 20%,rgba(255,255,255,.98) 42%); backdrop-filter:blur(14px); }
.agreement-row { display:flex; align-items:flex-start; gap:6px; margin-bottom:10px; color:#9aa4b3; font-size:11px; line-height:1.5; }
.agreement-check { flex:none; width:18px; height:18px; border:1px solid #c8d0de; border-radius:50%; color:#fff; text-align:center; font-size:12px; line-height:16px; }.agreement-check.checked { border-color:var(--gc-brand); background:var(--gc-brand); }
.agreement-link { color:var(--gc-brand-deep); }
.submit-btn { height:46px; min-height:46px; margin-top:0; border-radius:14px; font-size:15px; }
.submit-btn[disabled] { color:#fff; background:#c8d0de; opacity:1; }
</style>
