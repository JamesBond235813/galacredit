<template>
  <div class="page-shell ocr-page">
    <van-nav-bar left-arrow title="ID Verification" @click-left="router.back()" />

    <div class="page-inner ocr-inner">
      <header class="document-heading">
        <span>Front of your</span>
        <strong>Ghana Card</strong>
      </header>

      <section class="capture-panel">
        <div class="viewfinder">
          <div class="finder-corner top-left"></div>
          <div class="finder-corner top-right"></div>
          <div class="finder-corner bottom-left"></div>
          <div class="finder-corner bottom-right"></div>

          <img v-if="frontPreview" :src="frontPreview" alt="Ghana Card front" class="selected-preview" />
          <div v-else class="ghana-card-placeholder">
            <div class="ghana-card-topline">
              <span class="ghana-seal">GH</span>
              <div><b>ECOWAS IDENTITY CARD</b><small>REPUBLIC OF GHANA</small></div>
              <span class="ghana-flag"><i></i><i></i><i></i></span>
            </div>
            <div class="ghana-card-body">
              <div class="ghana-chip"></div>
              <div class="ghana-lines"><i></i><i></i><i></i><i></i></div>
              <div class="ghana-portrait"><span></span></div>
            </div>
          </div>

          <button type="button" class="upload-button" :class="{ 'upload-button-float': !!frontPreview }" @click="openPicker('front')">
            <van-icon name="photograph" />
            <span>{{ frontPreview ? 'Change' : 'Upload' }}</span>
          </button>
        </div>
      </section>

      <section class="note-section">
        <strong>Note:</strong>
        <p>Submitting a clear, valid Ghana Card scan can help you get a higher credit limit.</p>
      </section>

      <section class="reject-section">
        <h2><van-icon name="close" /> Photos that would be rejected</h2>
        <div class="reject-grid">
          <div v-for="item in rejectedExamples" :key="item.label" class="reject-item">
            <div class="reject-shot" :class="`reject-shot-${item.type}`">
              <div v-if="item.type === 'selfie'" class="selfie-figure"><span></span></div>
              <div v-else-if="item.type === 'blur'" class="blur-card"><b>GHANA CARD</b><i></i><i></i><i></i></div>
              <div v-else class="scenery"><i></i></div>
            </div>
            <p>{{ item.label }}</p>
          </div>
        </div>
      </section>
    </div>

    <footer class="ocr-footer">
      <div class="agreement-box">
        <van-checkbox v-model="agreed" icon-size="18px" checked-color="#2f7ef7" label-disabled>
          <span class="agreement-toggle" @click.stop="toggleAgreed">I have read and agree to the</span>
          <span class="agreement-link" @click.stop="goPersonalAgreement">Personal Data Authorization</span>
        </van-checkbox>
      </div>

      <van-button
        block
        type="primary"
        class="primary-action submit-btn"
        :disabled="!frontFile || !agreed"
        :loading="loading"
        @click="onSubmit"
      >
        Submit Identity Information
      </van-button>
    </footer>

    <transition name="sheet-fade">
      <div v-if="pickerVisible" class="picker-mask" @click="closePicker"></div>
    </transition>
    <transition name="sheet-up">
      <div v-if="pickerVisible" class="picker-sheet">
        <button type="button" class="picker-option" @click="chooseSource('camera')">Take Photo</button>
        <button type="button" class="picker-option" @click="chooseSource('album')">Choose from Gallery</button>
        <button type="button" class="picker-cancel" @click="closePicker">Cancel</button>
      </div>
    </transition>

    <input
      ref="frontCameraInput"
      type="file"
      accept="image/*"
      capture="environment"
      class="hidden-input"
      @change="handleFileChange($event, 'front')"
    />
    <input
      ref="frontAlbumInput"
      type="file"
      accept="image/*"
      class="hidden-input"
      @change="handleFileChange($event, 'front')"
    />
    <van-dialog
      v-model:show="showConfirm"
      title="Confirm Your Information"
      class-name="ocr-confirm-dialog"
      show-cancel-button
      confirm-button-color="#2f7ef7"
      @confirm="onConfirmInfo"
    >
      <van-cell-group inset>
        <van-cell class="ocr-confirm-cell" title="Full Name" :value="extractedInfo.name" />
        <van-cell class="ocr-confirm-cell" title="Ghana Card No.">
          <template #value>
            <span class="ocr-single-line-value">{{ extractedInfo.idNum }}</span>
          </template>
        </van-cell>
        <van-cell title="Residential Address" :value="extractedInfo.address" />
        <van-cell class="ocr-confirm-cell" title="Expiry Date">
          <template #value>
            <span class="ocr-single-line-value">{{ extractedInfo.expiry }}</span>
          </template>
        </van-cell>
      </van-cell-group>
    </van-dialog>
  </div>
