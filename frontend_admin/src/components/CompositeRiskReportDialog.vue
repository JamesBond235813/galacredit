<template>
  <el-dialog
    v-model="dialogVisible"
    title="GalaCredit Risk Report"
    width="1120px"
    top="2vh"
    append-to-body
    destroy-on-close
    class="composite-risk-dialog"
  >
    <div v-loading="loading" class="composite-risk-shell">
      <template v-if="payload">
        <section class="composite-hero">
          <div>
            <span class="composite-eyebrow">GalaCredit Risk</span>
            <h3>GalaCredit Risk Report</h3>
            <p>合并全景雷达与探针C数据，展示客户申请行为、履约付款行为及外部履约探查结果。</p>
          </div>
          <div class="hero-source">
            <span>系统数据</span>
            <span>全景雷达</span>
            <span>探针C</span>
          </div>
        </section>

        <section class="summary-grid">
          <div class="summary-item">
            <label>姓名</label>
            <span>{{ profile.name || normalizedReport.name || '--' }}</span>
          </div>
          <div class="summary-item">
            <label>手机号</label>
            <span>{{ profile.phone || normalizedReport.phone || '--' }}</span>
          </div>
          <div class="summary-item">
            <label>身份证号</label>
            <span>{{ profile.id_card || normalizedReport.id_card || '--' }}</span>
          </div>
          <div class="summary-item">
            <label>报告时间</label>
            <span>{{ formatDateTime(normalizedReport.query_time || payload.query_time) }}</span>
          </div>
        </section>

        <section class="report-section">
          <div class="section-head">
            <h4>系统风险核查</h4>
            <p>来自本系统黑名单、位置风控、登录拦截与手机号绑定记录。</p>
          </div>
          <div class="risk-tags">
            <el-tag :type="systemRisk.blacklist_hit ? 'danger' : 'success'">
              黑名单：{{ systemRisk.blacklist_hit ? '命中' : '未命中' }}
            </el-tag>
            <el-tag :type="systemRisk.location_risk_hit ? 'warning' : 'success'">
              风险地址：{{ systemRisk.location_risk_hit ? '命中' : '未命中' }}
            </el-tag>
            <el-tag :type="systemRisk.login_location_blocked ? 'danger' : 'success'">
              登录位置拦截：{{ systemRisk.login_location_blocked ? '触发' : '未触发' }}
            </el-tag>
            <el-tag type="info">同手机号绑定：{{ systemRisk.same_phone_binding_count || 0 }} 条</el-tag>
          </div>
          <table class="report-table">
            <tbody>
              <tr>
                <th>黑名单原因</th>
                <td>{{ systemRisk.blacklist_reason || '--' }}</td>
                <th>风险地址明细</th>
                <td>{{ systemRisk.location_risk_detail || '--' }}</td>
              </tr>
              <tr>
                <th>登录拦截原因</th>
                <td>{{ systemRisk.login_location_reason || '--' }}</td>
                <th>风险关键词</th>
                <td>{{ listText(systemRisk.location_risk_keywords) }}</td>
              </tr>
            </tbody>
          </table>
        </section>

        <section class="report-section">
          <div class="section-head">
            <h4>当前订单摘要</h4>
            <p>展示客户最近一笔订单的当前状态。</p>
          </div>
          <table class="report-table">
            <tbody>
              <tr>
                <th>订单状态</th>
                <td>{{ latestOrder.status || '--' }}</td>
                <th>授信额度</th>
                <td>{{ money(latestOrder.credit_limit) }}</td>
                <th>可用额度</th>
                <td>{{ money(latestOrder.available_credit_limit) }}</td>
              </tr>
              <tr>
                <th>商品名称</th>
                <td>{{ latestOrder.product_name || '--' }}</td>
                <th>应付金额</th>
                <td>{{ money(latestOrder.payment_amount || latestOrder.product_total_price) }}</td>
                <th>到期日</th>
                <td>{{ formatDateTime(latestOrder.due_date) }}</td>
              </tr>
            </tbody>
          </table>
        </section>

        <section class="report-section">
          <div class="section-head">
            <h4>全景雷达摘要</h4>
            <p>保留原始全景雷达报告，本报告提取关键字段展示。</p>
          </div>
          <table class="report-table">
            <tbody>
              <tr>
                <th>申请准入分</th>
                <td>{{ displayValue(applyDetail, 'A22160001') }}</td>
                <th>信用行为分</th>
                <td>{{ displayValue(behaviorDetail, 'B22170001') }}</td>
                <th>最近一次查询时间</th>
                <td>{{ displayValue(applyDetail, 'A22160007') }}</td>
              </tr>
              <tr>
                <th>机构总查询次数</th>
                <td>{{ displayValue(applyDetail, 'A22160006') }}</td>
                <th>近12个月M0+逾期订单笔数</th>
                <td>{{ displayValue(behaviorDetail, 'B22170026') }}</td>
                <th>近12个月累计逾期金额</th>
                <td>{{ displayValue(behaviorDetail, 'B22170032') }}</td>
              </tr>
            </tbody>
          </table>
        </section>

        <section class="report-section">
          <div class="section-head">
            <h4>探针C摘要</h4>
            <p>展示探针C返回的履约与逾期概况。</p>
          </div>
          <table class="report-table">
            <tbody>
              <tr>
                <th>结果</th>
                <td>{{ probeC.result_label || '--' }}</td>
                <th>最大逾期金额</th>
                <td>{{ probeData.max_overdue_amt || '--' }}</td>
                <th>最长逾期天数</th>
                <td>{{ probeData.max_overdue_days || '--' }}</td>
              </tr>
              <tr>
                <th>最近逾期时间</th>
                <td>{{ probeData.latest_overdue_time || '--' }}</td>
                <th>当前逾期机构数</th>
                <td>{{ probeData.currently_overdue || '--' }}</td>
                <th>当前履约机构数</th>
                <td>{{ probeData.currently_performance || '--' }}</td>
              </tr>
              <tr>
                <th>异常还款机构数</th>
                <td>{{ probeData.acc_exc || '--' }}</td>
                <th>睡眠机构数</th>
                <td>{{ probeData.acc_sleep || '--' }}</td>
                <th>报告来源</th>
                <td>{{ probeC.source || '--' }}</td>
              </tr>
              <tr>
                <th>最大履约金额</th>
                <td>{{ probeData.max_performance_amt || '--' }}</td>
                <th>最近履约时间</th>
                <td>{{ probeData.latest_performance_time || '--' }}</td>
                <th>履约笔数</th>
                <td>{{ probeData.count_performance || '--' }}</td>
              </tr>
            </tbody>
          </table>
        </section>

        <section class="report-section">
          <div class="section-head">
            <h4>最近访问记录</h4>
            <p>按时间由近到远展示最近访问、IP和经纬度解析结果。</p>
          </div>
          <el-table :data="recentAccess" size="small" border>
            <el-table-column prop="created_at" label="时间" min-width="150">
              <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
            </el-table-column>
            <el-table-column prop="title" label="操作" min-width="160" />
            <el-table-column prop="ip" label="IP" min-width="120" />
            <el-table-column prop="ip_address" label="IP地址" min-width="180" />
            <el-table-column prop="lon_lat" label="经纬度" min-width="140" />
            <el-table-column prop="lon_lat_address" label="经纬度地址" min-width="180" />
          </el-table>
        </section>
      </template>
      <el-empty v-else description="No GalaCredit risk report data" />
    </div>
  </el-dialog>
