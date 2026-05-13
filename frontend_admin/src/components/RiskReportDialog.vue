<template>
  <el-dialog
    v-model="dialogVisible"
    title="全景雷达风控报告"
    width="1100px"
    top="2vh"
    append-to-body
    destroy-on-close
    class="risk-dialog"
    @closed="emit('closed')"
  >
    <div v-loading="loading" class="risk-report-shell">
      <template v-if="normalizedReport">
        <section class="risk-hero">
          <div class="risk-hero-main">
            <span class="risk-eyebrow">Panorama Risk</span>
            <h3>全景雷达风控报告</h3>
            <p>按 `crm_songshu` 的风控报告结构复刻，展示申请行为、放款还款行为和当前授信画像。</p>
          </div>
          <div class="risk-hero-side">
            <div class="hero-metric">
              <span>申请准入分</span>
              <strong>{{ displayValue(applyDetail, 'A22160001') }}</strong>
            </div>
            <div class="hero-metric">
              <span>贷款行为分</span>
              <strong>{{ displayValue(behaviorDetail, 'B22170001') }}</strong>
            </div>
          </div>
        </section>

        <section class="summary-card">
          <div class="summary-item">
            <label>姓名</label>
            <span>{{ normalizedReport.name || '--' }}</span>
          </div>
          <div class="summary-item">
            <label>身份证号</label>
            <span>{{ normalizedReport.idCard || '--' }}</span>
          </div>
          <div class="summary-item">
            <label>手机号</label>
            <span>{{ normalizedReport.phone || '--' }}</span>
          </div>
          <div class="summary-item">
            <label>报告时间</label>
            <span>{{ formatDateTime(normalizedReport.queryTime) }}</span>
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
                <th>申请命中网络贷款类机构数</th>
                <td>{{ displayValue(applyDetail, 'A22160005') }}</td>
              </tr>
            </tbody>
          </table>
        </section>

        <section class="report-section">
          <div class="section-head">
            <div>
              <h4>放款还款详情</h4>
              <p>贷款行为置信度：{{ displayValue(behaviorDetail, 'B22170051') }}</p>
            </div>
          </div>

          <table class="report-table">
            <tbody>
              <tr>
                <th>贷款行为分</th>
                <td>{{ displayValue(behaviorDetail, 'B22170001') }}</td>
                <th>最近一次放款时间</th>
                <td>{{ displayValue(behaviorDetail, 'B22170054') }}</td>
                <th>贷款已结清订单数</th>
                <td>{{ displayValue(behaviorDetail, 'B22170052') }}</td>
              </tr>
              <tr>
                <th>信用贷款时长</th>
                <td>{{ displayValue(behaviorDetail, 'B22170053') }}</td>
                <th>最近一次履约距今天数</th>
                <td>{{ displayValue(behaviorDetail, 'B22170050') }}</td>
                <th>正常还款订单占贷款总订单数比例</th>
                <td class="emphasis danger">{{ displayValue(behaviorDetail, 'B22170034') }}</td>
              </tr>
            </tbody>
          </table>

          <table class="report-table">
            <thead>
              <tr>
                <th>行为时间</th>
                <th>机构数</th>
                <th>贷款笔数</th>
                <th>贷款总金额</th>
                <th>履约贷款总金额</th>
                <th>履约贷款数</th>
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
                  <th>近12个月贷款金额</th>
                  <th>1K及以下</th>
                  <th>1K-3K</th>
                  <th>3K-10K</th>
                  <th>1W以上</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <th>贷款笔数</th>
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
                  <th>近12个月消金类贷款机构数</th>
                  <th>近24个月消金类贷款机构数</th>
                  <th>近12个月网贷类贷款机构数</th>
                  <th>近24个月网贷类贷款机构数</th>
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
                <th>近6个月M0+逾期贷款笔数</th>
                <td>{{ displayValue(behaviorDetail, 'B22170025') }}</td>
                <th>近6个月M1+逾期贷款笔数</th>
                <td>{{ displayValue(behaviorDetail, 'B22170028') }}</td>
                <th>近6个月累计逾期金额</th>
                <td>{{ displayValue(behaviorDetail, 'B22170031') }}</td>
              </tr>
              <tr>
                <th>近12个月M0+逾期贷款笔数</th>
                <td class="emphasis danger">{{ displayValue(behaviorDetail, 'B22170026') }}</td>
                <th>近12个月M1+逾期贷款笔数</th>
                <td class="emphasis danger">{{ displayValue(behaviorDetail, 'B22170029') }}</td>
                <th>近12个月累计逾期金额</th>
                <td class="emphasis danger">{{ displayValue(behaviorDetail, 'B22170032') }}</td>
              </tr>
              <tr>
                <th>近24个月M0+逾期贷款笔数</th>
                <td>{{ displayValue(behaviorDetail, 'B22170027') }}</td>
                <th>近24个月M1+逾期贷款笔数</th>
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
              <h4>信用详情</h4>
              <p>当前机构授信能力与建议额度画像</p>
            </div>
          </div>
          <table class="report-table">
            <tbody>
              <tr>
                <th>网贷建议授信额度</th>
                <td>{{ displayValue(currentDetail, 'C22180001', '0') }}</td>
                <th>网贷额度置信度</th>
                <td class="emphasis danger">{{ displayValue(currentDetail, 'C22180002', '0') }}</td>
                <th>网络贷款类机构数</th>
                <td>{{ displayValue(currentDetail, 'C22180003', '0') }}</td>
              </tr>
              <tr>
                <th>网络贷款类产品数</th>
                <td>{{ displayValue(currentDetail, 'C22180004', '0') }}</td>
                <th>网络贷款机构最大授信额度</th>
                <td>{{ displayValue(currentDetail, 'C22180005', '0') }}</td>
                <th>网络贷款机构平均授信额度</th>
                <td>{{ displayValue(currentDetail, 'C22180006', '0') }}</td>
              </tr>
              <tr>
                <th>消金贷款类机构数</th>
                <td>{{ displayValue(currentDetail, 'C22180007', '0') }}</td>
                <th>消金贷款类产品数</th>
                <td>{{ displayValue(currentDetail, 'C22180008', '0') }}</td>
                <th>消金贷款类机构最大授信额度</th>
                <td>{{ displayValue(currentDetail, 'C22180009', '0') }}</td>
              </tr>
              <tr>
                <th>消金贷款类机构平均授信额度</th>
                <td>{{ displayValue(currentDetail, 'C22180010', '0') }}</td>
                <th>消金建议授信额度</th>
                <td>{{ displayValue(currentDetail, 'C22180011', '0') }}</td>
                <th>消金额度置信度</th>
                <td class="emphasis danger">{{ displayValue(currentDetail, 'C22180012', '0') }}</td>
              </tr>
            </tbody>
          </table>
        </section>
      </template>

      <div v-else class="empty-wrap">
        <el-empty description="暂无风控报告数据" />
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

