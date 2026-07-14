<!--
  神行库 · 模板管理（场景维度）
  对应原型 SXK_v3.html 页面5：
    - 4 个统计卡片（场景模板数 / 具体模板数 / 总使用次数 / 自定义场景数）
    - 场景卡片列表（每个场景下含子模板，点击查看详情/添加子模板）
    - 场景详情弹窗（template-detail-modal）
-->
<template>
  <div class="sxk-templates">
    <!-- 顶部欢迎条：与首页风格一致 -->
    <div class="sxk-page-welcome">
      <div class="sxk-page-welcome__left">
        <h2 class="sxk-page-welcome__title">
          场景模板管理
        </h2>
        <p class="sxk-page-welcome__desc">
          管理营销场景与子模板，支撑多 Agent 内容生成
        </p>
      </div>
      <div class="sxk-page-welcome__actions">
        <el-button
          type="primary"
          @click="onAddScene"
        >
          <el-icon><Grid /></el-icon>
          <span>新建场景</span>
        </el-button>
      </div>
    </div>

    <!-- 4 个统计卡片 -->
    <el-row :gutter="16">
      <el-col
        v-for="card in statCards"
        :key="card.label"
        :xs="24"
        :sm="12"
        :md="6"
      >
        <basic-block
          hover-shadow
          padding="small"
        >
          <div class="mini-stat">
            <div
              class="mini-stat__icon"
              :style="{ background: card.bg, color: card.color }"
            >
              <el-icon :size="20">
                <component :is="card.icon" />
              </el-icon>
            </div>
            <div class="mini-stat__body">
              <div
                class="mini-stat__value"
                :style="{ color: card.color }"
              >
                {{ card.value }}
              </div>
              <div class="mini-stat__label">
                {{ card.label }}
              </div>
            </div>
          </div>
        </basic-block>
      </el-col>
    </el-row>

    <!-- 场景卡片列表 -->
    <div
      v-loading="loading"
      class="scene-list"
    >
      <div
        v-for="scene in sceneList"
        :key="scene.scene_code"
        class="scene-card"
      >
        <!-- 紧凑横向布局：图标 | 名称+描述 | 标签 | 元信息 | 操作 -->
        <div
          class="scene-card__icon"
          :style="{ background: tplColor(scene.scene_code, scene.name).bg, color: tplColor(scene.scene_code, scene.name).color }"
        >
          <el-icon :size="20">
            <component :is="tplColor(scene.scene_code, scene.name).icon" />
          </el-icon>
        </div>

        <div
          class="scene-card__main"
          @click="onDetail(scene)"
        >
          <div class="scene-card__name-row">
            <span class="scene-card__name">{{ scene.name }}</span>
            <el-tag
              v-if="isCustomScene(scene.scene_code)"
              size="small"
              type="warning"
              effect="plain"
              class="scene-card__tag"
            >
              自定义
            </el-tag>
            <span class="scene-card__sub-count">· {{ getSceneTemplates(scene.scene_code).length }} 个子模板</span>
          </div>
          <div class="scene-card__desc">
            {{ scene.description || '暂无描述' }}
          </div>
        </div>

        <!-- 中部：子模板预览标签（限 2 个）-->
        <div class="scene-card__preview">
          <template v-if="getSceneTemplates(scene.scene_code).length > 0">
            <el-tag
              v-for="tpl in getSceneTemplates(scene.scene_code).slice(0, 2)"
              :key="tpl.template_id"
              size="small"
              effect="plain"
            >
              {{ tpl.name }}
            </el-tag>
            <span
              v-if="getSceneTemplates(scene.scene_code).length > 2"
              class="scene-card__more"
            >
              +{{ getSceneTemplates(scene.scene_code).length - 2 }}
            </span>
          </template>
        </div>

        <!-- 右侧：元信息 + 操作 -->
        <div class="scene-card__meta">
          <el-icon><Clock /></el-icon>
          <span>最近更新 {{ formatSceneUpdate(scene.scene_code) }}</span>
        </div>

        <div class="scene-card__actions">
          <el-button
            link
            type="primary"
            size="small"
            @click="onDetail(scene)"
          >
            查看详情
          </el-button>
          <span class="scene-card__divider">|</span>
          <el-button
            link
            type="danger"
            size="small"
            :icon="Delete"
            @click="onDeleteScene(scene)"
          >
            删除
          </el-button>
        </div>
      </div>

      <!-- 空状态 -->
      <div
        v-if="!loading && sceneList.length === 0"
        class="empty"
      >
        <el-icon style="font-size: 48px; color: var(--el-text-color-placeholder)">
          <Grid />
        </el-icon>
        <p>还没有任何场景，点击右上角"新建场景"开始创建</p>
      </div>
    </div>

    <!-- 场景详情弹窗 -->
    <template-detail-modal
      v-model="detailVisible"
      :template-id="detailTargetId"
      :scene-code="detailTargetSceneCode"
      @use="onUse"
    />

    <!-- 新增/编辑场景弹窗 -->
    <scene-create-modal
      v-model="sceneCreateVisible"
      :loading="sceneSaving"
      :edit-data="sceneEditData"
      @saved="onSceneSaved"
    />

    <!-- 管理场景弹窗 -->
    <el-dialog
      v-model="sceneManageVisible"
      width="640px"
      class="scene-manage-dialog"
      :show-close="false"
    >
      <div class="sm-head">
        <div class="sm-head__left">
          <el-icon
            :size="20"
            color="var(--el-color-primary)"
          >
            <Setting />
          </el-icon>
          <div>
            <h3>管理场景</h3>
            <p>查看、编辑或删除已有场景</p>
          </div>
        </div>
        <el-icon
          class="sm-head__close"
          @click="sceneManageVisible = false"
        >
          <Close />
        </el-icon>
      </div>
      <div class="sm-body">
        <div
          v-for="s in sceneSchemasList"
          :key="s.scene_code"
          class="sm-item"
        >
          <div
            class="sm-item__icon"
            :style="{ background: tplColor(s.scene_code, s.name).bg, color: tplColor(s.scene_code, s.name).color }"
          >
            <el-icon :size="18">
              <component :is="tplColor(s.scene_code, s.name).icon" />
            </el-icon>
          </div>
          <div class="sm-item__info">
            <div class="sm-item__name">
              {{ s.name }}
            </div>
            <div class="sm-item__desc">
              {{ s.description || '暂无描述' }}
            </div>
            <div class="sm-item__params">
              {{ (s.params || []).length }} 个参数
            </div>
          </div>
          <div class="sm-item__actions">
            <el-button
              link
              type="primary"
              @click="onEditScene(s)"
            >
              编辑
            </el-button>
            <el-button
              link
              type="danger"
              @click="onDeleteScene(s)"
            >
              删除
            </el-button>
          </div>
        </div>
        <div
          v-if="sceneSchemasList.length === 0"
          class="sm-empty"
        >
          暂无场景数据
        </div>
      </div>
      <div class="sm-foot">
        <el-button @click="sceneManageVisible = false">
          关闭
        </el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, markRaw, nextTick, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Grid,
  Document,
  PieChart,
  Share,
  Message,
  Promotion,
  Setting,
  Close,
  EditPen,
  Delete,
  Clock,
  Files,
  DataLine,
  Plus as PlusIcon,
  Monitor,        // 官网/Banner
  Histogram,      // 产品介绍
  TrendCharts,    // 竞品对比
  Medal,          // 客户案例
  Film,           // PPT/演示
  ChatDotRound    // 社交媒体
} from '@element-plus/icons-vue'
import sxkApi from '@/mock/sxkApi'
import TemplateDetailModal from './components/template-detail-modal.vue'
import SceneCreateModal from './components/scene-create-modal.vue'

