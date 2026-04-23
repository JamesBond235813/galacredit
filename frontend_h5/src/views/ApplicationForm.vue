<template>
  <div class="page-shell application-page">
    <van-nav-bar left-arrow title="补充资料" @click-left="router.back()" />

    <div class="page-inner application-inner">
      <header class="application-hero">
        <span class="hero-chip">流程 3 / 4</span>
        <h1 class="hero-title">补充联系人信息</h1>
        <p class="hero-desc">请填写两位紧急联系人信息，提交后系统自动进入审核。</p>
      </header>

      <div class="contact-grid">
        <article
          v-for="(contact, index) in contacts"
          :key="contact.key"
          class="page-card contact-card"
          :class="{ 'contact-card-active': relationPickerIndex === index }"
        >
          <div class="contact-head">
            <span class="contact-index">联系人 {{ index + 1 }}</span>
          </div>

          <div class="contact-fields">
            <label class="field-block contact-field">
              <input
                v-model.trim="contact.name"
                type="text"
                maxlength="12"
                placeholder="请输入联系人姓名"
              />
            </label>

            <label class="field-block contact-field">
              <div class="relation-field" @click.stop>
                <button
                  type="button"
                  class="relation-trigger"
                  :class="{ 'relation-trigger-empty': !contact.relation }"
                  @click="toggleRelationPicker(index)"
                >
                  <span>{{ contact.relation || '请选择与本人关系' }}</span>
                  <van-icon
                    name="arrow-down"
                    class="relation-arrow"
                    :class="{ 'relation-arrow-open': relationPickerIndex === index }"
                  />
                </button>

                <transition name="relation-drop">
                  <div
                    v-if="relationPickerIndex === index"
                    class="relation-menu"
                    :class="{ 'relation-menu-upward': index === contacts.length - 1 }"
                  >
                    <button
                      v-for="item in relationOptions"
                      :key="item"
                      type="button"
                      class="relation-option"
                      :class="{ 'relation-option-active': contact.relation === item }"
                      @click="selectRelation(index, item)"
                    >
                      {{ item }}
                    </button>
                  </div>
                </transition>
              </div>
            </label>

            <label class="field-block contact-field">
              <input
                :value="contact.phone"
                type="tel"
                inputmode="numeric"
                maxlength="11"
                placeholder="请输入联系人手机号"
                @input="onContactPhoneInput(index, $event)"
              />
            </label>
          </div>
        </article>
      </div>

      <p class="submit-note">提交后预计几分钟内返回审核结果，请保持手机畅通。</p>

      <van-button
        block
        type="primary"
        class="primary-action submit-btn"
        :loading="submitting"
        @click="submitForm"
      >
        提交审核
      </van-button>
    </div>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, reactive, ref } from 'vue';
import { useRouter } from 'vue-router';
import { closeToast, showToast } from 'vant';
import { getLoanStatus, getUserInfo, submitApplication } from '../api';

const router = useRouter();
const submitting = ref(false);

const contacts = reactive([
  { key: 'primary', name: '', phone: '', relation: '' },
  { key: 'secondary', name: '', phone: '', relation: '' }
]);

const relationOptions = ['父母', '子女', '兄弟姐妹', '同事', '朋友'];
const relationPickerIndex = ref(null);

const normalizePhone = (value) => value.replace(/\D/g, '').slice(0, 11);

const onContactPhoneInput = (index, event) => {
  contacts[index].phone = normalizePhone(event.target.value || '');
};

const toggleRelationPicker = (index) => {
  relationPickerIndex.value = relationPickerIndex.value === index ? null : index;
};

const selectRelation = (index, value) => {
  contacts[index].relation = value;
  relationPickerIndex.value = null;
};

const closeRelationPicker = () => {
  relationPickerIndex.value = null;
};

const shouldRedirectByLoanStatus = (status) => {
  if (status === 'REVIEWING' || status === 'APPROVED') {
    router.replace('/review');
    return true;
  }
  if (status === 'WITHDRAWING' || status === 'DISBURSED' || status === 'OVERDUE') {
    router.replace('/bill');
    return true;
  }
  return false;
};

const checkLoanFlowGuard = async () => {
  try {
    const loan = await getLoanStatus();
    return shouldRedirectByLoanStatus(loan?.status);
  } catch (error) {
    return false;
  }
};

const loadCurrentUserData = async () => {
  try {
    const user = await getUserInfo();
    contacts[0].name = user.emergency_contact1_name || '';
    contacts[0].relation = user.emergency_contact1_relation || '';
    contacts[0].phone = user.emergency_contact1_phone || '';
    contacts[1].name = user.emergency_contact2_name || '';
    contacts[1].relation = user.emergency_contact2_relation || '';
    contacts[1].phone = user.emergency_contact2_phone || '';
  } catch (error) {
    // handled by interceptor
  }
};

