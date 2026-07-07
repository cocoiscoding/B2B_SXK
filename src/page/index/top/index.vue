<template>
  <div class="top-bar">
    <div class="top-left">
      <!-- 折叠按钮 -->
      <div class="collapse-btn" @click="commonStore.setCollapse()">
        <el-icon><Fold v-if="!commonStore.isCollapse" /><Expand v-else /></el-icon>
      </div>
      <!-- Logo -->
      <div class="logo">
        <span class="logo-text">{{ website.indexTitle }}</span>
      </div>
    </div>

    <div class="top-right">
      <!-- 全屏 -->
      <div class="top-item" @click="toggleFullScreen">
        <el-icon><FullScreen /></el-icon>
      </div>
      <!-- 用户信息 -->
      <el-dropdown @command="handleCommand">
        <span class="user-info">
          <el-avatar :size="30" :src="userStore.userInfo.avatar">
            <el-icon><User /></el-icon>
          </el-avatar>
          <span class="username">{{ userStore.userInfo.nick_name || userStore.userInfo.user_name || '用户' }}</span>
          <el-icon><ArrowDown /></el-icon>
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
import { useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { Fold, Expand, FullScreen, User, ArrowDown } from '@element-plus/icons-vue'
import { useCommonStore } from '@/store/modules/common'
import { useUserStore } from '@/store/modules/user'
import website from '@/config/website'

const router = useRouter()
const commonStore = useCommonStore()
const userStore = useUserStore()

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
.top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: $header-height;
  background-color: #fff;
  padding: 0 16px;

  .top-left {
    display: flex;
    align-items: center;
    gap: 12px;

    .collapse-btn {
      cursor: pointer;
      font-size: 20px;
      &:hover {
        color: $primary-color;
      }
    }

    .logo-text {
      font-size: 18px;
      font-weight: 600;
      color: #303133;
      white-space: nowrap;
    }
  }

  .top-right {
    display: flex;
    align-items: center;
    gap: 16px;

    .top-item {
      cursor: pointer;
      font-size: 18px;
      &:hover {
        color: $primary-color;
      }
    }

    .user-info {
      display: flex;
      align-items: center;
      gap: 8px;
      cursor: pointer;

      .username {
        font-size: 14px;
      }
    }
  }
}
</style>
