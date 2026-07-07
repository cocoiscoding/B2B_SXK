<template>
  <div class="avue-contail" :class="{ 'avue--collapse': commonStore.isCollapse }">
    <!-- 顶部导航栏 -->
    <div class="avue-header">
      <Top ref="topRef" />
    </div>
    <div class="avue-layout">
      <!-- 左侧导航栏 -->
      <div class="avue-left">
        <Sidebar />
      </div>
      <div class="avue-main">
        <!-- 顶部标签卡 -->
        <Tags />
        <!-- 主体视图层 -->
        <div class="avue-view">
          <router-view v-slot="{ Component, route }">
            <keep-alive>
              <component :is="Component" :key="route.fullPath" v-if="route.meta.keepAlive" />
            </keep-alive>
            <component :is="Component" :key="route.fullPath" v-if="!route.meta.keepAlive" />
          </router-view>
        </div>
      </div>
    </div>
    <!-- 遮罩（移动端） -->
    <div class="avue-shade" @click="commonStore.setCollapse()" v-show="commonStore.isCollapse"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import Top from './top/index.vue'
import Sidebar from './sidebar/index.vue'
import Tags from './tags.vue'
import { useCommonStore } from '@/store/modules/common'
import { getScreenSize } from '@/util/admin'

const commonStore = useCommonStore()
const topRef = ref(null)

const handleResize = () => {
  commonStore.setScreen(getScreenSize())
}

onMounted(() => {
  commonStore.setScreen(getScreenSize())
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<style lang="scss" scoped>
.avue-shade {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.3);
  z-index: 99;
  display: none;
}
</style>
