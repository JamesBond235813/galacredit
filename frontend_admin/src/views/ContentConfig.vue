<template>
  <div class="admin-page content-config-page">
    <el-card class="panel-card">
      <template #header>
        <div class="section-head">
          <div>
            <h2>运营配置</h2>
            <p>这里先作为运营位预案和内容草稿区，当前保存到本地浏览器，后续接后端配置表时可无痛替换。</p>
          </div>
          <el-button type="primary" @click="saveDraft">保存草稿</el-button>
        </div>
      </template>

      <div class="config-grid">
        <section class="config-section">
          <h3>首页公告</h3>
          <el-input v-model="draft.announcement" type="textarea" :rows="3" placeholder="填写首页公告内容" />
        </section>
        <section class="config-section">
          <h3>Banner 位</h3>
          <el-input v-model="draft.bannerTitle" placeholder="Banner 标题" />
          <el-input v-model="draft.bannerBody" type="textarea" :rows="3" placeholder="Banner 文案" />
        </section>
        <section class="config-section">
          <h3>FAQ</h3>
          <el-input v-model="draft.faqQuestion" placeholder="问题" />
          <el-input v-model="draft.faqAnswer" type="textarea" :rows="3" placeholder="回答" />
        </section>
      </div>

      <div class="preview-grid">
        <article class="preview-card">
          <strong>公告预览</strong>
          <p>{{ draft.announcement || '暂无公告' }}</p>
        </article>
        <article class="preview-card">
          <strong>Banner 预览</strong>
          <p>{{ draft.bannerTitle || '--' }}</p>
          <span>{{ draft.bannerBody || '--' }}</span>
        </article>
        <article class="preview-card">
          <strong>FAQ 预览</strong>
          <p>{{ draft.faqQuestion || '--' }}</p>
          <span>{{ draft.faqAnswer || '--' }}</span>
        </article>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { reactive } from 'vue';
import { ElMessage } from 'element-plus';

const storageKey = 'galacredit_content_config_draft';
const loadDraft = () => {
  try {
    return JSON.parse(localStorage.getItem(storageKey) || '{"announcement":"","bannerTitle":"","bannerBody":"","faqQuestion":"","faqAnswer":""}');
  } catch (error) {
    return { announcement: '', bannerTitle: '', bannerBody: '', faqQuestion: '', faqAnswer: '' };
  }
};
const draft = reactive(loadDraft());

const saveDraft = () => {
  localStorage.setItem(storageKey, JSON.stringify(draft));
  ElMessage.success('草稿已保存到本地');
};
</script>
