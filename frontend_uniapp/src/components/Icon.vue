<script setup>
import { computed } from 'vue'
import { ICON_PATHS } from './iconPaths.js'

const props = defineProps({
  name: { type: String, required: true },
  size: { type: [String, Number], default: 24 },
  label: { type: String, default: '' },
  useVant: { type: Boolean, default: true }
})

const paths = computed(() => ICON_PATHS[props.name] || [])
const VANT_NAMES = Object.freeze({
  home: 'wap-home-o',
  'balance-list': 'balance-list-o',
  applications: 'orders-o',
  records: 'records',
  idcard: 'idcard',
  account: 'user-o',
  'user-circle': 'user-circle-o',
  'shield-check': 'shield-o',
  plus: 'plus',
  help: 'question-o',
  support: 'service-o',
  balance: 'balance-pay',
  document: 'orders-o',
  info: 'info-o',
  refresh: 'replay',
  message: 'comment-o',
  volume: 'volume-o',
  camera: 'photograph',
  'chevron-left': 'arrow-left',
  'chevron-right': 'arrow',
  warning: 'warning-o',
  close: 'close',
  passed: 'passed',
  underway: 'underway'
})
const vantName = computed(() => props.useVant ? (VANT_NAMES[props.name] || '') : '')
</script>

<template>
  <i
    v-if="vantName"
    class="gc-vant-icon"
    :class="`gc-vant-icon--${vantName}`"
    :style="{ fontSize: `${size}px` }"
    aria-hidden="true"
  />
  <svg
    v-else
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
