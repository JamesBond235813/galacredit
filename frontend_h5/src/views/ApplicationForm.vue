<template>
  <div class="page-shell application-page">
    <van-nav-bar left-arrow title="Additional Information" @click-left="router.back()" />

    <div class="page-inner application-inner">
      <header class="application-hero">
        <span class="hero-chip">Step 3 of 4</span>
        <h1 class="hero-title">Emergency Contacts</h1>
        <p class="hero-desc">Provide two emergency contacts from your address book.</p>
      </header>

      <div class="contact-grid">
        <article
          v-for="(contact, index) in contacts"
          :key="contact.key"
          class="page-card contact-card"
          :class="{ 'contact-card-active': relationPickerIndex === index }"
        >
          <div class="contact-head">
            <span class="contact-index">Emergency contact {{ index + 1 }} ({{ contact.categoryLabel }})</span>
          </div>

          <div class="contact-fields">
            <label class="contact-display-field contact-field">
              <span class="contact-display-label">Relatives</span>
              <div class="relation-field" @click.stop>
                <button
                  type="button"
                  class="relation-trigger"
                  :class="{ 'relation-trigger-empty': !contact.relation }"
                  @click="toggleRelationPicker(index)"
                >
                  <span>{{ contact.relation || 'Select relationship' }}</span>
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
                      v-for="item in contact.relationOptions"
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

            <button type="button" class="contact-display-field contact-action-field" @click="pickContact(index)">
              <span class="contact-display-label">PhoneNumber</span>
              <strong :class="{ 'contact-display-empty': !contact.phone }">
                {{ displayLocalPhone(contact.phone) || 'Select contact' }}
              </strong>
              <van-icon name="arrow" class="contact-display-arrow" />
            </button>

            <button type="button" class="contact-display-field contact-action-field" @click="pickContact(index)">
              <span class="contact-display-label">Full Name</span>
              <strong :class="{ 'contact-display-empty': !contact.name }">{{ contact.name || 'Select contact' }}</strong>
              <van-icon name="arrow" class="contact-display-arrow" />
            </button>
          </div>
        </article>
      </div>

      <van-button
        block
        type="primary"
        class="primary-action submit-btn"
        :loading="submitting"
        @click="submitForm"
      >
        Submit Application
      </van-button>
    </div>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, reactive, ref } from 'vue';
import { useRouter } from 'vue-router';
import { closeToast, showToast } from 'vant';
import { getLoanStatus, getUserInfo, submitApplication } from '../api';
import { formatGhanaContactLocalPhone, normalizeGhanaContactPhone, selectSingleContact } from '../utils/contactPicker';

const router = useRouter();
const submitting = ref(false);

const familyRelationOptions = ['Parents', 'Brothers or sisters', 'Grandparents', 'Couple', 'Children'];
const socialRelationOptions = ['Friends', 'Classmates', 'Colleagues'];
const contacts = reactive([
  { key: 'primary', category: 'FAMILY', categoryLabel: 'family', relationOptions: familyRelationOptions, name: '', phone: '', relation: '' },
  { key: 'secondary', category: 'SOCIAL', categoryLabel: 'friend', relationOptions: socialRelationOptions, name: '', phone: '', relation: '' }
]);

const relationPickerIndex = ref(null);

/**
 * Pick one contact from the device address book and fill the name and phone together.
 *
 * :param index: Contact position in the form
 * :return: Promise<void>
 */
const pickContact = async (index) => {
  try {
    const selected = await selectSingleContact();
    if (!selected) {
      return;
    }
    contacts[index].name = selected.name;
    contacts[index].phone = selected.phone;
  } catch (error) {
    showToast(error?.message || 'Unable to access your contacts');
  }
};

/**
 * Convert a normalized Ghana international phone number to a 9-digit local display value.
 *
 * :param value: Normalized phone number
 * :return: 9-digit local phone number
 */
