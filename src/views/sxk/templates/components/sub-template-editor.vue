<!--
  子模板编辑器（创建/编辑共用）— 对齐 SXK_v3.html 原型 subTemplateEditorModal
  布局：
    - 头部：图标 + 标题 + 副标题 + 关闭按钮
    - 可滚动内容：
      - 所属场景（select，编辑时只读）
      - 2 列：子模板名称（必填）+ 风格标签（必填）
      - 输出格式（select）
      - 模板描述（textarea，必填）
      - 提示词 Prompt（textarea + 变量引用提示）
      - 内容结构/章节（动态列表 + 添加章节按钮）
    - 底部：取消 + 保存
-->
<template>
  <el-dialog
    :model-value="modelValue"
    width="720px"
    top="7vh"
    :show-close="false"
    class="subtpl-editor-dialog"
    @update:model-value="(v) => $emit('update:modelValue', v)"
    @open="init"
  >
    <!-- 头部 -->
    <div class="ste-head">
      <div class="ste-head__left">
        <h3 class="ste-head__title">
          <el-icon class="ste-head__icon"><EditPen /></el-icon>
          {{ isEdit ? '编辑子模板' : '新建子模板' }}
        </h3>
        <p class="ste-head__sub">
          {{ isEdit ? '修改子模板的字段与配置' : `为「${currentSceneName}」场景新增子模板` }}
        </p>
      </div>
      <button class="ste-head__close" @click="$emit('update:modelValue', false)">
        <el-icon :size="20"><Close /></el-icon>
      </button>
    </div>

    <!-- 可滚动内容区 -->
    <div class="ste-body">
      <!-- 所属场景 -->
      <div class="ste-field">
        <label class="ste-field__label">所属场景 <span class="ste-field__req">*</span></label>
        <el-select
          v-model="form.scene"
          placeholder="请选择场景"
          :disabled="isEdit"
          style="width: 100%"
        >
          <el-option
            v-for="s in scenes"
            :key="s.scene_code"
            :label="s.name"
            :value="s.scene_code"
          />
        </el-select>
        <p class="ste-field__hint">
          {{ isEdit ? '所属场景不可变更' : '从已有场景中选择，或到「场景模板管理」页新建场景' }}
        </p>
      </div>

      <!-- 子模板名称 + 风格标签（2 列） -->
      <div class="ste-row">
        <div class="ste-field">
          <label class="ste-field__label">子模板名称 <span class="ste-field__req">*</span></label>
          <el-input v-model="form.name" placeholder="如：官网首页Banner" />
        </div>
        <div class="ste-field">
          <label class="ste-field__label">风格标签 <span class="ste-field__req">*</span></label>
          <el-input v-model="form.style" placeholder="如：专业正式 / 轻松活泼" />
        </div>
      </div>

      <!-- 输出格式 -->
      <div class="ste-field">
        <label class="ste-field__label">输出格式</label>
        <el-select v-model="form.format" style="width: 100%">
          <el-option label="长文案" value="long_text" />
          <el-option label="短文案" value="short_text" />
          <el-option label="表格" value="table" />
          <el-option label="大纲" value="outline" />
          <el-option label="邮件" value="email" />
        </el-select>
      </div>

      <!-- 模板描述 -->
      <div class="ste-field">
        <label class="ste-field__label">模板描述 <span class="ste-field__req">*</span></label>
        <el-input
          v-model="form.desc"
          type="textarea"
          :rows="3"
          placeholder="描述该子模板的适用场景与核心特点"
        />
      </div>

      <!-- 提示词 -->
      <div class="ste-field">
        <label class="ste-field__label">提示词（Prompt）</label>
        <el-input
          v-model="form.prompt"
          type="textarea"
          :rows="5"
          placeholder="请输入AI生成提示词，使用 [变量名] 引用产品字段"
        />
        <p class="ste-field__hint">使用 [变量名] 引用产品字段，如 [产品名]、[卖点]、[目标客户]</p>
      </div>

      <!-- 内容结构（章节） -->
      <!-- <div class="ste-field">
        <label class="ste-field__label">内容结构（章节）</label>
        <div class="section-list">
          <div
            v-for="(s, idx) in form.sections"
            :key="idx"
            class="section-row"
          >
            <el-input
              v-model="s.value"
              placeholder="如：行动号召（CTA）"
              size="small"
            />
            <el-button
              type="danger"
              size="small"
              class="section-row__del"
              @click="removeSection(idx)"
            >
              <el-icon><Close /></el-icon>
            </el-button>
          </div>
          <div v-if="form.sections.length === 0" class="section-empty">
            点击"+ 添加章节"开始定义
          </div>
        </div>
        <el-button size="small" class="section-add-btn" @click="addSection">
          <el-icon><Plus /></el-icon>
          <span>添加章节</span>
        </el-button>
      </div> -->
    </div>

    <!-- 底部 -->
    <template #footer>
      <div class="ste-footer">
        <div class="ste-footer__left" />
        <div class="ste-footer__right">
          <el-button @click="cancel">取消</el-button>
          <el-button type="primary" :loading="saving" @click="submit">保存</el-button>
        </div>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { EditPen, Close, Plus } from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  // 场景列表（用于所属场景下拉）
  scenes: { type: Array, default: () => [] },
  // 编辑模式：传入子模板数据则为编辑；不传为新增
  templateData: { type: Object, default: null },
  // 创建时预选的场景 code
  defaultScene: { type: String, default: '' }
})
const emit = defineEmits(['update:modelValue', 'saved'])

