<!--
  模板详情弹窗（对齐 SXK_v3.html 原型 templateDetailModal）
  三段式布局：
    - 头部：场景图标 + 场景名称 + 描述 + 关闭
    - 可滚动内容：场景参数（2 列网格卡片）+ 已有模板列表
    - 底部：管理子模板（左） / 使用此场景生成（右）
-->
<template>
  <el-dialog
    :model-value="modelValue"
    width="720px"
    top="6vh"
    :show-close="false"
    class="tpl-detail-dialog"
    @update:model-value="(v) => $emit('update:modelValue', v)"
    @open="load"
  >
    <div
      v-loading="loading"
      class="detail-wrap"
    >
      <!-- 头部 -->
      <div class="detail-head">
        <div
          class="detail-head__icon"
          :style="iconStyle"
        >
          <el-icon :size="28">
            <component :is="iconComp" />
          </el-icon>
        </div>
        <div class="detail-head__body">
          <h3>{{ sceneName || data?.name || '模板详情' }}</h3>
          <p>{{ sceneDesc || data?.description }}</p>
        </div>
        <button
          class="detail-head__close"
          @click="$emit('update:modelValue', false)"
        >
          <el-icon :size="20">
            <Close />
          </el-icon>
        </button>
      </div>

      <!-- 可滚动内容区 -->
      <div class="detail-body">
        <!-- 场景参数 -->
        <div class="detail-section">
          <div class="detail-section__header">
            <h4 class="detail-section__title">
              <el-icon class="detail-section__icon">
                <Checked />
              </el-icon>
              场景参数
            </h4>
            <el-button
              type="primary"
              size="small"
              @click="onEditScene"
            >
              <el-icon><EditPen /></el-icon>
              <span>编辑场景</span>
            </el-button>
          </div>
          <div class="param-grid">
            <div
              v-for="p in schemaParams"
              :key="p.key"
              class="param-card"
            >
              <div class="param-card__icon">
                <el-icon><Tickets /></el-icon>
              </div>
              <div class="param-card__content">
                <div class="param-card__name">
                  {{ p.label }}
                </div>
                <div class="param-card__desc">
                  {{ paramDesc(p) }}
                </div>
              </div>
            </div>
            <div
              v-if="schemaParams.length === 0"
              class="detail-empty"
            >
              当前场景暂无参数说明
            </div>
          </div>
        </div>

        <!-- 已有模板 -->
        <div class="detail-section">
          <div class="detail-section__header">
            <h4 class="detail-section__title">
              <el-icon class="detail-section__icon">
                <Files />
              </el-icon>
              已有模板
              <!-- <span class="detail-section__count">共 {{ siblingTemplates.length }} 个</span> -->
            </h4>
            <el-button
              type="primary"
              size="small"
              @click="onAddTemplate"
            >
              <el-icon><Plus /></el-icon>
              <span>添加模板</span>
            </el-button>
          </div>
          <div class="tpl-list">
            <div
              v-for="tpl in siblingTemplates"
              :key="tpl.template_id"
              class="tpl-card"
              :class="{ 'tpl-card--active': tpl.template_id === currentTemplateId }"
              @click="pickTemplate(tpl)"
            >
              <div class="tpl-card__main">
                <div class="tpl-card__title-row">
                  <el-icon
                    class="tpl-card__icon"
                    :style="{ color: sceneColor }"
                  >
                    <Document />
                  </el-icon>
                  <span class="tpl-card__name">{{ tpl.name }}</span>
                  <el-tag
                    size="small"
                    effect="light"
                    :style="styleTagStyle"
                  >
                    {{ formatLabel(tpl) }}
                  </el-tag>
                </div>
                <p class="tpl-card__desc">
                  {{ tpl.description }}
                </p>
                <div class="tpl-card__meta">
                  <span class="tpl-card__meta-item">
                    <el-icon><TrendCharts /></el-icon>
                    {{ tpl.use_count_30d || 0 }} 次使用
                  </span>
                  <span class="tpl-card__meta-item">
                    <el-icon><Clock /></el-icon>
                    {{ relativeTime(tpl.updated_at) }}
                  </span>
                </div>
              </div>
              <div class="tpl-card__actions">
                <button
                  class="tpl-card__edit-btn"
                  title="编辑此模板"
                  @click.stop="onEditSub(tpl)"
                >
                  <el-icon><EditPen /></el-icon>
                </button>
                <button
                  class="tpl-card__use-btn"
                  @click.stop="onUseItem(tpl)"
                >
                  使用
                </button>
              </div>
            </div>
            <div
              v-if="siblingTemplates.length === 0"
              class="detail-empty"
            >
              该场景下暂无模板
            </div>
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="detail-footer">
        <el-button
          type="primary"
          @click="onUse"
        >
          <el-icon><MagicStick /></el-icon>
          <span>使用此场景生成</span>
        </el-button>
      </div>
    </template>
  </el-dialog>

  <!-- 编辑场景弹窗 -->
  <SceneCreateModal
    v-model="sceneEditVisible"
    :edit-data="sceneEditData"
    @saved="onSceneSaved"
  />

  <!-- 子模板编辑器弹窗 -->
  <SubTemplateEditor
    v-model="subtplVisible"
    :scenes="sceneSchemasList"
    :template-data="subtplEditData"
    :default-scene="data?.scene_code || ''"
    @saved="onSubtplSaved"
  />
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Document,
  PieChart,
  Share,
  Message,
  Promotion,
  Close,
  Checked,
  Files,
  Tickets,
  Clock,
  TrendCharts,
  EditPen,
  MagicStick,
  Plus
} from '@element-plus/icons-vue'
import sxkApi from '@/mock/sxkApi'
import SceneCreateModal from './scene-create-modal.vue'
import SubTemplateEditor from './sub-template-editor.vue'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  templateId: { type: String, default: null },
  sceneCode: { type: String, default: '' }
})
const emit = defineEmits(['update:modelValue', 'use'])

