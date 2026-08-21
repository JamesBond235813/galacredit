<template>
  <div class="admin-page">
    <el-card class="panel-card filter-card">
      <el-form :inline="true" :model="filters">
        <el-form-item :label="tr('阶段', 'Stage')"><el-select v-model="filters.stage" style="width: 160px"><el-option :label="tr('全部', 'All')" value="" /><el-option label="APPLICATION" value="APPLICATION" /><el-option label="ORDER" value="ORDER" /><el-option label="REVIEW" value="REVIEW" /><el-option label="DISBURSEMENT" value="DISBURSEMENT" /></el-select></el-form-item>
        <el-form-item :label="tr('结果', 'Decision')"><el-select v-model="filters.decision" style="width: 150px"><el-option :label="tr('全部', 'All')" value="" /><el-option label="APPROVE" value="APPROVE" /><el-option label="REFER" value="REFER" /><el-option label="DECLINE" value="DECLINE" /><el-option label="BLOCK" value="BLOCK" /></el-select></el-form-item>
        <el-form-item><el-button type="primary" @click="fetchData">{{ tr('查询', 'Search') }}</el-button><el-button @click="resetFilters">{{ tr('重置', 'Reset') }}</el-button></el-form-item>
      </el-form>
    </el-card>
    <el-card class="panel-card">
      <template #header><div class="section-head"><div><h2>{{ tr('风控决策记录', 'Risk decisions') }}</h2><p>{{ tr('当前为 shadow mode，仅记录规则命中，不改变现有审批和放款结果。', 'Shadow mode records rule hits without changing current approval or disbursement results.') }}</p></div><el-tag type="warning">SHADOW</el-tag></div></template>
      <el-table v-loading="loading" :data="items" stripe>
        <el-table-column prop="created_at" :label="tr('时间', 'Time')" min-width="170" />
        <el-table-column prop="decision_id" :label="tr('决策ID', 'Decision ID')" min-width="190" />
        <el-table-column prop="stage" :label="tr('阶段', 'Stage')" width="130" />
        <el-table-column :label="tr('结果', 'Decision')" width="120"><template #default="{ row }"><el-tag :type="decisionType(row.decision)">{{ row.decision }}</el-tag></template></el-table-column>
        <el-table-column prop="score" :label="tr('风险分', 'Risk score')" width="100" />
        <el-table-column :label="tr('命中规则', 'Rule hits')" min-width="260"><template #default="{ row }"><el-tag v-for="item in row.rule_hits || []" :key="item.rule_code" size="small" class="rule-tag">{{ item.rule_code }}</el-tag><span v-if="!row.rule_hits?.length">--</span></template></el-table-column>
        <el-table-column prop="policy_version" :label="tr('策略版本', 'Policy version')" width="120" />
      </el-table>
      <div class="pagination-wrap"><el-pagination background layout="total, prev, pager, next" :total="total" :page-size="filters.limit" :current-page="filters.page" @current-change="handlePageChange" /></div>
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue';
import { getRiskDecisions } from '../api';
import { tr } from '../i18n/adminLocale';

const loading = ref(false);
const items = ref([]);
const total = ref(0);
const filters = reactive({ stage: '', decision: '', page: 1, limit: 20 });
const decisionType = (value) => ({ APPROVE: 'success', REFER: 'warning', DECLINE: 'danger', BLOCK: 'danger' }[value] || 'info');
const fetchData = async () => { loading.value = true; try { const result = await getRiskDecisions({ stage: filters.stage || undefined, decision: filters.decision || undefined, skip: (filters.page - 1) * filters.limit, limit: filters.limit }); items.value = result.items || []; total.value = Number(result.total || 0); } finally { loading.value = false; } };
const resetFilters = () => { filters.stage = ''; filters.decision = ''; filters.page = 1; fetchData(); };
const handlePageChange = (page) => { filters.page = page; fetchData(); };
onMounted(fetchData);
</script>

<style scoped>
.rule-tag { margin: 2px 4px 2px 0; }
</style>