</template>

<script setup>
import { onBeforeUnmount, ref } from 'vue';
import { useRouter } from 'vue-router';
import { showToast } from 'vant';
import { submitOCR } from '../api';
import { getOcrImageCompressionPlan } from '../utils/ocrImageCompression';

const router = useRouter();
const frontFile = ref(null);
const backFile = ref(null);
const frontPreview = ref('');
const backPreview = ref('');
const agreed = ref(false);
const loading = ref(false);
const showConfirm = ref(false);
const extractedInfo = ref({
  name: '',
  idNum: '',
  address: '',
  expiry: ''
});

const frontCameraInput = ref(null);
const frontAlbumInput = ref(null);
const pickerVisible = ref(false);
const pendingSide = ref('');

const rejectedExamples = [
  { label: 'Selfie', type: 'selfie' },
  { label: 'Blurred photos or incomplete ID photos', type: 'blur' },
  { label: 'Scenery or items', type: 'scenery' }
];

const revokePreview = (value) => {
  if (value) {
    URL.revokeObjectURL(value);
  }
};

const setFile = (side, file) => {
  const previewUrl = URL.createObjectURL(file);

  if (side === 'front') {
    revokePreview(frontPreview.value);
    frontFile.value = file;
    frontPreview.value = previewUrl;
    return;
  }

  revokePreview(backPreview.value);
  backFile.value = file;
  backPreview.value = previewUrl;
};

const compressImageIfNeeded = (file) =>
  new Promise((resolve) => {
    if (!file || !file.type.startsWith('image/')) {
      resolve(file);
      return;
    }
    const img = new Image();
    const reader = new FileReader();
    reader.onload = () => {
      img.src = String(reader.result || '');
    };
    reader.onerror = () => resolve(file);
    img.onload = () => {
      try {
        const plan = getOcrImageCompressionPlan({
          size: file.size,
          width: img.width,
          height: img.height
        });
        if (!plan.shouldCompress) {
          resolve(file);
          return;
        }
        const canvas = document.createElement('canvas');
        canvas.width = Math.round(img.width * plan.scale);
        canvas.height = Math.round(img.height * plan.scale);
        const ctx = canvas.getContext('2d');
        if (!ctx) {
          resolve(file);
          return;
        }
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        canvas.toBlob(
          (blob) => {
            if (!blob) {
              resolve(file);
              return;
            }
            resolve(new File([blob], file.name || `id-card-${Date.now()}.jpg`, { type: 'image/jpeg' }));
          },
          'image/jpeg',
          plan.quality
        );
      } catch (error) {
        resolve(file);
      }
    };
    img.onerror = () => resolve(file);
    reader.readAsDataURL(file);
  });

const openPicker = (side) => {
  pendingSide.value = side;
  pickerVisible.value = true;
};

const closePicker = () => {
  pickerVisible.value = false;
  pendingSide.value = '';
};

const chooseSource = (source) => {
  const inputMap = {
    front: {
      camera: frontCameraInput.value,
      album: frontAlbumInput.value
    },
    back: {}
  };

  inputMap[pendingSide.value]?.[source]?.click();
  closePicker();
};

const handleFileChange = async (event, side) => {
  const file = event.target.files?.[0];
  if (file) {
    const finalFile = await compressImageIfNeeded(file);
    setFile(side, finalFile);
  }

  event.target.value = '';
};