const normalizedReport = computed(() => {
  if (!props.report) {
    return null;
  }

  let reportDetail =
    props.report.reportJson ??
    props.report.report_json ??
    props.report.data?.reportJson ??
    props.report.data?.report_json ??
    props.report.data ??
    props.report;

  if (typeof reportDetail === 'string') {
    try {
      reportDetail = JSON.parse(reportDetail);
    } catch (error) {
      return null;
    }
  }

  const reportData = reportDetail?.data ?? {};
  return {
    ...reportDetail,
    ...reportData,
    apply_report_detail: reportDetail?.apply_report_detail ?? reportData?.apply_report_detail ?? {},
    behavior_report_detail: reportDetail?.behavior_report_detail ?? reportData?.behavior_report_detail ?? {},
    current_report_detail: reportDetail?.current_report_detail ?? reportData?.current_report_detail ?? {},
    name: props.report.name ?? props.report.user_name ?? '',
    idCard: props.report.idCard ?? props.report.id_card ?? props.report.user_id_card_num ?? '',
    phone: props.report.phone ?? props.report.user_phone ?? '',
    queryTime: props.report.queryTime ?? props.report.query_time ?? reportDetail?.queryTime ?? reportDetail?.query_time
  };
});

const applyDetail = computed(() => normalizedReport.value?.apply_report_detail ?? {});
const behaviorDetail = computed(() => normalizedReport.value?.behavior_report_detail ?? {});
const currentDetail = computed(() => normalizedReport.value?.current_report_detail ?? {});

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
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding: 20px 22px;
  border-radius: 20px;
  background:
    radial-gradient(circle at top right, rgba(56, 118, 255, 0.22), transparent 36%),
    linear-gradient(135deg, #0f4fc6 0%, #2e74ea 48%, #5e9bff 100%);
  color: #ffffff;
}

.risk-hero-main {
  flex: 1;
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

.summary-card {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin-top: 18px;
}

.summary-item {
  padding: 16px 18px;
  border-radius: 16px;
  background: #f7faff;
  border: 1px solid rgba(44, 114, 229, 0.09);
}

.summary-item label {
  display: block;
  margin-bottom: 8px;
  font-size: 12px;
  color: #7b8ca6;
}

.summary-item span {
  display: block;
  color: #24364d;
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
  .risk-hero,
  .summary-card {
    grid-template-columns: 1fr;
  }

  .risk-hero {
    flex-direction: column;
  }

  .risk-hero-side {
    min-width: 0;
  }

  .summary-card {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .summary-card {
    grid-template-columns: 1fr;
  }
}

:deep(.risk-dialog .el-dialog) {
  border-radius: 24px;
  overflow: hidden;
}

:deep(.risk-dialog .el-dialog__header) {
  margin-right: 0;
  padding: 22px 24px 12px;
}

:deep(.risk-dialog .el-dialog__body) {
  padding: 8px 24px 24px;
  background: #f4f7fb;
}
</style>
