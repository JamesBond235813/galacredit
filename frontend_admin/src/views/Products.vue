<template>
  <div class="admin-page">
    <el-card class="panel-card filter-card">
      <el-form :inline="true" :model="filters">
        <el-form-item :label="t('search')">
          <el-input v-model="filters.keyword" :placeholder="t('productSearch')" clearable @keyup.enter="fetchData" />
        </el-form-item>
        <el-form-item :label="t('status')">
          <el-select v-model="filters.isActive" style="width: 140px">
            <el-option :label="t('all')" value="ALL" />
            <el-option :label="t('active')" :value="true" />
            <el-option :label="t('inactive')" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchData">{{ t('search') }}</el-button>
          <el-button @click="resetFilters">{{ t('reset') }}</el-button>
          <el-button type="success" @click="openDialog()">{{ t('addLoanProduct') }}</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="panel-card">
      <el-table v-loading="loading" :data="tableData" stripe highlight-current-row @current-change="handleCurrentChange">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" :label="t('loanProduct')" min-width="220" />
        <el-table-column :label="t('type')" width="120">
          <template #default="{ row }">
            <el-tag :type="row.product_type === 'CASH_LOAN' ? 'success' : 'info'">
              {{ row.product_type === 'CASH_LOAN' ? t('cashLoan') : t('legacy') }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="t('nominalPrincipal')" min-width="120">
          <template #default="{ row }">{{ formatCurrency(resolveNominalAmount(row)) }}</template>
        </el-table-column>
        <el-table-column :label="t('upfrontFee')" min-width="120">
          <template #default="{ row }">{{ formatCurrency(resolveUpfrontFee(row)) }}</template>
        </el-table-column>
        <el-table-column :label="t('momoDisbursement')" min-width="120">
          <template #default="{ row }">{{ formatCurrency(resolveDisbursementAmount(row)) }}</template>
        </el-table-column>
        <el-table-column :label="t('term')" min-width="180">
          <template #default="{ row }">{{ formatTerm(row) }}</template>
        </el-table-column>
        <el-table-column :label="t('installments')" min-width="170">
          <template #default="{ row }">{{ formatInstallments(row) }}</template>
        </el-table-column>
        <el-table-column :label="t('status')" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'">{{ row.is_active ? t('active') : t('inactive') }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="t('updatedAt')" min-width="170">
          <template #default="{ row }">{{ formatDateTime(row.updated_at) }}</template>
        </el-table-column>
        <el-table-column :label="t('actions')" width="170" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDialog(row)">{{ t('edit') }}</el-button>
            <el-button v-if="row.product_type !== 'CASH_LOAN'" link type="primary" @click="selectRightsConfig(row)">{{ t('legacyRights') }}</el-button>
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

    <el-card v-if="hasLegacyProducts" class="panel-card rights-config-card">
      <template #header>
        <div class="rights-config-head">
          <div>
            <strong>{{ t('legacyRightsConfig') }}</strong>
            <p>{{ t('legacyRightsHint') }}</p>
          </div>
          <el-tag v-if="rightsConfigProduct">{{ rightsConfigProduct.name }}</el-tag>
        </div>
      </template>

      <el-empty v-if="!rightsConfigProduct" :description="t('selectLegacyProductHint')" />
      <div v-else class="rights-config-layout">
        <el-form label-width="110px" class="rights-config-form">
          <el-form-item label="客服电话">
            <el-input v-model="rightsForm.contact_phone" placeholder="例如：13800138000" />
          </el-form-item>

          <section v-for="(section, sectionIndex) in rightsForm.sections" :key="sectionIndex" class="rights-config-section">
            <div class="rights-section-head">
              <strong>图片组 {{ sectionIndex + 1 }}</strong>
              <el-button v-if="rightsForm.sections.length > 1" link type="danger" @click="removeRightsSection(sectionIndex)">删除</el-button>
            </div>
            <el-form-item label="标题">
              <el-input v-model="section.title" placeholder="例如：图片组1（酒店内景，2张）" />
            </el-form-item>
            <el-form-item label="图片">
              <div class="rights-images-editor">
                <div v-for="(image, imageIndex) in section.images" :key="imageIndex" class="rights-image-row">
                  <div class="rights-upload-item">
                    <img v-if="image" class="rights-upload-preview" :src="image" alt="" />
                    <div v-else class="rights-upload-placeholder">未上传</div>
                    <el-upload
                      :show-file-list="false"
                      accept="image/*"
                      :http-request="(options) => uploadRightsImage(options, sectionIndex, imageIndex)"
                    >
                      <el-button size="small" type="primary" plain>{{ image ? '更换图片' : '上传图片' }}</el-button>
                    </el-upload>
                  </div>
                  <el-button link type="danger" @click="removeRightsImage(sectionIndex, imageIndex)">删除</el-button>
                </div>
                <el-button type="primary" plain @click="addRightsImage(sectionIndex)">新增图片</el-button>
              </div>
            </el-form-item>
            <el-form-item label="文字介绍">
              <el-input v-model="section.desc" type="textarea" :rows="2" placeholder="填写该图片组下方展示的介绍文案" />
            </el-form-item>
          </section>

          <el-form-item>
            <el-button @click="addRightsSection">新增图片组</el-button>
            <el-button type="primary" :loading="rightsSaving" @click="saveRightsConfig">保存权益配置</el-button>
          </el-form-item>
        </el-form>

        <div class="rights-preview">
          <h3>H5预览</h3>
          <div class="rights-preview-box">
            <div class="rights-preview-phone">客服电话：{{ rightsForm.contact_phone || '--' }}</div>
            <div v-for="(section, index) in normalizedRightsSections" :key="index" class="rights-preview-section">
              <h4>{{ section.title }}</h4>
              <div class="rights-preview-images">
                <img v-for="(image, imageIndex) in section.images" :key="imageIndex" :src="image" alt="" />
              </div>
              <p>{{ section.desc }}</p>
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <el-dialog v-model="dialogVisible" width="760px" :title="editingId ? t('edit') : t('addLoanProduct')" destroy-on-close>
      <el-form label-width="120px">
        <el-form-item :label="t('productName')">
          <el-input v-model="form.name" placeholder="例如：GalaCredit 7-Day Flex" />
        </el-form-item>
        <el-form-item :label="t('businessType')">
          <el-radio-group v-model="form.product_type">
            <el-radio value="CASH_LOAN">{{ t('cashLoan') }}</el-radio>
            <el-radio value="ECARD_RIGHTS">历史兼容·E卡+权益</el-radio>
            <el-radio value="RIGHTS_ONLY">历史兼容·纯权益</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="form.product_type !== 'CASH_LOAN'" label="E卡面值">
          <el-input-number v-model="form.ecard_face_value" :min="0" :step="100" :disabled="form.product_type === 'RIGHTS_ONLY'" />
        </el-form-item>
        <el-form-item v-if="form.product_type !== 'CASH_LOAN'" label="旅游权益金额">
          <el-input-number v-model="form.rights_price" :min="0" :step="100" />
        </el-form-item>
        <el-form-item v-if="form.product_type !== 'CASH_LOAN'" label="旅游权益标题">
          <el-input v-model="form.rights_title" placeholder="例如：韶关丹霞山2日旅游" />
        </el-form-item>
        <el-form-item v-if="form.product_type !== 'CASH_LOAN'" label="旅游权益说明">
          <el-input v-model="form.rights_desc" type="textarea" :rows="3" placeholder="填写酒店、门票、晚餐等权益内容" />
        </el-form-item>
        <el-form-item :label="t('nominalPrincipal')">
          <el-input-number v-model="form.nominal_loan_amount" :min="1" :step="100" />
        </el-form-item>
        <el-form-item :label="t('upfrontFeeRate')">
          <el-input-number v-model="form.upfront_fee_rate" :min="0" :max="1" :step="0.01" />
          <span class="inline-tip">40%填写0.4</span>
        </el-form-item>
        <el-form-item v-if="form.product_type === 'CASH_LOAN'" :label="t('feeTotal')">
          <strong>{{ formatCurrency(calculatedUpfrontFee) }}</strong>
          <span class="inline-tip">根据名义本金和上扣费用率自动计算</span>
        </el-form-item>
        <el-form-item v-if="form.product_type === 'CASH_LOAN'" :label="t('auditFee')">
          <el-input-number v-model="form.audit_fee" :min="0" :step="10" />
        </el-form-item>
        <el-form-item v-if="form.product_type === 'CASH_LOAN'" :label="t('riskControlFee')">
          <el-input-number v-model="form.risk_control_fee" :min="0" :step="10" />
        </el-form-item>
        <el-form-item v-if="form.product_type === 'CASH_LOAN'" :label="t('systemFee')">
          <el-input-number v-model="form.system_fee" :min="0" :step="10" />
        </el-form-item>
        <el-form-item v-if="form.product_type === 'CASH_LOAN'" :label="t('interest')">
          <el-input-number v-model="form.interest_fee" :min="0" :step="10" />
        </el-form-item>
        <el-form-item v-if="form.product_type === 'CASH_LOAN'" :label="t('feeBreakdownTotal')">
          <strong :class="{ 'amount-warning': !feeComponentsMatch }">{{ formatCurrency(feeComponentsTotal) }}</strong>
          <span class="inline-tip">必须与费用总额一致</span>
        </el-form-item>
        <el-form-item v-if="form.product_type === 'CASH_LOAN'" :label="t('expectedMomo')">
          <strong>{{ formatCurrency(calculatedDisbursementAmount) }}</strong>
        </el-form-item>
        <el-form-item :label="t('interestStartDay')">
          <el-input-number v-model="form.interest_start_day" :min="1" :max="364" :step="1" />
        </el-form-item>
        <el-form-item :label="t('dueDay')">
          <el-input-number v-model="form.repayment_due_day" :min="1" :max="364" :step="1" />
        </el-form-item>
        <el-form-item :label="t('installmentCount')">
          <el-input-number v-model="form.installment_count" :min="1" :max="24" :step="1" />
        </el-form-item>
        <el-form-item :label="t('installmentRatios')">
          <el-input v-model="form.installment_ratios_text" placeholder="例如：60,40 或 0.6,0.4" />
          <span class="inline-tip">比例合计必须为 100% 或 1</span>
        </el-form-item>
        <el-form-item :label="t('dailyOverdueFee')">
          <el-input-number v-model="form.daily_overdue_fee" :min="0" :step="1" />
        </el-form-item>
        <el-form-item :label="t('activeSwitch')">
          <el-switch v-model="form.is_active" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">{{ t('cancel') }}</el-button>
        <el-button type="primary" :loading="saving" @click="submit">{{ t('save') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from 'vue';
import { ElMessage } from 'element-plus';
import { createProduct, getProducts, updateProduct, uploadProductRightsImage } from '../api';
import { formatCurrency, formatDateTime } from '../utils/format';
import { adminLocale, t } from '../i18n/adminLocale';

const loading = ref(false);
const saving = ref(false);
const total = ref(0);
const tableData = ref([]);
const dialogVisible = ref(false);
const editingId = ref(null);
const rightsConfigProduct = ref(null);
const rightsSaving = ref(false);

const filters = reactive({
  keyword: '',
  isActive: 'ALL',
  page: 1,
  size: 10
});

const form = reactive({
  name: '',
  ecard_face_value: 1000,
  rights_price: 600,
  rights_title: '韶关丹霞山旅游权益',
  rights_desc: '',
  term_days: 7,
  repayment_due_day: 7,
  payment_amount: 1600,
  nominal_loan_amount: 1000,
  upfront_fee_rate: 0.4,
  audit_fee: 50,
  risk_control_fee: 100,
  system_fee: 50,
  interest_fee: 200,
  interest_start_day: 1,
  installment_count: 1,
  installment_ratios_text: '1',
  daily_overdue_fee: 10,
  product_type: 'CASH_LOAN',
  is_active: true
});

const hasLegacyProducts = computed(() => tableData.value.some((item) => item.product_type !== 'CASH_LOAN'));
const calculatedUpfrontFee = computed(() => Number(form.nominal_loan_amount || 0) * Number(form.upfront_fee_rate || 0));
const feeComponentsTotal = computed(() => (
  Number(form.audit_fee || 0)
  + Number(form.risk_control_fee || 0)
  + Number(form.system_fee || 0)
  + Number(form.interest_fee || 0)
));
const feeComponentsMatch = computed(() => Math.abs(feeComponentsTotal.value - calculatedUpfrontFee.value) < 0.01);
const calculatedDisbursementAmount = computed(() => Math.max(Number(form.nominal_loan_amount || 0) - calculatedUpfrontFee.value, 0));

const resolveNominalAmount = (row) => Number(row?.nominal_loan_amount || row?.payment_amount || row?.ecard_face_value || 0);
const resolveUpfrontFee = (row) => {
  const nominal = resolveNominalAmount(row);
  return Number(row?.upfront_fee_amount || row?.fee_amount || nominal * Number(row?.upfront_fee_rate || 0));
};
const resolveDisbursementAmount = (row) => Number(row?.actual_disbursement_amount || Math.max(resolveNominalAmount(row) - resolveUpfrontFee(row), 0));
const formatRatios = (ratios = []) => (ratios.length ? ratios.map((item) => `${Number(item) <= 1 ? Number(item) * 100 : Number(item)}%`).join(' / ') : '--');
const formatTerm = (row) => adminLocale.value === 'en-GH'
  ? `Interest day ${row.interest_start_day || 1} · Due day ${row.repayment_due_day || row.term_days}`
  : `第 ${row.interest_start_day || 1} 天起息 · 第 ${row.repayment_due_day || row.term_days} 天到期`;
const formatInstallments = (row) => adminLocale.value === 'en-GH'
  ? `${row.installment_count || 1} installment(s) · ${formatRatios(row.installment_ratios)}`
  : `${row.installment_count || 1} 期 · ${formatRatios(row.installment_ratios)}`;

const rightsForm = reactive({
  contact_phone: '13800138000',
  sections: []
});

const defaultRightsSections = () => [
  {
    title: '图片组1（酒店内景，2张）',
    images: [
      'https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=900&q=80',
      'https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=900&q=80'
    ],
    desc: '酒店介绍：入住舒适酒店客房，周边交通便利，适合丹霞山行程入住与休整。'
  },
  {
    title: '图片组2（旅游景点照片，2张）',
    images: [
      'https://images.unsplash.com/photo-1469474968028-56623f02e42e?auto=format&fit=crop&w=900&q=80',
      'https://images.unsplash.com/photo-1501785888041-af3ef285b470?auto=format&fit=crop&w=900&q=80'
    ],
    desc: '景点介绍：丹霞地貌自然景观丰富，行程包含核心观景区域游览与打卡路线建议。'
  },
  {
    title: '图片组3（餐饮介绍）',
    images: ['https://images.unsplash.com/photo-1414235077428-338989a2e8c0?auto=format&fit=crop&w=1200&q=80'],
    desc: '餐饮简介：安排当地特色风味餐，覆盖正餐场景，具体菜单以实际安排为准。'
  }
];

const normalizeRightsDetail = (detail = null) => {
  const sections = Array.isArray(detail?.sections) && detail.sections.length ? detail.sections : defaultRightsSections();
  return {
    contact_phone: detail?.contact_phone || '13800138000',
    sections: sections.map((section) => ({
      title: section?.title || '',
      images: Array.isArray(section?.images) && section.images.length ? [...section.images] : [''],
      desc: section?.desc || ''
    }))
  };
};

const fillRightsForm = (detail) => {
  const normalized = normalizeRightsDetail(detail);
  rightsForm.contact_phone = normalized.contact_phone;
  rightsForm.sections.splice(0, rightsForm.sections.length, ...normalized.sections);
};

const normalizedRightsSections = computed(() =>
  rightsForm.sections.map((section) => ({
    title: section.title || '权益图片',
    images: (section.images || []).filter(Boolean),
    desc: section.desc || ''
  })).filter((section) => section.title || section.images.length || section.desc)
);

const fetchData = async () => {
  loading.value = true;
  try {
    const params = {
      keyword: filters.keyword || undefined,
      skip: (filters.page - 1) * filters.size,
      limit: filters.size
    };
    if (filters.isActive !== 'ALL') {
      params.is_active = filters.isActive;
    }
    const res = await getProducts(params);
    tableData.value = res.items || [];
    total.value = res.total || 0;
    if (rightsConfigProduct.value) {
      const latest = tableData.value.find((item) => item.id === rightsConfigProduct.value.id);
      if (latest) {
        rightsConfigProduct.value = latest;
        fillRightsForm(latest.rights_detail);
      }
    }
  } finally {
    loading.value = false;
  }
};

const handleCurrentChange = (row) => {
  if (row) {
    selectRightsConfig(row);
  }
};

const selectRightsConfig = (row) => {
  rightsConfigProduct.value = row;
  fillRightsForm(row.rights_detail);
};

const addRightsSection = () => {
  rightsForm.sections.push({ title: '', images: [''], desc: '' });
};

const removeRightsSection = (index) => {
  rightsForm.sections.splice(index, 1);
};

const addRightsImage = (sectionIndex) => {
  rightsForm.sections[sectionIndex].images.push('');
};

const uploadRightsImage = async (options, sectionIndex, imageIndex) => {
  const file = options.file;
  if (!file || !file.type?.startsWith('image/')) {
    ElMessage.warning('请上传图片文件');
    options.onError?.(new Error('invalid image'));
    return;
  }
  if (file.size > 8 * 1024 * 1024) {
    ElMessage.warning('图片不能超过8MB');
    options.onError?.(new Error('image too large'));
    return;
  }
  try {
    const formData = new FormData();
    formData.append('file', file);
    const result = await uploadProductRightsImage(formData);
    rightsForm.sections[sectionIndex].images[imageIndex] = result.url;
    options.onSuccess?.(result);
    ElMessage.success('图片已上传');
  } catch (error) {
    options.onError?.(error);
  }
};

const removeRightsImage = (sectionIndex, imageIndex) => {
  const images = rightsForm.sections[sectionIndex].images;
  images.splice(imageIndex, 1);
  if (!images.length) {
    images.push('');
  }
};

const resetFilters = () => {
  filters.keyword = '';
  filters.isActive = 'ALL';
  filters.page = 1;
  fetchData();
};

const handlePageChange = (page) => {
  filters.page = page;
  fetchData();
};

const resetForm = () => {
  form.name = '';
  form.ecard_face_value = 1000;
  form.rights_price = 600;
  form.rights_title = '韶关丹霞山旅游权益';
  form.rights_desc = '';
  form.term_days = 7;
  form.repayment_due_day = 7;
  form.payment_amount = 1600;
  form.nominal_loan_amount = 1000;
  form.upfront_fee_rate = 0.4;
  form.audit_fee = 50;
  form.risk_control_fee = 100;
  form.system_fee = 50;
  form.interest_fee = 200;
  form.interest_start_day = 1;
  form.installment_count = 1;
  form.installment_ratios_text = '1';
  form.daily_overdue_fee = 10;
  form.product_type = 'CASH_LOAN';
  form.is_active = true;
};

const openDialog = (row = null) => {
  if (!row) {
    editingId.value = null;
    resetForm();
    dialogVisible.value = true;
    return;
  }

  editingId.value = row.id;
  form.name = row.name;
  form.ecard_face_value = Number(row.ecard_face_value || 0);
  form.rights_price = Number(row.rights_price || 0);
  form.rights_title = row.rights_title || '';
  form.rights_desc = row.rights_desc || '';
  form.term_days = Number(row.term_days || 7);
  form.repayment_due_day = Number(row.repayment_due_day || row.term_days || 7);
  form.payment_amount = Number(row.payment_amount || 0);
  form.nominal_loan_amount = Number(row.nominal_loan_amount || row.payment_amount || 0);
  form.upfront_fee_rate = Number(row.upfront_fee_rate ?? 0.4);
  form.audit_fee = Number(row.fee_components?.audit_fee ?? 0);
  form.risk_control_fee = Number(row.fee_components?.risk_control_fee ?? 0);
  form.system_fee = Number(row.fee_components?.system_fee ?? 0);
  form.interest_fee = Number(row.fee_components?.interest_fee ?? 0);
  form.interest_start_day = Number(row.interest_start_day || 1);
  form.installment_count = Number(row.installment_count || 1);
  form.installment_ratios_text = (row.installment_ratios || [1]).join(',');
  form.daily_overdue_fee = Number(row.daily_overdue_fee ?? 10);
  form.product_type = row.product_type || 'CASH_LOAN';
  form.is_active = Boolean(row.is_active);
  dialogVisible.value = true;
};

const submit = async () => {
  if (!form.name.trim()) {
    ElMessage.warning('请填写贷款产品名称');
    return;
  }
  if (form.product_type !== 'CASH_LOAN' && !form.rights_title.trim()) {
    ElMessage.warning('历史兼容产品请填写权益标题');
    return;
  }
  if (form.product_type === 'ECARD_RIGHTS' && Number(form.ecard_face_value) <= 0) {
    ElMessage.warning('历史 E-card 产品请填写卡面值');
    return;
  }
  if (form.product_type === 'RIGHTS_ONLY') {
    form.ecard_face_value = 0;
  }
  if (Number(form.nominal_loan_amount) <= 0 || Number(form.upfront_fee_rate) < 0 || Number(form.upfront_fee_rate) > 1) {
    ElMessage.warning('请检查金额配置');
    return;
  }
  const rawRatios = form.installment_ratios_text.split(',').map((item) => Number(item.trim())).filter((item) => Number.isFinite(item));
  const ratioTotal = rawRatios.reduce((sum, item) => sum + item, 0);
  if (rawRatios.length !== Number(form.installment_count) || (Math.abs(ratioTotal - 1) > 0.001 && Math.abs(ratioTotal - 100) > 0.001)) {
    ElMessage.warning('分期期数与每期比例不匹配，比例合计必须为1或100');
    return;
  }
  if (Number(form.repayment_due_day) < 1) {
    ElMessage.warning('到期日不能少于1天');
    return;
  }
  if (form.product_type === 'CASH_LOAN' && !feeComponentsMatch.value) {
    ElMessage.warning('费用分项合计必须等于上扣费用总额');
    return;
  }

  saving.value = true;
  try {
    const payload = {
      name: form.name.trim(),
      ecard_face_value: Number(form.ecard_face_value),
      rights_price: Number(form.rights_price),
      rights_title: form.rights_title.trim(),
      rights_desc: form.rights_desc.trim() || undefined,
      term_days: Number(form.repayment_due_day),
      payment_amount: Number(form.nominal_loan_amount),
      nominal_loan_amount: Number(form.nominal_loan_amount),
      upfront_fee_rate: Number(form.upfront_fee_rate),
      fee_components: {
        audit_fee: Number(form.audit_fee || 0),
        risk_control_fee: Number(form.risk_control_fee || 0),
        system_fee: Number(form.system_fee || 0),
        interest_fee: Number(form.interest_fee || 0)
      },
      interest_start_day: Number(form.interest_start_day),
      repayment_due_day: Number(form.repayment_due_day),
      installment_count: Number(form.installment_count),
      installment_ratios: rawRatios.map((item) => (item > 1 ? item / 100 : item)),
      daily_overdue_fee: Number(form.daily_overdue_fee),
      product_type: form.product_type,
      is_active: form.is_active
    };
    if (editingId.value) {
      await updateProduct(editingId.value, payload);
      ElMessage.success(t('productUpdated'));
    } else {
      await createProduct(payload);
      ElMessage.success(t('productCreated'));
    }
    dialogVisible.value = false;
    fetchData();
  } finally {
    saving.value = false;
  }
};

const saveRightsConfig = async () => {
  if (!rightsConfigProduct.value?.id) {
    return;
  }
  const payload = {
    rights_detail: {
      contact_phone: rightsForm.contact_phone.trim(),
      sections: normalizedRightsSections.value
    }
  };
  if (!payload.rights_detail.contact_phone) {
    ElMessage.warning('请填写客服电话');
    return;
  }
  if (!payload.rights_detail.sections.length) {
    ElMessage.warning('请至少配置一个图片组');
    return;
  }
  rightsSaving.value = true;
  try {
    await updateProduct(rightsConfigProduct.value.id, payload);
    ElMessage.success('权益详情已保存');
    await fetchData();
  } finally {
    rightsSaving.value = false;
  }
};

fetchData();
</script>

<style scoped>
.pagination-wrap {
  margin-top: 18px;
  display: flex;
  justify-content: flex-end;
}

.inline-tip {
  margin-left: 10px;
  color: #7f8da2;
  font-size: 12px;
}

.amount-warning {
  color: #d97706;
}

.rights-config-card {
  min-height: 360px;
}

.rights-config-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.rights-config-head p {
  margin: 6px 0 0;
  color: #7f8da2;
  font-size: 12px;
}

.rights-config-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 360px;
  gap: 20px;
  align-items: start;
}

.rights-config-form {
  max-width: 980px;
}

.rights-config-section {
  margin-bottom: 16px;
  padding: 14px 14px 2px;
  border: 1px solid #e5edf7;
  border-radius: 8px;
  background: #fbfdff;
}

.rights-section-head {
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.rights-images-editor {
  width: 100%;
  display: grid;
  gap: 8px;
}

.rights-image-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 48px;
  gap: 8px;
  align-items: center;
}

.rights-upload-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.rights-upload-preview,
.rights-upload-placeholder {
  width: 128px;
  height: 72px;
  border-radius: 8px;
  border: 1px solid #dce7f5;
  background: #f5f8fc;
  object-fit: cover;
}

.rights-upload-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #9aa9bb;
  font-size: 12px;
}

.rights-preview h3 {
  margin: 0 0 10px;
  font-size: 15px;
  color: #16233a;
}

.rights-preview-box {
  padding: 14px;
  border: 1px solid #e5edf7;
  border-radius: 8px;
  background: #ffffff;
}

.rights-preview-phone {
  padding: 10px 12px;
  border-radius: 8px;
  background: #edf5ff;
  color: #23344f;
}

.rights-preview-section {
  margin-top: 14px;
}

.rights-preview-section h4 {
  margin: 0 0 8px;
  font-size: 13px;
  color: #23344f;
}

.rights-preview-images {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.rights-preview-images img {
  width: 100%;
  height: 76px;
  object-fit: cover;
  border-radius: 8px;
  border: 1px solid #e5edf7;
  background: #f5f7fb;
}

.rights-preview-section p {
  margin: 8px 0 0;
  color: #66788f;
  font-size: 12px;
  line-height: 1.6;
}

@media (max-width: 1180px) {
  .rights-config-layout {
    grid-template-columns: 1fr;
  }
}
</style>