const onSubmit = async () => {
  loading.value = true;
  try {
    const formData = new FormData();
    if (frontFile.value) {
      formData.append('front_image', frontFile.value);
    }
    if (backFile.value) {
      formData.append('back_image', backFile.value);
    }

    showToast({ type: 'loading', message: 'Reading your ID...', duration: 1500 });
    const res = await submitOCR(formData);
    if (res.access_token) {
      localStorage.setItem('token', res.access_token);
      if (res.refresh_token) {
        localStorage.setItem('refresh_token', res.refresh_token);
      }
    }

    extractedInfo.value = {
      name: res.name,
      idNum: res.id_card_num,
      address: res.id_address,
      expiry: res.id_expiry
    };
    if (res.phone_reclaimed) {
      showToast('Your verified mobile ownership has been updated');
    }
    showConfirm.value = true;
  } catch (error) {
    // handled by interceptor
  } finally {
    loading.value = false;
  }
};

const onConfirmInfo = () => {
  router.push('/face');
};

const toggleAgreed = () => {
  agreed.value = !agreed.value;
};

const goPersonalAgreement = () => {
  router.push('/personal-info-authorization');
};

onBeforeUnmount(() => {
  revokePreview(frontPreview.value);
  revokePreview(backPreview.value);
});
</script>

<style scoped>
.ocr-page {
  padding-bottom: calc(150px + var(--app-tabbar-space));
}

.ocr-page::before {
  height: 200px;
}

.ocr-inner {
  padding-top: calc(env(safe-area-inset-top, 0px) + 8px);
}

.ocr-hero {
  margin: 8px 0 16px;
}

.ocr-title {
  margin: 0;
  font-size: 20px;
  line-height: 1.35;
  font-weight: 800;
  color: var(--app-text);
}

.ocr-title-highlight {
  color: var(--app-primary-deep);
}

.ocr-subtitle {
  margin: 8px 0 0;
  max-width: 360px;
  font-size: 13px;
  line-height: 1.62;
  color: var(--app-text-soft);
}

.capture-stack {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.capture-card {
  padding: 14px;
}

.capture-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
  margin-bottom: 10px;
}

.capture-title {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
  color: var(--app-text);
}

.capture-desc {
  margin: 4px 0 0;
  font-size: 11px;
  line-height: 1.5;
  color: var(--app-text-soft);
}

.capture-status {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 28px;
  padding: 0 12px;
  flex-shrink: 0;
  border-radius: 999px;
  background: rgba(154, 168, 188, 0.12);
  color: var(--app-text-faint);
  font-size: 12px;
  font-weight: 700;
}

.capture-status-done {
  background: rgba(48, 215, 169, 0.14);
  color: #0daa79;
}

