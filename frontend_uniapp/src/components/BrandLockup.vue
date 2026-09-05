<script setup>
import logo from '../assets/logo.svg'
</script>

<template>
  <view class="gc-brand">
    <view class="gc-brand__logo" :style="{ backgroundImage: `url(${logo})` }" />
    <view>
      <text class="gc-brand__name">GalaCredit</text>
      <text class="gc-brand__tagline">Credit when it matters</text>
    </view>
  </view>
</template>
