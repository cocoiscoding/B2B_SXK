<!--
  场景弹窗（新增 / 编辑共用）— 对齐 SXK_v3.html 原型 sceneEditorModal
  布局：
    - 头部：图标 + 标题 + 副标题 + 关闭按钮
    - 可滚动内容：
      第一行 2 列：场景名称（必填）、场景描述
      第二行 2 列：主色选择、图标选择
      场景参数管理区（灰色背景 + 边框）：
        - 每个参数为白色卡片，含：参数名称 + 图标选择 + 删除按钮（第一行），参数说明（第二行）
        - 底部提示文字
    - 底部：取消 + 保存（右对齐）
  模式由 sceneData prop 决定：传入则为编辑，不传则为新增
-->
<template>
  <el-dialog
    :model-value="modelValue"
    width="720px"
    top="7vh"
    :show-close="false"
    class="scene-editor-dialog"
    @update:model-value="(v) => $emit('update:modelValue', v)"
    @open="init"
  >
    <!-- 头部 -->
    <div class="se-head">
      <div class="se-head__left">
        <h3 class="se-head__title">
          <el-icon class="se-head__icon"><Grid /></el-icon>
          {{ isEdit ? '编辑场景' : '新建场景' }}
        </h3>
        <p class="se-head__sub">
          {{ isEdit ? '修改场景信息和参数配置' : '定义一个新的模板场景，并设置其参数' }}
        </p>
      </div>
      <button class="se-head__close" @click="$emit('update:modelValue', false)">
        <el-icon :size="20"><Close /></el-icon>
      </button>
    </div>

    <!-- 可滚动内容区 -->
    <div class="se-body">
      <!-- 场景基础信息 -->
      <div class="se-row">
        <div class="se-field">
          <label class="se-field__label">场景名称 <span class="se-field__req">*</span></label>
          <el-input v-model="form.name" placeholder="如：客户案例包装" />
        </div>
        <div class="se-field">
          <label class="se-field__label">场景描述</label>
          <el-input v-model="form.description" placeholder="一句话说明该场景的用途" />
        </div>
      </div>

      <!-- 主色 + 图标 -->
      <!-- <div class="se-row">
        <div class="se-field">
          <label class="se-field__label">主色</label>
          <el-select v-model="form.color" style="width: 100%">
            <el-option label="蓝" value="blue" />
            <el-option label="橙" value="orange" />
            <el-option label="绿" value="green" />
            <el-option label="紫" value="purple" />
            <el-option label="红" value="red" />
            <el-option label="灰" value="gray" />
          </el-select>
        </div>
        <div class="se-field">
          <label class="se-field__label">图标</label>
          <el-select v-model="form.icon" style="width: 100%">
            <el-option label="文档" value="document" />
            <el-option label="图表" value="chart" />
            <el-option label="分享" value="share" />
            <el-option label="邮件" value="message" />
            <el-option label="喇叭" value="promotion" />
            <el-option label="客户" value="user" />
            <el-option label="灵感" value="light" />
          </el-select>
        </div>
      </div> -->

      <!-- 场景参数管理区 -->
      <div class="param-section">
        <div class="param-section__header">
          <span class="param-section__title">
            <el-icon class="param-section__icon"><Checked /></el-icon>
            场景参数（{{ form.params.length }}）
          </span>
          <el-button size="small" @click="addParam">
            <el-icon><Plus /></el-icon>
            <span>添加参数</span>
          </el-button>
        </div>

        <div class="param-list">
          <div
            v-for="(p, idx) in form.params"
            :key="idx"
            class="param-row"
          >
            <el-input
              v-model="p.name"
              placeholder="参数名称"
              size="small"
              class="param-row__name"
            />
            <span class="param-row__sep">：</span>
            <el-input
              v-model="p.desc"
              placeholder="参数的值"
              size="small"
              class="param-row__val"
            />
            <el-button
              link
              type="danger"
              size="small"
              @click="removeParam(idx)"
            >
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>
        </div>

        <div v-if="form.params.length === 0" class="param-empty">
          暂无参数，点击右上角"添加参数"
        </div>

        <p class="param-section__hint">场景参数说明该模板需要用户提供哪些输入项</p>
      </div>
    </div>

    <!-- 底部 -->
    <template #footer>
      <div class="se-footer">
        <div class="se-footer__left" />
        <div class="se-footer__right">
          <el-button @click="cancel">取消</el-button>
          <el-button type="primary" :loading="loading" @click="submit">保存</el-button>
        </div>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Grid, Close, Checked, Plus, Delete } from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  // 编辑模式：传入 { name, description, params } 则为编辑；不传则为新增
  sceneData: { type: Object, default: null },
  // 父组件 API 进行中状态，用于禁用按钮防重复提交
  loading: { type: Boolean, default: false }
})
const emit = defineEmits(['update:modelValue', 'saved'])

