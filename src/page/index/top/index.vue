<template>
  <div class="top-bar">
    <!-- 左侧：折叠按钮 + 面包屑（对齐原型 header 左侧 breadcrumb） -->
    <div class="top-left">
      <div class="collapse-btn" @click="commonStore.setCollapse()">
        <el-icon><Fold v-if="!commonStore.isCollapse" /><Expand v-else /></el-icon>
      </div>
      <!-- 面包屑：神行库 > 当前页（对齐原型 神行库 / chevron-right / 首页） -->
      <div class="breadcrumb">
        <span class="breadcrumb-parent">神行库</span>
        <el-icon class="breadcrumb-sep"><ArrowRight /></el-icon>
        <span class="breadcrumb-current">{{ currentPageTitle }}</span>
      </div>
    </div>

    <!-- 右侧：通知 + 用户（对齐原型 header 右侧） -->
    <div class="top-right">
      <!-- 全屏 -->
      <div class="top-item" @click="toggleFullScreen">
        <el-icon><FullScreen /></el-icon>
      </div>
      <!-- 通知铃铛（带红点，对齐原型 bell-outline） -->
      <div class="top-item top-item--bell">
        <el-icon><Bell /></el-icon>
        <span class="bell-dot"></span>
      </div>
      <div class="top-divider"></div>
      <!-- 用户信息 -->
      <el-dropdown @command="handleCommand">
        <span class="user-info">
          <el-avatar :size="32" :src="userStore.userInfo.avatar">
            <el-icon><User /></el-icon>
          </el-avatar>
          <span class="username">{{ userStore.userInfo.nick_name || userStore.userInfo.user_name || '用户' }}</span>
          <el-icon class="arrow-down"><ArrowDown /></el-icon>
        </span>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="info">个人信息</el-dropdown-item>
            <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { Fold, Expand, FullScreen, User, ArrowDown, ArrowRight, Bell } from '@element-plus/icons-vue'
import { useCommonStore } from '@/store/modules/common'
import { useUserStore } from '@/store/modules/user'

const router = useRouter()
const route = useRoute()
const commonStore = useCommonStore()
const userStore = useUserStore()

// 当前页面标题（从路由 meta.title 派生，用于面包屑）
const currentPageTitle = computed(() => route.meta?.title || '首页')

const toggleFullScreen = () => {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen()
  } else {
    document.exitFullscreen()
  }
  commonStore.setFullScren()
}

const handleCommand = async (command) => {
  if (command === 'logout') {
    try {
      await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
        type: 'warning'
      })
      await userStore.logOut()
      router.push('/login')
    } catch {
      // 取消
    }
  } else if (command === 'info') {
    router.push('/info/index')
  }
}
</script>

<style lang="scss" scoped>
// 顶栏（对齐原型 header：h-16 bg-white border-b flex items-center justify-between px-8）
.top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 100%;                 // 由 .avue-header 控制高度（64px）
  padding: 0 $spacing-2xl;      // px-8 = 32px

  .top-left {
    display: flex;
    align-items: center;
    gap: $spacing-md;

    .collapse-btn {
      cursor: pointer;
      font-size: $font-size-xl;
      color: $text-regular;
      transition: $transition-fast;
      &:hover {
        color: $primary-color;
      }
    }

    // 面包屑（对齐原型 text-sm text-gray-500）
    .breadcrumb {
      display: flex;
      align-items: center;
      gap: $spacing-xs;
      font-size: $font-size-sm;

      .breadcrumb-parent {
        color: $text-secondary;   // text-gray-500
      }

      .breadcrumb-sep {
        font-size: 12px;
        color: $text-placeholder;
      }

      .breadcrumb-current {
        color: $gray-900;         // text-gray-900 font-medium
        font-weight: 500;
      }
    }
  }

  .top-right {
    display: flex;
    align-items: center;
    gap: $spacing-md;

    .top-item {
      cursor: pointer;
      font-size: $font-size-xl;
      color: $text-placeholder;   // text-gray-400
      transition: $transition-fast;
      &:hover {
        color: $text-regular;     // hover:text-gray-600
      }
    }

    // 通知铃铛红点（对齐原型 absolute top-2 right-2 w-2 h-2 bg-red-500 rounded-full）
    .top-item--bell {
      position: relative;

      .bell-dot {
        position: absolute;
        top: 2px;
        right: 2px;
        width: 8px;
        height: 8px;
        background-color: #ef4444;  // bg-red-500
        border-radius: $radius-round;
      }
    }

    // 竖直分隔线（对齐原型 h-8 w-px bg-gray-200 mx-2）
    .top-divider {
      width: 1px;
      height: 32px;
      background-color: $border-base;
      margin: 0 $spacing-sm;
    }

    .user-info {
      display: flex;
      align-items: center;
      gap: $spacing-sm;
      cursor: pointer;
      padding: $spacing-xs $spacing-sm;
      border-radius: $radius-md;
      transition: $transition-fast;
      &:hover {
        background-color: $bg-hover;
      }

      .username {
        font-size: $font-size-sm;
        font-weight: 500;
        color: $text-primary;
      }

      .arrow-down {
        font-size: 12px;
        color: $text-secondary;
      }
    }
  }
}
</style>
