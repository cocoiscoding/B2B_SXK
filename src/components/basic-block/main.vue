<template>
  <div class="basic-block">
    <slot />
  </div>
</template>

<script setup>
// 通用块容器
</script>

<style lang="scss" scoped>
.basic-block {
  margin-bottom: 8px;
  padding: 16px;
  background: #fff;
  border-radius: 4px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}
</style>
