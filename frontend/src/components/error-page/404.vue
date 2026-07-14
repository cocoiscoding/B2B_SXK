<template>
  <div class="error-page">
    <div class="error-content">
      <h1 class="error-code">
        404
      </h1>
      <p class="error-desc">
        页面不存在
      </p>
      <el-button
        type="primary"
        @click="goHome"
      >
        返回首页
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
const router = useRouter()
const goHome = () => router.push('/')
</script>

<style lang="scss" scoped>
.error-page {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100vh;
  text-align: center;
}
.error-code {
  font-size: 120px;
  margin: 0;
  color: #409eff;
}
.error-desc {
  font-size: 18px;
  color: #606266;
  margin: 20px 0;
}
</style>
