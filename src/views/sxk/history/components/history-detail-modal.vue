<!--
  历史详情弹窗
  对应需求文档 5.4.3：
    - 弹窗宽 720px
    - 标题 + 元信息（产品/模板/时间）
    - 内容区（最大 400px 滚动）
    - 关闭 / 重新编辑此内容
-->
<template>
  <el-dialog
    :model-value="modelValue"
    title="历史详情"
    width="720px"
    @update:model-value="(v) => $emit('update:modelValue', v)"
    @open="load"
  >
    <div v-if="loading" class="loading">
      <el-icon class="rotating"><Loading /></el-icon>
      加载中...
    </div>

    <div v-else-if="data" class="detail">
      <div class="meta">
        <div class="meta-row">
          <label>产品</label>
          <span :class="{ 'is-deleted': data.product.is_deleted }">
            {{ data.product.name }}
            <el-tag v-if="data.product.is_deleted" size="small" type="info" effect="plain">已删除</el-tag>
          </span>
        </div>
        <div class="meta-row">
          <label>模板</label>
          <span>{{ data.template.name }}</span>
        </div>
        <div class="meta-row">
          <label>生成时间</label>
          <span>{{ formatDateTime(data.created_at) }}</span>
        </div>
        <div class="meta-row">
          <label>耗时</label>
          <span>{{ data.duration_ms ? (data.duration_ms / 1000).toFixed(1) + 's' : '—' }}</span>
        </div>
        <div class="meta-row">
          <label>选用版本</label>
          <el-tag effect="light">{{ data.selected_version || '未选用' }}</el-tag>
        </div>
      </div>

      <!-- 多版本 Tab 切换（5.4.2 F4-2 多版本对比） -->
      <el-tabs v-model="activeVersion" class="version-tabs">
        <el-tab-pane
          v-for="v in data.versions"
          :key="v.version_key"
          :name="v.version_key"
          :label="vLabel(v)"
        />
      </el-tabs>

      <div class="content" v-html="activeContent" />
    </div>

    <template #footer>
      <el-button @click="cancel">关闭</el-button>
      <el-button type="primary" @click="onEdit">重新编辑此内容</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import sxkApi from '@/mock/sxkApi'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  generationId: { type: String, default: null }
})
const emit = defineEmits(['update:modelValue', 'edit'])

// ========== 状态 ==========
const loading = ref(false)
const data = ref(null)
const activeVersion = ref('A')

// ========== 工具 ==========
const formatDateTime = (iso) => {
  if (!iso) return '—'
  const d = new Date(iso)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

const vLabel = (v) =>
  `${v.version_key}${v.is_recommended ? '（推荐）' : ''}`

// 当前展示内容
const activeContent = computed(() => {
  if (!data.value?.versions) return ''
  const v = data.value.versions.find((x) => x.version_key === activeVersion.value)
  return v?.content_html || '<p style="color:#6b7280">该版本无内容</p>'
})

// ========== 数据加载 ==========
const load = async () => {
  if (!props.generationId) return
  loading.value = true
  const res = await sxkApi.getGeneration(props.generationId)
  loading.value = false
  if (res.data) {
    data.value = res.data
    // 默认展示推荐版本，没有就 A
    const recommended = res.data.versions?.find((v) => v.is_recommended)
    activeVersion.value = recommended?.version_key || res.data.versions?.[0]?.version_key || 'A'
  } else {
    ElMessage.error(res.msg || '加载历史失败')
  }
}

// 监听 generationId 变化（弹窗复用场景）
watch(() => props.generationId, () => {
  if (props.modelValue) load()
})

// ========== 操作 ==========
const cancel = () => emit('update:modelValue', false)

const onEdit = () => {
  if (!data.value) return
  emit('edit', data.value.generation_id)
}
</script>

<style lang="scss" scoped>
// 加载 / 空状态（复用全局 sxkRotating 动画）
.loading,
.empty {
  padding: $spacing-2xl 0;
  text-align: center;
  color: $text-secondary;

  .rotating {
    animation: sxkRotating 1s linear infinite;
    margin-right: $spacing-sm;
  }
}

.detail {
  display: flex;
  flex-direction: column;
  gap: $spacing-lg;
}

.meta {
  display: flex;
  flex-direction: column;
  gap: $spacing-sm;
  padding: $spacing-md $spacing-lg;
  background: $bg-hover;
  border-radius: $radius-md;

  &-row {
    display: flex;
    align-items: center;
    gap: $spacing-md;
    font-size: $font-size-sm;

    label {
      width: 80px;
      color: $text-regular;
      flex-shrink: 0;
    }
    span {
      color: $text-primary;
    }
  }
}

.is-deleted {
  color: $text-secondary;
  text-decoration: line-through;
}

.version-tabs {
  :deep(.el-tabs__header) {
    margin-bottom: $spacing-sm;
  }
}

.content {
  max-height: 400px;
  overflow: auto;
  padding: $spacing-md $spacing-lg;
  border: 1px solid $border-light;
  border-radius: $radius-md;
  background: $bg-card;
  font-size: $font-size-base;
  line-height: 1.7;
  color: $text-primary;

  :deep(h2) {
    margin-top: 0;
    color: $primary-color;
    font-size: $font-size-xl;
  }
  :deep(table) {
    border-collapse: collapse;
    margin: $spacing-sm 0;
    th, td {
      padding: $spacing-xs $spacing-sm;
      border: 1px solid $border-base;
    }
    th {
      background: $gray-100;
    }
  }
}
</style>