// ========== 状态 ==========
const loading = ref(false)
const data = ref(null)
const sceneSchemasList = ref([])

// ========== 场景图标 / 配色 ==========
const ICON_MAP = {
  product_intro: Document,
  competitor: PieChart,
  channel_adapt: Share,
  email: Message,
  event: Promotion,
  other: Document
}
const COLOR_MAP = {
  product_intro: { bg: '#eff6ff', color: '#2563eb' },
  competitor: { bg: '#fff7ed', color: '#ea580c' },
  channel_adapt: { bg: '#f0fdf4', color: '#16a34a' },
  email: { bg: '#faf5ff', color: '#9333ea' },
  event: { bg: '#fee2e2', color: '#dc2626' },
  other: { bg: '#f1f5f9', color: '#475569' }
}

const sceneCode = computed(() => data.value?.scene_code || props.sceneCode || '')
const iconComp = computed(() => ICON_MAP[sceneCode.value] || Document)
const iconStyle = computed(() => {
  const c = COLOR_MAP[sceneCode.value] || COLOR_MAP.other
  return { background: c.bg, color: c.color }
})
const sceneColor = computed(() => (COLOR_MAP[sceneCode.value] || COLOR_MAP.other).color)
const styleTagStyle = computed(() => ({
  backgroundColor: (COLOR_MAP[sceneCode.value] || COLOR_MAP.other).bg,
  color: sceneColor.value,
  borderColor: 'transparent'
}))

// ========== 场景信息 ==========
const sceneSchema = computed(() =>
  sceneSchemasList.value.find((s) => s.scene_code === sceneCode.value)
)
const sceneName = computed(() => sceneSchema.value?.name || '')
const sceneDesc = computed(() => {
  if (!sceneSchema.value) return ''
  // 由参数列表生成一句描述
  return data.value?.description || ''
})
const schemaParams = computed(() => sceneSchema.value?.params || [])

// 当前选中模板 id（高亮）
const currentTemplateId = computed(() => data.value?.template_id || '')

// 同场景下的所有模板（已有模板列表）—— 来自 getTemplate 响应中的 templates 字段
const siblingTemplates = computed(() => {
  if (!data.value) return []
  return data.value.templates || [data.value]
})

// ========== 辅助方法 ==========
const paramDesc = (p) => {
  if (p.options && p.options.length) return p.options.join(' / ')
  if (p.default) return p.default
  return p.required ? '必填，文本类型' : '选填，文本类型'
}

const FORMAT_LABELS = {
  long_text: '长文案',
  short_text: '短文案',
  table: '表格',
  outline: '大纲',
  email: '邮件'
}
const formatLabel = (tpl) => FORMAT_LABELS[tpl.output_format] || tpl.output_format || '文本'

const relativeTime = (iso) => {
  if (!iso) return '—'
  const diff = Date.now() - new Date(iso).getTime()
  const day = Math.floor(diff / 86400000)
  if (day <= 0) return '今天'
  if (day === 1) return '1 天前'
  if (day < 30) return `${day} 天前`
  const month = Math.floor(day / 30)
  if (month < 12) return `${month} 个月前`
  return `${Math.floor(month / 12)} 年前`
}

