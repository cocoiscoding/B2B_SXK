<template>
  <div class="userinfo-page">
    <basic-block>
      <el-descriptions title="个人信息" :column="2" border>
        <el-descriptions-item label="用户名">{{ userStore.userInfo.user_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="昵称">{{ userStore.userInfo.nick_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="角色">{{ rolesText }}</el-descriptions-item>
        <el-descriptions-item label="租户">{{ userStore.userInfo.tenant_id || '-' }}</el-descriptions-item>
      </el-descriptions>
    </basic-block>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useUserStore } from '@/store/modules/user'

const userStore = useUserStore()
const rolesText = computed(() => {
  const roles = userStore.roles
  if (!roles || roles.length === 0) return '-'
  return roles.map((r) => r.role_name || r).join(', ')
})
</script>
