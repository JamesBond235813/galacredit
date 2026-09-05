<script setup>
import { computed } from 'vue'
import { ICON_PATHS } from './iconPaths.js'

const props = defineProps({
  name: { type: String, required: true },
  size: { type: [String, Number], default: 24 },
  label: { type: String, default: '' }
})

const paths = computed(() => ICON_PATHS[props.name] || [])
</script>

<template>
  <svg
    class="gc-icon"
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="1.8"
    stroke-linecap="round"
    stroke-linejoin="round"
    :role="label ? 'img' : undefined"
    :aria-label="label || undefined"
    :aria-hidden="label ? undefined : 'true'"
  >
    <path v-for="path in paths" :key="path" :d="path" />
  </svg>
</template>

<style scoped>
.gc-icon { display:block; flex:none; }
</style>
