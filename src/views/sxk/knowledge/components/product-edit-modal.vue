<!--
  产品添加/编辑弹窗
  - 对应需求文档 5.2.3 / 4.3.3 / 4.3.4
  - 字段规则（BR-K-03/04）：
      * 产品名称、分类必填
      * 功能列表 ≥ 1
      * 标签（target_customers / competitors / selling_points）支持回车添加
  - 通过 v-model 控制显示，:product-id 区分新增/编辑
-->
<template>
  <el-dialog
    :model-value="modelValue"
    :title="isEdit ? '编辑产品' : '添加产品'"
    width="640px"
    :close-on-click-modal="false"
    @update:model-value="(v) => $emit('update:modelValue', v)"
    @open="initForm"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="100px"
      v-loading="loading"
    >
      <el-form-item label="产品名称" prop="name">
        <el-input v-model="form.name" placeholder="如：智能数据平台 X" maxlength="64" show-word-limit />
      </el-form-item>

      <el-form-item label="产品分类" prop="category">
        <el-select v-model="form.category" placeholder="请选择" style="width: 100%">
          <el-option label="数据分析" value="数据分析" />
          <el-option label="CRM" value="CRM" />
          <el-option label="营销自动化" value="营销自动化" />
          <el-option label="其他" value="其他" />
        </el-select>
      </el-form-item>

      <el-form-item label="产品描述" prop="description">
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="3"
          placeholder="建议至少 10 字符，简明描述产品定位"
          maxlength="500"
          show-word-limit
        />
      </el-form-item>

      <!-- 功能特性：动态列表 -->
      <el-form-item label="功能特性" prop="features" required>
        <div class="dynamic-list">
          <div
            v-for="(f, idx) in form.features"
            :key="idx"
            class="dynamic-list__row"
          >
            <el-input
              v-model="f.name"
              placeholder="功能名称"
              style="width: 160px"
            />
            <el-input
              v-model="f.description"
              placeholder="功能描述（可选）"
              style="flex: 1"
            />
            <el-button
              :disabled="form.features.length <= 1"
              link
              type="danger"
              @click="removeFeature(idx)"
            >删除</el-button>
          </div>
          <el-button link type="primary" @click="addFeature">
            + 添加功能
          </el-button>
        </div>
      </el-form-item>

      <el-form-item label="目标客户">
        <tag-input v-model="form.target_customers" placeholder="回车添加（如：制造业）" />
      </el-form-item>

      <el-form-item label="价格信息">
        <el-input
          v-model="form.pricing"
          placeholder="如：基础版 ¥50,000/年"
          maxlength="255"
        />
      </el-form-item>

      <el-form-item label="竞品名称">
        <tag-input v-model="form.competitors" placeholder="回车添加（如：产品 Y）" />
      </el-form-item>

      <el-form-item label="产品卖点">
        <tag-input v-model="form.selling_points" placeholder="回车添加（如：部署快）" />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="cancel">取消</el-button>
      <el-button type="primary" :loading="saving" @click="submit">
        {{ isEdit ? '保存修改' : '创建产品' }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import sxkApi from '@/mock/sxkApi'
import TagInput from '@/components/tag-input/index.vue'

// ========== v-model ==========
const props = defineProps({
  modelValue: { type: Boolean, default: false },
  productId: { type: String, default: null }
})
const emit = defineEmits(['update:modelValue', 'saved'])

// ========== 表单状态 ==========
const formRef = ref(null)
const loading = ref(false)
const saving = ref(false)

const blankForm = () => ({
  name: '',
  category: '',
  description: '',
  pricing: '',
  features: [{ name: '', description: '' }],
  target_customers: [],
  competitors: [],
  selling_points: []
})
const form = reactive(blankForm())

const isEdit = computed(() => !!props.productId)

const rules = {
  name: [{ required: true, message: '请输入产品名称', trigger: 'blur' }],
  category: [{ required: true, message: '请选择分类', trigger: 'change' }]
}

// ========== 动态功能列表 ==========
const addFeature = () =>
  form.features.push({ name: '', description: '' })

const removeFeature = (idx) => {
  if (form.features.length <= 1) return
  form.features.splice(idx, 1)
}

// ========== 数据加载：编辑时回填 ==========
const initForm = async () => {
  // 每次打开都先重置
  Object.assign(form, blankForm())
  if (!props.productId) return
  loading.value = true
  const res = await sxkApi.getProduct(props.productId)
  loading.value = false
  if (res.data) {
    Object.assign(form, {
      ...res.data,
      features: res.data.features?.length
        ? res.data.features
        : [{ name: '', description: '' }]
    })
  } else {
    ElMessage.error(res.msg || '加载产品失败')
  }
}

// ========== 提交 ==========
const cancel = () => emit('update:modelValue', false)

const submit = async () => {
  try {
    await formRef.value?.validate()
  } catch {
    return
  }
  // BR-K-03 自定义校验：功能列表至少 1 项且 name 非空
  const validFeatures = form.features.filter((f) => f.name.trim())
  if (validFeatures.length === 0) {
    ElMessage.error('请至少添加一个功能特性')
    return
  }
  const payload = {
    ...form,
    features: validFeatures.map((f, i) => ({
      name: f.name.trim(),
      description: f.description?.trim() || '',
      sort_order: i + 1
    })),
    target_customers: form.target_customers.filter((s) => s.trim()),
    competitors: form.competitors.filter((s) => s.trim()),
    selling_points: form.selling_points.filter((s) => s.trim())
  }
  saving.value = true
  let res
  if (isEdit.value) {
    res = await sxkApi.updateProduct(props.productId, payload)
  } else {
    res = await sxkApi.createProduct(payload)
  }
  saving.value = false
  if (res.code === 0) {
    ElMessage.success(isEdit.value ? '已保存' : '已创建')
    emit('saved')
    emit('update:modelValue', false)
  } else {
    // 透传业务错误码对应提示（mock 阶段与接口文档一致）
    ElMessage.error(res.msg || '保存失败')
  }
}
</script>

<style lang="scss" scoped>
.dynamic-list {
  display: flex;
  flex-direction: column;
  gap: $spacing-sm;
  width: 100%;

  &__row {
    display: flex;
    align-items: center;
    gap: $spacing-sm;
  }
}
</style>
