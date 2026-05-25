<template>
  <div class="admin-page">
    <el-card class="panel-card filter-card">
      <el-form :inline="true" :model="filters">
        <el-form-item label="搜索">
          <el-input v-model="filters.keyword" placeholder="手机号 / 姓名 / 身份证号" clearable @keyup.enter="fetchData" />
        </el-form-item>
        <el-form-item v-if="isBusinessConsultant" label="成交日期">
          <el-date-picker
            v-model="filters.dealDateRange"
            type="daterange"
            value-format="YYYY-MM-DD"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            clearable
          />
        </el-form-item>
        <el-form-item v-if="!isBusinessConsultant" label="位置风控">
          <el-select v-model="filters.locationRiskBlocked" style="width: 160px">
            <el-option label="全部" value="ALL" />
            <el-option label="仅已锁定" value="LOCKED" />
            <el-option label="仅未锁定" value="NORMAL" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchData">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="panel-card">
      <el-table v-loading="loading" :data="tableData" stripe>
        <el-table-column prop="id" label="用户ID" width="90" />
        <el-table-column label="用户信息" min-width="220">
          <template #default="{ row }">
            <div class="user-name-row">
              <span>{{ row.name || '未实名' }}</span>
              <el-tag v-if="row.location_risk_blocked" type="danger" effect="plain" size="small">
                位置风控
              </el-tag>
              <el-tag v-if="row.risk_list_hit" type="warning" effect="plain" size="small">
                风险名单
              </el-tag>
            </div>
            <div class="sub-text">{{ row.phone }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="id_card_num" label="身份证号" min-width="180" />
        <el-table-column label="IP审查" width="100">
          <template #default="{ row }">
            <IpAuditTag @click="openIpAudit(row)" />
          </template>
        </el-table-column>
        <el-table-column label="当前状态" width="110">
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.current_loan_status)">{{ getStatusText(row.current_loan_status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="黑名单" width="100">
          <template #default="{ row }">
            <el-tag :type="row.blacklist_hit ? 'danger' : 'success'">{{ row.blacklist_hit ? '命中' : '未命中' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="风控报告" width="140">
          <template #default="{ row }">
            <el-button link type="primary" @click="openRiskReport(row)">查询</el-button>
          </template>
        </el-table-column>
        <el-table-column label="风险管理" width="220">
          <template #default="{ row }">
            <el-button v-if="!row.blacklist_hit" link type="danger" @click="handleBlacklist(row)">一键拉黑</el-button>
            <el-button v-else link type="primary" @click="handleRemoveBlacklist(row)">移出黑名单</el-button>
            <el-button
              v-if="row.location_risk_blocked && row.can_unlock_location_risk"
              link
              type="warning"
              @click="handleUnlockLocationRisk(row)"
            >
              解除位置风控
            </el-button>
          </template>
        </el-table-column>
        <el-table-column label="人脸状态" width="110">
          <template #default="{ row }">
            {{ row.face_auth_status || '--' }}
          </template>
        </el-table-column>
        <el-table-column label="来源渠道" min-width="140">
          <template #default="{ row }">
            <div>{{ row.source_channel_sales_name || '--' }}</div>
            <div class="sub-text">{{ row.source_channel_name ? `/${row.source_channel_name}` : '未绑定渠道' }}</div>
          </template>
        </el-table-column>
        <el-table-column label="资料提交" min-width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.application_submitted_at) }}
          </template>
        </el-table-column>
        <el-table-column :label="dealColumnConfig.timeLabel" min-width="160">
          <template #default="{ row }">
            {{ formatDateTime(row[dealColumnConfig.timeKey]) }}
          </template>
        </el-table-column>
        <el-table-column :label="dealColumnConfig.amountLabel" min-width="140">
          <template #default="{ row }">
            {{ formatCurrency(row[dealColumnConfig.amountKey]) }}
          </template>
        </el-table-column>
        <el-table-column label="最近登录" min-width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.last_login_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDrawer(row)">查看档案</el-button>
            <el-button v-if="!isBusinessConsultant" link type="warning" @click="openResetDialog(row)">重置密码</el-button>
            <el-button
              v-if="row.current_loan_status === 'CARD_REJECTED'"
              link
              type="primary"
              @click="handleReissue(row)"
            >
              二次发卡
            </el-button>
            <el-button
              v-if="row.current_loan_status === 'CARD_REJECTED'"
              link
              type="warning"
              @click="handleCloseReissue(row)"
            >
              退回待下单
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap">
        <el-pagination
          background
          layout="total, prev, pager, next"
          :total="total"
          :page-size="filters.size"
          :current-page="filters.page"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <el-drawer v-model="drawerVisible" size="1080px" title="用户档案详情" destroy-on-close>
      <div v-if="detail" class="identity-drawer-layout">
        <IdentityImagePanel :row="detail" />
        <div class="detail-stack">
        <section class="detail-card">
          <h3>实名资料</h3>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="姓名">{{ detail.name || '--' }}</el-descriptions-item>
            <el-descriptions-item label="手机号">{{ detail.phone }}</el-descriptions-item>
            <el-descriptions-item label="身份证号">{{ detail.id_card_num || '--' }}</el-descriptions-item>
            <el-descriptions-item label="人脸状态">{{ detail.face_auth_status || '--' }}</el-descriptions-item>
            <el-descriptions-item label="住址" :span="2">{{ detail.id_address || '--' }}</el-descriptions-item>
            <el-descriptions-item label="有效期" :span="2">{{ detail.id_expiry || '--' }}</el-descriptions-item>
          </el-descriptions>
        </section>

        <section class="detail-card" v-if="!isBusinessConsultant">
          <h3>渠道归因</h3>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="业务员">{{ detail.source_channel_sales_name || '--' }}</el-descriptions-item>
            <el-descriptions-item label="渠道名称">{{ detail.source_channel_name ? `/${detail.source_channel_name}` : '--' }}</el-descriptions-item>
            <el-descriptions-item label="绑定时间">{{ formatDateTime(detail.channel_bound_at) }}</el-descriptions-item>
            <el-descriptions-item label="最近渠道访问">{{ formatDateTime(detail.last_channel_visit_at) }}</el-descriptions-item>
          </el-descriptions>
        </section>

        <section class="detail-card" v-if="!isBusinessConsultant">
          <h3>紧急联系人</h3>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="联系人一" :span="2">
              {{ detail.emergency_contact1_name || '--' }} / {{ detail.emergency_contact1_relation || '--' }} / {{ detail.emergency_contact1_phone || '--' }}
            </el-descriptions-item>
            <el-descriptions-item label="联系人二" :span="2">
              {{ detail.emergency_contact2_name || '--' }} / {{ detail.emergency_contact2_relation || '--' }} / {{ detail.emergency_contact2_phone || '--' }}
            </el-descriptions-item>
          </el-descriptions>
        </section>

        <section class="detail-card" v-if="!isBusinessConsultant">
          <h3>地理位置（授权）</h3>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="风控状态">
              <el-tag :type="detail.location_risk_blocked ? 'danger' : 'success'">
                {{ detail.location_risk_blocked ? '已锁定' : '正常' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="风控时间">{{ formatDateTime(detail.location_risk_at) }}</el-descriptions-item>
            <el-descriptions-item label="风控原因" :span="2">{{ detail.location_risk_reason || '--' }}</el-descriptions-item>
            <el-descriptions-item label="定位时间">{{ formatDateTime(detail.location_updated_at) }}</el-descriptions-item>
            <el-descriptions-item label="定位来源">{{ detail.location_source || '--' }}</el-descriptions-item>
            <el-descriptions-item label="纬度">{{ detail.location_latitude || '--' }}</el-descriptions-item>
            <el-descriptions-item label="经度">{{ detail.location_longitude || '--' }}</el-descriptions-item>
            <el-descriptions-item label="精度(米)">{{ detail.location_accuracy || '--' }}</el-descriptions-item>
            <el-descriptions-item label="省市区" :span="1">
              {{ [detail.location_province, detail.location_city, detail.location_district].filter(Boolean).join(' / ') || '--' }}
            </el-descriptions-item>
            <el-descriptions-item label="最小行政区划" :span="2">{{ detail.location_street || '--' }}</el-descriptions-item>
            <el-descriptions-item label="地址" :span="2">{{ detail.location_address || '--' }}</el-descriptions-item>
          </el-descriptions>
          <div v-if="detail.location_risk_blocked && detail.can_unlock_location_risk" class="location-risk-actions">
            <el-button type="warning" plain @click="handleUnlockLocationRisk(detail, true)">解除位置风控</el-button>
          </div>
        </section>

        <section class="detail-card" v-if="!isBusinessConsultant">
          <h3>最新订单概览</h3>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="订单状态">
              <el-tag :type="getStatusTagType(detail.latest_loan?.status)">{{ getStatusText(detail.latest_loan?.status) }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="授信额度">
              {{ detail.latest_loan ? formatCurrency(detail.latest_loan.credit_limit) : '--' }}
            </el-descriptions-item>
            <el-descriptions-item label="账期">{{ detail.latest_loan?.term_days ? `${detail.latest_loan.term_days} 天` : '--' }}</el-descriptions-item>
            <el-descriptions-item label="总费率">
              {{ detail.latest_loan ? `${(Number(detail.latest_loan.fee_rate || 0) * 100).toFixed(0)}%` : '--' }}
            </el-descriptions-item>
            <el-descriptions-item label="E卡面值">
              {{ detail.latest_loan ? formatCurrency(resolveEcardFaceValue(detail.latest_loan)) : '--' }}
            </el-descriptions-item>
            <el-descriptions-item label="权益金额">
              {{ detail.latest_loan ? formatCurrency(resolveRightsPrice(detail.latest_loan)) : '--' }}
            </el-descriptions-item>
            <el-descriptions-item label="信用支付金额">
              {{ detail.latest_loan ? formatCurrency(resolvePaymentAmount(detail.latest_loan)) : '--' }}
            </el-descriptions-item>
            <el-descriptions-item label="成交时间">{{ formatDateTime(detail.latest_loan?.disbursed_at) }}</el-descriptions-item>
            <el-descriptions-item label="还款日">{{ formatDateTime(detail.latest_loan?.due_date) }}</el-descriptions-item>
            <el-descriptions-item label="违约金">
              {{ detail.latest_loan ? formatCurrency(detail.latest_loan.penalty_amount) : '--' }}
            </el-descriptions-item>
            <el-descriptions-item label="总应还">
              {{ detail.latest_loan ? formatCurrency(detail.latest_loan.total_repayment_amount) : '--' }}
            </el-descriptions-item>
            <el-descriptions-item label="每期应还">
              {{ detail.latest_loan ? formatCurrency(detail.latest_loan.installment_amount) : '--' }}
            </el-descriptions-item>
            <el-descriptions-item label="审批备注">{{ detail.latest_loan?.review_note || '--' }}</el-descriptions-item>
            <el-descriptions-item label="风控报告">
              <el-button link type="primary" @click="openRiskReport(detail)">查看最近报告</el-button>
            </el-descriptions-item>
            <el-descriptions-item label="购销合同">
              <el-button
                link
                type="primary"
                :disabled="!detail.latest_loan?.id"
                @click="openPurchaseContract(detail.latest_loan)"
              >
                查看已签合同
              </el-button>
            </el-descriptions-item>
          </el-descriptions>
        </section>

        <section class="detail-card" v-if="!isBusinessConsultant">
          <h3>用户操作时间线</h3>
          <div class="timeline-list">
            <div v-for="event in detail.events" :key="event.id" class="timeline-item">
              <strong>{{ event.title }}</strong>
              <p>{{ event.detail || '无补充说明' }}</p>
              <div class="timeline-meta">{{ event.operator_name || event.actor_type }} · {{ formatDateTime(event.created_at) }}</div>
            </div>
          </div>
        </section>
        <section class="detail-card" v-if="isBusinessConsultant">
          <h3>成交情况</h3>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="订单状态">
              <el-tag :type="getStatusTagType(detail.first_deal_loan?.status)">{{ getStatusText(detail.first_deal_loan?.status) }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="授信额度">
              {{ detail.first_deal_loan ? formatCurrency(detail.first_deal_loan.credit_limit) : '--' }}
            </el-descriptions-item>
            <el-descriptions-item label="账期">{{ detail.first_deal_loan?.term_days ? `${detail.first_deal_loan.term_days} 天` : '--' }}</el-descriptions-item>
            <el-descriptions-item label="总费率">
              {{ detail.first_deal_loan ? `${(Number(detail.first_deal_loan.fee_rate || 0) * 100).toFixed(0)}%` : '--' }}
            </el-descriptions-item>
            <el-descriptions-item label="E卡面值">
              {{ detail.first_deal_loan ? formatCurrency(resolveEcardFaceValue(detail.first_deal_loan)) : '--' }}
            </el-descriptions-item>
            <el-descriptions-item label="权益金额">
              {{ detail.first_deal_loan ? formatCurrency(resolveRightsPrice(detail.first_deal_loan)) : '--' }}
            </el-descriptions-item>
            <el-descriptions-item label="信用支付金额">
              {{ detail.first_deal_loan ? formatCurrency(resolvePaymentAmount(detail.first_deal_loan)) : '--' }}
            </el-descriptions-item>
            <el-descriptions-item label="成交时间">{{ formatDateTime(detail.first_deal_loan?.disbursed_at) }}</el-descriptions-item>
            <el-descriptions-item label="还款日">{{ formatDateTime(detail.first_deal_loan?.due_date) }}</el-descriptions-item>
            <el-descriptions-item label="违约金">
              {{ detail.first_deal_loan ? formatCurrency(detail.first_deal_loan.penalty_amount) : '--' }}
            </el-descriptions-item>
            <el-descriptions-item label="总应还">
              {{ detail.first_deal_loan ? formatCurrency(detail.first_deal_loan.total_repayment_amount) : '--' }}
            </el-descriptions-item>
            <el-descriptions-item label="每期应还">
              {{ detail.first_deal_loan ? formatCurrency(detail.first_deal_loan.installment_amount) : '--' }}
            </el-descriptions-item>
            <el-descriptions-item label="审批备注">{{ detail.first_deal_loan?.review_note || '--' }}</el-descriptions-item>
          </el-descriptions>
        </section>
        </div>
      </div>
    </el-drawer>

    <el-drawer
      v-model="createDrawerVisible"
      size="460px"
      title="新增用户"
      destroy-on-close
      :close-on-click-modal="false"
      :close-on-press-escape="false"
    >
      <el-form label-position="top">
        <el-form-item label="手机号" required>
          <el-input v-model="createForm.phone" maxlength="11" placeholder="请输入11位手机号" />
        </el-form-item>
        <el-form-item label="密码" required>
          <el-input v-model="createForm.password" type="password" maxlength="50" show-password placeholder="请输入至少6位密码" />
        </el-form-item>
        <el-form-item label="来源渠道">
          <el-select
            v-model="createForm.sourceChannelId"
            filterable
            remote
            reserve-keyword
            placeholder="输入业务员或渠道名称搜索"
            :remote-method="searchChannels"
            :loading="channelLoading"
            style="width: 100%"
          >
            <el-option
              v-for="item in channelOptions"
              :key="item.id"
              :label="`${item.sales_name} / ${item.channel_name}`"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="creating" @click="submitCreateUser">确定新增</el-button>
        </el-form-item>
      </el-form>
    </el-drawer>

    <el-dialog v-model="resetDialogVisible" width="520px" title="重置密码" destroy-on-close>
      <el-descriptions :column="1" border>
        <el-descriptions-item label="用户ID">{{ resetTarget.id }}</el-descriptions-item>
        <el-descriptions-item label="手机号">{{ resetTarget.phone }}</el-descriptions-item>
        <el-descriptions-item label="姓名">{{ resetTarget.name || '--' }}</el-descriptions-item>
      </el-descriptions>
      <div class="reset-form">
        <el-input v-model="resetForm.password" type="password" show-password placeholder="请输入新密码（至少6位）" maxlength="50" />
        <el-input v-model="resetForm.confirmPassword" type="password" show-password placeholder="请再次输入新密码" maxlength="50" />
      </div>
      <template #footer>
        <el-button @click="resetDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="resetting" @click="submitResetPassword">确认重置</el-button>
      </template>
    </el-dialog>
    <el-dialog v-model="contractDialogVisible" width="760px" title="小荷包商品购销合同" append-to-body destroy-on-close>
      <div v-loading="contractLoading" class="admin-contract-view">
        <div v-if="purchaseContract" class="admin-contract-meta">
          <span>合同编号：{{ purchaseContract.signature_no || '--' }}</span>
          <span>订单号：{{ purchaseContract.order_no || '--' }}</span>
          <span>签署时间：{{ formatDateTime(purchaseContract.signed_at) }}</span>
        </div>
        <div v-if="purchaseContract" class="admin-contract-content" v-html="purchaseContract.contract_content"></div>
        <el-empty v-else-if="!contractLoading" description="暂无已签署购销合同" />
      </div>
    </el-dialog>
    <RiskReportDialog v-model="riskDialogVisible" :loading="riskLoading" :report="riskReport" />
    <CompositeRiskReportDialog
      v-model="compositeRiskDialogVisible"
      :loading="compositeRiskLoading"
      :report="compositeRiskReport"
    />
    <IpAuditDialog v-model="ipAuditVisible" :loading="ipAuditLoading" :items="ipAuditItems" />
  </div>
</template>

<script setup>
import { ElMessage, ElMessageBox } from 'element-plus';
import { onMounted, reactive, ref } from 'vue';
import IdentityImagePanel from '../components/IdentityImagePanel.vue';
import IpAuditDialog from '../components/IpAuditDialog.vue';
import IpAuditTag from '../components/IpAuditTag.vue';
import RiskReportDialog from '../components/RiskReportDialog.vue';
import CompositeRiskReportDialog from '../components/CompositeRiskReportDialog.vue';
import { blacklistUser, closeCardReissue, createFrontUser, getCompositeRiskReportByUser, getLoanPurchaseContract, getRiskReportByUser, getUserDetail, getUserIpAudit, getUserSourceChannels, getUsers, reissueCardLoan, removeBlacklistUser, resetFrontUserPassword, unlockUserLocationRisk } from '../api';
import { readStoredAdminProfile } from '../constants/adminPages';
import { formatCurrency, formatDateTime, getStatusTagType, getStatusText } from '../utils/format';
import { getDealColumnConfig } from '../utils/usersDealColumns';
import { buildUsersQueryParams } from '../utils/usersFilters';

const loading = ref(false);
const tableData = ref([]);
const total = ref(0);
const drawerVisible = ref(false);
const detail = ref(null);
const riskDialogVisible = ref(false);
const riskLoading = ref(false);
const riskReport = ref(null);
const compositeRiskDialogVisible = ref(false);
const compositeRiskLoading = ref(false);
const compositeRiskReport = ref(null);
const ipAuditVisible = ref(false);
const ipAuditLoading = ref(false);
const ipAuditItems = ref([]);
const contractDialogVisible = ref(false);
const contractLoading = ref(false);
const purchaseContract = ref(null);

const createDrawerVisible = ref(false);
const creating = ref(false);
const channelLoading = ref(false);
const channelOptions = ref([]);
const createForm = reactive({
  phone: '',
  password: '',
  sourceChannelId: null
});

const resetDialogVisible = ref(false);
const resetting = ref(false);
const resetTarget = reactive({ id: null, phone: '', name: '' });
const resetForm = reactive({ password: '', confirmPassword: '' });

const resolveEcardFaceValue = (row) => Number(row?.ecard_face_value || row?.credit_limit || 0);
const resolveRightsPrice = (row) => Number(row?.rights_price || row?.fee_amount || 0);
const resolvePaymentAmount = (row) => Number(
  row?.product_total_price
  || row?.total_repayment_amount
  || (resolveEcardFaceValue(row) + resolveRightsPrice(row))
  || 0
);

const filters = reactive({
  keyword: '',
  page: 1,
  size: 10,
  dealDateRange: [],
  locationRiskBlocked: 'ALL'
});

const adminProfile = readStoredAdminProfile() || {};
const isBusinessConsultant = Array.isArray(adminProfile.roles) && adminProfile.roles.length === 1 && adminProfile.roles[0] === 'BUSINESS_CONSULTANT';
const dealColumnConfig = getDealColumnConfig(isBusinessConsultant);

const fetchData = async () => {
  loading.value = true;
  try {
    const res = await getUsers(buildUsersQueryParams(filters, isBusinessConsultant));
    tableData.value = res.items || [];
    total.value = res.total || 0;
  } finally {
    loading.value = false;
  }
};

const resetFilters = () => {
  filters.keyword = '';
  filters.dealDateRange = [];
  filters.locationRiskBlocked = 'ALL';
  filters.page = 1;
  fetchData();
};

const handlePageChange = (page) => {
  filters.page = page;
  fetchData();
};

const openIpAudit = async (row) => {
  ipAuditVisible.value = true;
  ipAuditLoading.value = true;
  ipAuditItems.value = [];
  try {
    const result = await getUserIpAudit(row.id);
    ipAuditItems.value = result.items || [];
  } finally {
    ipAuditLoading.value = false;
  }
};

const openDrawer = async (row) => {
  detail.value = null;
  drawerVisible.value = true;
  detail.value = await getUserDetail(row.id);
};

const openRiskReport = async (row) => {
  const userId = row.user_id || row.id;
  if (!userId) {
    return;
  }
  riskDialogVisible.value = true;
  riskLoading.value = true;
  riskReport.value = null;
  try {
    riskReport.value = await getCompositeRiskReportByUser({ user_id: userId });
  } catch (error) {
    riskDialogVisible.value = false;
  } finally {
    riskLoading.value = false;
  }
};

const openCompositeRiskReport = async (row) => {
  const userId = row.user_id || row.id;
  if (!userId) {
    return;
  }
  compositeRiskDialogVisible.value = true;
  compositeRiskLoading.value = true;
  compositeRiskReport.value = null;
  try {
    compositeRiskReport.value = await getCompositeRiskReportByUser({ user_id: userId });
  } catch (error) {
    compositeRiskDialogVisible.value = false;
  } finally {
    compositeRiskLoading.value = false;
  }
};

const openPurchaseContract = async (loan) => {
  if (!loan?.id) {
    return;
  }
  contractDialogVisible.value = true;
  contractLoading.value = true;
  purchaseContract.value = null;
  try {
    purchaseContract.value = await getLoanPurchaseContract(loan.id);
  } catch (error) {
    contractDialogVisible.value = false;
  } finally {
    contractLoading.value = false;
  }
};

const handleBlacklist = async (row) => {
  try {
    await ElMessageBox.confirm(`确认将 ${row.name || row.phone} 加入黑名单？`, '一键拉黑', {
      type: 'warning',
      confirmButtonText: '确认拉黑',
      cancelButtonText: '取消'
    });
  } catch (error) {
    return;
  }
  await blacklistUser(row.id, { note: '后台一键拉黑' });
  ElMessage.success('已加入黑名单');
  fetchData();
};

const handleRemoveBlacklist = async (row) => {
  try {
    await ElMessageBox.confirm(`确认将 ${row.name || row.phone} 移出黑名单？`, '移出黑名单', {
      type: 'warning',
      confirmButtonText: '确认移出',
      cancelButtonText: '取消'
    });
  } catch (error) {
    return;
  }
  await removeBlacklistUser(row.id, { note: '后台手动移出黑名单' });
  ElMessage.success('已移出黑名单');
  fetchData();
};

const handleUnlockLocationRisk = async (row, refreshDetail = false) => {
  try {
    await ElMessageBox.confirm(`确认解除 ${row.name || row.phone} 的位置风控锁定？`, '解除位置风控', {
      type: 'warning',
      confirmButtonText: '确认解除',
      cancelButtonText: '取消'
    });
  } catch (error) {
    return;
  }
  await unlockUserLocationRisk(row.id);
  ElMessage.success('位置风控已解除，历史定位记录保持不变');
  await fetchData();
  if (refreshDetail && detail.value?.id === row.id) {
    detail.value = await getUserDetail(row.id);
  }
};

const handleReissue = async (row) => {
  if (!row.current_loan_id) {
    return;
  }
  await reissueCardLoan(row.current_loan_id);
  ElMessage.success('已进入待发卡列表');
  fetchData();
};

const handleCloseReissue = async (row) => {
  if (!row.current_loan_id) {
    return;
  }
  await closeCardReissue(row.current_loan_id);
  ElMessage.success('已退回待下单');
  fetchData();
};

const searchChannels = async (keyword = '') => {
  channelLoading.value = true;
  try {
    const res = await getUserSourceChannels({
      keyword: keyword || undefined,
      limit: 50
    });
    channelOptions.value = Array.isArray(res) ? res : [];
  } finally {
    channelLoading.value = false;
  }
};

const openCreateDrawer = async () => {
  createForm.phone = '';
  createForm.password = '';
  createForm.sourceChannelId = null;
  channelOptions.value = [];
  createDrawerVisible.value = true;
  await searchChannels('');
  if (channelOptions.value.length > 0) {
    createForm.sourceChannelId = channelOptions.value[0].id;
  }
};

const submitCreateUser = async () => {
  if (!/^\d{11}$/.test(createForm.phone)) {
    ElMessage.warning('请输入11位手机号');
    return;
  }
  if (!createForm.password || createForm.password.length < 6) {
    ElMessage.warning('请输入至少6位密码');
    return;
  }
  creating.value = true;
  try {
    const payload = {
      phone: createForm.phone,
      password: createForm.password
    };
    if (createForm.sourceChannelId) {
      payload.source_channel_id = createForm.sourceChannelId;
    }
    await createFrontUser(payload);
    ElMessage.success('新增用户成功');
    createDrawerVisible.value = false;
    filters.page = 1;
    await fetchData();
  } finally {
    creating.value = false;
  }
};

const openResetDialog = (row) => {
  if (isBusinessConsultant) {
    ElMessage.warning('业务顾问无权重置密码');
    return;
  }
  resetTarget.id = row.id;
  resetTarget.phone = row.phone;
  resetTarget.name = row.name;
  resetForm.password = '';
  resetForm.confirmPassword = '';
  resetDialogVisible.value = true;
};

const submitResetPassword = async () => {
  if (!resetForm.password || resetForm.password.length < 6) {
    ElMessage.warning('请输入至少6位新密码');
    return;
  }
  if (resetForm.password !== resetForm.confirmPassword) {
    ElMessage.warning('两次输入的新密码不一致');
    return;
  }

  resetting.value = true;
  try {
    await resetFrontUserPassword(resetTarget.id, { password: resetForm.password });
    ElMessage.success('重置密码成功');
    resetDialogVisible.value = false;
  } finally {
    resetting.value = false;
  }
};

onMounted(() => {
  fetchData();
});
</script>

<style scoped>
.sub-text {
  margin-top: 4px;
  color: #7f8da2;
  font-size: 12px;
}

.user-name-row {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.location-risk-actions {
  margin-top: 12px;
}

.pagination-wrap {
  margin-top: 18px;
  display: flex;
  justify-content: flex-end;
}

.reset-form {
  margin-top: 16px;
  display: grid;
  gap: 12px;
}

.admin-contract-view {
  min-height: 220px;
}

.admin-contract-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 16px;
  margin-bottom: 12px;
  color: #66788f;
  font-size: 13px;
}

.admin-contract-content {
  max-height: 62vh;
  overflow-y: auto;
  padding-right: 6px;
  font-size: 13px;
  line-height: 1.8;
  color: #16233a;
}

.admin-contract-content :deep(h1) {
  text-align: center;
  font-size: 20px;
}

.admin-contract-content :deep(h2) {
  margin-top: 18px;
  font-size: 15px;
}

.admin-contract-content :deep(.contract-summary) {
  width: 100%;
  border-collapse: collapse;
}

.admin-contract-content :deep(.contract-summary th),
.admin-contract-content :deep(.contract-summary td) {
  border: 1px solid #d8e3f2;
  padding: 8px;
  text-align: left;
}

.admin-contract-content :deep(.contract-summary th) {
  width: 30%;
  background: #f4f8ff;
}
</style>
