<!--
  神行库 · 模板管理
  对应需求文档 5.5（US007/008）：
    - 4 个统计卡片（场景模板数 / 具体模板数 / 本月使用数 / 自定义模板数）
    - 2 列模板卡片网格
    - 模板详情弹窗
    - 创建自定义模板
-->
<template>
  <div class="sxk-templates">
    <!-- 顶部头 + 创建按钮 -->
    <basic-block>
      <div class="page-header">
        <div>
          <h2>营销场景模板</h2>
          <p>管理预置模板与自定义模板，支撑多 Agent 内容生成</p>
        </div>
        <div class="page-header__actions">
          <el-button type="primary" @click="onAddScene">
            <el-icon><Plus /></el-icon>
            <span>新增场景</span>
          </el-button>
          <!-- <el-button type="primary" @click="onCreate">
            <el-icon><Plus /></el-icon>
            <span>创建自定义模板</span>
          </el-button> -->
        </div>
      </div>
    </basic-block>

    <!-- 4 个统计卡片 -->
    <el-row :gutter="16">
      <el-col :xs="24" :sm="12" :md="6" v-for="card in statCards" :key="card.label">
        <basic-block hover-shadow padding="small">
          <div class="mini-stat">
            <div class="mini-stat__value" :style="{ color: card.color }">{{ card.value }}</div>
            <div class="mini-stat__label">{{ card.label }}</div>
          </div>
        </basic-block>
      </el-col>
    </el-row>

    <!-- 筛选条 -->
    <basic-block>
      <div class="filter-bar">
        <el-select v-model="filters.scene_code" placeholder="全部场景" clearable style="width: 200px" @change="loadList">
          <el-option label="全部场景" value="" />
          <el-option
            v-for="s in scenes"
            :key="s.code"
            :label="s.name"
            :value="s.code"
          />
        </el-select>
        <el-radio-group v-model="filters.is_custom" @change="loadList">
          <el-radio-button :value="null">全部</el-radio-button>
          <el-radio-button :value="false">预置</el-radio-button>
          <el-radio-button :value="true">自定义</el-radio-button>
        </el-radio-group>
      </div>
    </basic-block>

    <!-- 模板卡片网格（2 列） -->
    <el-row :gutter="16" v-loading="loading">
      <el-col
        :xs="24"
        :sm="24"
        :md="12"
        v-for="tpl in list"
        :key="tpl.template_id"
      >
        <div class="template-card">
          <div class="tpl-head">
            <div class="tpl-icon" :style="{ background: tplColor(tpl.scene_code).bg, color: tplColor(tpl.scene_code).color }">
              <el-icon :size="22"><component :is="tplColor(tpl.scene_code).icon" /></el-icon>
            </div>
            <div class="tpl-meta">
              <div class="tpl-name">
                {{ tpl.name }}
                <el-tag v-if="tpl.is_custom" size="small" effect="plain">自定义</el-tag>
              </div>
              <div class="tpl-tags">
                <el-tag
                  v-for="tag in tpl.tags"
                  :key="tag.tag_id"
                  size="small"
                  type="info"
                  effect="plain"
                >{{ tag.name }}</el-tag>
              </div>
            </div>
          </div>
          <div class="tpl-desc">{{ tpl.description }}</div>
          <div class="tpl-foot">
            <span class="tpl-stat">
              <el-icon><DataAnalysis /></el-icon>
              近 30 天使用 <b>{{ tpl.use_count_30d }}</b> 次
            </span>
            <span class="tpl-updated">最近更新：{{ formatDate(tpl.updated_at) }}</span>
          </div>
          <div class="tpl-actions">
            <el-button link type="primary" @click="onDetail(tpl)">查看模板</el-button>
            <el-button link type="primary" @click="onUse(tpl)">使用此场景生成</el-button>
          </div>
        </div>
      </el-col>
    </el-row>

    <div v-if="!loading && list.length === 0" class="empty">
      <p>未找到匹配的模板</p>
    </div>

    <!-- 模板详情弹窗 -->
    <template-detail-modal
      v-model="detailVisible"
      :template-id="detailTargetId"
      @use="onUse"
    />

    <!-- 创建模板弹窗 -->
    <template-create-modal
      v-model="createVisible"
      :meta="meta"
      @created="loadList"
    />

    <!-- 新增场景弹窗 -->
    <scene-create-modal
      v-model="sceneCreateVisible"
      @saved="onSceneSaved"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Plus,
  Document,
  PieChart,
  Share,
  Message,
  Promotion,
  DataAnalysis
} from '@element-plus/icons-vue'
import sxkApi from '@/mock/sxkApi'
import TemplateDetailModal from './components/template-detail-modal.vue'
import TemplateCreateModal from './components/template-create-modal.vue'
import SceneCreateModal from './components/scene-create-modal.vue'

const router = useRouter()

// ========== 状态 ==========
const list = ref([])
const loading = ref(false)
const filters = reactive({ scene_code: '', is_custom: null })
const scenes = ref([])
const meta = ref({ scene_codes: [], output_formats: [] })

const detailVisible = ref(false)
const detailTargetId = ref(null)
const createVisible = ref(false)
const sceneCreateVisible = ref(false)

