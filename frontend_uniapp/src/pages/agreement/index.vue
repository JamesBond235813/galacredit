<script setup>
import PageHeader from '../../components/PageHeader.vue'
</script>

<template>
  <view class="gc-page">
    <PageHeader title="Agreements and privacy" subtitle="Read how GalaCredit uses your information." :back="true" />
    <view class="gc-card">
      <text class="gc-section-title">User Agreement</text>
      <text class="copy">GalaCredit provides responsible credit services. Eligibility, fees, limits, disbursement and repayment dates are shown before you confirm a product. Applying does not guarantee approval.</text>
      <text class="gc-section-title">Information we use</text>
      <text class="copy">We may process your phone number, Ghana Card and face-verification images, application details, emergency contacts you choose, one-time location checks, device and browser signals, loan records and support history for account security, identity verification, credit assessment, servicing and legal obligations.</text>
      <text class="gc-section-title">SMS risk review</text>
      <text class="copy">Only an authorised internal Android build can offer optional SMS review. After your separate consent and Android permission, the device keeps only messages from the latest 90 days that match the published regular-expression keyword file sms_keys20260602.csv. Older, future-dated and unmatched messages are not uploaded. Google Play Android and iOS builds do not read SMS content, and the current builds do not read a complete installed-app list.</text>
      <text class="gc-section-title">Contacts, location and photos</text>
      <text class="copy">The app receives only the emergency contact you choose, requests location only after your action and permission, and uses selected Ghana Card and face images for identity verification. We do not upload your complete address book or continuously track your location.</text>
      <text class="gc-section-title">Your choices and rights</text>
      <text class="copy">You may decline optional sensitive collection and contact support about access, correction, retention, deletion and complaints. Some decisions may require the information needed for responsible lending and fraud prevention.</text>
      <view class="gc-safe-note">This operational notice must be reviewed by the Ghana compliance owner and qualified legal advisers before production launch. Contact support if you have questions about permissions, retention or data sharing.</view>
    </view>
  </view>
</template>

<style scoped>.copy { display:block; color:var(--gc-muted); font-size:24rpx; line-height:1.65; }</style>
