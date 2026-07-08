<!--
  创建自定义模板弹窗
  对应需求文档 5.5.4 / 4.5.3（US008 / BR-T-04/05/06）：
    - 模板名称（必填，场景下唯一）
    - 适用场景、输出格式
    - 描述、Prompt（必填，支持 [变量]）
    - 内容章节（≥ 1）
    - 章节 sections 动态增删
-->
<template>
  <el-dialog
    :model-value="modelValue"
    title="创建自定义模板"
    width="640px"
    :close-on-click-modal="false"
    @update:model-value="(v) => $emit('update:modelValue', v)"
    @open="init"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="100px"
    >
      <el-form-item label="模板名称" prop="name">
        <el-input v-model="form.name" placeholder="如：金融业产品介绍" maxlength="64" />
      </el-form-item>

      <el-form-item label="适用场景" prop="scene_code">
        <el-select v-model="form.scene_code" placeholder="请选择" style="width: 100%">
          <el-option
            v-for="s in meta.scene_codes || []"
            :key="s.code"
            :label="s.name"
            :value="s.code"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="输出格式" prop="output_format">
        <el-select v-model="form.output_format" placeholder="请选择" style="width: 100%">
          <el-option
            v-for="o in meta.output_formats || []"
            :key="o.code"
            :label="o.name"
            :value="o.code"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="模板描述">
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="2"
          placeholder="简明描述模板用途"
          maxlength="200"
        />
      </el-form-item>

      <el-form-item label="提示词 Prompt" prop="prompt">
        <el-input
          v-model="form.prompt"
          type="textarea"
          :rows="5"
          placeholder="支持 [变量名] 引用产品字段，例如：基于产品[name]、卖点[selling_points]"
        />
      </el-form-item>

      <el-form-item label="内容章节" prop="sections" required>
        <div class="sections">
          <div
            v-for="(s, idx) in form.sections"
            :key="idx"
            class="sections__row"
          >
            <el-input
              v-model="s.title"
              placeholder="章节标题"
              style="width: 180px"
            />
            <el-input
              v-model="s.guidance"
              placeholder="写作指导（可选）"
              style="flex: 1"
            />
            <el-button
              link
              type="danger"
              :disabled="form.sections.length <= 1"
              @click="removeSection(idx)"
            >删除</el-button>
          </div>
          <el-button link type="primary" @click="addSection">+ 添加章节</el-button>
        </div>
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="cancel">取消</el-button>
      <el-button type="primary" :loading="saving" @click="submit">保存模板</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import sxkApi from '@/mock/sxkApi'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  meta: {
    type: Object,
    default: () => ({ scene_codes: [], output_formats: [] })
  }
})
const emit = defineEmits(['update:modelValue', 'created'])

// ========== 表单 ==========
const blankForm = () => ({
  name: '',
  scene_code: '',
  output_format: 'long_text',
  description: '',
  prompt: '',
  sections: [{ title: '', guidance: '' }]
})
const form = reactive(blankForm())
const formRef = ref(null)
const saving = ref(false)

const rules = {
  name: [{ required: true, message: '请输入模板名称', trigger: 'blur' }],
  scene_code: [{ required: true, message: '请选择适用场景', trigger: 'change' }],
  output_format: [{ required: true, message: '请选择输出格式', trigger: 'change' }],
  prompt: [{ required: true, message: '请填写提示词', trigger: 'blur' }]
}

const init = () => {
  Object.assign(form, blankForm())
}

const addSection = () => form.sections.push({ title: '', guidance: '' })
const removeSection = (idx) => {
  if (form.sections.length <= 1) return
  form.sections.splice(idx, 1)
}

// ========== 提交 ==========
const cancel = () => emit('update:modelValue', false)

const submit = async () => {
  try {
    await formRef.value?.validate()
  } catch {
    return
  }
  // BR-T-05：至少 1 个章节
  const validSections = form.sections.filter((s) => s.title.trim())
  if (validSections.length === 0) {
    ElMessage.error('请至少添加一个章节')
    return
  }
  const payload = {
    name: form.name.trim(),
    scene_code: form.scene_code,
    output_format: form.output_format,
    description: form.description.trim(),
    prompt: form.prompt.trim(),
    sections: validSections.map((s, i) => ({
      title: s.title.trim(),
      guidance: s.guidance?.trim() || '',
      sort_order: i + 1
    }))
  }
  saving.value = true
  const res = await sxkApi.createTemplate(payload)
  saving.value = false
  if (res.code === 0) {
    ElMessage.success('已创建')
    emit('created')
    emit('update:modelValue', false)
  } else {
    // 业务错误码透传（含 4092 当前场景下重名）
    ElMessage.error(res.msg || '保存失败')
  }
}
</script>

<style lang="scss" scoped>
.sections {
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
