<template>
  <div class="avue-tags">
    <el-scrollbar>
      <div class="tags-wrapper">
        <div
          v-for="tag in tagsStore.tagList"
          :key="tag.value"
          class="tag-item"
          :class="{ active: isActive(tag) }"
          @click="goTag(tag)"
          @contextmenu.prevent="closeTag(tag)"
        >
          <span>{{ tag.label }}</span>
          <el-icon v-if="tag.close !== false" class="close-icon" @click.stop="closeTag(tag)">
            <Close />
          </el-icon>
        </div>
      </div>
    </el-scrollbar>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Close } from '@element-plus/icons-vue'
import { useTagsStore } from '@/store/modules/tags'

const route = useRoute()
const router = useRouter()
const tagsStore = useTagsStore()

const isActive = (tag) => {
  return tag.value === route.fullPath || tag.value === route.path
}

const goTag = (tag) => {
  router.push(tag.value)
}

const closeTag = (tag) => {
  const nowTag = tagsStore.closeTag(tag)
  if (nowTag && isActive(tag)) {
    goTag(nowTag)
  }
}
</script>

<style lang="scss" scoped>
.avue-tags {
  display: flex;
  align-items: center;
  padding: 0 $spacing-sm;

  .tags-wrapper {
    display: flex;
    align-items: center;
    gap: $spacing-xs;
    white-space: nowrap;
  }

  .tag-item {
    display: inline-flex;
    align-items: center;
    gap: $spacing-xs;
    padding: $spacing-xs $spacing-md;
    border-radius: $radius-sm;
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
