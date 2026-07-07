<template>
  <div class="login-container">
    <div class="login-box">
      <div class="login-title">注册</div>
      <el-form ref="formRef" :model="form" :rules="rules">
        <el-form-item prop="name">
          <el-input v-model="form.name" placeholder="昵称" prefix-icon="User" size="large" />
        </el-form-item>
        <el-form-item prop="account">
          <el-input v-model="form.account" placeholder="账号" prefix-icon="User" size="large" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="form.password" type="password" placeholder="密码" prefix-icon="Lock" size="large" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" class="login-btn" size="large" @click="handleRegister">注 册</el-button>
          <el-button size="large" @click="$router.push('/login')">返回登录</el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const formRef = ref(null)
const form = reactive({ name: '', account: '', password: '' })
const rules = {
  name: [{ required: true, message: '请输入昵称', trigger: 'blur' }],
  account: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}
const handleRegister = async () => {
  if (!formRef.value) return
  await formRef.value.validate()
  router.push('/login')
}
</script>
