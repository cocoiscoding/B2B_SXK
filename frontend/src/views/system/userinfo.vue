<template>
  <div class="sxk-userinfo">
    <!-- 页面标题 -->
    <div class="sxk-userinfo__head">
      <h2>个人信息</h2>
      <p>查看和管理你的账号信息与安全设置</p>
    </div>

    <!-- 用户横幅卡片：左侧头像 + 姓名/角色，右侧注册时间 -->
    <section class="sxk-userinfo__banner">
      <div class="banner-left">
        <div class="banner-avatar" :style="{ background: avatarBg }">{{ avatarText }}</div>
        <div class="banner-meta">
          <div class="banner-name">
            <span class="name-text">{{ displayName }}</span>
            <el-tag :type="info.is_admin ? 'danger' : 'primary'" effect="light" round>
              {{ info.is_admin ? '管理员' : '普通用户' }}
            </el-tag>
          </div>
          <div class="banner-sub">
            <el-icon><User /></el-icon>
            <span>{{ info.username || '-' }}</span>
            <el-icon class="ml"><Message /></el-icon>
            <span>{{ info.email || '-' }}</span>
          </div>
        </div>
      </div>
      <div class="banner-right">
        <div class="stat-item">
          <div class="stat-label">注册时间</div>
          <div class="stat-value">{{ formatDate(info.created_at) || '—' }}</div>
        </div>
      </div>
    </section>

    <!-- 账号信息 -->
    <section class="sxk-userinfo__card">
      <div class="card-title">
        <el-icon><Document /></el-icon>
        <span>账号信息</span>
        <el-button type="primary" text class="card-edit-btn" @click="openProfileDialog">编辑</el-button>
      </div>
      <el-descriptions :column="2" border class="sxk-userinfo__desc">
        <el-descriptions-item label="用户名">{{ info.username || '-' }}</el-descriptions-item>
        <el-descriptions-item label="姓名">{{ info.name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="角色">{{ info.is_admin ? '管理员' : '普通用户' }}</el-descriptions-item>
        <el-descriptions-item label="邮箱">{{ info.email || '-' }}</el-descriptions-item>
        <el-descriptions-item label="用户ID">{{ info.id || '-' }}</el-descriptions-item>
        <el-descriptions-item label="注册时间">{{ formatDate(info.created_at) || '-' }}</el-descriptions-item>
      </el-descriptions>
    </section>

    <!-- 安全设置 -->
    <section class="sxk-userinfo__card">
      <div class="card-title">
        <el-icon><Lock /></el-icon>
        <span>安全设置</span>
      </div>
      <div class="security-list">
        <div class="security-item">
          <div class="security-info">
            <div class="security-name">登录密码</div>
            <div class="security-desc">建议定期更换密码，保障账号安全</div>
          </div>
          <el-button type="primary" text @click="handleEditPassword">修改</el-button>
        </div>
        <div class="security-item">
          <div class="security-info">
            <div class="security-name">绑定邮箱</div>
            <div class="security-desc">{{ info.email ? `已绑定 ${info.email}` : '未绑定' }}</div>
          </div>
          <el-button type="primary" text @click="openProfileDialog">{{ info.email ? '更换' : '去绑定' }}</el-button>
        </div>
      </div>
    </section>

    <!-- 编辑资料弹窗 -->
    <el-dialog v-model="profileDialog" title="编辑个人资料" width="440px" append-to-body>
      <el-form ref="profileFormRef" :model="profileForm" :rules="profileRules" label-width="80px">
        <el-form-item label="用户名">
          <el-input :model-value="info.username" disabled />
        </el-form-item>
        <el-form-item label="姓名" prop="name">
          <el-input v-model="profileForm.name" placeholder="请输入姓名" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="profileForm.email" placeholder="请输入邮箱" />
        </el-form-item>
        <el-form-item label="头像色">
          <el-color-picker v-model="profileForm.color" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="profileDialog = false">取消</el-button>
        <el-button type="primary" :loading="profileSaving" @click="submitProfile">保存</el-button>
      </template>
    </el-dialog>

    <!-- 修改密码弹窗 -->
    <el-dialog v-model="pwdDialog" title="修改密码" width="420px" append-to-body>
      <el-form ref="pwdFormRef" :model="pwdForm" :rules="pwdRules" label-width="90px">
        <el-form-item label="原密码" prop="old">
          <el-input v-model="pwdForm.old" type="password" show-password placeholder="请输入原密码" />
        </el-form-item>
        <el-form-item label="新密码" prop="new">
          <el-input v-model="pwdForm.new" type="password" show-password placeholder="6-20 位" />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirm">
          <el-input v-model="pwdForm.confirm" type="password" show-password placeholder="请再次输入新密码" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="pwdDialog = false">取消</el-button>
        <el-button type="primary" :loading="pwdSaving" @click="submitPwd">确认修改</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { User, Message, Document, Lock } from '@element-plus/icons-vue'
import { useUserStore } from '@/store/modules/user'
import { updateUserInfo } from '@/api/user'

const userStore = useUserStore()
const info = computed(() => userStore.userInfo || {})

// 显示名：优先 name，其次 mock 遗留字段
const displayName = computed(() => info.value.name || info.value.nick_name || info.value.username || '用户')

// 头像首字
const avatarText = computed(() => {
  const name = info.value.name || info.value.username || ''
  return name ? name.charAt(0).toUpperCase() : 'U'
})

// 头像背景色：用用户 color 字段或品牌蓝渐变
const avatarBg = computed(() => {
  const c = info.value.color
  if (c) return c
  return `linear-gradient(135deg, #1a56db 0%, #3b82f6 100%)`
})

// 日期格式化
const formatDate = (val) => {
  if (!val) return ''
  const d = new Date(val)
  if (isNaN(d.getTime())) return String(val)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

// ========== 编辑资料 ==========
const profileDialog = ref(false)
const profileFormRef = ref(null)
const profileSaving = ref(false)
const profileForm = reactive({ name: '', email: '', color: '' })

const profileRules = {
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ]
}

const openProfileDialog = () => {
  profileForm.name = info.value.name || ''
  profileForm.email = info.value.email || ''
  profileForm.color = info.value.color || '#409eff'
  profileDialog.value = true
}

const submitProfile = async () => {
  try {
    await profileFormRef.value.validate()
    profileSaving.value = true
    const res = await updateUserInfo({
      name: profileForm.name,
      email: profileForm.email,
      color: profileForm.color
    })
    // 后端裸格式：直接返回 User 对象
    const updatedUser = res.data || {}
    // 同步到 store
    userStore.setUserInfo({ ...info.value, ...updatedUser })
    ElMessage.success('资料更新成功')
    profileDialog.value = false
  } catch (err) {
    if (err?.response?.data?.detail) {
      ElMessage.error(err.response.data.detail)
    }
  } finally {
    profileSaving.value = false
  }
}

// ========== 修改密码 ==========
const pwdDialog = ref(false)
const pwdFormRef = ref(null)
const pwdSaving = ref(false)
const pwdForm = reactive({ old: '', new: '', confirm: '' })

const validateConfirm = (rule, value, callback) => {
  if (value !== pwdForm.new) callback(new Error('两次输入的密码不一致'))
  else callback()
}

const pwdRules = {
  old: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
  new: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度 6-20 位', trigger: 'blur' }
  ],
  confirm: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    { validator: validateConfirm, trigger: 'blur' }
  ]
}

