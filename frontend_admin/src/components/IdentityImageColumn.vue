<template>
  <div class="identity-image-column">
    <el-image
      v-for="item in images"
      :key="item.label"
      class="identity-image"
      :src="resolveUrl(item.url)"
      :preview-src-list="previewList"
      fit="cover"
      preview-teleported
    >
      <template #error>
        <div class="image-empty">{{ item.label }}</div>
      </template>
    </el-image>
  </div>
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
.identity-image-column {
  display: flex;
  flex-direction: column;
  gap: 6px;
  width: 96px;
}

.identity-image {
  width: 96px;
  height: 60px;
  border-radius: 6px;
  background: #f3f6fb;
}

.image-empty {
  width: 96px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #9aa8bc;
  font-size: 12px;
}
</style>