</template>

<script setup>
import { computed } from 'vue';
import { formatCurrency, formatDateTime } from '../utils/format';

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  loading: {
    type: Boolean,
    default: false
  },
  report: {
    type: Object,
    default: null
  }
});

const emit = defineEmits(['update:modelValue']);

const dialogVisible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
});

const normalizedReport = computed(() => props.report || {});
const payload = computed(() => parsePayload(normalizedReport.value.report_json || normalizedReport.value.reportJson));
const profile = computed(() => payload.value?.user_profile || {});
const systemRisk = computed(() => payload.value?.system_risk || {});
const latestOrder = computed(() => payload.value?.latest_order || {});
const panoramaPayload = computed(() => payload.value?.panorama?.payload || {});
const panoramaData = computed(() => panoramaPayload.value?.data || {});
const applyDetail = computed(() => panoramaData.value?.apply_report_detail || panoramaPayload.value?.apply_report_detail || {});
const behaviorDetail = computed(() => panoramaData.value?.behavior_report_detail || panoramaPayload.value?.behavior_report_detail || {});
const probeC = computed(() => payload.value?.probe_c || {});
const probeData = computed(() => probeC.value?.payload?.data || {});
const recentAccess = computed(() => payload.value?.recent_access || []);

const parsePayload = (value) => {
  if (!value) {
    return null;
  }
  if (typeof value === 'object') {
    return value;
  }
  try {
    const parsed = JSON.parse(value);
    return typeof parsed === 'object' ? parsed : null;
  } catch (error) {
    return null;
  }
};

const displayValue = (source, key, fallback = '--') => {
  const value = source?.[key];
  if (value === 0 || value === '0') {
    return value;
  }
  return value || fallback;
};

const listText = (items) => (Array.isArray(items) && items.length ? items.join('、') : '--');
const money = (value) => (value || value === 0 ? formatCurrency(value) : '--');
</script>

<style scoped>
.composite-risk-shell {
  min-height: 320px;
  max-height: calc(100vh - 140px);
  overflow-y: auto;
  padding-right: 4px;
}

.composite-hero {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
  padding: 20px 22px;
  border-radius: 12px;
  color: #ffffff;
  background: linear-gradient(135deg, #163b76 0%, #2871b8 54%, #45a28d 100%);
}

.composite-eyebrow {
  display: inline-flex;
  padding: 5px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.16);
  font-size: 12px;
}

.composite-hero h3 {
  margin: 14px 0 8px;
  font-size: 26px;
  line-height: 1.15;
}

.composite-hero p {
  margin: 0;
  color: rgba(255, 255, 255, 0.86);
  line-height: 1.6;
}

.hero-source {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
  min-width: 220px;
}

.hero-source span {
  padding: 8px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.14);
  border: 1px solid rgba(255, 255, 255, 0.18);
  font-size: 12px;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin-top: 16px;
}

.summary-item {
  padding: 14px 16px;
  border-radius: 10px;
  background: #f7faff;
  border: 1px solid #e6edf8;
}

.summary-item label {
  display: block;
  margin-bottom: 7px;
  font-size: 12px;
  color: #73849b;
}

.summary-item span {
  display: block;
  color: #25384f;
  font-weight: 600;
  word-break: break-all;
}

.report-section {
  margin-top: 18px;
  padding: 18px;
  border-radius: 10px;
  background: #ffffff;
  border: 1px solid #e8eef8;
}

.section-head {
  margin-bottom: 12px;
}

.section-head h4 {
  margin: 0;
  color: #1f3c63;
  font-size: 17px;
}

.section-head p {
  margin: 6px 0 0;
  color: #6d7f96;
  font-size: 13px;
}

.risk-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}

.report-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
}

.report-table th,
.report-table td {
  padding: 10px;
  border: 1px solid #e7edf6;
  font-size: 12px;
  text-align: center;
  word-break: break-word;
}

.report-table th {
  background: #f8fbff;
  color: #59708f;
  font-weight: 500;
}

.report-table td {
  color: #2d4059;
}
</style>
