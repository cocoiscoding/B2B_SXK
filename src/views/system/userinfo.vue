<template>
  <div class="sxk-userinfo">
    <!-- 页面标题（与其他业务页统一：h2 24/700/gray-900 + 副标题） -->
    <div class="sxk-userinfo__head">
      <h2>个人信息</h2>
      <p>查看和管理你的账号信息与安全设置</p>
    </div>

    <!-- 用户横幅卡片：左侧头像 + 姓名/角色，右侧注册/最近登录 -->
    <section class="sxk-userinfo__banner">
      <div class="banner-left">
        <!-- 文字头像（avatar 为空时 fallback 为姓名首字，品牌蓝底白字） -->
        <div class="banner-avatar">{{ avatarText }}</div>
        <div class="banner-meta">
          <div class="banner-name">
            <span class="name-text">{{ info.real_name || info.nick_name || info.user_name || '用户' }}</span>
            <el-tag v-if="roleText" :type="info.role_id === 'r_admin' ? 'danger' : 'primary'" effect="light" round>
              {{ roleText }}
            </el-tag>
          </div>
          <div class="banner-sub">
            <el-icon><User /></el-icon>
            <span>{{ info.user_name || '-' }}</span>
            <el-icon class="ml"><OfficeBuilding /></el-icon>
            <span>{{ info.dept_name || '-' }}</span>
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
        <div class="stat-divider"></div>
        <div class="stat-item">
          <div class="stat-label">最近登录</div>
          <div class="stat-value">{{ formatDate(info.last_login_at) || '—' }}</div>
        </div>
      </div>
    </section>

    <!-- 账号信息 -->
    <section class="sxk-userinfo__card">
      <div class="card-title">
        <el-icon><Document /></el-icon>
        <span>账号信息</span>
      </div>
      <el-descriptions :column="2" border class="sxk-userinfo__desc">
        <el-descriptions-item label="用户名">{{ info.user_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="昵称">{{ info.nick_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="真实姓名">{{ info.real_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="角色">{{ roleText || '-' }}</el-descriptions-item>
        <el-descriptions-item label="所属部门">{{ info.dept_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="租户编号">{{ info.tenant_id || '-' }}</el-descriptions-item>
        <el-descriptions-item label="邮箱">{{ info.email || '-' }}</el-descriptions-item>
        <el-descriptions-item label="手机号">{{ info.phone || '-' }}</el-descriptions-item>
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
            <div class="security-name">绑定手机</div>
            <div class="security-desc">{{ info.phone ? `已绑定 ${info.phone}` : '未绑定' }}</div>
          </div>
          <el-button type="primary" text>{{ info.phone ? '更换' : '去绑定' }}</el-button>
        </div>
        <div class="security-item">
          <div class="security-info">
            <div class="security-name">绑定邮箱</div>
            <div class="security-desc">{{ info.email ? `已绑定 ${info.email}` : '未绑定' }}</div>
          </div>
          <el-button type="primary" text>{{ info.email ? '更换' : '去绑定' }}</el-button>
        </div>
      </div>
    </section>

    <!-- 修改密码弹窗（mock 阶段仅前端校验） -->
    <el-dialog v-model="pwdDialog" title="修改密码" width="420px" append-to-body>
      <el-form ref="pwdFormRef" :model="pwdForm" :rules="pwdRules" label-width="90px">
        <el-form-item label="原密码" prop="old">
          <el-input v-model="pwdForm.old" type="password" show-password placeholder="请输入原密码" />
        </el-form-item>
        <el-form-item label="新密码" prop="new">
          <el-input v-model="pwdForm.new" type="password" show-password placeholder="6-20 位，需含字母与数字" />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirm">
          <el-input v-model="pwdForm.confirm" type="password" show-password placeholder="请再次输入新密码" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="pwdDialog = false">取消</el-button>
        <el-button type="primary" @click="submitPwd">确认修改</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { User, OfficeBuilding, Message, Document, Lock } from '@element-plus/icons-vue'
import { useUserStore } from '@/store/modules/user'

const userStore = useUserStore()
const info = computed(() => userStore.userInfo || {})

// 角色文本：兼容 roles 数组或 role_name 字段
const roleText = computed(() => {
  const roles = userStore.roles
  if (roles && roles.length) {
    return roles.map((r) => r.role_name || r.role_alias || r).join('、')
  }
  return info.value.role_name || ''
})

// 头像首字（取真实姓名/昵称/用户名第一个字符）
const avatarText = computed(() => {
  const name = info.value.real_name || info.value.nick_name || info.value.user_name || ''
  return name ? name.charAt(0).toUpperCase() : 'U'
})

// 简单日期格式化：兼容 ISO 字符串 / 'YYYY-MM-DD HH:mm:ss'
const formatDate = (val) => {
  if (!val) return ''
  const d = new Date(val)
  if (isNaN(d.getTime())) return String(val)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

// ========== 修改密码（mock 阶段仅前端交互） ==========
const pwdDialog = ref(false)
const pwdFormRef = ref(null)
const pwdForm = reactive({ old: '', new: '', confirm: '' })

const validateConfirm = (rule, value, callback) => {
  if (value !== pwdForm.new) callback(new Error('两次输入的密码不一致'))
  else callback()
}

const pwdRules = {
  old: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
  new: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度 6-20 位', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value && !/(?=.*[a-zA-Z])(?=.*\d)/.test(value)) {
          callback(new Error('需同时包含字母与数字'))
        } else callback()
      },
      trigger: 'blur'
    }
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
    // Mock 阶段：不真实修改，仅提示成功
    ElMessage.success('密码修改成功（Mock 演示，未真实提交）')
    pwdDialog.value = false
  } catch {
    // 校验失败
  }
}
</script>

<style lang="scss" scoped>
// 个人信息页：与 Dashboard / knowledge 风格保持一致
.sxk-userinfo {
  display: flex;
  flex-direction: column;
  gap: $spacing-md;

  // 页面标题（统一：h2 700/gray-900 + 副标题 sm/gray-500）
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

  // 用户横幅卡片：品牌色浅底 + 左头像/右统计
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

      // 文字头像：64px 圆形，品牌蓝渐变底 + 白字
      .banner-avatar {
        width: 64px;
        height: 64px;
        border-radius: $radius-round;
        background: linear-gradient(135deg, #{$primary-color} 0%, #{$primary-color-hover} 100%);
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

      .stat-divider {
        width: 1px;
        height: 32px;
        background-color: rgba(26, 86, 219, 0.2);
      }
    }
  }

  // 信息卡片（白底 + 边框 + 圆角，对齐 basic-block 视觉）
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