// ========== 工具 ==========
const formatDate = (iso) => {
  if (!iso) return '—'
  const d = new Date(iso)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

const ICON_MAP = {
  product_intro: Document,
  competitor: PieChart,
  channel_adapt: Share,
  email: Message,
  event: Promotion,
  other: Document
}
// 场景色：对齐原型 SXK.html（Tailwind *-50 底 + *-600 字）
const COLOR_MAP = {
  product_intro: { bg: '#eff6ff', color: '#2563eb' },  // blue-50 / blue-600
  competitor: { bg: '#fff7ed', color: '#ea580c' },      // orange-50 / orange-600
  channel_adapt: { bg: '#f0fdf4', color: '#16a34a' },  // green-50 / green-600
  email: { bg: '#faf5ff', color: '#9333ea' },           // purple-50 / purple-600
  event: { bg: '#fee2e2', color: '#dc2626' },           // red-50 / red-600
  other: { bg: '#f1f5f9', color: '#475569' }            // slate-50 / slate-600
}
const tplColor = (code) => ({
  ...(COLOR_MAP[code] || COLOR_MAP.other),
  icon: ICON_MAP[code] || Document
})

// ========== 计算属性：4 张统计卡 ==========
const statCards = computed(() => {
  const total = list.value.length
  const customCount = list.value.filter((t) => t.is_custom).length
  const useCount = list.value.reduce((sum, t) => sum + (t.use_count_30d || 0), 0)
  const sceneCount = new Set(list.value.map((t) => t.scene_code)).size
  return [
    { label: '场景模板数', value: sceneCount, color: '#2563eb' },   // blue-600
    { label: '模板总数', value: total, color: '#16a34a' },          // green-600
    { label: '本月使用次数', value: useCount, color: '#ea580c' },    // orange-600
    { label: '自定义模板', value: customCount, color: '#9333ea' }    // purple-600
  ]
})

// ========== 数据 ==========
const loadList = async () => {
  loading.value = true
  const res = await sxkApi.listTemplates({
    page: 1,
    size: 100,
    scene_code: filters.scene_code,
    is_custom: filters.is_custom
  })
  loading.value = false
  if (res.data) list.value = res.data.items || []
}

const loadMeta = async () => {
  const res = await sxkApi.getTemplateMeta()
  if (res.data) {
    meta.value = res.data
    scenes.value = res.data.scene_codes || []
  }
}

// ========== 操作 ==========
const onCreate = () => {
  createVisible.value = true
}
const onAddScene = () => {
  sceneCreateVisible.value = true
}
const onSceneSaved = async (scene) => {
  const res = await sxkApi.createScene(scene)
  if (res.code === 0) {
    ElMessage.success(`场景「${scene.name}」已保存`)
    loadMeta()
  } else {
    ElMessage.error(res.msg || '保存失败')
  }
}
const onDetail = (tpl) => {
  detailTargetId.value = tpl.template_id
  detailVisible.value = true
}
const onUse = async (tpl) => {
  // 4.5.6：调用使用次数 +1 接口
  await sxkApi.useTemplate(tpl.template_id)
  // 5.5.3：使用此场景生成 → 跳转内容生成并预设场景
  detailVisible.value = false
  ElMessage.success(`已使用「${tpl.name}」预设场景`)
  router.push({ path: '/generate/index', query: { scene: tpl.scene_code, template: tpl.template_id } })
}

onMounted(() => {
  loadList()
  loadMeta()
})
</script>

<style lang="scss" scoped>
.sxk-templates {
  display: flex;
  flex-direction: column;
  gap: $spacing-md;
}

// ========== 页面头部 ==========
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;

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

  &__actions {
    display: flex;
    align-items: center;
    gap: $spacing-sm;
  }
}

// ========== 统计卡片 ==========
.mini-stat {
  text-align: center;
  padding: $spacing-md 0;

  &__value {
    font-size: $font-size-3xl;
    font-weight: 700;
    line-height: 1.2;
  }
  &__label {
    font-size: $font-size-sm;
    color: $text-regular;
    margin-top: $spacing-xs;
  }
}

// ========== 筛选条 ==========
.filter-bar {
  display: flex;
  align-items: center;
  gap: $spacing-lg;
  flex-wrap: wrap;
}

// ========== 模板卡片 ==========
.template-card {
  margin-bottom: $spacing-lg;
  padding: $spacing-lg $spacing-xl;
  background: $bg-card;
  border: 1px solid $border-base;
  border-radius: $radius-lg;
  transition: $transition-base;

  &:hover {
    border-color: $primary-color;
    box-shadow: $shadow-hover;
  }

  .tpl-head {
    display: flex;
    align-items: center;
    gap: $spacing-md;
    margin-bottom: $spacing-md;
  }

  .tpl-icon {
    width: 44px;
    height: 44px;
    border-radius: $radius-lg;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  .tpl-meta {
    flex: 1;

    .tpl-name {
      font-size: $font-size-lg;
      font-weight: 600;
      color: $text-primary;
      display: flex;
      align-items: center;
      gap: $spacing-sm;
    }
    .tpl-tags {
      display: flex;
      gap: $spacing-xs;
      margin-top: $spacing-xs;
      flex-wrap: wrap;
    }
  }

  .tpl-desc {
    font-size: $font-size-sm;
    color: $text-regular;
    line-height: 1.6;
    margin-bottom: $spacing-md;
    min-height: 42px;
  }

  .tpl-foot {
    display: flex;
    justify-content: space-between;
    font-size: $font-size-xs;
    color: $text-regular;
    padding-top: $spacing-md;
    border-top: 1px solid $border-light;

    .tpl-stat {
      display: flex;
      align-items: center;
      gap: $spacing-xs;
      b {
        color: $primary-color;
        font-weight: 600;
        margin: 0 2px;
      }
    }
  }

  .tpl-actions {
    margin-top: $spacing-md;
    display: flex;
    gap: $spacing-md;
  }
}

.empty {
  text-align: center;
  color: $text-secondary;
  padding: $spacing-2xl 0;
}
</style>
