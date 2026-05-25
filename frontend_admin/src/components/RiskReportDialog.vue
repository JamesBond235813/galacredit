<template>
  <el-dialog
    v-model="dialogVisible"
    title=""
    width="1100px"
    top="2vh"
    append-to-body
    destroy-on-close
    class="risk-dialog"
    @closed="emit('closed')"
  >
    <div v-loading="loading" class="risk-report-shell">
      <template v-if="payload">
        <section class="risk-hero">
          <div class="risk-hero-top">
            <div class="risk-hero-main">
              <span class="risk-eyebrow">Xiaohebao Risk</span>
              <h3>小荷包风险报告</h3>
              <p>合并全景雷达与探针C数据，展示客户申请行为、履约付款行为及外部履约探查结果。</p>
            </div>
            <div class="risk-hero-side">
              <div class="hero-metric">
                <span>申请准入分</span>
                <strong>{{ displayValue(applyDetail, 'A22160001') }}</strong>
              </div>
              <div class="hero-metric">
                <span>信用行为分</span>
                <strong>{{ displayValue(behaviorDetail, 'B22170001') }}</strong>
              </div>
            </div>
          </div>
          <div class="hero-profile-grid">
            <div class="hero-profile-item">
              <label>客户姓名</label>
              <span>{{ profile.name || normalizedReport.name || '--' }}</span>
            </div>
            <div class="hero-profile-item">
              <label>身份证号</label>
              <span>{{ profile.id_card || normalizedReport.id_card || '--' }}</span>
            </div>
            <div class="hero-profile-item">
              <label>手机号</label>
              <span>{{ profile.phone || normalizedReport.phone || '--' }}</span>
            </div>
            <div class="hero-profile-item">
              <label>报告时间</label>
              <span>{{ formatDateTime(normalizedReport.query_time || payload.query_time) }}</span>
            </div>
          </div>
        </section>

        <section class="report-section">
          <div class="section-head">
            <div>
              <h4>申请行为详情</h4>
              <p>申请准入置信度：{{ displayValue(applyDetail, 'A22160002') }}</p>
            </div>
          </div>
          <table class="report-table">
            <tbody>
              <tr>
                <th>申请准入分</th>
                <td>{{ displayValue(applyDetail, 'A22160001') }}</td>
                <th>近1个月机构总查询笔数</th>
                <td>{{ displayValue(applyDetail, 'A22160008') }}</td>
                <th>申请命中机构数</th>
                <td>{{ displayValue(applyDetail, 'A22160003') }}</td>
              </tr>
              <tr>
                <th>机构总查询次数</th>
                <td>{{ displayValue(applyDetail, 'A22160006') }}</td>
                <th>近3个月机构总查询笔数</th>
                <td>{{ displayValue(applyDetail, 'A22160009') }}</td>
                <th>申请命中消金类机构数</th>
                <td>{{ displayValue(applyDetail, 'A22160004') }}</td>
              </tr>
              <tr>
                <th>最近一次查询时间</th>
                <td>{{ displayValue(applyDetail, 'A22160007') }}</td>
                <th>近6个月机构总查询笔数</th>
                <td>{{ displayValue(applyDetail, 'A22160010') }}</td>
                <th>申请命中网络信用服务类机构数</th>
                <td>{{ displayValue(applyDetail, 'A22160005') }}</td>
              </tr>
            </tbody>
          </table>
        </section>

        <section class="report-section">
          <div class="section-head">
            <div>
              <h4>履约付款详情</h4>
              <p>信用行为置信度：{{ displayValue(behaviorDetail, 'B22170051') }}</p>
            </div>
          </div>

          <table class="report-table">
            <tbody>
              <tr>
                <th>信用行为分</th>
                <td>{{ displayValue(behaviorDetail, 'B22170001') }}</td>
                <th>最近一次服务发放时间</th>
                <td>{{ displayValue(behaviorDetail, 'B22170054') }}</td>
                <th>已结清订单数</th>
                <td>{{ displayValue(behaviorDetail, 'B22170052') }}</td>
              </tr>
              <tr>
                <th>信用服务时长</th>
                <td>{{ displayValue(behaviorDetail, 'B22170053') }}</td>
                <th>最近一次履约距今天数</th>
                <td>{{ displayValue(behaviorDetail, 'B22170050') }}</td>
                <th>正常付款订单占总订单数比例</th>
                <td class="emphasis danger">{{ displayValue(behaviorDetail, 'B22170034') }}</td>
              </tr>
            </tbody>
          </table>

          <table class="report-table">
            <thead>
              <tr>
                <th>行为时间</th>
                <th>机构数</th>
                <th>订单笔数</th>
                <th>订单总金额</th>
                <th>履约订单总金额</th>
                <th>履约订单数</th>
                <th>失败扣款数</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in behaviorTimeRows" :key="row.label">
                <th>{{ row.label }}</th>
                <td>{{ displayValue(behaviorDetail, row.keys[0]) }}</td>
                <td>{{ displayValue(behaviorDetail, row.keys[1]) }}</td>
                <td>{{ displayValue(behaviorDetail, row.keys[2]) }}</td>
                <td class="emphasis success">{{ displayValue(behaviorDetail, row.keys[3]) }}</td>
                <td class="emphasis success">{{ displayValue(behaviorDetail, row.keys[4]) }}</td>
                <td>{{ displayValue(behaviorDetail, row.keys[5]) }}</td>
              </tr>
            </tbody>
          </table>

          <div class="grid-block">
            <table class="report-table">
              <thead>
                <tr>
                  <th>近12个月订单金额</th>
                  <th>1K及以下</th>
                  <th>1K-3K</th>
                  <th>3K-10K</th>
                  <th>1W以上</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <th>订单笔数</th>
                  <td>{{ displayValue(behaviorDetail, 'B22170012', '0') }}</td>
                  <td>{{ displayValue(behaviorDetail, 'B22170013', '0') }}</td>
                  <td>{{ displayValue(behaviorDetail, 'B22170014', '0') }}</td>
                  <td>{{ displayValue(behaviorDetail, 'B22170015', '0') }}</td>
                </tr>
              </tbody>
            </table>

            <table class="report-table">
              <thead>
                <tr>
                  <th>近12个月消费信用类机构数</th>
                  <th>近24个月消费信用类机构数</th>
                  <th>近12个月线上信用类机构数</th>
                  <th>近24个月线上信用类机构数</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>{{ displayValue(behaviorDetail, 'B22170021', '0') }}</td>
                  <td>{{ displayValue(behaviorDetail, 'B22170022', '0') }}</td>
                  <td>{{ displayValue(behaviorDetail, 'B22170023', '0') }}</td>
                  <td>{{ displayValue(behaviorDetail, 'B22170024', '0') }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <table class="report-table">
            <tbody>
              <tr>
                <th>近6个月M0+逾期订单笔数</th>
                <td>{{ displayValue(behaviorDetail, 'B22170025') }}</td>
                <th>近6个月M1+逾期订单笔数</th>
                <td>{{ displayValue(behaviorDetail, 'B22170028') }}</td>
                <th>近6个月累计逾期金额</th>
                <td>{{ displayValue(behaviorDetail, 'B22170031') }}</td>
              </tr>
              <tr>
                <th>近12个月M0+逾期订单笔数</th>
                <td class="emphasis danger">{{ displayValue(behaviorDetail, 'B22170026') }}</td>
                <th>近12个月M1+逾期订单笔数</th>
                <td class="emphasis danger">{{ displayValue(behaviorDetail, 'B22170029') }}</td>
                <th>近12个月累计逾期金额</th>
                <td class="emphasis danger">{{ displayValue(behaviorDetail, 'B22170032') }}</td>
              </tr>
              <tr>
                <th>近24个月M0+逾期订单笔数</th>
                <td>{{ displayValue(behaviorDetail, 'B22170027') }}</td>
                <th>近24个月M1+逾期订单笔数</th>
                <td>{{ displayValue(behaviorDetail, 'B22170030') }}</td>
                <th>近24个月累计逾期金额</th>
                <td>{{ displayValue(behaviorDetail, 'B22170033') }}</td>
              </tr>
            </tbody>
          </table>
        </section>

        <section class="report-section">
          <div class="section-head">
            <div>
              <h4>探针C信息</h4>
              <p>展示探针C返回的履约与逾期概况。</p>
            </div>
          </div>
          <table class="report-table">
            <tbody>
              <tr>
                <th>探查结果</th>
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
      </template>

      <div v-else class="empty-wrap">
        <el-empty description="暂无小荷包风险报告数据" />
      </div>
    </div>
  </el-dialog>
</template>

<script setup>
import { computed } from 'vue';
import { formatDateTime } from '../utils/format';

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

const emit = defineEmits(['update:modelValue', 'closed']);

const dialogVisible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
});