const saving = ref(false)
const isEdit = computed(() => !!props.templateData)

// 当前选中场景的名称（用于副标题展示）
const currentSceneName = computed(() => {
  const found = props.scenes.find((s) => s.scene_code === form.scene)
  return found ? found.name : '未选择'
})

const blankForm = () => ({
  scene: props.defaultScene || '',
  name: '',
  style: '',
  format: 'long_text',
  desc: '',
  prompt: '',
  sections: []
})
const form = reactive(blankForm())

const init = () => {
  if (props.templateData) {
    // 编辑模式：回填
    Object.assign(form, {
      scene: props.templateData.scene_code || '',
      name: props.templateData.name || '',
      style: props.templateData.style || '',
      format: props.templateData.output_format || 'long_text',
      desc: props.templateData.description || '',
      prompt: props.templateData.prompt || '',
      sections: (props.templateData.sections || []).map((s) => ({ value: s.title || s.value || '' }))
    })
  } else {
    Object.assign(form, blankForm())
  }
}

const addSection = () => {
  form.sections.push({ value: '' })
}
const removeSection = (idx) => {
  form.sections.splice(idx, 1)
}

const cancel = () => {
  emit('update:modelValue', false)
}

const submit = async () => {
  if (!form.scene) {
    ElMessage.warning('请选择所属场景')
    return
  }
  if (!form.name.trim()) {
    ElMessage.warning('请输入子模板名称')
    return
  }
  if (!form.style.trim()) {
    ElMessage.warning('请输入风格标签')
    return
  }
  if (!form.desc.trim()) {
    ElMessage.warning('请填写模板描述')
    return
  }
  saving.value = true
  try {
    const sections = form.sections
      .map((s) => s.value.trim())
      .filter((v) => v)
      .map((title, idx) => ({ title, sort_order: idx + 1 }))

    emit('saved', {
      scene_code: form.scene,
      name: form.name.trim(),
      style: form.style.trim(),
      output_format: form.format,
      description: form.desc.trim(),
      prompt: form.prompt.trim(),
      sections
    })
    ElMessage.success(isEdit.value ? '子模板已更新' : '子模板已保存')
    emit('update:modelValue', false)
  } finally {
    saving.value = false
  }
}
</script>

<style lang="scss">
// 全局样式：覆盖 el-dialog 默认 padding（弹窗 teleport 到 body，scoped 无法穿透）
.subtpl-editor-dialog {
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
// ========== 头部 ==========
.ste-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: $spacing-lg $spacing-lg $spacing-md;
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

  &__sub {
    font-size: 12px;
    color: $text-placeholder;
    margin: $spacing-xs 0 0;
  }

  &__close {
    flex-shrink: 0;
    background: none;
    border: none;
    cursor: pointer;
    color: $text-placeholder;
    padding: 4px;
    border-radius: $radius-sm;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    justify-content: center;

    &:hover {
      color: $text-primary;
      background: $gray-100;
    }
  }
}

// ========== 可滚动内容区 ==========
.ste-body {
  max-height: calc(86vh - 160px);
  overflow-y: auto;
  padding: $spacing-lg;
  display: flex;
  flex-direction: column;
  gap: $spacing-lg;
}

// ========== 2 列布局 ==========
.ste-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: $spacing-lg;
}

.ste-field {
  &__label {
    display: block;
    font-size: 13px;
    font-weight: 500;
    color: $text-primary;
    margin-bottom: $spacing-sm;
  }

  &__req {
    color: #ef4444;
    margin-left: 2px;
  }

  &__hint {
    font-size: 12px;
    color: $text-placeholder;
    margin: $spacing-xs 0 0;
  }
}

// ========== 章节列表 ==========
.section-list {
  display: flex;
  flex-direction: column;
  gap: $spacing-sm;
  margin-bottom: $spacing-sm;
}

.section-row {
  display: flex;
  align-items: center;
  gap: $spacing-sm;

  &__del {
    flex-shrink: 0;
  }
}

.section-empty {
  text-align: center;
  color: $text-placeholder;
  font-size: 12px;
  padding: $spacing-sm 0;
}

.section-add-btn {
  margin-top: $spacing-xs;
}

// ========== 底部 ==========
.ste-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: $spacing-sm $spacing-lg $spacing-md;
  border-top: 1px solid $border-light;

  &__right {
    display: flex;
    gap: $spacing-sm;
    margin-left: auto;
  }
}
</style>
