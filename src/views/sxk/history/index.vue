<!--
  神行库 · 生成历史（卡片式列表）
  对齐后端参考版 B2B-SXK-FastApi/frontend 的卡片式历史布局
-->
<template>
  <div class="sxk-history">
    <!-- ========== 顶部标题 ========== -->
    <basic-block>
      <div class="page-header">
        <div class="page-header__title">
          <h2>生成历史</h2>
          <p>共 <b>{{ list.length }}</b> 条记录</p>
        </div>
        <div class="page-header__actions">
          <el-button :icon="Refresh" @click="load" :loading="loading">刷新</el-button>
        </div>
      </div>
    </basic-block>

    <!-- ========== 搜索 + 筛选 ========== -->
    <basic-block>
      <div class="search-bar">
        <el-input
          v-model="filters.keyword"
          placeholder="按产品名称模糊搜索"
          clearable
          style="max-width: 360px"
          @keyup.enter="search"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>

        <el-select
          v-model="filters.scene_code"
          placeholder="全部场景"
          clearable
          style="width: 200px"
          @change="search"
        >
          <el-option label="全部场景" value="" />
          <el-option
            v-for="s in scenes"
            :key="s.scene_code"
            :label="s.name"
            :value="s.scene_code"
          />
        </el-select>

        <el-select
          v-model="filters.validated"
          placeholder="校验状态"
          clearable
          style="width: 140px"
          @change="search"
        >
          <el-option label="全部" value="" />
          <el-option label="校验通过" value="true" />
          <el-option label="待完善" value="false" />
        </el-select>

        <el-button type="primary" @click="search">搜索</el-button>
        <el-button @click="reset">重置</el-button>
      </div>
    </basic-block>

    <!-- ========== 卡片列表 ========== -->
    <basic-block>
      <div v-if="loading && list.length === 0" class="sxk-history__loading">
        <el-icon class="rotating"><Loading /></el-icon>
        加载中...
      </div>
      <div v-else-if="!filteredList.length" class="sxk-history__empty">
        <el-empty :description="emptyText" />
      </div>
      <div v-else class="sxk-history__list">
        <div
          v-for="row in filteredList"
          :key="row.generation_id"
          class="sxk-history__card"
          :class="{ 'is-valid': row.validated, 'is-highlight': highlightId === row.generation_id }"
          :data-gid="row.generation_id"
          @click="onView(row)"
        >
          <!-- 左侧 4px 侧边条（已校验=蓝、待校验=橙） -->
          <div class="sxk-history__card-bar" />

          <div class="sxk-history__card-main">
            <div class="sxk-history__card-top">
              <span class="sxk-history__card-product">
                {{ row.product?.name || '已删除产品' }}
              </span>
              <span
                v-if="row.scene_name"
                class="sxk-history__card-scene"
              >
                / {{ row.scene_name }}
              </span>
              <span
                class="sxk-history__card-status"
                :class="row.validated ? 'is-pass' : 'is-warn'"
              >
                <span class="sxk-history__card-status-dot" />
                <span>{{ row.validated ? '已校验' : '待完善' }}</span>
              </span>
            </div>

            <div class="sxk-history__card-meta">
              <span v-if="splitChannels(row.channel).length" class="sxk-history__card-channel">
                渠道 · {{ splitChannels(row.channel).join(' / ') }}
              </span>
              <span>{{ formatDateTime(row.created_at) }}</span>
              <span
                v-if="row.created_by"
                class="sxk-history__card-creator"
                :style="{ color: memberColor(displayCreator(row)) }"
              >
                <span class="sxk-history__card-creator-dot" :style="{ background: memberColor(displayCreator(row)) }" />
                {{ displayCreator(row) }}
              </span>
            </div>
          </div>

          <!-- 右侧操作：反馈 + 导出 + 删除 -->
          <div class="sxk-history__card-actions" @click.stop>
            <button
              class="sxk-history__icon-btn is-like"
              :class="{ 'is-active': row.feedback === 'like' }"
              title="点赞"
              @click="onSetFeedback(row, 'like')"
            >
              <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
                <path d="M2 21h4V9H2v12zm20-11c0-1.1-.9-2-2-2h-6.31l.95-4.57.03-.32c0-.41-.17-.79-.44-1.06L13.17 1 7.59 6.59C7.22 6.95 7 7.45 7 8v10c0 1.1.9 2 2 2h9c.83 0 1.54-.5 1.84-1.22l3.02-7.05c.09-.23.14-.47.14-.73v-2z" />
              </svg>
            </button>
            <button
              class="sxk-history__icon-btn is-dislike"
              :class="{ 'is-active': row.feedback === 'dislike' }"
              title="点踩"
              @click="onSetFeedback(row, 'dislike')"
            >
              <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
                <path d="M22 3h-4v12h4V3zm-20 11c0 1.1.9 2 2 2h6.31l-.95 4.57-.03.32c0 .41.17.79.44 1.06L10.83 23l5.59-5.59c.36-.36.58-.86.58-1.41V6c0-1.1-.9-2-2-2H5c-.83 0-1.54.5-1.84 1.22L.14 12.27c-.09.23-.14.47-.14.73v2z" />
              </svg>
            </button>
            <el-button text size="small" @click="onExport(row)">导出</el-button>
            <el-button text size="small" type="danger" @click="onDelete(row)">
              删除
            </el-button>
          </div>
        </div>
      </div>
    </basic-block>

    <!-- ========== 详情弹窗 ========== -->
    <history-detail-modal
      v-model="detailVisible"
      :generation-id="detailTargetId"
      :version-index="detailTargetIndex"
      @edit="goEdit"
      @deleted="onDeleted"
      @updated="onUpdated"
    />
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, reactive, ref, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Search,
  Loading,
  Refresh
} from '@element-plus/icons-vue'
import BasicBlock from '@/components/basic-block/main.vue'
import { sxkApi } from '@/mock/sxkApi'
import HistoryDetailModal from './components/history-detail-modal.vue'

