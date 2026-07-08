<!--
  通用块容器（在原 basic-block 基础上扩展）
  - header 插槽：用于标题区 + 右侧按钮
  - hoverShadow prop：true 时启用 hover 阴影效果（AC-22 / US001 验收项）
  - padding prop：自定义内边距（默认 'medium'，'none' 可去掉 padding）
-->
<template>
  <div class="basic-block" :class="classes" :style="style">
    <!-- 标题区（可选） -->
    <div v-if="$slots.header" class="basic-block__header">
      <div class="basic-block__header-left">
        <slot name="header" />
      </div>
      <div v-if="$slots.aside" class="basic-block__header-aside">
        <slot name="aside" />
      </div>
    </div>
    <!-- 主体区 -->
    <div class="basic-block__body">
      <slot />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  hoverShadow: { type: Boolean, default: false },
  padding: { type: String, default: 'medium' } // none | small | medium
})

const classes = computed(() => ({
  'basic-block--hover': props.hoverShadow,
  [`basic-block--pad-${props.padding}`]: true
}))

const style = {}
</script>

<style lang="scss" scoped>
// 通用块容器（对齐原型卡片：bg-white rounded-lg border border-gray-200 shadow-sm）
.basic-block {
  padding: $spacing-lg;
  background: $bg-card;
  border: 1px solid $border-base;       // border-gray-200
  border-radius: $radius-lg;            // rounded-lg = 8px
  box-shadow: $shadow-sm;               // shadow-sm
  transition: $transition-base;
  // 不设默认 margin-bottom：垂直间距统一由父容器 flex gap 控制，
  // 避免与 gap 叠加导致块间距不均（knowledge/history/templates 容器均用 gap）

  &--pad-none { padding: 0; }
  &--pad-small { padding: $spacing-sm $spacing-md; }

  // hover 阴影（对齐原型 hover:shadow-md）
  &--hover:hover {
    box-shadow: $shadow-md;
  }

  &__header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: $spacing-md;
    padding-bottom: $spacing-sm;
    border-bottom: 1px solid $border-light;
    font-size: $font-size-lg;
    font-weight: 700;                   // 对齐原型 text-xl font-bold
    color: $gray-900;                   // text-gray-900
  }

  &__header-aside {
    font-size: $font-size-base;
    font-weight: normal;
  }
}
</style>
