<template>
  <el-config-provider :locale="elementLocale">
    <router-view />
  </el-config-provider>
</template>

<script setup>
import { computed } from 'vue';
import en from 'element-plus/dist/locale/en.mjs';
import zhCn from 'element-plus/dist/locale/zh-cn.mjs';
import { adminLocale } from './i18n/adminLocale';

const elementLocale = computed(() => adminLocale.value === 'en-GH' ? en : zhCn);
</script>