const router = useRouter()
const route = useRoute()

// ========== 状态 ==========
const filters = reactive({ keyword: '', scene_code: '', validated: '' })
const list = ref([])
const loading = ref(false)
const scenes = ref([])

const detailVisible = ref(false)
const detailTargetId = ref(null)
const detailTargetIndex = ref(0)
// 来自 /generate 跳转的高亮卡片（自动清除）
const highlightId = ref(null)

// 简单的成员色映射（与后端参考版 memberColor 一致）
const memberColor = (id) => {
  if (!id) return '#bbb'
  // 用用户名 hash 生成稳定颜色
  let hash = 0
  for (let i = 0; i < id.length; i++) {
    hash = (hash * 31 + id.charCodeAt(i)) & 0xffffffff
  }
  const colors = ['#1A56DB', '#16a34a', '#ea580c', '#9333ea', '#dc2626', '#0891b2', '#ca8a04']
  return colors[Math.abs(hash) % colors.length]
}

// ========== 计算属性 ==========
const filteredList = computed(() => {
  const kw = String(filters.keyword || '').trim().toLowerCase()
  return list.value.filter((g) => {
    if (filters.scene_code && g.scene_code !== filters.scene_code) return false
    if (filters.validated === 'true' && !g.validated) return false
    if (filters.validated === 'false' && g.validated) return false
    if (kw && !(g.product?.name || '').toLowerCase().includes(kw)) return false
    return true
  })
})

const emptyText = computed(() => {
  if (filters.keyword || filters.scene_code || filters.validated) {
    return '未找到匹配的历史记录'
  }
  return '暂无生成历史'
})

// ========== 工具 ==========
const formatDateTime = (iso) => {
  if (!iso) return ''
  const d = new Date(iso)
  if (isNaN(d.getTime())) return ''
  return (
    d.getFullYear() +
    '-' +
    String(d.getMonth() + 1).padStart(2, '0') +
    '-' +
    String(d.getDate()).padStart(2, '0') +
    ' ' +
    String(d.getHours()).padStart(2, '0') +
    ':' +
    String(d.getMinutes()).padStart(2, '0')
  )
}

const splitChannels = (channel) => {
  if (!channel) return []
  return String(channel)
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean)
}

// 创建人显示规整：把后端 user_id 形式（u_xxx）回退为当前登录用户名
// 后端 history 表没有 created_by 列，orchestrator 写的是 user["id"]
const isUserId = (s) => typeof s === 'string' && /^u_[a-f0-9]+$/i.test(s)
let cachedUsername = ''
try {
  const raw = localStorage.getItem('sxk-access-user') || sessionStorage.getItem('sxk-user')
  if (raw) {
    const u = JSON.parse(raw)
    cachedUsername = u?.username || u?.name || ''
  }
} catch {
  /* ignore */
}
const displayCreator = (row) => {
  const cb = row?.created_by
  if (cb && !isUserId(cb)) return cb
  return cachedUsername || '当前用户'
}

