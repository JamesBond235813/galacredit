<script setup>
defineProps({
  loading: Boolean,
  empty: Boolean,
  emptyText: { type: String, default: 'Nothing to show yet.' },
  error: { type: String, default: '' },
  retryable: { type: Boolean, default: true }
})
const emit = defineEmits(['retry'])
</script>

<template>
  <view v-if="loading" class="gc-async-state"><view class="gc-spinner" /><text>Loading securely…</text></view>
  <view v-else-if="error" class="gc-async-state gc-async-state--error"><text>{{ error }}</text><button v-if="retryable" class="gc-retry" @click="emit('retry')">Try again</button></view>
  <view v-else-if="empty" class="gc-async-state"><text>{{ emptyText }}</text></view>
  <slot v-else />
</template>

<style scoped>
.gc-async-state { display:flex; flex-direction:column; align-items:center; justify-content:center; min-height:220rpx; padding:24rpx; text-align:center; color:var(--gc-muted); font-size:24rpx; }
.gc-async-state--error { color:var(--gc-danger); }
.gc-retry { min-height:68rpx; margin-top:20rpx; padding:0 28rpx; border:1rpx solid #f0c27a; border-radius:18rpx; color:var(--gc-brand-deep); background:#fff4e4; font-size:23rpx; font-weight:700; }
.gc-retry::after { border:0; }
.gc-spinner { width:42rpx; height:42rpx; margin-bottom:18rpx; border:5rpx solid #f6d9ae; border-top-color:var(--gc-brand); border-radius:50%; animation:gc-spin 800ms linear infinite; }
@keyframes gc-spin { to { transform:rotate(360deg); } }
</style>
