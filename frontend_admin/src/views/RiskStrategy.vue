<template>
  <div class="admin-page">
    <el-card class="panel-card">
      <template #header>
        <div class="section-head">
          <div>
            <h2>风控策略预留</h2>
            <p>当前先保留入口与展示区，等待外部三方数据、评分模型和自动决策规则接入后再启用配置。</p>
          </div>
        </div>
      </template>

      <el-empty description="策略中心预留中" />
      <div class="reserve-grid">
        <article class="reserve-card" v-for="item in items" :key="item.title">
          <strong>{{ item.title }}</strong>
          <p>{{ item.desc }}</p>
        </article>
      </div>
    </el-card>
  </div>
</template>

<script setup>
const items = [
  { title: '规则版本', desc: '后续支持策略版本、灰度范围和回放记录。' },
  { title: '外部数据', desc: '接入后再展示设备、IP、通讯录、多头和历史命中信息。' },
  { title: '自动决策', desc: '支持自动通过、自动拒绝和转人工复核。' }
];
</script>
