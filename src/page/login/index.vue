<template>
  <div class="login-container">
    <div class="login-box">
      <div class="login-title">{{ website.indexTitle }}</div>
      <el-form ref="loginFormRef" :model="loginForm" :rules="loginRules" class="login-form">
        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            prefix-icon="User"
            placeholder="请输入用户名"
            size="large"
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            prefix-icon="Lock"
            type="password"
            placeholder="请输入密码"
            size="large"
            show-password
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        <el-form-item v-if="website.captchaMode">
          <el-row :gutter="10" style="width: 100%">
            <el-col :span="14">
              <el-input v-model="loginForm.code" placeholder="验证码" size="large" @keyup.enter="handleLogin" />
            </el-col>
            <el-col :span="10">
              <div class="captcha-img" @click="refreshCaptcha">
                <img v-if="captchaUrl" :src="captchaUrl" alt="验证码" />
                <span v-else>点击获取</span>
              </div>
            </el-col>
          </el-row>
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            size="large"
            class="login-btn"
            :loading="loading"
            @click="handleLogin"
          >
            登 录
          </el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/store/modules/user'
import { getCaptcha } from '@/api/user'
import website from '@/config/website'
import { baseUrl } from '@/config/env'
import { randomString } from '@/util/util'

const router = useRouter()
const userStore = useUserStore()

const loginFormRef = ref(null)
const loading = ref(false)
const captchaUrl = ref('')

const loginForm = reactive({
  tenantId: website.tenantId,
  username: '',
  password: '',
  type: 'account',
  key: randomString(),
  code: '',
  switchMode: website.switchMode,
  captchaMode: website.captchaMode
})

const loginRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const refreshCaptcha = () => {
  loginForm.key = randomString()
  captchaUrl.value = `${baseUrl}/api/blade-auth/oauth/captcha?key=${loginForm.key}`
}

const handleLogin = async () => {
  if (!loginFormRef.value) return
  try {
    await loginFormRef.value.validate()
    loading.value = true
    await userStore.loginByUsername(loginForm)
    ElMessage.success('登录成功')
    router.push('/')
  } catch (error) {
    if (error) {
      console.error(error)
    }
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  if (website.captchaMode) {
    refreshCaptcha()
  }
})
</script>

<style lang="scss" scoped>
.captcha-img {
  height: 40px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;

  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
}
</style>