// ========== 加载 ==========
const load = async () => {
  loading.value = true
  // 每次打开都重新加载场景 schema，确保新创建的场景在列表中
  const sceneRes = await sxkApi.getSceneSchemas()
  if (sceneRes.code === 0 && sceneRes.data) {
    sceneSchemasList.value = sceneRes.data.scenes || []
  }
  // 无模板 ID：仅加载场景信息（空模板列表）
  if (!props.templateId) {
    data.value = {
      scene_code: props.sceneCode,
      templates: []
    }
    loading.value = false
    return
  }
  const res = await sxkApi.getTemplate(props.templateId, props.sceneCode)
  loading.value = false
  if (res.code === 0 && res.data) {
    data.value = res.data
  } else {
    ElMessage.error(res.msg || '加载模板失败')
  }
}

watch([() => props.templateId, () => props.modelValue], () => {
  if (props.modelValue) load()
})

// ========== 操作 ==========
const pickTemplate = (tpl) => {
  // 保留 scene_code 和 templates，避免场景参数区域塌缩和列表丢失
  data.value = { ...tpl, scene_code: data.value.scene_code, templates: data.value.templates }
}

const onEditSub = async (tpl) => {
  // 获取完整模板数据（siblings 只有最小字段）
  const res = await sxkApi.getTemplate(tpl.template_id, data.value?.scene_code)
  if (res.code === 0 && res.data) {
    subtplEditData.value = res.data
    subtplVisible.value = true
  } else {
    ElMessage.error(res.msg || '获取模板数据失败')
  }
}

const onUseItem = (tpl) => {
  emit('use', tpl)
  emit('update:modelValue', false)
}

const onManageSub = () => {
  ElMessage.info('管理子模板功能开发中')
}

// ========== 编辑场景弹窗 ==========
const sceneEditVisible = ref(false)
const sceneEditData = computed(() => {
  if (!sceneSchema.value) return null
  // 将 params 数组转为 { label: desc } 对象，与详情弹窗中场景参数的展示一致
  const paramsObj = {}
  if (schemaParams.value.length) {
    schemaParams.value.forEach((p) => {
      paramsObj[p.label || p.key] = paramDesc(p)
    })
  }
  return {
    name: sceneName.value,
    description: sceneSchema.value?.description || data.value?.description || '',
    params: paramsObj
  }
})

const onEditScene = () => {
  sceneEditVisible.value = true
}

const onSceneSaved = async (payload) => {
  if (!data.value) return
  const sc = data.value.scene_code
  const res = await sxkApi.updateScene(sc, payload)
  if (res.code === 0) {
    ElMessage.success('场景已更新')
    // 更新本地场景数据
    const schema = sceneSchemasList.value.find((s) => s.scene_code === sc)
    if (schema) {
      schema.name = payload.name
      schema.description = payload.description
      if (payload.params) {
        const newParams = Object.entries(payload.params).map(([label, desc]) => {
          const orig = schema.params?.find((p) => p.label === label || p.key === label)
          if (orig) {
            if (desc.includes(' / ')) {
              return { ...orig, label, options: desc.split(' / ').map((s) => s.trim()) }
            }
            return { ...orig, label, default: desc }
          }
          return { key: label, type: 'text', label, required: false, default: desc }
        })
        schema.params = newParams
      }
    }
    sceneEditVisible.value = false
  } else {
    ElMessage.error(res.msg || '保存失败')
  }
}

// ========== 子模板编辑器 ==========
const subtplVisible = ref(false)
const subtplEditData = ref(null)

const onAddTemplate = () => {
  subtplEditData.value = null
  subtplVisible.value = true
}

const onSubtplSaved = async (payload) => {
  if (!data.value) return
  let res
  if (subtplEditData.value) {
    // 编辑模式：调用 updateTemplate
    res = await sxkApi.updateTemplate(subtplEditData.value.template_id, payload)
  } else {
    // 新增模式：调用 createTemplate
    res = await sxkApi.createTemplate(payload)
  }
  if (res.code === 0) {
    subtplEditData.value = null
    await load()
  } else {
    ElMessage.error(res.msg || '保存失败')
  }
}

const onUse = () => {
  if (!data.value) return
  emit('use', data.value)
}
</script>

