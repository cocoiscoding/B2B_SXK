<template>
  <div class="avue-tags">
    <el-scrollbar>
      <div class="tags-wrapper">
        <el-tooltip
          v-for="tag in tagsStore.tagList"
          :key="tag.tabId || tag.value"
          :content="tag.sublabel ? `${tag.label} · ${tag.sublabel}` : tag.label"
          placement="bottom"
          :show-after="500"
          effect="dark"
        >
        <div
          class="tag-item"
          :class="{ active: isActive(tag) }"
          @click="goTag(tag)"
          @contextmenu.prevent="openContextMenu($event, tag)"
        >
          <div class="tag-text">
            <span class="tag-label">{{ tag.label }}</span>
            <span v-if="tag.sublabel" class="tag-sublabel">{{ tag.sublabel }}</span>
          </div>
          <el-icon
            v-if="tag.close !== false"
            class="close-icon"
            @click.stop="closeTag(tag)"
          >
            <Close />
          </el-icon>
        </div>
        </el-tooltip>
      </div>
    </el-scrollbar>

    <!-- 右键上下文菜单 -->
    <ul
      v-if="contextMenu.visible"
      class="context-menu"
      :style="{ left: contextMenu.x + 'px', top: contextMenu.y + 'px' }"
    >
      <li @click="onCloseCurrent">关闭</li>
      <li @click="onCloseOthers">关闭其他</li>
      <li @click="onCloseAll">关闭全部</li>
    </ul>
  </div>
</template>

<script setup>
import { reactive, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Close } from '@element-plus/icons-vue'
import { useTagsStore } from '@/store/modules/tags'

const route = useRoute()
const router = useRouter()
const tagsStore = useTagsStore()

// 右键菜单状态
const contextMenu = reactive({
  visible: false,
  x: 0,
  y: 0,
  tag: null
})

// 判断 tag 是否为当前激活
const isActive = (tag) => {
  if (tag.tabId === 'tab_welcome') {
    return route.path === '/dashboard' || route.path === '/dashboard/index'
  }
  return tag.tabId && route.query.tabId === tag.tabId
}

const goTag = (tag) => {
  router.push(tag.value)
}

const closeTag = (tag) => {
  const wasActive = isActive(tag)
  const nowTag = tagsStore.closeTag(tag)
  if (wasActive && nowTag) {
    goTag(nowTag)
  }
}

// 打开右键菜单
const openContextMenu = (e, tag) => {
  // 首页 tab 不弹菜单
  if (tag.close === false) return
  contextMenu.visible = true
  contextMenu.x = e.clientX
  contextMenu.y = e.clientY
  contextMenu.tag = tag
}

// 关闭菜单
const hideContextMenu = () => {
  contextMenu.visible = false
}

// 关闭当前
const onCloseCurrent = () => {
  hideContextMenu()
  if (contextMenu.tag) closeTag(contextMenu.tag)
}

// 关闭其他（保留首页和当前）
const onCloseOthers = () => {
  hideContextMenu()
  if (contextMenu.tag) {
    tagsStore.delOtherTag(contextMenu.tag)
    goTag(contextMenu.tag)
  }
}

// 关闭全部（仅保留首页）
const onCloseAll = () => {
  hideContextMenu()
  tagsStore.delAllTag()
  goTag(tagsStore.tagWel)
}

// 点击页面其他区域时关闭菜单
const handleOutsideClick = () => {
  if (contextMenu.visible) hideContextMenu()
}

onMounted(() => {
  document.addEventListener('click', handleOutsideClick)
})
onUnmounted(() => {
  document.removeEventListener('click', handleOutsideClick)
})
</script>

<style lang="scss" scoped>
.avue-tags {
  display: flex;
  align-items: center;
  padding: $spacing-sm $spacing-md;

  .tags-wrapper {
    display: flex;
    align-items: center;
    gap: $spacing-sm;
    white-space: nowrap;
  }

  .tag-item {
    display: inline-flex;
    align-items: center;
    gap: $spacing-xs;
    padding: $spacing-xs $spacing-md;
    border-radius: $radius-md;
    cursor: pointer;
    font-size: $font-size-sm;
    border: 1px solid $border-base;
    background: $bg-card;
    color: $text-regular;
    transition: $transition-base;

    &:hover {
      color: $primary-color;
      border-color: $primary-color;
    }

    &.active {
      background-color: $primary-color;
      color: #fff;
      border-color: $primary-color;

      .tag-sublabel {
        color: rgba(255, 255, 255, 0.75);
      }
    }

    .tag-text {
      display: inline-flex;
      align-items: baseline;
      gap: 4px;
      max-width: 220px;
    }

    .tag-label {
      flex-shrink: 0;
    }

    .tag-sublabel {
      font-size: $font-size-xs;
      color: $text-secondary;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .close-icon {
      font-size: $font-size-xs;
      border-radius: $radius-round;
      flex-shrink: 0;
      &:hover {
        background-color: rgba(255, 255, 255, 0.3);
      }
    }
  }
}

.context-menu {
  position: fixed;
  z-index: 9999;
  margin: 0;
  padding: 4px 0;
  list-style: none;
  background: #fff;
  border: 1px solid $border-base;
  border-radius: $radius-md;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
  min-width: 100px;
  user-select: none;

  li {
    padding: 6px 16px;
    font-size: $font-size-sm;
    cursor: pointer;
    color: $text-regular;
    transition: $transition-base;

    &:hover {
      background: rgba(64, 158, 255, 0.08);
      color: $primary-color;
    }
  }
}
</style>
