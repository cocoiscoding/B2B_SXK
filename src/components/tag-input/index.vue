<!--
  标签输入器（Tag Input）
  - 支持：回车添加 / 单击删除 / 失焦自动补全已输入未回车的文本
  - 用于：产品知识库的目标客户/竞品/卖点，自定义模板的标签等
-->
<template>
  <div class="tag-input" :class="{ 'is-focused': focused, 'is-disabled': disabled }">
    <el-tag
      v-for="(tag, idx) in modelValue"
      :key="tag + '-' + idx"
      :closable="!disabled"
      type="info"
      effect="plain"
      @close="remove(idx)"
    >
      {{ tag }}
    </el-tag>
    <input
      v-if="!disabled"
      v-model="input"
      class="tag-input__native"
      :placeholder="modelValue.length === 0 ? placeholder : ''"
      @keydown.enter.prevent="commit"
      @keydown.delete="onBackspace"
      @blur="onBlur"
      @focus="focused = true"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  placeholder: { type: String, default: '回车添加' },
  disabled: { type: Boolean, default: false }
})
const emit = defineEmits(['update:modelValue'])

const input = ref('')
const focused = ref(false)

// 添加标签
const commit = () => {
  const val = input.value.trim()
  if (!val) return
  if (props.modelValue.includes(val)) {
    input.value = ''
    return
  }
  emit('update:modelValue', [...props.modelValue, val])
  input.value = ''
}

// 删除标签
const remove = (idx) => {
  const next = props.modelValue.slice()
  next.splice(idx, 1)
  emit('update:modelValue', next)
}

// 失焦时自动提交
const onBlur = () => {
  focused.value = false
  commit()
}

// 输入框为空且按删除 → 删除最后一个标签
const onBackspace = () => {
  if (input.value === '' && props.modelValue.length > 0) {
    remove(props.modelValue.length - 1)
  }
}

// 暴露 commit 方法给父组件（用于父组件在 submit 前强制收集未提交的输入）
defineExpose({ commit })
</script>

<style lang="scss" scoped>
.tag-input {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: $spacing-xs;
  min-height: 32px;
  padding: $spacing-xs $spacing-sm;
  border: 1px solid $border-base;
  border-radius: $radius-sm;
  background: $bg-card;
  transition: $transition-fast;
  cursor: text;

  &:hover {
    border-color: $border-dark;
  }
  &.is-focused {
    border-color: $primary-color;
    box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.1);
  }
  &.is-disabled {
    cursor: default;
    background: $gray-50;
    &:hover {
      border-color: $border-base;
    }
  }

  &__native {
    flex: 1;
    min-width: 120px;
    border: none;
    outline: none;
    background: transparent;
    font-size: $font-size-base;
    padding: $spacing-xs 0;
    color: $text-primary;
  }
}
</style>
