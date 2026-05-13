<template>
  <el-dialog v-model="visible" width="680px" title="IP审查" destroy-on-close>
    <el-table v-loading="loading" :data="items" stripe>
      <el-table-column prop="ip" label="IP地址" width="150" />
      <el-table-column label="行政区划" min-width="180">
        <template #default="{ row }">
          {{ [row.country, row.province, row.city, row.district].filter(Boolean).join(' / ') || '--' }}
        </template>
      </el-table-column>
      <el-table-column prop="operation" label="用户操作" min-width="150" />
      <el-table-column label="最近时间" width="170">
        <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
      </el-table-column>
    </el-table>
  </el-dialog>
</template>

<script setup>
import { computed } from 'vue';
import { formatDateTime } from '../utils/format';

const props = defineProps({
  modelValue: Boolean,
  loading: Boolean,
  items: { type: Array, default: () => [] }
});
const emit = defineEmits(['update:modelValue']);
const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
});
</script>