<style lang="scss">
// 全局样式：覆盖 el-dialog 默认 padding（弹窗 teleport 到 body，scoped 无法穿透）
.tpl-detail-dialog {
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
.detail-wrap {
  display: flex;
  flex-direction: column;
  max-height: 82vh;
}

// ========== 头部 ==========
.detail-head {
  display: flex;
  align-items: flex-start;
  gap: $spacing-lg;
  padding: $spacing-lg $spacing-lg $spacing-md;
  border-bottom: 1px solid $border-light;
  flex-shrink: 0;

  &__icon {
    width: 56px;
    height: 56px;
    border-radius: $radius-xl;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  &__body {
    flex: 1;
    min-width: 0;

    h3 {
      margin: 0;
      font-size: $font-size-xl;
      font-weight: 700;
      color: $text-primary;
    }
    p {
      margin: $spacing-xs 0 0;
      font-size: $font-size-sm;
      color: $text-secondary;
      line-height: 1.5;
    }
  }

  &__close {
    flex-shrink: 0;
    width: 32px;
    height: 32px;
    border: none;
    background: transparent;
    color: $text-placeholder;
    cursor: pointer;
    border-radius: $radius-md;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.15s;

    &:hover {
      color: $text-primary;
      background: $bg-hover;
    }
  }
}

// ========== 可滚动内容 ==========
.detail-body {
  overflow-y: auto;
  padding: $spacing-lg;
  flex: 1;
}

// ========== 通用区块 ==========
.detail-section {
  margin-bottom: $spacing-xl;

  &:last-child {
    margin-bottom: 0;
  }

  &__header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: $spacing-md;
  }

  &__title {
    display: flex;
    align-items: center;
    margin: 0 0 $spacing-sm;
    font-size: $font-size-sm;
    font-weight: 600;
    color: $text-primary;
  }

  &__header &__title {
    margin: 0;
  }

  &__icon {
    margin-right: $spacing-xs;
    color: $primary-color;
    font-size: 16px;
  }

  &__count {
    font-size: $font-size-xs;
    color: $text-placeholder;
  }
}

.detail-empty {
  text-align: center;
  padding: $spacing-lg 0;
  font-size: $font-size-sm;
  color: $text-secondary;
}

// ========== 场景参数卡片网格 ==========
.param-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: $spacing-sm;
}

.param-card {
  display: flex;
  align-items: flex-start;
  gap: $spacing-sm;
  padding: $spacing-sm $spacing-md;
  background: $bg-hover;
  border-radius: $radius-md;
  transition: background 0.15s;

  &:hover {
    background: $bg-hover;
  }

  &__icon {
    width: 32px;
    height: 32px;
    background: #fff;
    border-radius: $radius-sm;
    display: flex;
    align-items: center;
    justify-content: center;
    color: $primary-color;
    font-size: 16px;
    flex-shrink: 0;
  }

  &__content {
    flex: 1;
    min-width: 0;
  }

  &__name {
    font-size: $font-size-sm;
    font-weight: 500;
    color: $text-primary;
  }

  &__desc {
    margin-top: 2px;
    font-size: $font-size-xs;
    color: $text-placeholder;
    line-height: 1.4;
  }
}

// ========== 已有模板列表 ==========
.tpl-list {
  display: flex;
  flex-direction: column;
  gap: $spacing-sm;
}

.tpl-card {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: $spacing-sm;
  padding: $spacing-sm $spacing-md;
  border: 1px solid $border-light;
  border-radius: $radius-md;
  cursor: pointer;
  transition: all 0.15s;

  &:hover {
    border-color: $primary-color-light;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  }

  &--active {
    border-color: $primary-color;
    background: $primary-color-light;
  }

  &__main {
    flex: 1;
    min-width: 0;
  }

  &__title-row {
    display: flex;
    align-items: center;
    gap: $spacing-xs;
    margin-bottom: $spacing-xs;
  }

  &__icon {
    font-size: 16px;
    flex-shrink: 0;
  }

  &__name {
    font-size: $font-size-sm;
    font-weight: 500;
    color: $text-primary;
  }

  &__desc {
    margin: 0 0 $spacing-xs;
    padding-left: 22px;
    font-size: $font-size-xs;
    color: $text-regular;
    line-height: 1.5;
  }

  &__meta {
    display: flex;
    align-items: center;
    gap: $spacing-md;
    padding-left: 22px;
    font-size: $font-size-xs;
    color: $text-placeholder;
  }

  &__meta-item {
    display: flex;
    align-items: center;
    gap: 4px;
  }

  &__actions {
    display: flex;
    align-items: center;
    gap: $spacing-xs;
    flex-shrink: 0;
  }

  &__edit-btn {
    width: 28px;
    height: 28px;
    border: none;
    background: transparent;
    color: $text-placeholder;
    cursor: pointer;
    border-radius: $radius-sm;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.15s;

    &:hover {
      color: $primary-color;
      background: $primary-color-light;
    }
  }

  &__use-btn {
    padding: 6px 12px;
    background: $primary-color-light;
    color: $primary-color;
    border: none;
    border-radius: $radius-sm;
    font-size: $font-size-xs;
    cursor: pointer;
    transition: all 0.15s;

    &:hover {
      background: $primary-color;
      color: #fff;
    }
  }
}

// ========== 底部 ==========
.detail-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: $spacing-sm $spacing-lg $spacing-md;
  border-top: 1px solid $border-light;
  flex-shrink: 0;
}
</style>
