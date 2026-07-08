<template>
  <div class="sidebar">
    <!-- 侧边栏 Logo 区（对齐登录页品牌区：毛玻璃圆角图标框 + 神行库标题） -->
    <div class="sidebar-logo">
      <div class="logo-badge">
        <!-- 闪电图标（原型 mdi:lightning-bolt，用内联 SVG 实现） -->
        <svg class="logo-icon" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
          <path d="M7 2v11h3v9l7-12h-4l3-8z" />
        </svg>
      </div>
      <span v-show="!commonStore.isCollapse" class="logo-text">神行库</span>
    </div>
    <!-- 导航菜单 -->
    <el-scrollbar class="sidebar-scroll">
      <el-menu
        :default-active="activeMenu"
        :collapse="commonStore.isCollapse"
        background-color="transparent"
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
// 侧边栏背景改为渐变（见 <style>），菜单背景透明
const SIDEBAR_TEXT = 'rgba(255,255,255,0.85)'   // $sidebar-text（背景调浅后提升对比度）
const SIDEBAR_TEXT_ACTIVE = '#ffffff'           // $sidebar-text-active

const resolvePath = (basePath, childPath) => {
  if (childPath.startsWith('/')) return childPath
  return `/${basePath}/${childPath}`.replace(/\/+/g, '/')
}
</script>

<style lang="scss" scoped>
// 侧边栏：渐变背景 + 装饰光斑 + 装饰圆，与登录页左侧品牌区风格统一
.sidebar {
  position: relative;
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
  // 品牌蓝渐变 + 装饰光斑（与登录页 .login-brand 一致）
  // 色阶整体调浅一档：blue-700→blue-600，indigo-600→indigo-500
  background:
    radial-gradient(circle at 100% 0%, rgba(255, 255, 255, 0.12) 0%, transparent 45%),
    radial-gradient(circle at 0% 100%, rgba(139, 92, 246, 0.15) 0%, transparent 45%),
    linear-gradient(180deg, #2563eb 0%, #3b6fd8 55%, #6366f1 100%);

  // 背景装饰圆：增加层次感（与登录页 ::before/::after 呼应）
  &::before,
  &::after {
    content: '';
    position: absolute;
    border-radius: 50%;
    pointer-events: none;
  }
  &::before {
    width: 200px;
    height: 200px;
    top: 100px;
    right: -120px;
    background: rgba(255, 255, 255, 0.06);
  }
  &::after {
    width: 160px;
    height: 160px;
    bottom: 60px;
    left: -100px;
    background: rgba(255, 255, 255, 0.05);
  }
}

// Logo 区（对齐登录页 brand-header：毛玻璃圆角图标框 + 标题）
.sidebar-logo {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: $spacing-sm;
  height: $header-height;
  padding: 0 $spacing-xl;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  flex-shrink: 0;

  // 毛玻璃图标框（对齐登录页 .brand-logo）
  .logo-badge {
    flex-shrink: 0;
    width: 36px;
    height: 36px;
    border-radius: $radius-md;
    background: rgba(255, 255, 255, 0.2);
    backdrop-filter: blur(8px);
    border: 1px solid rgba(255, 255, 255, 0.25);
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .logo-icon {
    width: 20px;
    height: 20px;
    color: #fff;
  }

  .logo-text {
    font-size: $font-size-xl;
    font-weight: 700;
    color: #fff;
    letter-spacing: 0.1em;
    white-space: nowrap;
  }
}

// 菜单滚动区：占据剩余高度
.sidebar-scroll {
  flex: 1;
  position: relative;
  z-index: 1;

  :deep(.el-scrollbar__view) {
    height: 100%;
  }
}

:deep(.el-menu) {
  border-right: none;
  background-color: transparent;
}

// 菜单项通用：圆角胶囊 + 平滑过渡 + 文字字距/字重优化
:deep(.el-menu-item),
:deep(.el-sub-menu__title) {
  margin: 4px 12px;              // 上下左右留白，让背景呈胶囊而非贯通整条
  padding-left: 12px !important; // 与 margin 配合（原 24px = margin12 + padding12）
  padding-right: 12px !important;
  border-radius: $radius-md;     // 圆角胶囊
  background-color: transparent !important;
  font-weight: 500;              // 半透明文字加粗到 500 更清晰
  letter-spacing: 0.02em;        // 微字距，更精致
  transition: all 0.25s ease;    // 颜色/背景平滑过渡
}

// 菜单项图标尺寸与右边距对齐原型 text-xl mr-3（24px / 12px）
// 图标颜色跟随文字透明度，hover/active 时变亮
:deep(.el-menu-item .el-icon),
:deep(.el-sub-menu__title .el-icon) {
  font-size: 20px;
  margin-right: 12px;
  transition: color 0.25s ease;
}

// 菜单项 hover 态：白色 10% 半透明胶囊 + 文字变亮
:deep(.el-menu-item:hover),
:deep(.el-sub-menu__title:hover) {
  background-color: $sidebar-bg-hover !important;
  color: #ffffff !important;
}

// 当前激活项：毛玻璃高亮胶囊 + 左侧圆角指示条 + 柔和投影
:deep(.el-menu-item.is-active) {
  position: relative;
  // 渐变白底（135° 从亮到暗）增加立体感
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.22) 0%, rgba(255, 255, 255, 0.1) 100%) !important;
  backdrop-filter: blur(6px);
  color: #ffffff !important;
  font-weight: 600;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);

  // 左侧圆角指示条（独立伪元素，比 inset box-shadow 更精致）
  &::before {
    content: '';
    position: absolute;
    left: 0;
    top: 50%;
    transform: translateY(-50%);
    width: 4px;
    height: 60%;
    border-radius: 0 4px 4px 0;
    background: #ffffff;
    box-shadow: 0 0 8px rgba(255, 255, 255, 0.5);
  }

  .el-icon {
    color: #ffffff !important;
  }
}

// 底部版权（对齐原型：p-6 border-t border-white/10 text-white/60 text-xs）
.sidebar-footer {
  position: relative;
  z-index: 1;
  padding: $spacing-xl;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.75);
  font-size: $font-size-xs;
  flex-shrink: 0;
}
</style>