// ========== 数据加载 ==========
const load = async () => {
  loading.value = true
  try {
    const resp = await sxkApi.listHistory({ page: 1, size: 200 })
    list.value = resp.data?.items || []
  } catch (e) {
    list.value = []
    ElMessage.error('加载历史失败：' + (e?.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

const loadScenes = async () => {
  try {
    const resp = await sxkApi.getSceneSchemas()
    scenes.value = resp.data?.scenes || []
  } catch {
    scenes.value = []
  }
}

onMounted(async () => {
  await load()
  await loadScenes()
  // 数据加载完成后再处理跳转参数
  handleOpenDetailFromQuery()
})

// 监听 query.openDetail 变化（用户从其他页面再次携带参数进来时也能响应）
watch(
  () => route.query.openDetail,
  (newVal) => {
    if (newVal) handleOpenDetailFromQuery()
  }
)

/**
 * 处理 URL query 中的 openDetail 参数：
 * - 自动查找对应记录
 * - 自动打开详情弹窗
 * - 滚动并高亮目标卡片
 * - 清除 query，避免刷新重复触发
 */
let openDetailLocked = false
async function handleOpenDetailFromQuery() {
  // 防止 onMounted 与 watch 重复触发
  if (openDetailLocked) return
  const openId = route.query.openDetail
  if (!openId) return
  openDetailLocked = true
  // 如果 list 为空，先等待数据加载（避免在 onMounted 外被 watch 触发时 list 还没就绪）
  if (list.value.length === 0) {
    const ok = await waitListReady(20, 200)
    if (!ok) {
      console.warn('[history] list 加载超时，跳过自动打开')
      openDetailLocked = false
      return
    }
  }
  const target = list.value.find((r) => r.generation_id === openId)
  if (!target) {
    console.warn('[history] 在 list 中找不到目标', openId, 'list.length =', list.value.length)
    openDetailLocked = false
    return
  }
  // 打开详情弹窗 - 先设值，再用 nextTick 等待
  detailTargetId.value = target.generation_id
  detailTargetIndex.value = 0
  // 强制异步下一帧再设置 visible，避免首次渲染时 el-dialog 内部状态未就绪
  await nextTick()
  detailVisible.value = true
  // 监听 dialog 实际打开事件
  await nextTick()
  // 高亮 + 滚动（用 nextTick 等待弹窗 + 卡片 DOM 就绪）
  highlightId.value = target.generation_id
  await nextTick()
  const el = document.querySelector(
    `.sxk-history__card[data-gid="${target.generation_id}"]`
  )
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }
  // 2.4s 后清除高亮
  setTimeout(() => {
    highlightId.value = null
  }, 2400)
  // 最后清除 query，避免下次刷新重复触发（保留 highlight）
  router.replace({ query: { ...route.query, openDetail: undefined } })
}

/**
 * 等待 list 加载完成（轮询）
 * @param {number} maxRetry 最大重试次数
 * @param {number} interval 重试间隔 ms
 * @returns {Promise<boolean>} 是否就绪
 */
function waitListReady(maxRetry = 20, interval = 200) {
  return new Promise((resolve) => {
    let retry = 0
    const tick = () => {
      if (list.value.length > 0 || retry >= maxRetry) {
        resolve(list.value.length > 0)
        return
      }
      retry++
      setTimeout(tick, interval)
    }
    tick()
  })
}

// ========== 业务方法 ==========
const search = () => {
  // 搜索为纯前端过滤，无需重新拉取
}

const reset = () => {
  filters.keyword = ''
  filters.scene_code = ''
  filters.validated = ''
}

const onView = (row) => {
  detailTargetId.value = row.generation_id
  detailTargetIndex.value = 0
  detailVisible.value = true
}

const onExport = async (row) => {
  try {
    await sxkApi.exportDocx(row.generation_id)
    ElMessage.success('已开始导出')
  } catch (e) {
    ElMessage.error('导出失败：' + (e?.message || '未知错误'))
  }
}

const onDelete = (row) => {
  ElMessageBox.confirm('确认删除该历史记录？删除后不可恢复。', '删除历史', {
    type: 'warning',
    confirmButtonText: '确认删除',
    cancelButtonText: '取消'
  })
    .then(async () => {
      try {
        const resp = await sxkApi.removeHistory(row.generation_id)
        if (resp.code !== 0) {
          ElMessage.error(resp.msg || '删除失败')
          return
        }
        ElMessage.success('已删除')
        load()
      } catch (e) {
        ElMessage.error('删除失败：' + (e?.message || '未知错误'))
      }
    })
    .catch(() => {})
}

const onSetFeedback = async (row, fb) => {
  const next = row.feedback === fb ? '' : fb
  try {
    const resp = await sxkApi.setHistoryFeedback(row.generation_id, next)
    if (resp.code !== 0) {
      ElMessage.error(resp.msg || '操作失败')
      return
    }
    // 同步本地行
    Object.assign(row, resp.data)
    ElMessage.success(next ? (next === 'like' ? '已点赞' : '已踩') : '已取消标记')
  } catch (e) {
    ElMessage.error('操作失败：' + (e?.message || '未知错误'))
  }
}

const goEdit = (generationId) => {
  router.push({ path: '/generate/index', query: { gid: generationId } })
}

const onDeleted = () => {
  detailVisible.value = false
  load()
}

const onUpdated = (updated) => {
  // 同步列表中对应行
  const idx = list.value.findIndex((x) => x.generation_id === updated.generation_id)
  if (idx !== -1) {
    list.value[idx] = { ...list.value[idx], ...updated }
  }
}
</script>

<style lang="scss" scoped>
// ============================================================
// 生成历史（卡片式列表）—— 对齐后端参考版 B2B-SXK-FastApi/frontend
// 结构：1) 页面头  2) 搜索条  3) 卡片列表  4) 加载/空状态
// ============================================================

.sxk-history {
  display: flex;
  flex-direction: column;
  gap: $spacing-md;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: $spacing-md;
  &__title {
    h2 {
      margin: 0 0 4px;
      font-size: $font-size-xl;
      color: $text-primary;
    }
    p {
      margin: 0;
      font-size: $font-size-sm;
      color: $text-regular;
    }
  }
}

.search-bar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: $spacing-sm;
}

.sxk-history__loading {
  text-align: center;
  padding: $spacing-2xl 0;
  color: $text-regular;
  .rotating {
    animation: sxkRotating 1s linear infinite;
    margin-right: $spacing-sm;
  }
}

.sxk-history__empty {
  padding: $spacing-xl 0;
}

.sxk-history__list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.sxk-history__card {
  display: flex;
  width: 100%;
  background: $bg-card;
  border: 1px solid $border-base;
  border-radius: $radius-md;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: $shadow-sm;

  &:hover {
    box-shadow: $shadow-md;
    border-color: $primary-color-light;
    transform: translateY(-1px);
  }

  // 左侧 4px 侧边条：默认蓝
  &-bar {
    width: 4px;
    flex-shrink: 0;
    background: $primary-color;
  }
  // 待校验时为橙
  &:not(.is-valid) &-bar {
    background: #faad14;
  }

  // 来自 /generate 跳转的"高亮定位"动画（2.4s）
  &.is-highlight {
    border-color: $primary-color;
    box-shadow: 0 0 0 3px rgba($primary-color, 0.2), $shadow-md;
    animation: sxk-history-pulse 1.2s ease-in-out 2;
  }
}
@keyframes sxk-history-pulse {
  0%, 100% {
    box-shadow: 0 0 0 3px rgba($primary-color, 0.2), $shadow-md;
  }
  50% {
    box-shadow: 0 0 0 8px rgba($primary-color, 0.05), $shadow-md;
  }
}

.sxk-history__card-main {
  flex: 1 1 auto;
  padding: 12px 16px;
  min-width: 0;
}

.sxk-history__card-top {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}

.sxk-history__card-product {
  font-weight: 600;
  font-size: 15px;
  color: $text-primary;
}

// 场景（与产品名同行，斜杠分隔，不喧宾夺主）
.sxk-history__card-scene {
  font-size: 13px;
  color: $text-regular;
  font-weight: 400;
}

// 校验状态胶囊（圆点+文字，与详情弹窗一致）
.sxk-history__card-status {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 1px 8px 1px 6px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 500;
  line-height: 1.5;
  border: 1px solid transparent;
  margin-left: auto;

  &-dot {
    width: 5px;
    height: 5px;
    border-radius: 50%;
    background: currentColor;
  }
  &.is-pass {
    background: #ecfdf5;
    color: #047857;
    border-color: #a7f3d0;
  }
  &.is-warn {
    background: #fffbeb;
    color: #b45309;
    border-color: #fde68a;
  }
}

.sxk-history__card-meta {
  display: flex;
  gap: 14px;
  font-size: 12.5px;
  color: $text-regular;
  flex-wrap: wrap;
  align-items: center;
}

.sxk-history__card-channel {
  color: $primary-color;
  font-weight: 500;
}

.sxk-history__card-creator {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-weight: 500;

  &-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    flex-shrink: 0;
  }
}

.sxk-history__card-actions {
  display: flex;
  align-items: center;
  gap: 2px;
  padding: 0 12px;
  border-left: 1px solid $border-light;
  flex-shrink: 0;
}

// 反馈 icon 按钮（自绘 SVG 拇指，不再用 emoji）
.sxk-history__icon-btn {
  width: 30px;
  height: 30px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  color: $text-placeholder;
  border-radius: $radius-sm;
  cursor: pointer;
  transition: all 0.15s ease;
  flex-shrink: 0;

  &:hover {
    background: $gray-100;
  }
  &.is-like:hover,
  &.is-like.is-active {
    color: $success-color;
    background: rgba(103, 194, 58, 0.1);
  }
  &.is-dislike:hover,
  &.is-dislike.is-active {
    color: $danger-color;
    background: rgba(245, 108, 108, 0.1);
  }
}
</style>
