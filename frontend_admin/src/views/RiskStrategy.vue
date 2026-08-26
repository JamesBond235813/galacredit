<template>
  <div class="admin-page risk-strategy-page">
    <section class="summary-grid">
      <article v-for="card in summaryCards" :key="card.label" class="summary-card">
        <span>{{ card.label }}</span>
        <strong>{{ card.value }}</strong>
        <p>{{ card.tip }}</p>
      </article>
    </section>

    <el-card class="panel-card">
      <template #header>
        <div class="section-head">
          <div>
            <h2>{{ tr('策略版本管理', 'Policy version management') }}</h2>
            <p>{{ tr('在这里维护风控策略版本、参数配置、启停状态和灰度比例；策略决策记录仍保留在下方。', 'Manage policy versions, parameters, enable/disable state and rollout here; decision records remain below.') }}</p>
          </div>
          <div class="section-actions">
            <el-button @click="fetchPolicies">{{ tr('刷新', 'Refresh') }}</el-button>
            <el-button type="primary" @click="openCreateDrawer">{{ tr('新建版本', 'New version') }}</el-button>
          </div>
        </div>
      </template>

      <el-form :inline="true" :model="policyFilters" class="policy-filter-form">
        <el-form-item :label="tr('策略标识', 'Policy key')">
          <el-input
            v-model="policyFilters.policyKey"
            :placeholder="tr('默认加载当前加纳现金贷基线策略', 'Load the default Ghana baseline policy')"
            clearable
            style="width: 320px"
            @keyup.enter="fetchPolicies"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchPolicies">{{ tr('查询', 'Search') }}</el-button>
          <el-button @click="resetPolicyFilter">{{ tr('重置', 'Reset') }}</el-button>
        </el-form-item>
      </el-form>

      <el-table v-loading="policyLoading" :data="policyRows" stripe>
        <el-table-column prop="policy_key" :label="tr('策略标识', 'Policy key')" min-width="190" />
        <el-table-column prop="version_no" :label="tr('版本号', 'Version')" width="100">
          <template #default="{ row }">v{{ row.version_no }}</template>
        </el-table-column>
        <el-table-column :label="tr('状态', 'Status')" width="120">
          <template #default="{ row }">
            <el-tag :type="policyStatusType(row.status)">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="rollout_percent" :label="tr('灰度', 'Rollout')" width="100">
          <template #default="{ row }">{{ row.rollout_percent }}%</template>
        </el-table-column>
        <el-table-column :label="tr('模式', 'Mode')" width="110">
          <template #default="{ row }">
            <el-tag effect="plain">{{ row.config_json?.mode || '--' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="tr('策略摘要', 'Summary')" min-width="340">
          <template #default="{ row }">
            <div class="sub-text">{{ row.config_summary?.policy_name || '--' }}</div>
            <div class="sub-text">{{ row.config_summary?.description || '--' }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="created_by" :label="tr('创建人', 'Created by')" width="120" />
        <el-table-column prop="created_at" :label="tr('创建时间', 'Created at')" min-width="170">
          <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column :label="tr('操作', 'Actions')" width="280" fixed="right">
          <template #default="{ row }">
            <div class="row-action-group">
              <el-button link type="info" @click="openHistoryDrawer(row)">{{ tr('版本记录', 'History') }}</el-button>
              <el-button link type="primary" @click="openEditDrawer(row)">{{ tr('编辑', 'Edit') }}</el-button>
              <el-button link type="success" @click="handleCopy(row)">{{ tr('复制', 'Copy') }}</el-button>
              <el-button link type="warning" :disabled="row.status === 'ACTIVE'" @click="handleActivate(row)">{{ tr('激活', 'Activate') }}</el-button>
              <el-button link type="danger" :disabled="row.status === 'DISABLED'" @click="handleDisable(row)">{{ tr('停用', 'Disable') }}</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card class="panel-card">
      <template #header>
        <div class="section-head">
          <div>
            <h2>{{ tr('决策记录', 'Decision records') }}</h2>
            <p>{{ tr('当前风控仍以 shadow mode 记录决策、规则命中和特征快照，不直接改变审批结果。', 'The current risk engine records decisions, rule hits and feature snapshots in shadow mode without changing approvals.') }}</p>
          </div>
        </div>
      </template>

      <el-form :inline="true" :model="decisionFilters" class="policy-filter-form">
        <el-form-item :label="tr('阶段', 'Stage')">
          <el-select v-model="decisionFilters.stage" style="width: 160px">
            <el-option :label="tr('全部', 'All')" value="" />
            <el-option label="APPLICATION" value="APPLICATION" />
            <el-option label="ORDER" value="ORDER" />
            <el-option label="REVIEW" value="REVIEW" />
            <el-option label="DISBURSEMENT" value="DISBURSEMENT" />
          </el-select>
        </el-form-item>
        <el-form-item :label="tr('结果', 'Decision')">
          <el-select v-model="decisionFilters.decision" style="width: 150px">
            <el-option :label="tr('全部', 'All')" value="" />
            <el-option label="APPROVE" value="APPROVE" />
            <el-option label="REFER" value="REFER" />
            <el-option label="DECLINE" value="DECLINE" />
            <el-option label="BLOCK" value="BLOCK" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchDecisions">{{ tr('查询', 'Search') }}</el-button>
          <el-button @click="resetDecisionFilter">{{ tr('重置', 'Reset') }}</el-button>
        </el-form-item>
      </el-form>

      <el-table v-loading="decisionLoading" :data="decisionRows" stripe>
        <el-table-column prop="created_at" :label="tr('时间', 'Time')" min-width="170" />
        <el-table-column prop="decision_id" :label="tr('决策ID', 'Decision ID')" min-width="190" />
        <el-table-column prop="stage" :label="tr('阶段', 'Stage')" width="130" />
        <el-table-column :label="tr('结果', 'Decision')" width="120">
          <template #default="{ row }">
            <el-tag :type="decisionType(row.decision)">{{ row.decision }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="score" :label="tr('风险分', 'Risk score')" width="100" />
        <el-table-column :label="tr('策略版本', 'Policy version')" width="120">
          <template #default="{ row }">{{ row.policy_version }}</template>
        </el-table-column>
        <el-table-column :label="tr('命中规则', 'Rule hits')" min-width="260">
          <template #default="{ row }">
            <el-tag v-for="item in row.rule_hits || []" :key="item.rule_code" size="small" class="rule-tag">{{ item.rule_code }}</el-tag>
            <span v-if="!row.rule_hits?.length">--</span>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap">
        <el-pagination
          background
          layout="total, prev, pager, next"
          :total="decisionTotal"
          :page-size="decisionFilters.limit"
          :current-page="decisionFilters.page"
          @current-change="handleDecisionPageChange"
        />
      </div>
    </el-card>

    <el-card class="panel-card">
      <template #header>
        <div class="section-head">
          <div>
            <h2>{{ tr('设备风险信号', 'Device risk signals') }}</h2>
            <p>{{ tr('展示敏感信息授权、短信/App 摘要、设备指纹与风险标记，不直接暴露完整原始内容。', 'Show sensitive authorization, SMS/app summaries, device fingerprints and risk flags without exposing full raw content.') }}</p>
          </div>
          <div class="section-actions">
            <el-select v-model="signalFilters.riskLevel" style="width: 160px">
              <el-option :label="tr('全部等级', 'All levels')" value="" />
              <el-option label="INFO" value="INFO" />
              <el-option label="LOW" value="LOW" />
              <el-option label="MEDIUM" value="MEDIUM" />
              <el-option label="HIGH" value="HIGH" />
            </el-select>
            <el-button type="primary" @click="fetchSignals">{{ tr('查询', 'Search') }}</el-button>
            <el-button @click="resetSignalFilter">{{ tr('重置', 'Reset') }}</el-button>
          </div>
        </div>
      </template>

      <el-table v-loading="signalLoading" :data="signalRows" stripe>
        <el-table-column prop="created_at" :label="tr('时间', 'Time')" min-width="170">
          <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column prop="user_id" :label="tr('用户ID', 'User ID')" width="100" />
        <el-table-column :label="tr('授权', 'Consent')" width="110">
          <template #default="{ row }">
            <el-tag :type="row.consent_granted ? 'success' : 'warning'">{{ row.consent_granted ? tr('已授权', 'Granted') : tr('未授权', 'Pending') }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="risk_level" :label="tr('风险等级', 'Risk level')" width="120">
          <template #default="{ row }">
            <el-tag :type="riskLevelType(row.risk_level)">{{ row.risk_level }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="device_fingerprint" :label="tr('设备指纹', 'Fingerprint')" min-width="220" />
        <el-table-column :label="tr('短信命中', 'SMS hits')" min-width="160">
          <template #default="{ row }">
            <span>{{ signalText(row.keyword_hits?.sms) }}</span>
          </template>
        </el-table-column>
        <el-table-column :label="tr('应用命中', 'App hits')" min-width="160">
          <template #default="{ row }">
            <span>{{ signalText(row.keyword_hits?.apps) }}</span>
          </template>
        </el-table-column>
        <el-table-column :label="tr('设备命中', 'Device hits')" min-width="160">
          <template #default="{ row }">
            <span>{{ signalText(row.keyword_hits?.device) }}</span>
          </template>
        </el-table-column>
        <el-table-column :label="tr('风险标记', 'Flags')" min-width="220">
          <template #default="{ row }">
            <el-tag v-for="item in row.risk_flags || []" :key="item" size="small" class="rule-tag">{{ item }}</el-tag>
            <span v-if="!row.risk_flags?.length">--</span>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap">
        <el-pagination
          background
          layout="total, prev, pager, next"
          :total="signalTotal"
          :page-size="signalFilters.limit"
          :current-page="signalFilters.page"
          @current-change="handleSignalPageChange"
        />
      </div>
    </el-card>

    <el-drawer
      v-model="drawerVisible"
      size="920px"
      :title="drawerTitle"
      destroy-on-close
      class="policy-drawer"
    >
      <el-form :model="policyForm" label-width="110px" class="policy-form">
        <el-form-item :label="tr('策略标识', 'Policy key')">
          <el-input v-model="policyForm.policy_key" :disabled="true" />
        </el-form-item>
        <el-form-item :label="tr('版本号', 'Version')">
          <el-input v-model="policyVersionLabel" :disabled="true" />
        </el-form-item>
        <el-form-item :label="tr('状态', 'Status')">
          <el-select v-model="policyForm.status">
            <el-option label="DRAFT" value="DRAFT" />
            <el-option label="SHADOW" value="SHADOW" />
            <el-option label="ACTIVE" value="ACTIVE" />
            <el-option label="DISABLED" value="DISABLED" />
          </el-select>
        </el-form-item>
        <el-form-item :label="tr('灰度比例', 'Rollout')">
          <el-input-number v-model="policyForm.rollout_percent" :min="0" :max="100" />
        </el-form-item>
        <el-form-item :label="tr('策略模式', 'Mode')">
          <el-select v-model="policyForm.mode">
            <el-option label="SHADOW" value="SHADOW" />
            <el-option label="ENFORCE" value="ENFORCE" />
          </el-select>
        </el-form-item>
        <el-form-item :label="tr('策略名称', 'Policy name')">
          <el-input v-model="policyForm.policy_name" />
        </el-form-item>
        <el-form-item :label="tr('策略说明', 'Description')">
          <el-input v-model="policyForm.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item :label="tr('拒绝分', 'Block score')">
          <el-input-number v-model="policyForm.block_score" :min="0" :max="100" :step="1" />
        </el-form-item>
        <el-form-item :label="tr('转人工分', 'Refer score')">
          <el-input-number v-model="policyForm.refer_score" :min="0" :max="100" :step="1" />
        </el-form-item>
        <el-form-item :label="tr('24h申请上限', '24h application limit')">
          <el-input-number v-model="policyForm.application_count_24h" :min="0" :max="999" />
        </el-form-item>
        <el-form-item :label="tr('24h设备上限', '24h device limit')">
          <el-input-number v-model="policyForm.device_account_count_24h" :min="0" :max="999" />
        </el-form-item>

        <el-divider>{{ tr('规则配置', 'Rule settings') }}</el-divider>
        <div class="rule-grid">
          <article v-for="rule in ruleCatalog" :key="rule.key" class="rule-card">
            <div class="rule-card-head">
              <strong>{{ rule.labelZh }}</strong>
              <span>{{ rule.key }}</span>
            </div>
            <el-switch v-model="policyForm[`${rule.field}_enabled`]" :active-text="tr('启用', 'On')" :inactive-text="tr('停用', 'Off')" />
            <el-input-number v-model="policyForm[`${rule.field}_points`]" :min="0" :max="200" :step="1" />
          </article>
        </div>

        <el-divider>{{ tr('配置预览', 'Config preview') }}</el-divider>
        <el-input :model-value="policyConfigPreview" type="textarea" :rows="16" readonly />
      </el-form>

      <template #footer>
        <div class="drawer-footer">
          <el-button @click="drawerVisible = false">{{ tr('取消', 'Cancel') }}</el-button>
          <el-button type="primary" :loading="policySaving" @click="savePolicy">{{ tr('保存', 'Save') }}</el-button>
        </div>
      </template>
    </el-drawer>

    <el-drawer
      v-model="historyVisible"
      size="860px"
      :title="tr('策略版本记录', 'Policy history')"
      destroy-on-close
      class="policy-drawer"
    >
      <div class="history-head">
        <strong>{{ historyPolicyKey }}</strong>
        <span>{{ tr('用于查看同一策略下各版本的变更轨迹、状态和灰度配置。', 'View change history, status and rollout settings for the same policy.') }}</span>
      </div>
      <el-table v-loading="historyLoading" :data="historyRows" stripe>
        <el-table-column prop="version_no" :label="tr('版本号', 'Version')" width="100">
          <template #default="{ row }">v{{ row.version_no }}</template>
        </el-table-column>
        <el-table-column prop="status" :label="tr('状态', 'Status')" width="120">
          <template #default="{ row }">
            <el-tag :type="policyStatusType(row.status)">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="rollout_percent" :label="tr('灰度', 'Rollout')" width="100">
          <template #default="{ row }">{{ row.rollout_percent }}%</template>
        </el-table-column>
        <el-table-column :label="tr('策略摘要', 'Summary')" min-width="300">
          <template #default="{ row }">
            <div class="sub-text">{{ row.config_summary?.policy_name || '--' }}</div>
            <div class="sub-text">{{ row.config_summary?.description || '--' }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="created_by" :label="tr('创建人', 'Created by')" width="120" />
        <el-table-column prop="created_at" :label="tr('创建时间', 'Created at')" min-width="170">
          <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
        </el-table-column>
      </el-table>
    </el-drawer>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import {
  activateRiskPolicy,
  copyRiskPolicy,
  createRiskPolicy,
  disableRiskPolicy,
  getRiskDecisions,
  getRiskSignals,
  getRiskPolicyHistory,
  getRiskPolicies,
  updateRiskPolicy,
} from '../api';
import { formatDateTime } from '../utils/format';
import { tr } from '../i18n/adminLocale';

const DEFAULT_POLICY_KEY = 'GHANA_CASH_LOAN_BASELINE';
const ruleCatalog = [
  { key: 'BLACKLIST_HIT', field: 'blacklist_hit', labelZh: '黑名单命中', labelEn: 'Blacklist hit' },
  { key: 'EXTERNAL_RISK_LIST_HIT', field: 'external_risk_list_hit', labelZh: '外部名单命中', labelEn: 'External risk list' },
  { key: 'LOCATION_RISK_LOCKED', field: 'location_risk_locked', labelZh: '位置风控', labelEn: 'Location risk' },
  { key: 'IDENTITY_NOT_VERIFIED', field: 'identity_not_verified', labelZh: '实名未完成', labelEn: 'Identity not verified' },
  { key: 'FACE_NOT_VERIFIED', field: 'face_not_verified', labelZh: '人脸未完成', labelEn: 'Face not verified' },
  { key: 'PHONE_MISSING', field: 'phone_missing', labelZh: '手机号缺失', labelEn: 'Phone missing' },
  { key: 'CURRENT_LOAN_OVERDUE', field: 'current_loan_overdue', labelZh: '当前订单逾期', labelEn: 'Current overdue' },
  { key: 'OVERDUE_CREDIT_LOCKED', field: 'overdue_credit_locked', labelZh: '逾期额度锁定', labelEn: 'Overdue credit lock' },
  { key: 'DEVICE_ENV_HIGH_RISK', field: 'device_env_high_risk', labelZh: '设备环境高风险', labelEn: 'Device environment risk' },
  { key: 'SMS_LOAN_OVERDUE', field: 'sms_loan_overdue', labelZh: '短信借贷逾期', labelEn: 'SMS loan overdue' },
  { key: 'GAMBLING_SIGNAL', field: 'gambling_signal', labelZh: '博彩信号', labelEn: 'Gambling signal' },
  { key: 'APP_DEBT_PRESSURE', field: 'app_debt_pressure', labelZh: '应用债务压力', labelEn: 'App debt pressure' },
  { key: 'DEVICE_SHARED_MULTI_USER', field: 'device_shared_multi_user', labelZh: '设备多人共用', labelEn: 'Shared device' },
];

const policyFilters = reactive({ policyKey: DEFAULT_POLICY_KEY });
const policyLoading = ref(false);
const policySaving = ref(false);
const policyRows = ref([]);
const historyVisible = ref(false);
const historyLoading = ref(false);
const historyRows = ref([]);
const historyPolicyKey = ref(DEFAULT_POLICY_KEY);

const decisionLoading = ref(false);
const decisionRows = ref([]);
const decisionTotal = ref(0);
const decisionFilters = reactive({ stage: '', decision: '', page: 1, limit: 20 });

const signalLoading = ref(false);
const signalRows = ref([]);
const signalTotal = ref(0);
const signalFilters = reactive({ riskLevel: '', page: 1, limit: 20 });

const drawerVisible = ref(false);
const editingMode = ref('create');
const policyVersionLabel = ref('v1');
const policyForm = reactive(createEmptyPolicyForm());

const drawerTitle = computed(() => (editingMode.value === 'edit' ? tr('编辑策略版本', 'Edit policy version') : tr('新建策略版本', 'Create policy version')));

const summaryCards = computed(() => {
  const active = policyRows.value.find((item) => item.status === 'ACTIVE') || policyRows.value[0] || null;
  return [
    { label: tr('版本总数', 'Version count'), value: policyRows.value.length, tip: tr('当前策略历史版本条数', 'Current history records') },
    { label: tr('当前启用', 'Active version'), value: active ? `v${active.version_no}` : '--', tip: active ? `${active.status} · ${active.policy_key}` : tr('暂无启用版本', 'No active version') },
    { label: tr('灰度比例', 'Rollout'), value: active ? `${active.rollout_percent}%` : '--', tip: tr('当前启用版本的灰度配置', 'Rollout of the active version') },
    { label: tr('最近创建', 'Latest created'), value: active ? formatDateTime(active.created_at) : '--', tip: active ? (active.created_by || '--') : '--' },
  ];
});

const policyConfigPreview = computed(() => JSON.stringify(buildPolicyConfig(), null, 2));

function createEmptyPolicyForm() {
  return {
    id: null,
    policy_key: DEFAULT_POLICY_KEY,
    version_no: null,
    status: 'DRAFT',
    rollout_percent: 0,
    policy_name: '',
    description: '',
    mode: 'SHADOW',
    refer_score: 35,
    block_score: 80,
    application_count_24h: 5,
    device_account_count_24h: 3,
    blacklist_hit_enabled: true,
    blacklist_hit_points: 100,
    external_risk_list_hit_enabled: true,
    external_risk_list_hit_points: 100,
    location_risk_locked_enabled: true,
    location_risk_locked_points: 35,
    identity_not_verified_enabled: true,
    identity_not_verified_points: 25,
    face_not_verified_enabled: true,
    face_not_verified_points: 20,
    phone_missing_enabled: true,
    phone_missing_points: 80,
    current_loan_overdue_enabled: true,
    current_loan_overdue_points: 45,
    overdue_credit_locked_enabled: true,
    overdue_credit_locked_points: 40,
    device_env_high_risk_enabled: true,
    device_env_high_risk_points: 70,
    sms_loan_overdue_enabled: true,
    sms_loan_overdue_points: 45,
    gambling_signal_enabled: true,
    gambling_signal_points: 35,
    app_debt_pressure_enabled: true,
    app_debt_pressure_points: 30,
    device_shared_multi_user_enabled: true,
    device_shared_multi_user_points: 40,
  };
}

function resetPolicyForm(baseRow = null) {
  const source = baseRow?.config_json || {};
  const config = source && typeof source === 'object' ? source : {};
  const thresholds = config.decision_thresholds || {};
  const velocity = config.velocity || {};
  const rulePoints = config.rule_points || {};
  const ruleEnables = config.rule_enables || {};

  policyForm.id = baseRow?.id || null;
  policyForm.policy_key = baseRow?.policy_key || policyFilters.policyKey || DEFAULT_POLICY_KEY;
  policyForm.version_no = baseRow?.version_no || null;
  policyForm.status = baseRow?.status || 'DRAFT';
  policyForm.rollout_percent = Number(baseRow?.rollout_percent ?? 0);
  policyForm.policy_name = config.policy_name || '';
  policyForm.description = config.description || '';
  policyForm.mode = config.mode || 'SHADOW';
  policyForm.refer_score = Number(thresholds.refer_score ?? 35);
  policyForm.block_score = Number(thresholds.block_score ?? 80);
  policyForm.application_count_24h = Number(velocity.application_count_24h ?? 5);
  policyForm.device_account_count_24h = Number(velocity.device_account_count_24h ?? 3);

  for (const rule of ruleCatalog) {
    policyForm[`${rule.field}_enabled`] = ruleEnables[rule.key] ?? true;
    policyForm[`${rule.field}_points`] = Number(rulePoints[rule.key] ?? getDefaultRulePoints(rule.key));
  }
}

function getDefaultRulePoints(ruleKey) {
  return {
    BLACKLIST_HIT: 100,
    EXTERNAL_RISK_LIST_HIT: 100,
    LOCATION_RISK_LOCKED: 35,
    IDENTITY_NOT_VERIFIED: 25,
    FACE_NOT_VERIFIED: 20,
    PHONE_MISSING: 80,
    CURRENT_LOAN_OVERDUE: 45,
    OVERDUE_CREDIT_LOCKED: 40,
    DEVICE_ENV_HIGH_RISK: 70,
    SMS_LOAN_OVERDUE: 45,
    GAMBLING_SIGNAL: 35,
    APP_DEBT_PRESSURE: 30,
    DEVICE_SHARED_MULTI_USER: 40,
  }[ruleKey] || 0;
}

function buildPolicyConfig() {
  const rulePoints = {};
  const ruleEnables = {};
  for (const rule of ruleCatalog) {
    rulePoints[rule.key] = Number(policyForm[`${rule.field}_points`] ?? getDefaultRulePoints(rule.key));
    ruleEnables[rule.key] = Boolean(policyForm[`${rule.field}_enabled`]);
  }
  return {
    policy_name: policyForm.policy_name.trim(),
    description: policyForm.description.trim(),
    mode: policyForm.mode,
    decision_thresholds: {
      refer_score: Number(policyForm.refer_score || 35),
      block_score: Number(policyForm.block_score || 80),
    },
    rule_points: rulePoints,
    rule_enables: ruleEnables,
    velocity: {
      application_count_24h: Number(policyForm.application_count_24h || 0),
      device_account_count_24h: Number(policyForm.device_account_count_24h || 0),
    },
  };
}

function policyStatusType(status) {
  return {
    ACTIVE: 'success',
    SHADOW: 'warning',
    DRAFT: 'info',
    DISABLED: 'danger',
  }[status] || 'info';
}

function decisionType(value) {
  return { APPROVE: 'success', REFER: 'warning', DECLINE: 'danger', BLOCK: 'danger' }[value] || 'info';
}

function riskLevelType(value) {
  return { INFO: 'info', LOW: 'success', MEDIUM: 'warning', HIGH: 'danger' }[value] || 'info';
}

function signalText(items) {
  const values = Array.isArray(items) ? items.filter(Boolean) : [];
  return values.length ? values.join(' · ') : '--';
}

async function fetchPolicies() {
  policyLoading.value = true;
  try {
    const result = await getRiskPolicies({ policy_key: policyFilters.policyKey || undefined });
    policyRows.value = result.items || [];
  } finally {
    policyLoading.value = false;
  }
}

async function fetchDecisions() {
  decisionLoading.value = true;
  try {
    const result = await getRiskDecisions({
      stage: decisionFilters.stage || undefined,
      decision: decisionFilters.decision || undefined,
      skip: (decisionFilters.page - 1) * decisionFilters.limit,
      limit: decisionFilters.limit,
    });
    decisionRows.value = result.items || [];
    decisionTotal.value = Number(result.total || 0);
  } finally {
    decisionLoading.value = false;
  }
}

async function fetchSignals() {
  signalLoading.value = true;
  try {
    const result = await getRiskSignals({
      risk_level: signalFilters.riskLevel || undefined,
      skip: (signalFilters.page - 1) * signalFilters.limit,
      limit: signalFilters.limit,
    });
    signalRows.value = result.items || [];
    signalTotal.value = Number(result.total || 0);
  } finally {
    signalLoading.value = false;
  }
}

async function openHistoryDrawer(row) {
  historyVisible.value = true;
  historyPolicyKey.value = row.policy_key;
  historyLoading.value = true;
  try {
    const result = await getRiskPolicyHistory(row.policy_key);
    historyRows.value = result.items || [];
  } finally {
    historyLoading.value = false;
  }
}

function resetPolicyFilter() {
  policyFilters.policyKey = DEFAULT_POLICY_KEY;
  fetchPolicies();
}

function resetDecisionFilter() {
  decisionFilters.stage = '';
  decisionFilters.decision = '';
  decisionFilters.page = 1;
  fetchDecisions();
}

function resetSignalFilter() {
  signalFilters.riskLevel = '';
  signalFilters.page = 1;
  fetchSignals();
}

function handleDecisionPageChange(page) {
  decisionFilters.page = page;
  fetchDecisions();
}

function handleSignalPageChange(page) {
  signalFilters.page = page;
  fetchSignals();
}

function openCreateDrawer() {
  editingMode.value = 'create';
  const active = policyRows.value.find((item) => item.status === 'ACTIVE') || policyRows.value[0] || null;
  resetPolicyForm(active);
  policyForm.id = null;
  policyForm.version_no = null;
  policyForm.status = 'DRAFT';
  policyVersionLabel.value = 'new';
  drawerVisible.value = true;
}

function openEditDrawer(row) {
  editingMode.value = 'edit';
  resetPolicyForm(row);
  policyVersionLabel.value = `v${row.version_no}`;
  drawerVisible.value = true;
}

async function savePolicy() {
  policySaving.value = true;
  try {
    const payload = {
      policy_key: policyForm.policy_key,
      status: policyForm.status,
      rollout_percent: Number(policyForm.rollout_percent || 0),
      config_json: buildPolicyConfig(),
    };
    if (editingMode.value === 'edit' && policyForm.id) {
      await updateRiskPolicy(policyForm.id, payload);
      ElMessage.success(tr('策略版本已更新', 'Policy version updated'));
    } else {
      await createRiskPolicy(payload);
      ElMessage.success(tr('策略版本已创建', 'Policy version created'));
    }
    drawerVisible.value = false;
    await fetchPolicies();
  } finally {
    policySaving.value = false;
  }
}

async function handleCopy(row) {
  await copyRiskPolicy(row.id);
  ElMessage.success(tr('已复制为新版本', 'Copied to a new version'));
  await fetchPolicies();
}

async function handleActivate(row) {
  await ElMessageBox.confirm(
    tr('确定激活该策略版本吗？激活后，同策略下其他启用版本会自动回到 shadow。', 'Activate this version? Other active versions of the same policy will be moved back to shadow.'),
    tr('激活策略版本', 'Activate policy version'),
    { type: 'warning' }
  );
  await activateRiskPolicy(row.id);
  ElMessage.success(tr('策略版本已激活', 'Policy version activated'));
  await fetchPolicies();
}

async function handleDisable(row) {
  await ElMessageBox.confirm(
    tr('确定停用该策略版本吗？', 'Disable this policy version?'),
    tr('停用策略版本', 'Disable policy version'),
    { type: 'warning' }
  );
  await disableRiskPolicy(row.id);
  ElMessage.success(tr('策略版本已停用', 'Policy version disabled'));
  await fetchPolicies();
}

onMounted(async () => {
  await Promise.all([fetchPolicies(), fetchDecisions(), fetchSignals()]);
});
</script>

<style scoped>
.risk-strategy-page {
  gap: 18px;
}

.section-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.policy-filter-form {
  margin-bottom: 12px;
}

.row-action-group {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}

.history-head {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 12px;
}

.history-head strong {
  font-size: 15px;
  color: #1d2f49;
}

.history-head span {
  font-size: 12px;
  color: #7a8aa1;
}

.rule-tag {
  margin: 2px 4px 2px 0;
}

.policy-form {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0 16px;
}

.policy-form :deep(.el-form-item) {
  margin-bottom: 14px;
}

.rule-grid {
  grid-column: 1 / -1;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.rule-card {
  border: 1px solid #e7edf6;
  border-radius: 8px;
  padding: 12px;
  background: #fff;
}

.rule-card-head {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 10px;
}

.rule-card-head strong {
  font-size: 14px;
  color: #1d2f49;
}

.rule-card-head span {
  font-size: 12px;
  color: #7a8aa1;
}

.policy-drawer :deep(.el-drawer__body) {
  overflow: auto;
}

.drawer-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

@media (max-width: 1200px) {
  .policy-form,
  .rule-grid {
    grid-template-columns: 1fr;
  }
}
</style>
