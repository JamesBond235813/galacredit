<template>
  <div class="app-layout">
    <!-- 顶部常态波纹渐变底色 -->
    <div class="layout-bg"></div>
    
    <div class="layout-content">
      <router-view v-slot="{ Component }">
        <transition name="van-fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </div>

    <!-- Vant Tabbar -->
    <van-tabbar v-model="active" route active-color="#1A56A6" inactive-color="#C0C4CC">
      <van-tabbar-item replace to="/home" icon="balance-list-o">
        小钱包
      </van-tabbar-item>
      <van-tabbar-item replace to="/profile" icon="user-o">
        我的
      </van-tabbar-item>
    </van-tabbar>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useRoute } from 'vue-router';

const route = useRoute();
const active = computed({
  get: () => (route.meta.tab === 'profile' ? 1 : 0),
  set: () => {}
});
</script>

<style>
/* 全局波纹纹理定义 */
.app-layout {
  min-height: 100vh;
  position: relative;
  background: transparent;
  padding-bottom: var(--app-tabbar-space);
}

/* 绘制参考图中的浅色拓扑网格波云纹理效果 */
.layout-bg {
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 360px;
  background: 
    radial-gradient(circle at top left, rgba(255,255,255,0.7) 0%, transparent 34%),
    radial-gradient(circle at top right, rgba(47,126,247,0.08) 0%, transparent 42%),
    repeating-radial-gradient(circle at top right, transparent, transparent 14px, rgba(44,95,183,0.04) 14px, rgba(44,95,183,0.04) 15px);
  z-index: 0;
  pointer-events: none;
}

.layout-content {
  position: relative;
  z-index: 1;
  height: 100%;
}

.van-tabbar {
  left: 14px;
  right: 14px;
  bottom: calc(10px + env(safe-area-inset-bottom, 0px));
  width: auto;
  height: var(--app-tabbar-height);
  border-radius: calc(var(--app-tabbar-height) / 2);
  border: 1px solid var(--app-border);
  background: rgba(255, 255, 255, 0.94);
  box-shadow: var(--app-shadow);
  backdrop-filter: blur(12px);
  overflow: hidden;
}

.van-tabbar::after {
  display: none;
}

.van-tabbar-item {
  color: var(--app-text-faint);
}

.van-tabbar-item--active {
  background: transparent;
}

.van-tabbar-item--active .van-tabbar-item__icon,
.van-tabbar-item--active .van-tabbar-item__text {
  color: var(--app-primary-deep);
  font-weight: 600;
}
</style>
