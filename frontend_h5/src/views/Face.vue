<template>
  <div class="page-shell face-page">
    <van-nav-bar left-arrow title="人脸识别" @click-left="router.back()" />

    <div class="page-inner face-inner">
      <header class="face-hero">
        <span class="hero-chip">流程 2 / 4</span>
        <h1 class="hero-title">请完成人脸活体核验</h1>
        <p class="hero-desc">为保障申请真实性，系统将校验是否为本人操作，预计 10 秒内完成。</p>
      </header>

      <div class="tip-row">
        <span v-for="item in tips" :key="item" class="tip-pill">{{ item }}</span>
      </div>

      <section class="page-card scan-card">
        <div class="card-head">
          <div>
            <h2 class="card-title">活体检测</h2>
            <p class="card-desc">请将面部保持在取景框中央</p>
          </div>
          <span class="capture-status" :class="{ 'capture-status-done': success }">
            {{ success ? '已完成' : scanning ? '识别中' : '待识别' }}
          </span>
        </div>

        <div class="scan-panel">
          <div class="scan-grid">
            <span></span>
            <span></span>
            <span></span>
            <span></span>
          </div>

          <div class="scan-ring" :class="{ 'scan-ring-scanning': scanning, 'scan-ring-success': success }">
            <div class="scan-core">
              <van-icon :name="success ? 'passed' : 'user-circle-o'" />
            </div>
            <div v-if="scanning" class="scan-line"></div>
          </div>
        </div>

        <div class="status-block">
          <h3 class="status-title">
            <template v-if="!scanning && !success">请正对镜头并保持稳定</template>
            <template v-else-if="scanning">正在进行活体检测...</template>
            <template v-else>识别成功，继续补充资料</template>
          </h3>
          <p class="status-desc">
            <template v-if="!success">请避免逆光、遮挡和频繁晃动。</template>
            <template v-else>下一步需要填写两位紧急联系人信息。</template>
          </p>
          <p v-if="faceImageName" class="selected-face-tip">已选择照片：{{ faceImageName }}</p>
        </div>

        <van-button
          block
          type="primary"
          class="primary-action face-btn"
          :loading="scanning || redirecting"
          @click="startScan"
        >
          {{ success ? '正在跳转...' : '开始识别' }}
        </van-button>
      </section>

      <p class="safe-note">
        <van-icon name="shield-o" />
        认证影像仅用于实名核验与风控审核
      </p>
    </div>

    <input
      ref="faceFrontCameraInput"
      type="file"
      accept="image/*"
      capture="user"
      class="hidden-input"
      @change="handleFaceImageChange"
    />
    <input
      ref="faceBackCameraInput"
      type="file"
      accept="image/*"
      capture="environment"
      class="hidden-input"
      @change="handleFaceImageChange"
    />
    <input
      ref="faceAlbumInput"
      type="file"
      accept="image/*"
      class="hidden-input"
      @change="handleFaceImageChange"
    />
    <canvas ref="canvasRef" class="hidden-input"></canvas>

    <teleport to="body">
      <transition name="sheet-fade">
        <div v-if="cameraModalVisible" class="camera-mask" @click="closeLiveCamera"></div>
      </transition>
      <transition name="sheet-up">
        <div v-if="cameraModalVisible" class="camera-sheet">
          <div class="camera-sheet-head">
            <span>{{ activeFacingMode === 'user' ? '前置相机' : '后置相机' }}</span>
            <button type="button" class="camera-close" @click="closeLiveCamera">关闭</button>
          </div>
          <video ref="videoRef" class="camera-preview" autoplay playsinline muted></video>
          <div class="camera-actions">
            <button type="button" class="camera-switch" @click="openLiveCamera(activeFacingMode === 'user' ? 'environment' : 'user')">
              切换摄像头
            </button>
            <button type="button" class="camera-capture" @click="captureFromVideo">拍照并识别</button>
          </div>
        </div>
      </transition>

      <transition name="sheet-fade">
        <div v-if="pickerVisible" class="picker-mask" @click="closePicker"></div>
      </transition>
      <transition name="sheet-up">
        <div v-if="pickerVisible" class="picker-sheet">
          <button type="button" class="picker-option" @click="chooseSource('front-camera')">前置拍照</button>
          <button type="button" class="picker-option" @click="chooseSource('back-camera')">后置拍照</button>
          <button type="button" class="picker-option" @click="chooseSource('album')">从相册选择</button>
          <button type="button" class="picker-cancel" @click="closePicker">取消</button>
        </div>
      </transition>
    </teleport>
  </div>
</template>

<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { showToast } from 'vant';
import { getUserInfo, submitFaceAuth } from '../api';

