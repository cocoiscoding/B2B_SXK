<!--
  模板详情弹窗
  对应需求文档 5.5.3：
    - 弹窗宽 800px，三段式：头部 / 中部 / 底部
    - 头部：图标 + 标题 + 描述 + 关闭按钮
    - 中部：场景参数说明 + 已有模板列表
    - 底部：编辑模板 / 使用此场景生成
-->
<template>
  <el-dialog
    :model-value="modelValue"
    :title="data?.name || '模板详情'"
    width="800px"
    @update:model-value="(v) => $emit('update:modelValue', v)"
    @open="load"
  >
    <div v-loading="loading" v-if="data" class="detail">
      <!-- 头部 -->
      <div class="detail-head">
        <div class="detail-head__icon" :style="iconStyle">
          <el-icon :size="28"><component :is="iconComp" /></el-icon>
        </div>
        <div class="detail-head__body">
          <h3>{{ data.name }}</h3>
          <p>{{ data.description }}</p>
          <div class="tags">
            <el-tag effect="plain" size="small">{{ sceneName }}</el-tag>
            <el-tag
              v-for="tag in data.tags"
              :key="tag.tag_id"
              effect="plain"
              size="small"
              type="info"
            >{{ tag.name }}</el-tag>
            <el-tag v-if="data.is_custom" size="small" type="warning" effect="plain">自定义</el-tag>
            <el-tag v-else size="small" effect="plain">预置</el-tag>
          </div>
        </div>
        <div class="detail-head__stat">
          <div class="stat-num">{{ data.use_count_30d }}</div>
          <div class="stat-label">近 30 天使用次数</div>
        </div>
      </div>

      <el-divider />

      <!-- 中部：参数 schema + 章节 -->
      <el-tabs>
        <el-tab-pane label="参数说明">
          <div v-if="schemaParams.length === 0" class="text-sub">
            当前场景暂无参数说明
          </div>
          <el-table :data="schemaParams" border size="small">
            <el-table-column label="参数" prop="key" width="140" />
            <el-table-column label="类型" prop="type" width="100" />
            <el-table-column label="中文名" prop="label" width="140" />
            <el-table-column label="可选值 / 说明">
              <template #default="{ row }">
                <span v-if="row.options">可选：{{ row.options.join('、') }}</span>
                <span v-else>{{ row.required ? '必填，文本类型' : '选填，文本类型' }}</span>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="内容结构">
          <div v-if="!data.sections || data.sections.length === 0" class="text-sub">
            该模板未定义章节
          </div>
          <ol v-else class="sections-list">
            <li v-for="s in data.sections" :key="s.section_id || s.title">
              <b>{{ s.title }}</b>
              <p>{{ s.guidance || '—' }}</p>
            </li>
          </ol>
        </el-tab-pane>

        <el-tab-pane label="提示词 Prompt">
          <pre class="prompt">{{ data.prompt }}</pre>
        </el-tab-pane>
      </el-tabs>
    </div>

    <template #footer>
      <el-button @click="onEdit">编辑模板</el-button>
      <el-button type="primary" @click="onUse">使用此场景生成</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Document,
  PieChart,
  Share,
  Message,
  Promotion
} from '@element-plus/icons-vue'
import sxkApi from '@/mock/sxkApi'
import { mockSceneSchemas } from '@/mock/data'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  templateId: { type: String, default: null }
})
const emit = defineEmits(['update:modelValue', 'use'])

// ========== 状态 ==========
const loading = ref(false)
const data = ref(null)

// ========== 计算 ==========
const ICON_MAP = {
  product_intro: Document,
  competitor: PieChart,
  channel_adapt: Share,
  email: Message,
  event: Promotion,
  other: Document
}
// 场景色：对齐原型 SXK.html（Tailwind *-50 底 + *-600 字，与 templates/index.vue 同步）
const COLOR_MAP = {
  product_intro: { bg: '#eff6ff', color: '#2563eb' },  // blue-50 / blue-600
  competitor: { bg: '#fff7ed', color: '#ea580c' },      // orange-50 / orange-600
  channel_adapt: { bg: '#f0fdf4', color: '#16a34a' },  // green-50 / green-600
  email: { bg: '#faf5ff', color: '#9333ea' },           // purple-50 / purple-600
  event: { bg: '#fee2e2', color: '#dc2626' },           // red-50 / red-600
  other: { bg: '#f1f5f9', color: '#475569' }            // slate-50 / slate-600
}
const iconComp = computed(() => ICON_MAP[data.value?.scene_code] || Document)
const iconStyle = computed(() => {
  const c = COLOR_MAP[data.value?.scene_code] || COLOR_MAP.other
  return { background: c.bg, color: c.color }
})

const sceneName = computed(() => {
  if (!data.value) return ''
  const found = mockSceneSchemas.find((s) => s.scene_code === data.value.scene_code)
  return found?.name || data.value.scene_code
})

const schemaParams = computed(() => {
  if (!data.value) return []
  const found = mockSceneSchemas.find((s) => s.scene_code === data.value.scene_code)
  return found?.params || []
})

// ========== 加载 ==========
const load = async () => {
  if (!props.templateId) return
  loading.value = true
  const res = await sxkApi.getTemplate(props.templateId)
  loading.value = false
  if (res.data) {
    data.value = res.data
  } else {
    ElMessage.error(res.msg || '加载模板失败')
  }
}

watch(() => props.templateId, () => {
  if (props.modelValue) load()
})

// ========== 操作 ==========
const onEdit = () => {
  // 5.5.3：编辑模板按钮开发中
  ElMessage.info('编辑模板功能开发中')
}

const onUse = () => {
  if (!data.value) return
  emit('use', data.value)
}
</script>

<style lang="scss" scoped>
.detail-head {
  display: flex;
  align-items: center;
  gap: $spacing-lg;

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
    h3 {
      margin: 0 0 $spacing-xs;
      font-size: $font-size-xl;
      color: $text-primary;
    }
    p {
      margin: 0 0 $spacing-sm;
      font-size: $font-size-sm;
      color: $text-regular;
      line-height: 1.5;
    }
    .tags {
      display: flex;
      flex-wrap: wrap;
      gap: $spacing-xs;
    }
  }

  &__stat {
    text-align: center;
    flex-shrink: 0;
    padding: 0 $spacing-lg;
    border-left: 1px dashed $border-base;

    .stat-num {
      font-size: $font-size-2xl;
      font-weight: 700;
      color: $primary-color;
      line-height: 1.2;
    }
    .stat-label {
      font-size: $font-size-xs;
      color: $text-secondary;
      margin-top: $spacing-xs;
    }
  }
}

.text-sub {
  color: $text-secondary;
  font-size: $font-size-sm;
  text-align: center;
  padding: $spacing-md 0;
}

.sections-list {
  margin: 0;
  padding-left: $spacing-xl;
  li {
    margin-bottom: $spacing-md;

    b {
      font-size: $font-size-base;
      color: $text-primary;
    }
    p {
      margin: $spacing-xs 0 0;
      font-size: $font-size-sm;
      color: $text-regular;
    }
  }
}

.prompt {
  margin: 0;
  padding: $spacing-md $spacing-lg;
  background: $bg-hover;
  border-radius: $radius-md;
  font-family: $font-family-mono;
  font-size: $font-size-sm;
  line-height: 1.6;
  color: $text-primary;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