const validateForm = () => {
  for (let index = 0; index < contacts.length; index += 1) {
    const contact = contacts[index];
    if (!contact.name.trim()) {
      showToast(`请填写联系人 ${index + 1} 姓名`);
      return false;
    }
    if (!/^\d{11}$/.test(contact.phone.trim())) {
      showToast(`请输入联系人 ${index + 1} 的11位手机号`);
      return false;
    }
    if (!contact.relation.trim()) {
      showToast(`请填写联系人 ${index + 1} 与您的关系`);
      return false;
    }
  }
  if (contacts[0].phone.trim() === contacts[1].phone.trim()) {
    showToast('两位紧急联系人手机号不能相同');
    return false;
  }
  return true;
};

const submitForm = async () => {
  if (submitting.value || !validateForm()) {
    return;
  }

  submitting.value = true;
  try {
    showToast({ type: 'loading', duration: 0, message: '资料提交中...' });
    await submitApplication({
      emergency_contacts: contacts.map((contact) => ({
        name: contact.name.trim(),
        relation: contact.relation.trim(),
        phone: contact.phone.trim()
      }))
    });
    closeToast();
    showToast('资料已提交');
    router.replace('/review');
  } catch (error) {
    closeToast();
  } finally {
    submitting.value = false;
  }
};

onMounted(async () => {
  document.addEventListener('click', closeRelationPicker);
  const redirected = await checkLoanFlowGuard();
  if (!redirected) {
    loadCurrentUserData();
  }
});

onBeforeUnmount(() => {
  document.removeEventListener('click', closeRelationPicker);
});
</script>

<style scoped>
.application-page {
  min-height: 100vh;
}

.application-inner {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 10px;
  padding: calc(env(safe-area-inset-top, 0px) + 6px) 12px 10px;
}

.application-hero {
  width: 100%;
}

.hero-chip {
  display: inline-flex;
  align-items: center;
  min-height: 22px;
  padding: 0 10px;
  border-radius: 999px;
  background: rgba(47, 126, 247, 0.1);
  color: var(--app-primary-deep);
  font-size: 10px;
  font-weight: 700;
}

.hero-title {
  margin: 8px 0 0;
  font-size: 19px;
  line-height: 1.16;
  font-weight: 800;
  color: var(--app-text);
}

.hero-desc {
  margin: 5px 0 0;
  font-size: 11px;
  line-height: 1.4;
  color: var(--app-text-soft);
}

.contact-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 8px;
}

.contact-card {
  position: relative;
  z-index: 1;
  overflow: visible;
  padding: 10px 12px;
}

.contact-card-active {
  z-index: 12;
}

.contact-head {
  margin-bottom: 8px;
}

.contact-index {
  display: inline-flex;
  align-items: center;
  min-height: 21px;
  padding: 0 8px;
  border-radius: 999px;
  background: rgba(47, 126, 247, 0.08);
  color: var(--app-primary-deep);
  font-size: 10px;
  font-weight: 700;
}

.contact-fields {
  display: grid;
  grid-template-columns: 1fr;
  gap: 5px;
}

.field-block {
  display: block;
  padding: 7px 10px;
  border-radius: 12px;
  background: #f7faff;
  border: 1px solid #e8eef8;
}

.contact-field {
  min-height: 38px;
  border-radius: 12px;
  display: flex;
  align-items: center;
}

.field-block input {
  width: 100%;
  height: 18px;
  padding: 0;
  border: 0;
  outline: none;
  background: transparent;
  color: var(--app-text);
  font-size: 12px;
}

.relation-field {
  position: relative;
  width: 100%;
}

.relation-trigger {
  width: 100%;
  min-height: 18px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  color: var(--app-text);
  font-size: 12px;
  line-height: 1.25;
}

.relation-trigger-empty {
  color: #b2bed0;
}

.relation-arrow {
  flex-shrink: 0;
  font-size: 12px;
  color: #92a4c0;
  transition: transform 0.2s ease, color 0.2s ease;
}

.relation-arrow-open {
  transform: rotate(180deg);
  color: var(--app-primary-deep);
}

.relation-menu {
  position: absolute;
  left: 0;
  right: 0;
  top: calc(100% + 6px);
  z-index: 30;
  padding: 6px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.98);
  border: 1px solid rgba(47, 126, 247, 0.14);
  box-shadow: 0 14px 28px rgba(31, 47, 71, 0.12);
  backdrop-filter: blur(14px);
}

.relation-menu-upward {
  top: auto;
  bottom: calc(100% + 6px);
}

.relation-option {
  width: 100%;
  min-height: 34px;
  padding: 0 10px;
  border-radius: 10px;
  text-align: left;
  color: var(--app-text);
  font-size: 12px;
  font-weight: 500;
}

.relation-option + .relation-option {
  margin-top: 2px;
}

.relation-option-active {
  background: rgba(47, 126, 247, 0.08);
  color: var(--app-primary-deep);
}

.relation-drop-enter-active,
.relation-drop-leave-active {
  transition: opacity 0.18s ease, transform 0.18s ease;
}

.relation-drop-enter-from,
.relation-drop-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

.submit-note {
  width: 100%;
  margin: 0;
  text-align: center;
  font-size: 10px;
  line-height: 1.3;
  color: var(--app-text-faint);
}

.submit-btn {
  width: 100%;
  height: 42px !important;
  font-size: 15px !important;
}
</style>
