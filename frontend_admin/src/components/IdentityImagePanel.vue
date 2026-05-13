<template>
  <aside class="identity-image-panel">
    <article v-for="item in images" :key="item.label" class="identity-photo-card">
      <div class="identity-photo-title">{{ item.label }}</div>
      <el-image
        v-if="item.url"
        class="identity-photo"
        :src="resolveUrl(item.url)"
        :preview-src-list="previewList"
        fit="cover"
        preview-teleported
      />
      <div v-else class="identity-photo-empty">暂无照片</div>
    </article>
  </aside>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  row: { type: Object, default: () => ({}) }
});

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || '';
const origin = apiBaseUrl.replace(/\/api\/?$/, '');

const resolveUrl = (url) => {
  if (!url) return '';
  if (/^https?:\/\//.test(url)) return url;
  return `${origin}${url}`;
};

const images = computed(() => [
  { label: '身份证正面', url: props.row.id_card_front_image_url },
  { label: '身份证反面', url: props.row.id_card_back_image_url },
  { label: '人脸照片', url: props.row.face_image_url }
]);

const previewList = computed(() => images.value.map((item) => resolveUrl(item.url)).filter(Boolean));
</script>

<style scoped>
.identity-image-panel {
  width: 320px;
  flex: 0 0 320px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.identity-photo-card {
  padding: 10px;
  border: 1px solid #e7edf6;
  border-radius: 8px;
  background: #fff;
}

.identity-photo-title {
  margin-bottom: 8px;
  color: #40546f;
  font-size: 13px;
  font-weight: 600;
}

.identity-photo,
.identity-photo-empty {
  width: 100%;
  height: 190px;
  border-radius: 6px;
  background: #f3f6fb;
}

.identity-photo-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #9aa8bc;
  font-size: 13px;
}
</style>
