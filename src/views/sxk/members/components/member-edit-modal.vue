<!--
  成员添加/编辑弹窗
  - 对应 Phase C
  - 字段：用户名（仅新增时必填）、密码（仅新增时必填）、昵称、邮箱、颜色、是否管理员
  - 通过 v-model 控制显示，:member-id 区分新增/编辑
-->
<template>
  <el-dialog
    :model-value="modelValue"
    width="520px"
    top="10vh"
    :show-close="false"
    :close-on-click-modal="false"
    class="member-edit-dialog"
    @update:model-value="(v) => $emit('update:modelValue', v)"
    @open="initForm"
  >
    <div class="me-head">
      <h3 class="me-head__title">
        <el-icon class="me-head__icon"><component :is="isEdit ? EditPen : Plus" /></el-icon>
        {{ isEdit ? '编辑成员' : '添加成员' }}
      </h3>
      <button class="me-head__close" @click="$emit('update:modelValue', false)">
        <el-icon :size="20"><Close /></el-icon>
      </button>
    </div>

    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="92px"
      v-loading="loading"
      class="me-form"
    >
      <el-form-item label="用户名" prop="username">
        <el-input v-model="form.username" :disabled="isEdit" placeholder="登录用户名（仅新增时设置）" maxlength="32" />
      </el-form-item>

      <el-form-item v-if="!isEdit" label="密码" prop="password">
        <el-input v-model="form.password" type="password" show-password placeholder="初始密码" maxlength="64" />
      </el-form-item>

      <el-form-item label="昵称" prop="nickname">
        <el-input v-model="form.nickname" placeholder="显示名称" maxlength="32" />
      </el-form-item>

      <el-form-item label="邮箱" prop="email">
        <el-input v-model="form.email" placeholder="如：alice@example.com" maxlength="64" />
      </el-form-item>

      <el-form-item label="主题色">
        <el-color-picker v-model="form.color" :predefine="colorPresets" />
      </el-form-item>

      <el-form-item label="角色">
        <el-switch
          v-model="form.is_admin"
          active-text="管理员"
          inactive-text="普通成员"
          inline-prompt
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <div class="me-foot">
        <el-button @click="cancel">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submit">
          {{ isEdit ? '保存修改' : '创建成员' }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Close, EditPen, Plus } from '@element-plus/icons-vue'
import sxkApi from '@/mock/sxkApi'

// ========== 预设颜色 ==========
const colorPresets = [
  '#3b82f6',  // 蓝
  '#10b981',  // 翠
  '#f59e0b',  // 橙
  '#ef4444',  // 红
  '#8b5cf6',  // 紫
  '#06b6d4',  // 青
  '#ec4899',  // 粉
  '#6b7280'   // 灰
]

// ========== v-model ==========
const props = defineProps({
  modelValue: { type: Boolean, default: false },
  memberId: { type: String, default: null }
})
const emit = defineEmits(['update:modelValue', 'saved'])

// ========== 表单状态 ==========
const formRef = ref(null)
const loading = ref(false)
const saving = ref(false)

const blankForm = () => ({
  username: '',
  password: '',
  nickname: '',
  email: '',
  color: '#3b82f6',
  is_admin: false
})
const form = reactive(blankForm())

const isEdit = computed(() => !!props.memberId)

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 32, message: '用户名长度 3-32', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 64, message: '密码长度 6-64', trigger: 'blur' }
  ],
  nickname: [{ required: true, message: '请输入昵称', trigger: 'blur' }],
  email: [
    {
      validator: (rule, value, cb) => {
        if (!value) return cb()
        if (!/^[\w.+-]+@[\w-]+\.[\w.-]+$/.test(value)) {
          return cb(new Error('邮箱格式不正确'))
        }
        cb()
      },
      trigger: 'blur'
    }
  ]
}

// ========== 数据加载 ==========
const initForm = async () => {
  Object.assign(form, blankForm())
  if (!props.memberId) return
  loading.value = true
  try {
    const res = await sxkApi.listMembers()
    loading.value = false
    if (res.code === 0) {
      const target = (res.data || []).find((m) => m.id === props.memberId)
      if (target) {
        Object.assign(form, {
          username: target.username,
          nickname: target.nickname || '',
          email: target.email || '',
          color: target.color || '#3b82f6',
          is_admin: !!target.is_admin
        })
      }
    }
  } catch {
    loading.value = false
  }
}

const cancel = () => emit('update:modelValue', false)

const submit = async () => {
  try {
    await formRef.value?.validate()
  } catch {
    return
  }
  saving.value = true
  let res
  if (isEdit.value) {
    // 编辑：不传 username / password
    const payload = {
      nickname: form.nickname,
      email: form.email,
      color: form.color,
      is_admin: form.is_admin
    }
    res = await sxkApi.updateMember(props.memberId, payload)
  } else {
    res = await sxkApi.createMember({ ...form })
  }
  saving.value = false
  if (res.code === 0) {
    ElMessage.success(isEdit.value ? '已保存' : '已创建')
    emit('saved')
    emit('update:modelValue', false)
  } else {
    ElMessage.error(res.msg || '保存失败')
  }
}
</script>

<style lang="scss">
// 全局样式：覆盖 el-dialog 默认 padding
.member-edit-dialog {
  .el-dialog__header {
    display: none;
  }
  .el-dialog__body {
    padding: 0;
  }
  .el-dialog__footer {
    padding: 0;
  }
}
</style>

<style lang="scss" scoped>
.me-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: $spacing-lg;
  border-bottom: 1px solid $border-light;

  &__title {
    display: flex;
    align-items: center;
    gap: $spacing-sm;
    font-size: 16px;
    font-weight: 600;
    color: $text-primary;
    margin: 0;
  }

  &__icon {
    color: $primary-color;
    font-size: 20px;
  }

  &__close {
    background: none;
    border: none;
    cursor: pointer;
    color: $text-placeholder;
    padding: 4px;
    border-radius: $radius-sm;
    display: flex;

    &:hover {
      color: $text-primary;
      background: $gray-100;
    }
  }
}

.me-form {
  padding: $spacing-lg;
}

.me-foot {
  display: flex;
  justify-content: flex-end;
  gap: $spacing-sm;
  padding: $spacing-md $spacing-lg;
  border-top: 1px solid $border-light;
}
</style>