.viewfinder {
  position: relative;
  aspect-ratio: 2.18 / 1;
  border-radius: 16px;
  background: linear-gradient(180deg, #ffffff 0%, #f9fbff 100%);
  border: 1px solid #e7edf6;
  box-shadow: 0 10px 22px rgba(31, 47, 71, 0.06);
  overflow: hidden;
}

.finder-corner {
  position: absolute;
  width: 15px;
  height: 15px;
  border: 2px solid rgba(47, 126, 247, 0.9);
  z-index: 3;
}

.top-left {
  top: 12px;
  left: 12px;
  border-right: none;
  border-bottom: none;
}

.top-right {
  top: 12px;
  right: 12px;
  border-left: none;
  border-bottom: none;
}

.bottom-left {
  bottom: 12px;
  left: 12px;
  border-right: none;
  border-top: none;
}

.bottom-right {
  bottom: 12px;
  right: 12px;
  border-left: none;
  border-top: none;
}

.selected-preview {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.placeholder-id {
  position: absolute;
  inset: 50% auto auto 50%;
  width: 72%;
  height: 62%;
  transform: translate(-50%, -50%);
  border-radius: 10px;
  opacity: 0.3;
  background: linear-gradient(145deg, #eff4ff 0%, #dde7fb 100%);
  overflow: hidden;
}

.placeholder-id-front {
  padding: 13px 12px;
}

.front-copy {
  width: 58%;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.front-copy span,
.back-title span,
.back-copy span,
.guide-lines span {
  display: block;
  border-radius: 999px;
  background: rgba(120, 147, 198, 0.56);
}

.front-copy span {
  height: 5px;
}

.front-copy span:nth-child(1) {
  width: 56%;
}

.front-copy span:nth-child(2) {
  width: 84%;
}

.front-copy span:nth-child(3) {
  width: 72%;
}

.front-copy span:nth-child(4) {
  width: 94%;
}

.portrait-box {
  position: absolute;
  right: 14px;
  top: 14px;
  width: 44px;
  height: 56px;
  border-radius: 10px;
  background: linear-gradient(180deg, #f4f7ff 0%, #dbe7ff 100%);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 3px;
}

.portrait-head {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #7e9fd7;
}

.portrait-body {
  width: 24px;
  height: 14px;
  border-radius: 12px 12px 8px 8px;
  background: #5b80c4;
}

.front-bar {
  position: absolute;
  left: 12px;
  right: 16px;
  bottom: 14px;
  height: 7px;
  border-radius: 999px;
  background: rgba(120, 147, 198, 0.48);
}

.placeholder-id-back {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.back-emblem {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: radial-gradient(circle, #d5e2fb 0%, #87a6de 100%);
}

.back-title {
  width: 60%;
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.back-title span,
.back-copy span {
  height: 5px;
}

.back-title span:nth-child(1) {
  width: 100%;
}

.back-title span:nth-child(2) {
  width: 82%;
}

.back-copy {
  width: 46%;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.back-copy span:nth-child(1) {
  width: 100%;
}

.back-copy span:nth-child(2) {
  width: 76%;
}

.lens-button {
  position: absolute;
  left: 50%;
  top: 50%;
  width: 48px;
  height: 48px;
  transform: translate(-50%, -50%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--app-primary-deep);
  color: #ffffff;
  box-shadow: 0 12px 24px rgba(44, 95, 183, 0.24);
  z-index: 4;
  font-size: 22px;
}

.lens-button-float {
  top: auto;
  left: auto;
  right: 12px;
  bottom: 12px;
  width: 38px;
  height: 38px;
  transform: none;
  font-size: 18px;
}

.guide-section {
  margin-top: 18px;
}

.guide-title {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: var(--app-text);
}

.guide-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
  margin-top: 12px;
}

.guide-item {
  text-align: center;
}

.guide-shot {
  height: 52px;
  padding: 6px;
  border-radius: 8px;
  background: #f6f9fe;
  border: 1px solid #edf2fa;
  overflow: hidden;
}

.guide-card {
  height: 100%;
  padding: 6px;
  border-radius: 6px;
  background: linear-gradient(145deg, #f4f8ff 0%, #edf4ff 100%);
}

.guide-headline {
  width: 54%;
  height: 4px;
  border-radius: 999px;
  background: rgba(154, 177, 214, 0.3);
}

.guide-body {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 7px;
}

.guide-avatar {
  width: 13px;
  height: 13px;
  border-radius: 50%;
  background: #9abcf3;
  flex-shrink: 0;
}

.guide-lines {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.guide-lines span {
  height: 3px;
}

.guide-lines span:nth-child(1) {
  width: 72%;
}

.guide-lines span:nth-child(2) {
  width: 90%;
}

.guide-lines span:nth-child(3) {
  width: 60%;
}

.guide-shot-cut .guide-card {
  transform: scale(1.12) translateX(8%);
}

.guide-shot-blur .guide-card {
  filter: blur(1.8px);
}

.guide-shot-flash {
  background: radial-gradient(circle at center, rgba(255, 255, 255, 0.96) 0%, rgba(246, 249, 255, 1) 76%);
}

.guide-shot-flash .guide-card {
  opacity: 0.5;
}

.guide-label {
  margin: 6px 0 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 2px;
  font-size: 10px;
  font-weight: 600;
}

.guide-label-ok {
  color: #0daa79;
}

.guide-label-bad {
  color: var(--app-danger);
}

.ocr-footer {
  position: fixed;
  left: 50%;
  bottom: var(--app-tabbar-space);
  z-index: 10;
  width: min(430px, 100%);
  transform: translateX(-50%);
  padding: 10px 16px calc(12px + env(safe-area-inset-bottom, 0px));
  background: linear-gradient(180deg, rgba(247, 251, 255, 0) 0%, rgba(250, 252, 255, 0.9) 20%, rgba(255, 255, 255, 0.98) 42%);
  backdrop-filter: blur(14px);
}

.agreement-box {
  margin-bottom: 10px;
}

:deep(.van-checkbox) {
  align-items: flex-start;
}

:deep(.van-checkbox__label) {
  font-size: 11px;
  line-height: 1.5;
  color: var(--app-text-faint);
}

.agreement-link {
  color: var(--app-primary-deep);
  cursor: pointer;
}

.agreement-toggle {
  cursor: pointer;
}

.submit-btn.van-button--disabled {
  background: #c8d0de !important;
  box-shadow: none;
  opacity: 1;
}

.submit-btn {
  height: 46px !important;
  font-size: 15px !important;
}

.hidden-input {
  display: none;
}

:deep(.ocr-confirm-dialog) {
  width: min(92vw, 392px);
}

:deep(.ocr-confirm-dialog .van-dialog__header) {
  font-size: 24px;
  font-weight: 700;
  color: var(--app-text);
}

:deep(.ocr-confirm-dialog .van-cell__title) {
  flex: 0 0 72px;
}

:deep(.ocr-confirm-dialog .van-cell__value) {
  display: flex;
  justify-content: flex-end;
}

.ocr-single-line-value {
  display: inline-block;
  max-width: 100%;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.picker-mask {
  position: fixed;
  inset: 0;
  z-index: 120;
  background: rgba(15, 23, 42, 0.36);
}

.picker-sheet {
  position: fixed;
  left: 50%;
  bottom: calc(var(--app-tabbar-space) + 10px);
  z-index: 121;
  width: min(398px, calc(100% - 16px));
  transform: translateX(-50%);
}

.picker-option,
.picker-cancel {
  width: 100%;
  min-height: 54px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.98);
  box-shadow: 0 16px 34px rgba(15, 23, 42, 0.12);
  font-size: 16px;
  font-weight: 600;
}

.picker-option + .picker-option {
  margin-top: 10px;
}

.picker-cancel {
  margin-top: 12px;
  color: var(--app-text-soft);
}

.sheet-fade-enter-active,
.sheet-fade-leave-active {
  transition: opacity 0.2s ease;
}

.sheet-fade-enter-from,
.sheet-fade-leave-to {
  opacity: 0;
}

.sheet-up-enter-active,
.sheet-up-leave-active {
  transition: transform 0.24s ease, opacity 0.24s ease;
}

.sheet-up-enter-from,
.sheet-up-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(16px);
}

.ocr-page { padding-bottom: calc(150px + var(--app-tabbar-space)); background: var(--app-bg-soft); }
.ocr-page::before { display: none; }
.ocr-inner { padding-top: 22px; }
.document-heading { display: flex; flex-direction: column; gap: 12px; margin-bottom: 14px; color: var(--app-text); }
.document-heading span { font-size: 20px; line-height: 1.2; }
.document-heading strong { padding: 18px 16px; border-radius: 8px; background: #f5f8fd; font-size: 20px; line-height: 1.2; }
.capture-panel { padding: 8px; border-radius: 8px; background: #f2f4f8; }
.viewfinder { aspect-ratio: 1.58 / 1; border: 0; border-radius: 6px; background: #f2f4f8; box-shadow: none; }
.finder-corner { width: 22px; height: 22px; border-width: 4px; border-color: #bfc8d8; border-radius: 3px; }
.top-left, .top-right { top: 4px; }
.bottom-left, .bottom-right { bottom: 4px; }
.top-left, .bottom-left { left: 4px; }
.top-right, .bottom-right { right: 4px; }
.ghana-card-placeholder { position: absolute; inset: 17% 9%; padding: 9px; border-radius: 7px; background: linear-gradient(135deg, #e5f4f8 0%, #f2f8ef 54%, #e9f2fb 100%); box-shadow: 0 5px 12px rgba(34, 63, 95, 0.08); color: #52677f; }
.ghana-card-topline { display: flex; align-items: center; gap: 7px; font-size: 7px; text-align: center; }
.ghana-card-topline div { flex: 1; }
.ghana-card-topline b, .ghana-card-topline small { display: block; line-height: 1.25; }
.ghana-seal { display: grid; width: 24px; height: 24px; place-items: center; border: 2px solid #d1a141; border-radius: 50%; color: #317360; font-size: 8px; font-weight: 800; }
.ghana-flag { display: flex; width: 30px; flex-direction: column; }
.ghana-flag i { height: 6px; background: #d94a48; }
.ghana-flag i:nth-child(2) { background: #e5c34d; }
.ghana-flag i:nth-child(3) { background: #3b9868; }
.ghana-card-body { display: grid; grid-template-columns: 42px 1fr 54px; align-items: center; gap: 8px; margin-top: 12px; }
.ghana-chip { height: 34px; border-radius: 6px; background: linear-gradient(135deg, #e7c675, #b88f3e); }
.ghana-lines { display: flex; flex-direction: column; gap: 7px; }
.ghana-lines i { width: 90%; height: 4px; border-radius: 4px; background: rgba(88, 115, 143, 0.28); }
.ghana-lines i:nth-child(2) { width: 68%; }
.ghana-lines i:nth-child(4) { width: 78%; }
.ghana-portrait { height: 66px; border-radius: 6px; background: rgba(204, 218, 228, 0.9); overflow: hidden; }
.ghana-portrait span { display: block; width: 42px; height: 58px; margin: 12px auto 0; border-radius: 50% 50% 35% 35%; background: #9fb1c4; }
.upload-button { position: absolute; left: 50%; top: 50%; z-index: 4; display: flex; width: 74px; height: 74px; transform: translate(-50%, -50%); align-items: center; justify-content: center; flex-direction: column; gap: 3px; border-radius: 50%; background: var(--app-primary-deep); color: #ffffff; box-shadow: 0 10px 22px rgba(47, 126, 247, 0.25); font-size: 21px; }
.upload-button span { font-size: 12px; font-weight: 700; }
.upload-button-float { left: auto; top: auto; right: 12px; bottom: 12px; width: 58px; height: 58px; transform: none; }
.note-section { margin-top: 18px; }
.note-section strong { font-size: 16px; color: var(--app-text); }
.note-section p { margin: 5px 0 0; font-size: 14px; line-height: 1.5; color: var(--app-text-faint); }
.reject-section { margin-top: 18px; }
.reject-section h2 { display: flex; align-items: center; gap: 7px; margin: 0 0 12px; font-size: 16px; color: var(--app-text); }
.reject-section h2 .van-icon { display: grid; width: 22px; height: 22px; place-items: center; border: 2px solid var(--app-danger); border-radius: 50%; color: var(--app-danger); font-size: 13px; }
.reject-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; }
.reject-item { min-width: 0; text-align: center; }
.reject-shot { position: relative; height: 72px; border: 1px solid #e4e9f1; border-radius: 7px; background: #eef3f8; overflow: hidden; }
.reject-item p { margin: 7px 0 0; font-size: 10px; line-height: 1.3; color: var(--app-text-faint); }
.selfie-figure { position: absolute; inset: 12px 25px 0; border-radius: 50% 50% 0 0; background: #8eb4d6; }
.selfie-figure span { position: absolute; left: 50%; top: -3px; width: 28px; height: 28px; transform: translateX(-50%); border-radius: 50%; background: #506f91; }
.blur-card { position: absolute; inset: 12px 8px; padding: 8px; border-radius: 5px; background: #e8f1ed; filter: blur(1.7px); text-align: left; }
.blur-card b { font-size: 7px; }
.blur-card i { display: block; width: 70%; height: 3px; margin-top: 6px; background: #91a5b5; }
.scenery { position: absolute; inset: 0; background: linear-gradient(#b9dcf2 0 48%, #d5c178 49% 100%); }
.scenery::before, .scenery::after { position: absolute; bottom: 27px; content: ''; border-style: solid; border-width: 0 30px 24px; border-color: transparent transparent #819e88; }
.scenery::before { left: -8px; }
.scenery::after { right: -12px; border-bottom-color: #76917c; }
</style>
