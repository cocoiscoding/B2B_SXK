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
  padding: 0 8px;

  .tags-wrapper {
    display: flex;
    align-items: center;
    gap: 4px;
    white-space: nowrap;
  }

  .tag-item {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 4px 12px;
    border-radius: 3px;
    cursor: pointer;
    font-size: 13px;
    border: 1px solid #e4e7ed;
    background: #fff;
    transition: all 0.2s;

    &:hover {
      color: $primary-color;
    }

    &.active {
      background-color: $primary-color;
      color: #fff;
      border-color: $primary-color;
    }

    .close-icon {
      font-size: 12px;
      border-radius: 50%;
      &:hover {
        background-color: rgba(255, 255, 255, 0.3);
      }
    }
  }
}
</style>