const router = useRouter()
const route = useRoute()

// ========== 状态 ==========
const allTemplates = ref([])     // 全部模板（扁平列表）
const loading = ref(false)

const detailVisible = ref(false)
const detailTargetId = ref(null)
const detailTargetSceneCode = ref('')
const sceneCreateVisible = ref(false)
const sceneSaving = ref(false)

// 场景管理弹窗
const sceneManageVisible = ref(false)
const sceneSchemasList = ref([])
const sceneEditData = ref(null)  // null=新增模式，对象=编辑模式

// ========== 工具 ==========
const formatDate = (iso) => {
  if (!iso) return '—'
  const d = new Date(iso)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

// ========== 场景图标 / 配色：使用共享 util（与 dashboard 页面保持完全一致） ==========
// 关键：从 src/util/scene-style 引入，避免两个页面展示同一场景时样式不一致
import { getSceneStyle as tplColor } from '@/util/scene-style'

// 旧版 code → 配色映射（兼容）
const COLOR_MAP_LEGACY = {
  product_intro: { bg: '#eff6ff', color: '#2563eb' },
  competitor: { bg: '#fff7ed', color: '#ea580c' },
  channel_adapt: { bg: '#f0fdf4', color: '#16a34a' },
  email: { bg: '#faf5ff', color: '#9333ea' },
  event: { bg: '#fee2e2', color: '#dc2626' },
  other: { bg: '#f1f5f9', color: '#475569' }
}

// 判断是否自定义场景
// 后端预置场景的 id 是 S001-S006（见 B2B-SXK-FastApi/app/seed_data.py SEED_SCENARIOS）
// mock 场景的 id 是 product_intro/competitor/...（见 src/mock/data.js mockSceneSchemas）
// 两端 ID 格式不同，需要同时兼容（用 startsWith 判定）
const PRESET_SCENE_IDS = ['S001', 'S002', 'S003', 'S004', 'S005', 'S006', 'S007', 'S008', 'S009', 'S010']
const PRESET_SCENE_CODES = ['product_intro', 'competitor', 'channel_adapt', 'email', 'event', 'other']
const isCustomScene = (code) => {
  if (!code) return true  // 防御性：code 为空时视为自定义
  // 后端预置：S0xx 格式
  if (PRESET_SCENE_IDS.includes(code)) return false
  // mock 预置：product_intro / competitor / ... 格式
  if (PRESET_SCENE_CODES.includes(code)) return false
  // 用户自定义：以 S 开头但不在预置列表中（如 S123ABC），或纯 UUID
  return true
}

// ========== 计算属性 ==========
// 场景列表（来源于 getSceneSchemas）
const sceneList = computed(() => sceneSchemasList.value)

// 按场景分组获取模板
const getSceneTemplates = (sceneCode) => {
  return allTemplates.value.filter((t) => t.scene_code === sceneCode)
}

// 获取场景下最近更新时间
const formatSceneUpdate = (sceneCode) => {
  const tpls = getSceneTemplates(sceneCode)
  if (tpls.length === 0) return '—'
  const sorted = [...tpls].sort((a, b) => new Date(b.updated_at || 0) - new Date(a.updated_at || 0))
  return formatDate(sorted[0].updated_at)
}

// 4 张统计卡
const statCards = computed(() => {
  const sceneCount = sceneList.value.length
  const tplCount = allTemplates.value.length
  const useCount = allTemplates.value.reduce((sum, t) => sum + (t.use_count_30d || 0), 0)
  const customSceneCount = sceneList.value.filter((s) => isCustomScene(s.scene_code)).length
  return [
    { label: '场景模板数', value: sceneCount, color: '#2563eb', bg: '#eff6ff', icon: markRaw(Grid) },
    { label: '具体模板数', value: tplCount, color: '#16a34a', bg: '#f0fdf4', icon: markRaw(Files) },
    { label: '总使用次数', value: useCount, color: '#ea580c', bg: '#fff7ed', icon: markRaw(DataLine) },
    { label: '自定义场景', value: customSceneCount, color: '#9333ea', bg: '#faf5ff', icon: markRaw(PlusIcon) }
  ]
})

// ========== 数据加载 ==========
const loadAllTemplates = async () => {
  loading.value = true
  try {
    const res = await sxkApi.listTemplates({ page: 1, size: 500 })
    if (res.data) allTemplates.value = res.data.items || []
  } catch (e) {
    console.error('[Templates] loadAllTemplates failed', e)
    ElMessage.error('加载模板列表失败')
  } finally {
    loading.value = false
  }
}

const loadSceneSchemas = async () => {
  try {
    const res = await sxkApi.getSceneSchemas()
    if (res.data) {
      sceneSchemasList.value = res.data.scenes || []
    }
  } catch (e) {
    console.error('[Templates] loadSceneSchemas failed', e)
  }
}

// ========== 操作 ==========
const onAddScene = () => {
  sceneEditData.value = null
  sceneCreateVisible.value = true
}

const onSceneSaved = async (scene) => {
  sceneSaving.value = true
  try {
    if (sceneEditData.value) {
      // 编辑模式：更新场景
      const res = await sxkApi.updateScene(sceneEditData.value.scene_code, scene)
      if (res.code === 0) {
        ElMessage.success(`场景「${scene.name}」已更新`)
        sceneCreateVisible.value = false
        sceneEditData.value = null
        loadSceneSchemas()
      } else {
        ElMessage.error(res.msg || '保存失败')
      }
    } else {
      // 新增模式
      const res = await sxkApi.createScene(scene)
      if (res.code === 0) {
        ElMessage.success(`场景「${scene.name}」已保存`)
        sceneCreateVisible.value = false
        loadSceneSchemas()
      } else {
        ElMessage.error(res.msg || '保存失败')
      }
    }
  } catch {
    // axios 拦截器已提示错误
  } finally {
    sceneSaving.value = false
  }
}

// 点击场景 → 打开详情弹窗（传场景下第一个模板 ID 或 null）
const onDetail = (scene) => {
  const tpls = getSceneTemplates(scene.scene_code)
  detailTargetId.value = tpls.length > 0 ? tpls[0].template_id : ''
  detailTargetSceneCode.value = scene.scene_code
  detailVisible.value = true
}

// 使用此场景生成 → 跳转内容生成页
const onUse = async (tpl) => {
  detailVisible.value = false
  ElMessage.success(`已使用「${tpl.name || ''}」预设场景`)
  router.push({ path: '/generate/index', query: { scene: tpl.scene_code, template: tpl.template_id } })
}

const onUseScene = (scene) => {
  const tpls = getSceneTemplates(scene.scene_code)
  if (tpls.length > 0) {
    onUse({ ...tpls[0], scene_code: scene.scene_code })
  } else {
    ElMessage.success(`已预设场景「${scene.name}」`)
    router.push({ path: '/generate/index', query: { scene: scene.scene_code } })
  }
}

// ========== 场景管理 ==========
const onManageScenes = async () => {
  await loadSceneSchemas()
  sceneManageVisible.value = true
}

const onEditScene = (scene) => {
  sceneEditData.value = scene
  sceneManageVisible.value = false
  sceneCreateVisible.value = true
}

const onEditSceneFromCard = (scene) => {
  sceneEditData.value = scene
  sceneCreateVisible.value = true
}

const onDeleteScene = async (scene) => {
  const tplCount = getSceneTemplates(scene.scene_code).length
  try {
    await ElMessageBox.confirm(
      `确定要删除场景「${scene.name}」吗？${tplCount > 0 ? `该场景下有 ${tplCount} 个子模板，也将一并删除。` : ''}此操作不可恢复。`,
      '删除确认',
      { type: 'warning', confirmButtonText: '确定删除', cancelButtonText: '取消' }
    )
  } catch {
    return // 用户取消
  }
  try {
    const res = await sxkApi.deleteScene(scene.scene_code)
    if (res.code === 0) {
      ElMessage.success(`场景「${scene.name}」已删除`)
      loadSceneSchemas()
      loadAllTemplates()
    } else {
      ElMessage.error(res.msg || '删除失败')
    }
  } catch {
    // axios 拦截器已提示错误
  }
}

onMounted(async () => {
  loadAllTemplates()
  await loadSceneSchemas()  // 关键：await 等数据加载完
  // 关键：处理首页"营销场景"卡片点击跳转过来时的 openDetail query
  await nextTick()           // 等 DOM 更新
  await openDetailFromQuery()
})

/**
 * 关键：处理首页"营销场景"卡片点击跳转过来时的 openDetail query
 * 直接在数据加载完成后检查 query，找到场景就打开弹窗
 */
const openDetailFromQuery = async () => {
  const code = route.query.openDetail
  if (!code) return
  if (sceneSchemasList.value.length === 0) {
    ElMessage.warning('场景数据加载中，请稍后再试')
    return
  }
  const scene = sceneSchemasList.value.find((s) => s.scene_code === code)
  // 多 Tab：清除 openDetail 但保留 tabId，避免 permission.js 重新生成 tabId
  const cleanQuery = { tabId: route.query.tabId }
  if (scene) {
    // 关键：用 nextTick 等待弹窗绑定完成
    nextTick(() => {
      onDetail(scene)
      // 清除 query，避免刷新或后退时再次触发
      router.replace({ path: '/templates/index', query: cleanQuery })
    })
  } else {
    ElMessage.warning(`未找到场景「${code}」，可能已被删除`)
    router.replace({ path: '/templates/index', query: cleanQuery })
  }
}
</script>

<style lang="scss" scoped>
.sxk-templates {
  display: flex;
  flex-direction: column;
  gap: $spacing-md;
}

// ========== 页面头部（已迁移到 .sxk-page-welcome，参考 common.scss） ==========
// 关键：删除了旧的 .page-header，使用全局 .sxk-page-welcome 组件

// ========== 统计卡片 ==========
.mini-stat {
  display: flex;
  align-items: center;
  gap: $spacing-md;

  &__icon {
    flex-shrink: 0;
    width: 40px;
    height: 40px;
    border-radius: $radius-md;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  &__body {
    flex: 1;
    min-width: 0;
  }

  &__value {
    font-size: $font-size-2xl;
    font-weight: 700;
    line-height: 1.2;
  }
  &__label {
    font-size: $font-size-sm;
    color: $text-regular;
    margin-top: 2px;
  }
}

// ========== 场景卡片列表 ==========
.scene-list {
  display: flex;
  flex-direction: column;
  // 关键：卡片间距收紧，从 12px 减到 8px，整体更紧凑
  gap: 8px;
}

.scene-card {
  // 关键：横向紧凑布局，单行展示所有信息
  display: flex;
  align-items: center;
  gap: $spacing-md;
  padding: $spacing-sm $spacing-md;
  background: $bg-card;
  border: 1px solid $border-base;
  border-radius: $radius-md;
  box-shadow: $shadow-sm;
  transition: $transition-base;
  min-height: 64px;

  &:hover {
    border-color: $primary-color;
    box-shadow: $shadow-hover;
    background: $bg-hover;
  }

  // 图标：紧凑 40×40
  &__icon {
    flex-shrink: 0;
    width: 40px;
    height: 40px;
    border-radius: $radius-md;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  // 主信息区：名称 + 描述（可点击）
  &__main {
    flex: 1;
    min-width: 0;  // 关键：让子元素的 ellipsis 生效
    cursor: pointer;
    overflow: hidden;

    &:hover {
      .scene-card__name {
        color: $primary-color;
      }
    }
  }

  &__name-row {
    display: flex;
    align-items: center;
    gap: $spacing-xs;
    margin-bottom: 2px;
  }

  &__name {
    font-size: $font-size-base;
    font-weight: 600;
    color: $text-primary;
    transition: color 0.2s;
    white-space: nowrap;
  }

  &__tag {
    flex-shrink: 0;
  }

  &__sub-count {
    font-size: $font-size-xs;
    color: $text-secondary;
    white-space: nowrap;
  }

  // 描述：1行省略
  &__desc {
    font-size: $font-size-xs;
    color: $text-regular;
    line-height: 1.5;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  // 子模板预览标签（限 2 个）
  &__preview {
    display: flex;
    align-items: center;
    gap: $spacing-xs;
    flex-shrink: 0;
    max-width: 200px;
    overflow: hidden;
  }

  &__more {
    color: $text-secondary;
    font-size: $font-size-xs;
    flex-shrink: 0;
  }

  // 元信息（最近更新时间）
  &__meta {
    display: flex;
    align-items: center;
    gap: $spacing-xs;
    color: $text-secondary;
    font-size: $font-size-xs;
    flex-shrink: 0;
    white-space: nowrap;
  }

  // 操作按钮
  &__actions {
    display: flex;
    align-items: center;
    gap: $spacing-xs;
    flex-shrink: 0;
  }

  &__divider {
    color: $border-base;
    margin: 0 $spacing-xs;
  }

  // 兼容旧版引用（防止编译警告）
  &__empty-preview {
    color: $text-placeholder;
  }

  // 兼容旧版引用（防止编译警告）
  &__foot {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding-top: $spacing-md;
    border-top: 1px solid $border-light;

    &-left {
      display: flex;
      align-items: center;
      gap: $spacing-xs;
      font-size: $font-size-xs;
      color: $text-secondary;
    }

    &-right {
      display: flex;
      align-items: center;
      gap: $spacing-xs;
    }
  }

  // 兼容旧版引用（防止编译警告）
  &__divider-old {
    color: $border-base;
  }
}

// ========== 空状态 ==========
.empty {
  text-align: center;
  color: $text-secondary;
  padding: $spacing-2xl 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: $spacing-md;
}

// ========== 场景管理弹窗 ==========
.scene-manage-dialog {
  // 隐藏 el-dialog 默认 header（使用自定义 header）
  .el-dialog__header {
    display: none;
  }
  .el-dialog__body {
    padding: 0;
  }
  .el-dialog__footer {
    display: none;
  }
}

.sm-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: $spacing-lg $spacing-xl;
  border-bottom: 1px solid $border-light;

  &__left {
    display: flex;
    align-items: center;
    gap: $spacing-md;

    h3 {
      margin: 0;
      font-size: $font-size-lg;
      font-weight: 600;
      color: $text-primary;
    }
    p {
      margin: 0;
      font-size: $font-size-xs;
      color: $text-regular;
    }
  }

  &__close {
    cursor: pointer;
    color: $text-secondary;
    font-size: 18px;
    transition: $transition-base;

    &:hover {
      color: $text-primary;
    }
  }
}

.sm-body {
  max-height: calc(60vh - 80px);
  overflow-y: auto;
  padding: $spacing-md $spacing-xl;
}

.sm-item {
  display: flex;
  align-items: center;
  gap: $spacing-md;
  padding: $spacing-md;
  border: 1px solid $border-light;
  border-radius: $radius-md;
  margin-bottom: $spacing-md;
  transition: $transition-base;

  &:last-child {
    margin-bottom: 0;
  }
  &:hover {
    border-color: $primary-color;
  }

  &__icon {
    width: 36px;
    height: 36px;
    border-radius: $radius-md;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  &__info {
    flex: 1;
    min-width: 0;

    .sm-item__name {
      font-size: $font-size-base;
      font-weight: 600;
      color: $text-primary;
    }
    .sm-item__desc {
      font-size: $font-size-xs;
      color: $text-regular;
      margin-top: 2px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .sm-item__params {
      font-size: $font-size-xs;
      color: $text-secondary;
      margin-top: 4px;
    }
  }

  &__actions {
    display: flex;
    gap: $spacing-xs;
    flex-shrink: 0;
  }
}

.sm-empty {
  text-align: center;
  color: $text-secondary;
  padding: $spacing-2xl 0;
}

.sm-foot {
  display: flex;
  justify-content: flex-end;
  gap: $spacing-sm;
  padding: $spacing-md $spacing-xl;
  border-top: 1px solid $border-light;
}
</style>