const router = useRouter();
const scanning = ref(false);
const success = ref(false);
const redirecting = ref(false);
const faceFrontCameraInput = ref(null);
const faceBackCameraInput = ref(null);
const faceAlbumInput = ref(null);
const faceImage = ref(null);
const faceImageName = ref('');
const pickerVisible = ref(false);
const cameraModalVisible = ref(false);
const activeFacingMode = ref('user');
const videoRef = ref(null);
const canvasRef = ref(null);
let mediaStream = null;
let redirectTimer = null;

const tips = ['正对镜头', '环境明亮', '无明显遮挡'];

const continueIfAlreadyPassed = async (silent = false) => {
  try {
    const user = await getUserInfo();
    if (user?.face_auth_status === 'PASSED') {
      success.value = true;
      redirecting.value = true;
      if (!silent) {
        showToast('检测到已完成人脸核验，继续下一步');
      }
      redirectTimer = window.setTimeout(() => {
        nextStep();
      }, 260);
      return true;
    }
  } catch (error) {
    // ignore
  }
  return false;
};

const doFaceAuth = async () => {
  if (scanning.value || redirecting.value || !faceImage.value) {
    return;
  }

  scanning.value = true;
  try {
    const formData = new FormData();
    formData.append('face_image', faceImage.value);
    const res = await submitFaceAuth(formData);
    success.value = true;
    const scoreText = res?.score === null || res?.score === undefined ? '' : `（分值 ${res.score}）`;
    showToast(`人脸核验通过${scoreText}`);
    redirecting.value = true;
    redirectTimer = window.setTimeout(() => {
      nextStep();
    }, 500);
  } catch (error) {
    const detail = error?.response?.data?.detail || '';
    if (
      typeof detail === 'string' &&
      ['人脸识别信息与身份证信息不符', '人脸核验未通过', '信息比对不通过', '姓名与身份证号不匹配', '信息比对失败', '不符'].some((key) =>
        detail.includes(key)
      )
    ) {
      router.push({
        path: '/face-mismatch',
        query: { reason: detail }
      });
      return;
    }
    // 容错：移动端在弱网/超时场景下可能出现“后端已通过但前端未收到成功响应”。
    // 发生异常时主动回查实名状态，若已通过则继续后续流程。
    await continueIfAlreadyPassed(true);
  } finally {
    scanning.value = false;
  }
};

const startScan = () => {
  if (scanning.value || redirecting.value) {
    return;
  }
  if (!faceImage.value) {
    pickerVisible.value = true;
    return;
  }
  doFaceAuth();
};

const closePicker = () => {
  pickerVisible.value = false;
};

const chooseSource = (type) => {
  closePicker();
  if (type === 'album') {
    faceAlbumInput.value?.click();
    return;
  }
  openLiveCamera(type === 'front-camera' ? 'user' : 'environment');
};

const openLiveCamera = async (facingMode) => {
  activeFacingMode.value = facingMode;
  try {
    if (!window.isSecureContext || !navigator.mediaDevices?.getUserMedia) {
      throw new Error('NOT_SUPPORTED');
    }
    stopLiveCamera();
    mediaStream = await navigator.mediaDevices.getUserMedia({
      audio: false,
      video: { facingMode: { ideal: facingMode } }
    });
    cameraModalVisible.value = true;
    await nextTick();
    if (videoRef.value) {
      videoRef.value.srcObject = mediaStream;
      await videoRef.value.play();
    }
  } catch (error) {
    showToast('当前环境不支持实时相机，已切换系统拍照');
    if (facingMode === 'user') {
      faceFrontCameraInput.value?.click();
    } else {
      faceBackCameraInput.value?.click();
    }
  }
};

const stopLiveCamera = () => {
  if (mediaStream) {
    mediaStream.getTracks().forEach((track) => track.stop());
    mediaStream = null;
  }
  if (videoRef.value?.srcObject) {
    videoRef.value.srcObject = null;
  }
};

const closeLiveCamera = () => {
  cameraModalVisible.value = false;
  stopLiveCamera();
};

const setFaceFile = (file) => {
  faceImage.value = file;
  faceImageName.value = file.name || '已拍照';
};

