<template>
  <div class="sidebar">
    <el-scrollbar>
      <el-menu
        :default-active="activeMenu"
        :collapse="commonStore.isCollapse"
        background-color="#001529"
        text-color="rgba(255,255,255,0.65)"
        active-text-color="#fff"
        :unique-opened="true"
        router
      >
        <template v-for="item in menuList" :key="item.path">
          <!-- 单级菜单 -->
          <el-menu-item v-if="!item.children || item.children.length === 0" :index="item.path">
            <el-icon v-if="item.meta?.icon"><component :is="item.meta.icon" /></el-icon>
            <template #title>{{ item.meta?.title || item.name }}</template>
          </el-menu-item>
          <!-- 多级菜单 -->
          <el-sub-menu v-else :index="item.path">
            <template #title>
              <el-icon v-if="item.meta?.icon"><component :is="item.meta.icon" /></el-icon>
              <span>{{ item.meta?.title || item.name }}</span>
            </template>
            <el-menu-item
              v-for="child in item.children"
              :key="child.path"
              :index="resolvePath(item.path, child.path)"
            >
              <el-icon v-if="child.meta?.icon"><component :is="child.meta.icon" /></el-icon>
              <template #title>{{ child.meta?.title || child.name }}</template>
            </el-menu-item>
          </el-sub-menu>
        </template>
      </el-menu>
    </el-scrollbar>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useCommonStore } from '@/store/modules/common'
import { useUserStore } from '@/store/modules/user'

const route = useRoute()
const commonStore = useCommonStore()
const userStore = useUserStore()

const activeMenu = computed(() => route.path)
const menuList = computed(() => userStore.menu)

const resolvePath = (basePath, childPath) => {
  if (childPath.startsWith('/')) return childPath
  return `/${basePath}/${childPath}`.replace(/\/+/g, '/')
}
</script>

<style lang="scss" scoped>
.sidebar {
  height: 100%;
  background-color: #001529;

  :deep(.el-menu) {
    border-right: none;
  }
}
</style>