const handleEditPassword = () => {
  pwdForm.old = ''
  pwdForm.new = ''
  pwdForm.confirm = ''
  pwdDialog.value = true
}

const submitPwd = async () => {
  try {
    await pwdFormRef.value.validate()
    pwdSaving.value = true
    await updateUserInfo({
      old_password: pwdForm.old,
      new_password: pwdForm.new
    })
    ElMessage.success('密码修改成功')
    pwdDialog.value = false
  } catch (err) {
    if (err?.response?.data?.detail) {
      ElMessage.error(err.response.data.detail)
    }
  } finally {
    pwdSaving.value = false
  }
}
</script>

<style lang="scss" scoped>
// 个人信息页：与 Dashboard / knowledge 风格保持一致
.sxk-userinfo {
  display: flex;
  flex-direction: column;
  gap: $spacing-md;

  // 页面标题
  &__head {
    h2 {
      margin: 0 0 $spacing-xs;
      font-size: $font-size-xl;
      font-weight: 700;
      color: $gray-900;
    }
    p {
      margin: 0;
      font-size: $font-size-sm;
      color: $text-regular;
    }
  }

  // 用户横幅卡片
  &__banner {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: $spacing-lg;
    padding: $spacing-xl $spacing-2xl;
    background: linear-gradient(135deg, #{$primary-color-light} 0%, #{$primary-color-lighter} 100%);
    border-radius: $radius-lg;
    flex-wrap: wrap;

    .banner-left {
      display: flex;
      align-items: center;
      gap: $spacing-lg;

      .banner-avatar {
        width: 64px;
        height: 64px;
        border-radius: $radius-round;
        color: #fff;
        font-size: 28px;
        font-weight: 700;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
        box-shadow: 0 4px 12px rgba(26, 86, 219, 0.25);
      }

      .banner-meta {
        .banner-name {
          display: flex;
          align-items: center;
          gap: $spacing-sm;
          margin-bottom: $spacing-xs;

          .name-text {
            font-size: 20px;
            font-weight: 700;
            color: $gray-900;
          }
        }

        .banner-sub {
          display: flex;
          align-items: center;
          flex-wrap: wrap;
          font-size: $font-size-sm;
          color: $text-secondary;

          .ml {
            margin-left: $spacing-md;
          }

          .el-icon {
            margin-right: 4px;
          }
        }
      }
    }

    .banner-right {
      display: flex;
      align-items: center;
      gap: $spacing-xl;

      .stat-item {
        text-align: right;

        .stat-label {
          font-size: $font-size-xs;
          color: $text-secondary;
          margin-bottom: 4px;
        }

        .stat-value {
          font-size: $font-size-base;
          font-weight: 600;
          color: $gray-900;
        }
      }
    }
  }

  // 信息卡片
  &__card {
    padding: $spacing-lg;
    background: $bg-card;
    border: 1px solid $border-base;
    border-radius: $radius-lg;
    box-shadow: $shadow-sm;

    .card-title {
      display: flex;
      align-items: center;
      gap: $spacing-sm;
      margin-bottom: $spacing-lg;
      font-size: $font-size-base;
      font-weight: 700;
      color: $gray-900;

      .el-icon {
        color: $primary-color;
        font-size: 18px;
      }

      .card-edit-btn {
        margin-left: auto;
        font-size: $font-size-sm;
      }
    }
  }

  // el-descriptions 样式微调
  &__desc {
    :deep(.el-descriptions__label) {
      width: 110px;
      color: $text-secondary;
      font-weight: 500;
      background-color: $bg-page !important;
    }
    :deep(.el-descriptions__content) {
      color: $text-primary;
    }
  }

  // 安全设置列表
  .security-list {
    display: flex;
    flex-direction: column;
  }

  .security-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: $spacing-lg 0;
    border-bottom: 1px solid $border-light;

    &:last-child {
      border-bottom: none;
    }

    .security-info {
      .security-name {
        font-size: $font-size-base;
        font-weight: 500;
        color: $text-primary;
        margin-bottom: 2px;
      }

      .security-desc {
        font-size: $font-size-sm;
        color: $text-secondary;
      }
    }
  }
}
</style>
