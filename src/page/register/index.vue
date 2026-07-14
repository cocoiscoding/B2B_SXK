<template>
  <div class="login-container">
    <!-- ============ 左侧：品牌展示区（与登录页完全一致）============ -->
    <aside class="login-brand">
      <div class="brand-header">
        <div class="brand-logo">{{ website.logo }}</div>
        <div class="brand-name">{{ website.indexTitle }}</div>
      </div>

      <div class="brand-body">
        <h1 class="brand-title">开启你的<br/>智能营销之旅</h1>
        <p class="brand-subtitle">注册账号，即可体验 AI 驱动的产品营销内容生成、知识库管理与多渠道分发能力。</p>

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

      <div class="brand-footer">
        <span>© 2026 神行库 · 营销 AI</span>
      </div>
    </aside>

    <!-- ============ 右侧：注册表单区 ============ -->
    <main class="login-main">
      <div class="login-box">
        <!-- 表单标题 -->
        <div class="login-head">
          <h2>创建账号</h2>
          <p>填写以下信息完成注册</p>
        </div>

        <el-form ref="regFormRef" :model="regForm" :rules="regRules" class="login-form">
          <el-form-item prop="username">
            <el-input
              v-model="regForm.username"
              :prefix-icon="User"
              placeholder="请输入用户名"
              size="large"
            />
          </el-form-item>
          <el-form-item prop="email">
            <el-input
              v-model="regForm.email"
              :prefix-icon="Message"
              placeholder="请输入邮箱"
              size="large"
            />
          </el-form-item>
          <el-form-item prop="password">
            <el-input
              v-model="regForm.password"
              :prefix-icon="Lock"
              type="password"
              placeholder="请输入密码（6-20 位，含字母与数字）"
              size="large"
              show-password
            />
          </el-form-item>
          <el-form-item prop="confirm">
            <el-input
              v-model="regForm.confirm"
              :prefix-icon="Lock"
              type="password"
              placeholder="请再次输入密码"
              size="large"
              show-password
              @keyup.enter="handleRegister"
            />
          </el-form-item>
          <el-form-item prop="code">
            <el-row :gutter="10" style="width: 100%">
              <el-col :span="14">
                <el-input v-model="regForm.code" :prefix-icon="Picture" placeholder="验证码" size="large" @keyup.enter="handleRegister" />
              </el-col>
              <el-col :span="10">
                <div class="captcha-img" @click="refreshCaptcha">
                  <div v-if="captchaSvg" class="captcha-img__svg" v-html="captchaSvg" />
                  <span v-else>点击获取</span>
                </div>
              </el-col>
            </el-row>
          </el-form-item>

          <!-- 用户协议 -->
          <div class="login-options">
            <el-checkbox v-model="agreed">
              我已阅读并同意<a class="agree-link" @click.prevent="onAgreement">《用户协议》</a>
            </el-checkbox>
          </div>

          <el-form-item>
            <el-button
              type="primary"
              size="large"
              class="login-btn"
              :loading="loading"
              :disabled="!agreed"
              @click="handleRegister"
            >
              注 册
            </el-button>
          </el-form-item>
        </el-form>

        <!-- 已有账号？去登录 -->
        <div class="login-tip login-tip--center">
          <span>已有账号？</span>
          <a class="link" @click="goLogin">立即登录</a>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, Message, Picture, MagicStick, DataAnalysis, Promotion } from '@element-plus/icons-vue'
import { getCaptcha, registerByInfo } from '@/api/user'
import website from '@/config/website'
import { randomString } from '@/util/util'

const router = useRouter()

const regFormRef = ref(null)
const loading = ref(false)
const agreed = ref(false)
const captchaSvg = ref('')

// 左侧品牌区特性亮点（与登录页保持一致的品牌传达）
const features = [
  { icon: MagicStick, title: 'AI 智能生成', desc: '一键生成多渠道营销内容' },
  { icon: DataAnalysis, title: '知识库管理', desc: '结构化沉淀产品信息' },
  { icon: Promotion, title: '多渠道分发', desc: '微信 / LinkedIn / PPT 适配' }
]

const regForm = reactive({
  username: '',
  email: '',
  password: '',
  confirm: '',
  key: randomString(),
  code: ''
})

// 密码强度规则：6-20 位，需同时含字母与数字
const validatePassword = (rule, value, callback) => {
  if (value && !/(?=.*[a-zA-Z])(?=.*\d)/.test(value)) {
    callback(new Error('密码需同时包含字母与数字'))
  } else callback()
}

const validateConfirm = (rule, value, callback) => {
  if (value !== regForm.password) callback(new Error('两次输入的密码不一致'))
  else callback()
}

const validateCode = (rule, value, callback) => {
  if (!value) {
    callback(new Error('请输入验证码'))
  } else {
    // Mock 阶段：与登录页一致，前端比对 sessionStorage 中的答案
    const answer = sessionStorage.getItem('sxk-captcha-text')
    if (answer && value.toLowerCase() !== answer.toLowerCase()) {
      callback(new Error('验证码不正确'))
    } else {
      callback()
    }
  }
}

const regRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度 3-20 个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度 6-20 位', trigger: 'blur' },
    { validator: validatePassword, trigger: 'blur' }
  ],
  confirm: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    { validator: validateConfirm, trigger: 'blur' }
  ],
  code: [{ validator: validateCode, trigger: 'blur' }]
}

/**
 * 刷新本地 SVG 验证码（复用登录页同一套 getCaptcha 接口）
 */
const refreshCaptcha = async () => {
  regForm.key = randomString()
  try {
    const resp = await getCaptcha()
    const payload = resp.data || resp || {}
    regForm.key = payload.key || regForm.key
    captchaSvg.value = payload.svg || ''
    if (payload.text) {
      sessionStorage.setItem('sxk-captcha-text', payload.text)
    }
  } catch (e) {
    captchaSvg.value = ''
  }
}

const onAgreement = () => {
  ElMessage.info('用户协议内容待完善')
}

const handleRegister = async () => {
  if (!regFormRef.value) return
  if (!agreed.value) {
    ElMessage.warning('请先勾选同意用户协议')
    return
  }
  try {
    await regFormRef.value.validate()
    loading.value = true
    // 真实链路：POST /api/sxk/auth/register
    // 请求体：{ username, email, password, key, code }
    // code !== 0 时由 axios 拦截器统一提示并 reject，进入下方 catch
    await registerByInfo(
      regForm.username,
      regForm.email,
      regForm.password,
      regForm.key,
      regForm.code
    )
    ElMessage.success('注册成功，请使用新账号登录')
    router.push('/login')
  } catch (error) {
    // 表单校验失败 / 注册失败（如验证码错误、用户名已存在）
    // 拦截器已提示具体错误，这里刷新验证码
    refreshCaptcha()
  } finally {
    loading.value = false
  }
}

const goLogin = () => {
  router.push('/login')
}

onMounted(() => {
  refreshCaptcha()
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