const compressImageIfNeeded = (file) =>
  new Promise((resolve) => {
    const limit = 2.5 * 1024 * 1024;
    if (!file || file.size <= limit || !file.type.startsWith('image/')) {
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
        const maxSide = 1600;
        const scale = Math.min(1, maxSide / Math.max(img.width, img.height));
        const width = Math.round(img.width * scale);
        const height = Math.round(img.height * scale);
        const canvas = document.createElement('canvas');
        canvas.width = width;
        canvas.height = height;
        const ctx = canvas.getContext('2d');
        if (!ctx) {
          resolve(file);
          return;
        }
        ctx.drawImage(img, 0, 0, width, height);
        canvas.toBlob(
          (blob) => {
            if (!blob) {
              resolve(file);
              return;
            }
            const compressed = new File([blob], file.name || `face-${Date.now()}.jpg`, {
              type: 'image/jpeg'
            });
            resolve(compressed);
          },
          'image/jpeg',
          0.82
        );
      } catch (error) {
        resolve(file);
      }
    };
    img.onerror = () => resolve(file);
    reader.readAsDataURL(file);
  });

const captureFromVideo = () => {
  const video = videoRef.value;
  const canvas = canvasRef.value;
  if (!video || !canvas) {
    showToast('相机初始化失败，请重试');
    return;
  }
  const width = video.videoWidth || 720;
  const height = video.videoHeight || 1280;
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext('2d');
  if (!ctx) {
    showToast('拍照失败，请重试');
    return;
  }
  ctx.drawImage(video, 0, 0, width, height);
  canvas.toBlob(
    (blob) => {
      if (!blob) {
        showToast('拍照失败，请重试');
        return;
      }
      const file = new File([blob], `face-${Date.now()}.jpg`, { type: 'image/jpeg' });
      setFaceFile(file);
      closeLiveCamera();
      showToast('已获取照片，开始核验');
      doFaceAuth();
    },
    'image/jpeg',
    0.92
  );
};

const handleFaceImageChange = async (event) => {
  const file = event.target.files?.[0];
  if (!file) {
    showToast('未获取到照片，请重试');
    return;
  }
  const finalFile = await compressImageIfNeeded(file);
  setFaceFile(finalFile);
  event.target.value = '';
  showToast('已获取照片，开始核验');
  doFaceAuth();
};

const nextStep = () => {
  router.push('/application-form');
};

onMounted(() => {
  success.value = false;
  redirecting.value = false;
});

onBeforeUnmount(() => {
  if (redirectTimer) {
    window.clearTimeout(redirectTimer);
  }
  stopLiveCamera();
});
</script>

<style scoped>
.face-page {
  min-height: 100vh;
}

.face-inner {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 12px;
  padding-top: calc(env(safe-area-inset-top, 0px) + 8px);
}

.face-hero {
  width: 100%;
  margin: 6px 0 0;
}

.hero-chip {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 0 12px;
  border-radius: 999px;
  background: rgba(47, 126, 247, 0.1);
  color: var(--app-primary-deep);
  font-size: 12px;
  font-weight: 700;
}

.hero-title {
  margin: 12px 0 0;
  font-size: 24px;
  line-height: 1.28;
  font-weight: 800;
  color: var(--app-text);
}

.hero-desc {
  margin: 8px 0 0;
  font-size: 13px;
  line-height: 1.65;
  color: var(--app-text-soft);
}

.tip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  width: 100%;
}

.tip-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 34px;
  padding: 0 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.68);
  border: 1px solid rgba(47, 126, 247, 0.08);
  color: var(--app-primary-deep);
  font-size: 12px;
  font-weight: 600;
}

.scan-card {
  width: 100%;
  padding: 16px;
}

.card-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.card-title {
  margin: 0;
  font-size: 17px;
  font-weight: 700;
  color: var(--app-text);
}

