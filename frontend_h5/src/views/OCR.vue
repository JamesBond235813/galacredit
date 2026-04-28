<template>
  <div class="page-shell ocr-page">
    <van-nav-bar left-arrow title="实名认证" @click-left="router.back()" />

    <div class="page-inner ocr-inner">
      <header class="ocr-hero">
        <h1 class="ocr-title">
          完成实名认证最高可申请<span class="ocr-title-highlight">8,000额度</span>
        </h1>
        <p class="ocr-subtitle">
          为配合国家监管机构要求，您的身份信息将通过合作机构进行验证
        </p>
      </header>

      <section class="capture-stack">
        <article class="page-card capture-card">
          <div class="capture-head">
            <div>
              <h2 class="capture-title">上传人像面</h2>
              <p class="capture-desc">请拍摄身份证头像面，确保信息清晰完整</p>
            </div>
            <span class="capture-status" :class="{ 'capture-status-done': !!frontFile }">
              {{ frontFile ? '已选择' : '待上传' }}
            </span>
          </div>

          <div class="viewfinder">
            <div class="finder-corner top-left"></div>
            <div class="finder-corner top-right"></div>
            <div class="finder-corner bottom-left"></div>
            <div class="finder-corner bottom-right"></div>

            <img v-if="frontPreview" :src="frontPreview" alt="身份证人像面" class="selected-preview" />

            <div v-else class="placeholder-id placeholder-id-front">
              <div class="front-copy">
                <span></span>
                <span></span>
                <span></span>
                <span></span>
              </div>
              <div class="portrait-box">
                <div class="portrait-head"></div>
                <div class="portrait-body"></div>
              </div>
              <div class="front-bar"></div>
            </div>

            <button
              type="button"
              class="lens-button"
              :class="{ 'lens-button-float': !!frontPreview }"
              @click="openPicker('front')"
            >
              <van-icon name="photograph" />
            </button>
          </div>
        </article>

        <article class="page-card capture-card">
          <div class="capture-head">
            <div>
              <h2 class="capture-title">上传国徽面</h2>
              <p class="capture-desc">请拍摄身份证国徽面，避免反光和缺边</p>
            </div>
            <span class="capture-status" :class="{ 'capture-status-done': !!backFile }">
              {{ backFile ? '已选择' : '待上传' }}
            </span>
          </div>

          <div class="viewfinder">
            <div class="finder-corner top-left"></div>
            <div class="finder-corner top-right"></div>
            <div class="finder-corner bottom-left"></div>
            <div class="finder-corner bottom-right"></div>

            <img v-if="backPreview" :src="backPreview" alt="身份证国徽面" class="selected-preview" />

            <div v-else class="placeholder-id placeholder-id-back">
              <div class="back-emblem"></div>
              <div class="back-title">
                <span></span>
                <span></span>
              </div>
              <div class="back-copy">
                <span></span>
                <span></span>
              </div>
            </div>

            <button
              type="button"
              class="lens-button"
              :class="{ 'lens-button-float': !!backPreview }"
              @click="openPicker('back')"
            >
              <van-icon name="photograph" />
            </button>
          </div>
        </article>
      </section>

      <section class="guide-section">
        <h2 class="guide-title">拍摄须知</h2>
        <div class="guide-grid">
          <div v-for="item in tips" :key="item.label" class="guide-item">
            <div class="guide-shot" :class="`guide-shot-${item.type}`">
              <div class="guide-card">
                <div class="guide-headline"></div>
                <div class="guide-body">
                  <div class="guide-avatar"></div>
                  <div class="guide-lines">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              </div>
            </div>
            <p class="guide-label" :class="{ 'guide-label-ok': item.ok, 'guide-label-bad': !item.ok }">
              <van-icon :name="item.ok ? 'passed' : 'close'" />
              <span>{{ item.label }}</span>
            </p>
          </div>
        </div>
      </section>
    </div>

    <footer class="ocr-footer">
      <div class="agreement-box">
        <van-checkbox v-model="agreed" icon-size="18px" checked-color="#2f7ef7">
          我已阅读并同意<span class="agreement-link">《个人信息授权协议》</span>和
          <span class="agreement-link">《信用消费服务协议》</span>
        </van-checkbox>
      </div>

      <van-button
        block
        type="primary"
        class="primary-action submit-btn"
        :disabled="!frontFile || !backFile || !agreed"
        :loading="loading"
        @click="onSubmit"
      >
        提交实名信息
      </van-button>
    </footer>

    <transition name="sheet-fade">
      <div v-if="pickerVisible" class="picker-mask" @click="closePicker"></div>
    </transition>
    <transition name="sheet-up">
      <div v-if="pickerVisible" class="picker-sheet">
        <button type="button" class="picker-option" @click="chooseSource('camera')">拍照</button>
        <button type="button" class="picker-option" @click="chooseSource('album')">从相册选择</button>
        <button type="button" class="picker-cancel" @click="closePicker">取消</button>
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
    <input
      ref="backCameraInput"
      type="file"
      accept="image/*"
      capture="environment"
      class="hidden-input"
      @change="handleFileChange($event, 'back')"
    />
    <input
      ref="backAlbumInput"
      type="file"
      accept="image/*"
      class="hidden-input"
      @change="handleFileChange($event, 'back')"
    />

    <van-dialog
      v-model:show="showConfirm"
      title="请核对以下信息"
      class-name="ocr-confirm-dialog"
      show-cancel-button
      confirm-button-color="#2f7ef7"
      @confirm="onConfirmInfo"
    >
      <van-cell-group inset>
        <van-cell class="ocr-confirm-cell" title="姓名" :value="extractedInfo.name" />
        <van-cell class="ocr-confirm-cell" title="身份证号">
          <template #value>
            <span class="ocr-single-line-value">{{ extractedInfo.idNum }}</span>
          </template>
        </van-cell>
        <van-cell title="居住地址" :value="extractedInfo.address" />
        <van-cell class="ocr-confirm-cell" title="有效期">
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
const backCameraInput = ref(null);
const backAlbumInput = ref(null);
const pickerVisible = ref(false);
const pendingSide = ref('');

const tips = [
  { label: '标准', type: 'good', ok: true },
  { label: '缺边', type: 'cut', ok: false },
  { label: '模糊', type: 'blur', ok: false },
  { label: '闪光强烈', type: 'flash', ok: false }
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
    back: {
      camera: backCameraInput.value,
      album: backAlbumInput.value
    }
  };

  inputMap[pendingSide.value]?.[source]?.click();
  closePicker();
};

const handleFileChange = (event, side) => {
  const file = event.target.files?.[0];
  if (file) {
    setFile(side, file);
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

    showToast({ type: 'loading', message: '正在智能识别...', duration: 1500 });
    const res = await submitOCR(formData);

    extractedInfo.value = {
      name: res.name,
      idNum: res.id_card_num,
      address: res.id_address,
      expiry: res.id_expiry
    };
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
</style>