const behaviorTimeRows = [
  { label: '近1个月', keys: ['B22170016', 'B22170002', 'B22170007', 'B22170040', 'B22170045', 'B22170035'] },
  { label: '近3个月', keys: ['B22170017', 'B22170003', 'B22170008', 'B22170041', 'B22170046', 'B22170036'] },
  { label: '近6个月', keys: ['B22170018', 'B22170004', 'B22170009', 'B22170042', 'B22170047', 'B22170037'] },
  { label: '近12个月', keys: ['B22170019', 'B22170005', 'B22170010', 'B22170043', 'B22170048', 'B22170038'] },
  { label: '近24个月', keys: ['B22170020', 'B22170006', 'B22170011', 'B22170044', 'B22170049', 'B22170039'] }
];

const normalizedReport = computed(() => props.report || {});
const payload = computed(() => parsePayload(normalizedReport.value.report_json || normalizedReport.value.reportJson));
const profile = computed(() => payload.value?.user_profile || {});
const panoramaPayload = computed(() => payload.value?.panorama?.payload || {});
const panoramaData = computed(() => panoramaPayload.value?.data || {});
const applyDetail = computed(() => panoramaData.value?.apply_report_detail || panoramaPayload.value?.apply_report_detail || {});
const behaviorDetail = computed(() => panoramaData.value?.behavior_report_detail || panoramaPayload.value?.behavior_report_detail || {});
const probeC = computed(() => payload.value?.probe_c || {});
const probeData = computed(() => probeC.value?.payload?.data || {});

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
</script>

