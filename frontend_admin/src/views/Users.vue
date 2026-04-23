<template>
  <div class="admin-page">
    <el-card class="panel-card filter-card">
      <el-form :inline="true" :model="filters">
        <el-form-item label="搜索">
          <el-input v-model="filters.keyword" placeholder="手机号 / 姓名 / 身份证号" clearable @keyup.enter="fetchData" />
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
            <div>{{ row.name || '未实名' }}</div>
            <div class="sub-text">{{ row.phone }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="id_card_num" label="身份证号" min-width="180" />
        <el-table-column label="当前状态" width="110">
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.current_loan_status)">{{ getStatusText(row.current_loan_status) }}</el-tag>
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
        <el-table-column label="最近登录" min-width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.last_login_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="110" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDrawer(row)">查看档案</el-button>
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

    <el-drawer v-model="drawerVisible" size="680px" title="用户档案详情" destroy-on-close>
      <div v-if="detail" class="detail-stack">
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

        <section class="detail-card">
          <h3>渠道归因</h3>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="业务员">{{ detail.source_channel_sales_name || '--' }}</el-descriptions-item>
            <el-descriptions-item label="渠道名称">{{ detail.source_channel_name ? `/${detail.source_channel_name}` : '--' }}</el-descriptions-item>
            <el-descriptions-item label="绑定时间">{{ formatDateTime(detail.channel_bound_at) }}</el-descriptions-item>
            <el-descriptions-item label="最近渠道访问">{{ formatDateTime(detail.last_channel_visit_at) }}</el-descriptions-item>
          </el-descriptions>
        </section>

        <section class="detail-card">
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

        <section class="detail-card">
          <h3>地理位置（授权）</h3>
          <el-descriptions :column="2" border>
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
        </section>

        <section class="detail-card">
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
          </el-descriptions>
        </section>

        <section class="detail-card">
          <h3>用户操作时间线</h3>
          <div class="timeline-list">
            <div v-for="event in detail.events" :key="event.id" class="timeline-item">
              <strong>{{ event.title }}</strong>
              <p>{{ event.detail || '无补充说明' }}</p>
              <div class="timeline-meta">{{ event.operator_name || event.actor_type }} · {{ formatDateTime(event.created_at) }}</div>
            </div>
          </div>
        </section>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue';
import { getUserDetail, getUsers } from '../api';
import { formatCurrency, formatDateTime, getStatusTagType, getStatusText } from '../utils/format';

const loading = ref(false);
const tableData = ref([]);
const total = ref(0);
const drawerVisible = ref(false);
const detail = ref(null);

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
  size: 10
});

const fetchData = async () => {
  loading.value = true;
  try {
    const res = await getUsers({
      keyword: filters.keyword || undefined,
      skip: (filters.page - 1) * filters.size,
      limit: filters.size
    });
    tableData.value = res.items || [];
    total.value = res.total || 0;
  } finally {
    loading.value = false;
  }
};

const resetFilters = () => {
  filters.keyword = '';
  filters.page = 1;
  fetchData();
};

const handlePageChange = (page) => {
  filters.page = page;
  fetchData();
};

const openDrawer = async (row) => {
  drawerVisible.value = true;
  detail.value = await getUserDetail(row.id);
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

.pagination-wrap {
  margin-top: 18px;
  display: flex;
  justify-content: flex-end;
}
</style>
