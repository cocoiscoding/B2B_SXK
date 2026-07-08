<template>
  <div class="sidebar">
    <!-- 侧边栏 Logo 区（对齐原型：h-16 闪电图标 + 神行库标题） -->
    <div class="sidebar-logo">
      <!-- 闪电图标（原型 mdi:lightning-bolt，用内联 SVG 实现） -->
      <svg class="logo-icon" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
        <path d="M7 2v11h3v9l7-12h-4l3-8z" />
      </svg>
      <span v-show="!commonStore.isCollapse" class="logo-text">神行库</span>
    </div>
    <!-- 导航菜单 -->
    <el-scrollbar class="sidebar-scroll">
      <el-menu
        :default-active="activeMenu"
        :collapse="commonStore.isCollapse"
        :background-color="SIDEBAR_BG"
        :text-color="SIDEBAR_TEXT"
        :active-text-color="SIDEBAR_TEXT_ACTIVE"
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
    <!-- 底部版权（对齐原型：border-t border-white/10 text-white/60 text-xs） -->
    <div v-show="!commonStore.isCollapse" class="sidebar-footer">
      © 2026 神行库 AI 平台
    </div>
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
// 神行库修改：兼容 menu.props.path = 'path'，菜单字段直接是 name/path/source（参考 store/modules/user.js 的 initSxkMenu）
const menuList = computed(() => userStore.menu)

// el-menu 属性需要字符串色值，这里与 styles/variables.scss 的 token 保持一致
// 严格对齐原型 SXK.html：侧边栏品牌蓝底 bg-[#1A56DB]
const SIDEBAR_BG = '#1A56DB'                    // $sidebar-bg
const SIDEBAR_TEXT = 'rgba(255,255,255,0.65)'   // $sidebar-text
const SIDEBAR_TEXT_ACTIVE = '#ffffff'           // $sidebar-text-active

const resolvePath = (basePath, childPath) => {
  if (childPath.startsWith('/')) return childPath
  return `/${basePath}/${childPath}`.replace(/\/+/g, '/')
}
</script>

<style lang="scss" scoped>
.sidebar {
  display: flex;
  flex-direction: column;
  height: 100%;
  background-color: $sidebar-bg;
}

// Logo 区（对齐原型：h-16 flex items-center px-6 border-b border-white/10）
.sidebar-logo {
  display: flex;
  align-items: center;
  height: $header-height;        // 与顶栏同高（原型 h-16 = 64px）
  padding: 0 $spacing-xl;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  flex-shrink: 0;

  .logo-icon {
    width: 24px;
    height: 24px;
    margin-right: $spacing-sm;
    color: #fff;
    flex-shrink: 0;
  }

  .logo-text {
    font-size: $font-size-xl;     // text-xl
    font-weight: 700;             // font-bold
    color: #fff;
    letter-spacing: 0.1em;        // tracking-wider
    white-space: nowrap;
  }
}

// 菜单滚动区：占据剩余高度（对齐原型 nav flex-1）
.sidebar-scroll {
  flex: 1;

  :deep(.el-scrollbar__view) {
    height: 100%;
  }
}

:deep(.el-menu) {
  border-right: none;
  background-color: $sidebar-bg;
}

// 菜单项内边距对齐原型 px-6 py-4（水平 24px / 垂直 16px）
// el-menu 默认 padding-left 20px 且随层级递增，这里统一覆盖为 24px
:deep(.el-menu-item),
:deep(.el-sub-menu__title) {
  padding-left: 24px !important;
  padding-right: 24px !important;
}

// 菜单项图标尺寸与右边距对齐原型 text-xl mr-3（24px / 12px）
:deep(.el-menu-item .el-icon),
:deep(.el-sub-menu__title .el-icon) {
  font-size: 20px;
  margin-right: 12px;
}

// 菜单项 hover 态：白色 10% 半透明（对齐原型 hover:bg-white/10）
:deep(.el-menu-item:hover),
:deep(.el-sub-menu__title:hover) {
  background-color: $sidebar-bg-hover !important;
}

// 当前激活项：白色半透明背景 + 白色左边框（严格对齐原型 .sidebar-active）
:deep(.el-menu-item.is-active) {
  background-color: $sidebar-active-bg !important;
  color: $sidebar-text-active !important;
  // 原型 border-left: 4px solid #fff（用 box-shadow 模拟，避免影响 el-menu 布局）
  box-shadow: inset 4px 0 0 0 $sidebar-active-border;
}

// 底部版权（对齐原型：p-6 border-t border-white/10 text-white/60 text-xs）
.sidebar-footer {
  padding: $spacing-xl;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.6);
  font-size: $font-size-xs;
  flex-shrink: 0;
}
</style>
