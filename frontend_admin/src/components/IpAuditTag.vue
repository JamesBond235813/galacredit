<template>
  <button type="button" class="ip-audit-tag" @click="$emit('click')">ip</button>
</template>

<script setup>
defineEmits(['click']);
</script>

<style scoped>
.ip-audit-tag {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 38px;
  height: 24px;
  padding: 0 10px;
  border: 1px solid #ffd6d9;
  border-radius: 4px;
  background: #fff1f2;
  color: #f56c6c;
  font-size: 12px;
  line-height: 1;
  cursor: pointer;
}

.ip-audit-tag:hover {
  border-color: #ffb8bf;
  background: #ffe8eb;
}
</style>