<style scoped>
.risk-report-shell {
  min-height: 320px;
  max-height: calc(100vh - 140px);
  overflow-y: auto;
  padding-right: 4px;
}

.risk-hero {
  display: grid;
  gap: 18px;
  padding: 20px 22px;
  border-radius: 20px;
  background:
    radial-gradient(circle at top right, rgba(56, 118, 255, 0.22), transparent 36%),
    linear-gradient(135deg, #0f4fc6 0%, #2e74ea 48%, #5e9bff 100%);
  color: #ffffff;
}

.risk-hero-top {
  display: flex;
  justify-content: space-between;
  gap: 18px;
}

.risk-hero-main {
  flex: 1;
  min-width: 0;
}

.risk-eyebrow {
  display: inline-flex;
  padding: 5px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.16);
  font-size: 12px;
  letter-spacing: 0.6px;
  text-transform: uppercase;
}

.risk-hero-main h3 {
  margin: 14px 0 8px;
  font-size: 28px;
  line-height: 1.1;
}

.risk-hero-main p {
  margin: 0;
  max-width: 620px;
  color: rgba(255, 255, 255, 0.84);
  line-height: 1.6;
}

.risk-hero-side {
  display: grid;
  grid-template-columns: repeat(2, minmax(120px, 1fr));
  gap: 12px;
  min-width: 280px;
}

.hero-metric {
  padding: 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.14);
  border: 1px solid rgba(255, 255, 255, 0.18);
}

.hero-metric span {
  display: block;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.74);
}

.hero-metric strong {
  display: block;
  margin-top: 10px;
  font-size: 28px;
  line-height: 1;
}

.hero-profile-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.hero-profile-item {
  min-width: 0;
  padding: 12px 14px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.14);
  border: 1px solid rgba(255, 255, 255, 0.18);
}

.hero-profile-item label {
  display: block;
  margin-bottom: 7px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.72);
}

.hero-profile-item span {
  display: block;
  color: #ffffff;
  font-weight: 600;
  word-break: break-all;
}

.report-section {
  margin-top: 20px;
  padding: 20px;
  border-radius: 18px;
  background: #ffffff;
  border: 1px solid #e8eef8;
  box-shadow: 0 12px 28px rgba(34, 76, 142, 0.06);
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}

.section-head h4 {
  margin: 0;
  font-size: 18px;
  color: #1d3760;
}

.section-head p {
  margin: 6px 0 0;
  color: #6e819d;
  font-size: 13px;
}

.report-table {
  width: 100%;
  margin-top: 14px;
  border-collapse: collapse;
  table-layout: fixed;
}

.report-table th,
.report-table td {
  padding: 11px 10px;
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
  background: #ffffff;
}

.grid-block {
  display: grid;
  grid-template-columns: 1fr;
  gap: 14px;
  margin-top: 14px;
}

.emphasis.success {
  color: #14905f;
  font-weight: 700;
}

.emphasis.danger {
  color: #d84b47;
  font-weight: 700;
}

.empty-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 280px;
}

@media (max-width: 1200px) {
  .risk-hero {
    grid-template-columns: 1fr;
  }

  .risk-hero-top {
    flex-direction: column;
  }

  .risk-hero-side {
    min-width: 0;
  }

  .hero-profile-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .hero-profile-grid {
    grid-template-columns: 1fr;
  }
}

:deep(.risk-dialog .el-dialog) {
  border-radius: 24px;
  overflow: hidden;
}

:deep(.risk-dialog .el-dialog__header) {
  margin-right: 0;
  padding: 10px 24px 0;
}

:deep(.risk-dialog .el-dialog__title) {
  display: none;
}

:deep(.risk-dialog .el-dialog__body) {
  padding: 10px 24px 24px;
  background: #f4f7fb;
}
</style>
