<template>
  <div class="login-container">
    <!-- ============ 左侧：品牌展示区 ============ -->
    <aside class="login-brand">
      <!-- 顶部 Logo + 产品名 -->
      <div class="brand-header">
        <div class="brand-logo">{{ website.logo }}</div>
        <div class="brand-name">{{ website.indexTitle }}</div>
      </div>

      <!-- 中部：主标语 + 特性亮点 -->
      <div class="brand-body">
        <h1 class="brand-title">让产品营销<br/>更智能、更高效</h1>
        <p class="brand-subtitle">基于 AI 的产品营销内容生成平台，从产品知识管理到多渠道内容分发的一站式解决方案。</p>

        <ul class="brand-features">
          <li v-for="f in features" :key="f.title">
            <div class="feature-icon">
              <el-icon><component :is="f.icon" /></el-icon>
            </div>
            <div class="feature-text">
              <div class="feature-title">{{ f.title }}</div>
              <div class="feature-desc">{{ f.desc }}</div>
            </div>
          </li>
        </ul>
      </div>

      <!-- 底部版权 -->
      <div class="brand-footer">
        <span>© 2026 神行库 · 营销 AI</span>
      </div>
    </aside>

    <!-- ============ 右侧：登录表单区 ============ -->
    <main class="login-main">
      <div class="login-box">
        <!-- 表单标题 -->
        <div class="login-head">
          <h2>欢迎回来</h2>
          <p>请输入您的账号信息登录</p>
        </div>

        <el-form ref="loginFormRef" :model="loginForm" :rules="loginRules" class="login-form">
          <el-form-item prop="username">
            <el-input
              v-model="loginForm.username"
              :prefix-icon="User"
              placeholder="请输入用户名"
              size="large"
              @keyup.enter="handleLogin"
            />
          </el-form-item>
          <el-form-item prop="password">
            <el-input
              v-model="loginForm.password"
              :prefix-icon="Lock"
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
                <el-input v-model="loginForm.code" :prefix-icon="Picture" placeholder="验证码" size="large" @keyup.enter="handleLogin" />
              </el-col>
              <el-col :span="10">
                <div class="captcha-img" @click="refreshCaptcha">
                  <!-- Phase 4：使用本地 SVG 验证码（v-html 注入），后端就绪后可改回 <img :src="captchaUrl"> -->
                  <div v-if="captchaSvg" class="captcha-img__svg" v-html="captchaSvg" />
                  <span v-else>点击获取</span>
                </div>
              </el-col>
            </el-row>
          </el-form-item>

          <!-- 记住我 + 忘记密码 -->
          <div class="login-options">
            <el-checkbox v-model="remember">记住我</el-checkbox>
            <a class="forget-link" @click="onForget">忘记密码？</a>
          </div>

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

        <!-- 体验账号提示 -->
        <div class="login-tip">
          <el-icon><InfoFilled /></el-icon>
          <span>体验账号：<b>admin</b> / 任意密码即可登录</span>
        </div>

        <!-- 还没有账号？去注册 -->
        <div class="login-tip login-tip--center">
          <span>还没有账号？</span>
          <a class="link" @click="goRegister">立即注册</a>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, Picture, InfoFilled, MagicStick, DataAnalysis, Promotion } from '@element-plus/icons-vue'
import { useUserStore } from '@/store/modules/user'
import { getCaptcha } from '@/api/user'
import website from '@/config/website'
import { randomString } from '@/util/util'

const router = useRouter()
const userStore = useUserStore()

const loginFormRef = ref(null)
const loading = ref(false)
const remember = ref(false)
// Phase 4：本地 SVG 验证码串；后端就绪后改回 captchaUrl
const captchaSvg = ref('')

// 左侧品牌区特性亮点
const features = [
  { icon: MagicStick, title: 'AI 智能生成', desc: '一键生成多渠道营销内容' },
  { icon: DataAnalysis, title: '知识库管理', desc: '结构化沉淀产品信息' },
  { icon: Promotion, title: '多渠道分发', desc: '微信 / LinkedIn / PPT 适配' }
]

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

/**
 * 刷新本地 SVG 验证码
 * Phase 4：后端未启，本地生成 SVG；后端就绪后可改回 await getCaptcha() 拉真实图片
 */
const refreshCaptcha = async () => {
  loginForm.key = randomString()
  try {
    const resp = await getCaptcha()
    const payload = resp.data || resp || {}
    loginForm.key = payload.key || loginForm.key
    captchaSvg.value = payload.svg || ''
    // 把当前验证码正确答案暂存到 sessionStorage（仅前端演示用），便于登录时校验
    // 注意：真实环境必须由后端校验，前端任何"客户端比对"都属安全隐患
    if (payload.text) {
      sessionStorage.setItem('sxk-captcha-text', payload.text)
    }
  } catch (e) {
    captchaSvg.value = ''
  }
}

// 忘记密码（mock 阶段仅提示）
const onForget = () => {
  ElMessage.info('请联系管理员重置密码')
}

// 跳转注册页
const goRegister = () => {
  router.push('/register')
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
  border: 1px solid $border-base;
  border-radius: $radius-md;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  background: $bg-card;
  transition: $transition-fast;
  &:hover {
    border-color: $primary-color;
  }

  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  // Phase 4：本地 SVG 验证码容器
  &__svg {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    :deep(svg) {
      width: 100%;
      height: 100%;
      display: block;
    }
  }
}
</style>
