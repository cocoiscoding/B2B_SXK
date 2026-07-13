<template>
  <div class="avue-tags">
    <el-scrollbar>
      <div class="tags-wrapper">
        <div
          v-for="tag in tagsStore.tagList"
          :key="tag.tabId || tag.value"
          class="tag-item"
          :class="{ active: isActive(tag) }"
          @click="goTag(tag)"
          @contextmenu.prevent="closeTag(tag)"
        >
          <span>{{ tag.label }}</span>
          <el-icon
            v-if="tag.close !== false"
            class="close-icon"
            @click.stop="closeTag(tag)"
          >
            <Close />
          </el-icon>
        </div>
      </div>
    </el-scrollbar>
  </div>
</template>

<script setup>
import { useRoute, useRouter } from 'vue-router'
import { Close } from '@element-plus/icons-vue'
import { useTagsStore } from '@/store/modules/tags'

const route = useRoute()
const router = useRouter()
const tagsStore = useTagsStore()

// 判断 tag 是否为当前激活
const isActive = (tag) => {
  // 首页 tab（固定 tabId）
  if (tag.tabId === 'tab_welcome') {
    return route.path === '/dashboard' || route.path === '/dashboard/index'
  }
  // 其他 tab 按 tabId 匹配
  return tag.tabId && route.query.tabId === tag.tabId
}

const goTag = (tag) => {
  router.push(tag.value)
}

const closeTag = (tag) => {
  const wasActive = isActive(tag)
  const nowTag = tagsStore.closeTag(tag)
  // 如果关闭的是当前激活的标签，跳转到相邻标签
  if (wasActive && nowTag) {
    goTag(nowTag)
  }
}
</script>

<style lang="scss" scoped>
.avue-tags {
  display: flex;
  align-items: center;
  // 上下留白让标签与顶栏分隔线拉开距离，横向留出滚动条空间
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
    }

    .close-icon {
      font-size: $font-size-xs;
      border-radius: $radius-round;
      &:hover {
        background-color: rgba(255, 255, 255, 0.3);
      }
    }
  }
}
</style>