const isEdit = computed(() => !!props.sceneData)

const blankForm = () => ({
  name: '',
  description: '',
  color: 'blue',
  icon: 'document',
  params: []
})
const form = reactive(blankForm())

const init = () => {
  if (props.sceneData) {
    // 编辑模式：回填
    const paramsArr = props.sceneData.params
      ? Object.entries(props.sceneData.params).map(([name, desc]) => ({ name, desc }))
      : []
    Object.assign(form, {
      name: props.sceneData.name || '',
      description: props.sceneData.description || '',
      color: props.sceneData.color || 'blue',
      icon: props.sceneData.icon || 'document',
      params: paramsArr
    })
  } else {
    Object.assign(form, blankForm())
  }
}

const addParam = () => {
  form.params.push({ name: '', desc: '' })
}
const removeParam = (idx) => {
  form.params.splice(idx, 1)
}

const cancel = () => {
  emit('update:modelValue', false)
}

const submit = () => {
  if (!form.name.trim()) {
    ElMessage.warning('请输入场景名称')
    return
  }
  // 参数清洗：过滤掉 name 或 desc 为空的行
  const cleaned = form.params
    .filter((p) => p.name.trim() && p.desc.trim())
    .map((p) => ({ name: p.name.trim(), desc: p.desc.trim() }))

  // 暂存为对象格式 { name: desc }
  const paramsObj = {}
  cleaned.forEach((p) => { paramsObj[p.name] = p.desc })

  // 只 emit 数据，由父组件控制 API 调用、提示和关闭
  emit('saved', {
    name: form.name.trim(),
    description: form.description.trim(),
    color: form.color,
    icon: form.icon,
    params: paramsObj
  })
}
</script>

<style lang="scss">
// 全局样式：覆盖 el-dialog 默认 padding（弹窗 teleport 到 body，scoped 无法穿透）
.scene-editor-dialog {
  .el-dialog__header {
    display: none; // 使用自定义头部，隐藏默认 header
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
.se-head {
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
.se-body {
  max-height: calc(86vh - 160px);
  overflow-y: auto;
  padding: $spacing-lg;
  display: flex;
  flex-direction: column;
  gap: $spacing-lg;
}

// ========== 2 列布局 ==========
.se-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: $spacing-lg;
}

.se-field {
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
}

// ========== 场景参数管理区 ==========
.param-section {
  background: $gray-100;
  border: 1px solid $border-light;
  border-radius: $radius-md;
  padding: $spacing-md;

  &__header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: $spacing-md;
  }

  &__title {
    display: flex;
    align-items: center;
    gap: $spacing-xs;
    font-size: 13px;
    font-weight: 600;
    color: $text-primary;
  }

  &__icon {
    color: $primary-color;
    font-size: 16px;
  }

  &__hint {
    font-size: 12px;
    color: $text-placeholder;
    margin: $spacing-sm 0 0;
  }
}

.param-list {
  display: flex;
  flex-direction: column;
  gap: $spacing-sm;
}

// 每行参数：参数名称 + 分隔符 + 参数的值 + 删除按钮
.param-row {
  display: flex;
  align-items: center;
  gap: $spacing-sm;

  &__name {
    width: 150px;
    flex-shrink: 0;
  }

  &__sep {
    color: $text-secondary;
    flex-shrink: 0;
  }

  &__val {
    flex: 1;
  }
}

.param-empty {
  text-align: center;
  color: $text-placeholder;
  padding: $spacing-md 0;
  font-size: 12px;
}

// ========== 底部 ==========
.se-footer {
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