.card-desc {
  margin: 4px 0 0;
  font-size: 12px;
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

.scan-panel {
  position: relative;
  margin: 14px 0 12px;
  padding: 16px 0;
  border-radius: 22px;
  background:
    radial-gradient(circle at center, rgba(47, 126, 247, 0.08) 0%, rgba(47, 126, 247, 0.02) 52%, transparent 52%),
    linear-gradient(180deg, #fbfdff 0%, #f5f9ff 100%);
}

.scan-grid span {
  position: absolute;
  width: 16px;
  height: 16px;
  border: 2px solid rgba(47, 126, 247, 0.36);
}

.scan-grid span:nth-child(1) {
  top: 16px;
  left: 16px;
  border-right: none;
  border-bottom: none;
}

.scan-grid span:nth-child(2) {
  top: 16px;
  right: 16px;
  border-left: none;
  border-bottom: none;
}

.scan-grid span:nth-child(3) {
  bottom: 16px;
  left: 16px;
  border-right: none;
  border-top: none;
}

.scan-grid span:nth-child(4) {
  bottom: 16px;
  right: 16px;
  border-left: none;
  border-top: none;
}

.scan-ring {
  position: relative;
  width: 188px;
  height: 188px;
  margin: 0 auto;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background:
    radial-gradient(circle at center, rgba(47, 126, 247, 0.08) 0%, rgba(47, 126, 247, 0.03) 58%, transparent 58%),
    linear-gradient(180deg, #ffffff 0%, #f6fbff 100%);
  border: 2px solid rgba(47, 126, 247, 0.16);
  box-shadow: inset 0 0 0 10px rgba(255, 255, 255, 0.85);
  overflow: hidden;
}

.scan-ring-scanning {
  border-color: rgba(47, 126, 247, 0.56);
  box-shadow: 0 0 0 10px rgba(47, 126, 247, 0.06), inset 0 0 0 10px rgba(255, 255, 255, 0.85);
}

.scan-ring-success {
  border-color: rgba(48, 215, 169, 0.65);
  box-shadow: 0 0 0 10px rgba(48, 215, 169, 0.06), inset 0 0 0 10px rgba(255, 255, 255, 0.85);
}

.scan-core {
  width: 148px;
  height: 148px;
  border-radius: 50%;
  background: linear-gradient(180deg, #f8fbff 0%, #edf5ff 100%);
  color: var(--app-primary-deep);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 74px;
}

.scan-ring-success .scan-core {
  color: #0daa79;
}

.scan-line {
  position: absolute;
  left: 16px;
  right: 16px;
  height: 4px;
  border-radius: 999px;
  background: var(--app-gradient);
  box-shadow: 0 0 16px rgba(47, 126, 247, 0.44);
  animation: scanning 2s linear infinite;
}

@keyframes scanning {
  0% {
    top: 22px;
    opacity: 0;
  }

  10% {
    opacity: 1;
  }

  90% {
    opacity: 1;
  }

  100% {
    top: calc(100% - 26px);
    opacity: 0;
  }
}

.status-block {
  text-align: center;
}

.status-title {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  color: var(--app-text);
}

.status-desc {
  margin: 8px 0 0;
  font-size: 13px;
  line-height: 1.6;
  color: var(--app-text-soft);
}

.selected-face-tip {
  margin: 10px 0 0;
  font-size: 12px;
  color: var(--app-primary-deep);
  line-height: 1.4;
}

.face-btn {
  margin-top: 16px;
}

.safe-note {
  width: 100%;
  margin: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  font-size: 12px;
  color: var(--app-text-faint);
}

.hidden-input {
  display: none;
}

.camera-mask {
  position: fixed;
  inset: 0;
  background: rgba(10, 20, 42, 0.52);
  z-index: 90;
}

.camera-sheet {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 91;
  background: #0f1f38;
  border-radius: 18px 18px 0 0;
  padding: 12px 12px calc(env(safe-area-inset-bottom, 0px) + 12px);
  box-shadow: 0 -10px 28px rgba(0, 0, 0, 0.25);
}

.camera-sheet-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: #d8e4ff;
  font-size: 14px;
  margin-bottom: 8px;
}

.camera-close {
  border: 0;
  background: transparent;
  color: #9fb5e8;
  font-size: 13px;
}

.camera-preview {
  width: 100%;
  aspect-ratio: 3 / 4;
  object-fit: cover;
  border-radius: 14px;
  background: #0a1324;
}

.camera-actions {
  display: flex;
  gap: 8px;
  margin-top: 10px;
}

.camera-switch,
.camera-capture {
  border: 0;
  border-radius: 10px;
  height: 42px;
  font-size: 14px;
  font-weight: 600;
}

.camera-switch {
  flex: 1;
  background: rgba(122, 156, 220, 0.24);
  color: #d4e2ff;
}

.camera-capture {
  flex: 2;
  background: var(--app-gradient);
  color: #fff;
}

.picker-mask {
  position: fixed;
  inset: 0;
  background: rgba(16, 30, 56, 0.32);
  z-index: 80;
}

.picker-sheet {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 81;
  padding: 12px 12px calc(env(safe-area-inset-bottom, 0px) + 12px);
  background: rgba(255, 255, 255, 0.96);
  backdrop-filter: blur(18px);
  border-radius: 18px 18px 0 0;
  box-shadow: 0 -10px 28px rgba(16, 42, 88, 0.16);
}

.picker-option,
.picker-cancel {
  width: 100%;
  height: 48px;
  border: 0;
  border-radius: 12px;
  font-size: 15px;
  font-weight: 600;
  margin-top: 8px;
}

.picker-option {
  background: rgba(47, 126, 247, 0.1);
  color: var(--app-primary-deep);
}

.picker-cancel {
  background: rgba(154, 168, 188, 0.18);
  color: var(--app-text-soft);
}

.sheet-fade-enter-active,
.sheet-fade-leave-active {
  transition: opacity 0.22s ease;
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
  transform: translateY(18px);
  opacity: 0;
}
</style>