const displayLocalPhone = (value) => formatGhanaContactLocalPhone(value);

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
    contacts[0].relation = familyRelationOptions.includes(user.emergency_contact1_relation) ? user.emergency_contact1_relation : '';
    contacts[0].phone = normalizeGhanaContactPhone(user.emergency_contact1_phone) || user.emergency_contact1_phone || '';
    contacts[1].name = user.emergency_contact2_name || '';
    contacts[1].relation = socialRelationOptions.includes(user.emergency_contact2_relation) ? user.emergency_contact2_relation : '';
    contacts[1].phone = normalizeGhanaContactPhone(user.emergency_contact2_phone) || user.emergency_contact2_phone || '';
  } catch (error) {
    // handled by interceptor
  }
};

const validateForm = () => {
  for (let index = 0; index < contacts.length; index += 1) {
    const contact = contacts[index];
    if (!contact.name.trim()) {
      showToast(`Enter the name of contact ${index + 1}`);
      return false;
    }
    if (!/^233\d{9}$/.test(contact.phone.trim()) && !/^\d{11}$/.test(contact.phone.trim())) {
      showToast(`Select a valid contact ${index + 1} from your address book`);
      return false;
    }
    if (!contact.relation.trim()) {
      showToast(`Select your relationship with contact ${index + 1}`);
      return false;
    }
    if (!contact.relationOptions.includes(contact.relation)) {
      showToast(`Select a valid ${contact.categoryLabel} relationship for contact ${index + 1}`);
      return false;
    }
  }
  if (contacts[0].phone.trim() === contacts[1].phone.trim()) {
    showToast('The two contacts must use different mobile numbers');
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
    showToast({ type: 'loading', duration: 0, message: 'Submitting application...' });
    await submitApplication({
      emergency_contacts: contacts.map((contact) => ({
        name: contact.name.trim(),
        relation: contact.relation.trim(),
        phone: contact.phone.trim(),
        source: 'CONTACT_PICKER',
        category: contact.category
      }))
    });
    closeToast();
    showToast('Application submitted');
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
  gap: 12px;
  padding: calc(env(safe-area-inset-top, 0px) + 8px) 12px 12px;
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
  margin: 10px 0 0;
  font-size: 24px;
  line-height: 1.16;
  font-weight: 800;
  color: var(--app-text);
}

.hero-desc {
  margin: 6px 0 0;
  font-size: 14px;
  line-height: 1.4;
  color: var(--app-text-soft);
}

.contact-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
}

.contact-card {
  position: relative;
  z-index: 1;
  overflow: visible;
  padding: 14px 12px;
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
  max-width: 100%;
  min-height: 24px;
  padding: 0 10px;
  border-radius: 999px;
  background: rgba(47, 126, 247, 0.08);
  color: var(--app-primary-deep);
  font-size: 12px;
  font-weight: 700;
  line-height: 1.3;
}

.contact-fields {
  display: grid;
  grid-template-columns: 1fr;
  gap: 8px;
}

.contact-display-field {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 12px;
  min-height: 56px;
  padding: 0 14px;
  border: 1px solid #e8eef8;
  border-radius: 12px;
  background: #f7faff;
  text-align: left;
}

.contact-display-label {
  flex-shrink: 0;
  width: 104px;
  color: var(--app-text-faint);
  font-size: 14px;
  font-weight: 600;
}

.contact-display-field strong {
  min-width: 0;
  flex: 1;
  overflow: hidden;
  color: var(--app-text);
  font-size: 16px;
  font-weight: 700;
  text-align: right;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.contact-display-empty {
  color: #b2bed0 !important;
  font-weight: 600 !important;
}

.contact-action-field {
  cursor: pointer;
}

.contact-display-arrow {
  flex-shrink: 0;
  color: var(--app-text-soft);
  font-size: 14px;
}

.contact-field {
  background: #ffffff;
  border-color: #d8e2f0;
}

.relation-field {
  position: relative;
  width: 100%;
}

.relation-trigger {
  width: 100%;
  min-height: 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  color: var(--app-text);
  font-size: 16px;
  font-weight: 700;
  line-height: 1.25;
}

.relation-trigger-empty {
  color: #b2bed0;
}

.relation-arrow {
  flex-shrink: 0;
  font-size: 14px;
  color: var(--app-text-soft);
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
  min-height: 40px;
  padding: 0 10px;
  border-radius: 10px;
  text-align: left;
  color: var(--app-text);
  font-size: 15px;
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

.submit-btn {
  width: 100%;
  height: 48px !important;
  font-size: 17px !important;
}
</style>
