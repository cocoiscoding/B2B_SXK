<!--
  神行库 · 生成历史（卡片式列表）
  对齐后端参考版 B2B-SXK-FastApi/frontend 的卡片式历史布局
-->
<template>
  <div class="sxk-history">
    <!-- ========== 顶部欢迎条：与首页风格一致 ========== -->
    <div class="sxk-page-welcome">
      <div class="sxk-page-welcome__left">
        <h2 class="sxk-page-welcome__title">生成历史</h2>
        <p class="sxk-page-welcome__desc">共 <b style="color: #6366f1; font-size: 14px;">{{ total }}</b> 条记录</p>
      </div>
      <div class="sxk-page-welcome__actions">
        <el-button :icon="Refresh" @click="load" :loading="loading">刷新</el-button>
      </div>
    </div>

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

    <!-- ========== 表格列表（替换原卡片列表） ========== -->
    <basic-block>
      <div v-if="loading && list.length === 0" class="sxk-history__loading">
        <el-icon class="rotating"><Loading /></el-icon>
        加载中...
      </div>
      <div v-else-if="!list.length" class="sxk-history__empty">
        <el-empty :description="emptyText" />
      </div>
      <el-table
        v-else
        :data="list"
        class="sxk-history__table"
        :row-class-name="tableRowClass"
        v-loading="loading"
        :highlight-current-row="false"
        @row-click="onView"
        stripe
        border
        style="width: 100%; cursor: pointer;"
      >
        <!-- 产品（关键：去掉小图标） -->
        <el-table-column label="产品" min-width="200" prop="product.name" show-overflow-tooltip>
          <template #default="{ row }">
            <span>{{ row.product?.name || '已删除产品' }}</span>
          </template>
        </el-table-column>

        <!-- 场景 -->
        <el-table-column label="场景" min-width="160" show-overflow-tooltip>
          <template #default="{ row }">
            <el-tag v-if="row.scene_name" type="primary" effect="light" size="small">
              {{ row.scene_name }}
            </el-tag>
            <span v-else class="text-secondary">—</span>
          </template>
        </el-table-column>

        <!-- 渠道 -->
        <el-table-column label="渠道" min-width="180" show-overflow-tooltip>
          <template #default="{ row }">
            <template v-if="splitChannels(row.channel).length">
              <el-tag
                v-for="ch in splitChannels(row.channel)"
                :key="ch"
                size="small"
                effect="plain"
                round
                class="sxk-history__channel-tag"
              >
                {{ ch }}
              </el-tag>
            </template>
            <span v-else class="text-secondary">—</span>
          </template>
        </el-table-column>

        <!-- 创建人 -->
        <el-table-column label="创建人" min-width="110" show-overflow-tooltip>
          <template #default="{ row }">
            <span
              v-if="row.created_by"
              class="sxk-history__cell-creator"
              :style="{ color: memberColor(displayCreator(row)) }"
            >
              <span
                class="sxk-history__cell-creator-dot"
                :style="{ background: memberColor(displayCreator(row)) }"
              />
              {{ displayCreator(row) }}
            </span>
            <span v-else class="text-secondary">—</span>
          </template>
        </el-table-column>

        <!-- 校验状态 -->
        <el-table-column label="校验状态" width="100">
          <template #default="{ row }">
            <el-tag
              :type="row.validated ? 'success' : 'warning'"
              effect="light"
              size="small"
            >
              <span class="sxk-history__status-dot" :class="row.validated ? 'is-pass' : 'is-warn'" />
              {{ row.validated ? '已校验' : '待完善' }}
            </el-tag>
          </template>
        </el-table-column>

        <!-- 反馈 -->
        <el-table-column label="反馈" width="100">
          <template #default="{ row }">
            <div class="sxk-history__cell-feedback" @click.stop>
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
            </div>
          </template>
        </el-table-column>

        <!-- 时间 -->
        <el-table-column label="生成时间" width="160">
          <template #default="{ row }">
            <span class="text-secondary">{{ formatDateTime(row.created_at) }}</span>
          </template>
        </el-table-column>

        <!-- 操作 -->
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <div class="sxk-history__cell-actions" @click.stop>
              <el-button text size="small" type="primary" @click="onView(row)">
                查看
              </el-button>
              <el-dropdown trigger="click" @command="(fmt) => onExport(row, fmt)">
                <el-button text size="small">
                  导出 <el-icon><ArrowDown /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="docx">Word (.docx)</el-dropdown-item>
                    <el-dropdown-item command="markdown">Markdown (.md)</el-dropdown-item>
                    <el-dropdown-item command="txt">纯文本 (.txt)</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
              <el-button text size="small" type="danger" @click="onDelete(row)">
                删除
              </el-button>
            </div>
          </template>
        </el-table-column>

        <!-- 空表格占位 -->
        <template #empty>
          <el-empty :description="emptyText" />
        </template>
      </el-table>

      <!-- ========== 分页 ========== -->
      <el-pagination
        v-model:current-page="pager.page"
        v-model:page-size="pager.size"
        :page-sizes="[10, 20, 50, 100]"
        :total="total"
        :background="true"
        layout="total, sizes, prev, pager, next, jumper"
        class="sxk-history__pager"
        @current-change="load"
        @size-change="load"
      />
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
  Refresh,
  ArrowDown
} from '@element-plus/icons-vue'
import BasicBlock from '@/components/basic-block/main.vue'
import { sxkApi } from '@/mock/sxkApi'
import HistoryDetailModal from './components/history-detail-modal.vue'

const router = useRouter()
const route = useRoute()

// ========== 状态 ==========
const filters = reactive({ keyword: '', scene_code: '', validated: '' })
const list = ref([])
const total = ref(0)                       // 关键：总条数（来自后端）
const loading = ref(false)
const scenes = ref([])
const pager = reactive({ page: 1, size: 10 })  // 关键：分页（默认 10/页）

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
// 关键：原 filteredList 已废弃，搜索/筛选由后端分页接口处理

const emptyText = computed(() => {
  if (filters.keyword || filters.scene_code || filters.validated) {
    return '未找到匹配的历史记录'
  }
  return '暂无生成历史'
})

/**
 * 关键：表格行高亮类名（来自 /generate 跳转时高亮目标行）
 */
const tableRowClass = ({ row }) => {
  if (highlightId.value && highlightId.value === row.generation_id) {
    return 'sxk-history__row-highlight'
  }
  return ''
}

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

// ========== 数据加载（后端分页） ==========
const load = async () => {
  loading.value = true
  try {
    const resp = await sxkApi.listHistory({
      page: pager.page,
      size: pager.size,
      keyword: filters.keyword,
      scene_code: filters.scene_code,
      status: filters.validated === 'true' ? 'success' : (filters.validated === 'false' ? 'pending' : '')
    })
    list.value = resp.data?.items || []
    total.value = resp.data?.total || 0
  } catch (e) {
    list.value = []
    total.value = 0
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
  // 关键：搜索时重置到第 1 页
  pager.page = 1
  load()
}

const reset = () => {
  filters.keyword = ''
  filters.scene_code = ''
  filters.validated = ''
  pager.page = 1
  pager.size = 10
  load()
}

const onView = (row) => {
  detailTargetId.value = row.generation_id
  detailTargetIndex.value = 0
  detailVisible.value = true
}

const onExport = async (row, format = 'docx') => {
  // 真实链路：responseType=blob 直接由浏览器下载
  // Mock 阶段：sxkApi.exportHistory 会本地生成 blob 触发下载
  try {
    await sxkApi.exportHistory(row.generation_id, format)
    const labelMap = { docx: 'Word', markdown: 'Markdown', txt: '纯文本' }
    ElMessage.success(`已开始导出 ${labelMap[format] || format}`)
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

// ========== 页面头部（已迁移到 .sxk-page-welcome，参考 common.scss） ==========
// 关键：删除了旧的 .page-header，使用全局 .sxk-page-welcome 组件

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

// ========== 表格样式（替换原卡片样式） ==========
.sxk-history__table {
  border-radius: $radius-md;
  overflow: hidden;
  transition: $transition-base;

  :deep(.el-table__row) {
    transition: $transition-base;
    cursor: pointer;

    &:hover > td.el-table__cell {
      background: rgba(99, 102, 241, 0.04) !important;
    }
  }

  :deep(.sxk-history__row-highlight > td.el-table__cell) {
    background: rgba(99, 102, 241, 0.08) !important;
    animation: sxk-history-pulse 1.2s ease-in-out 2;
  }
}

@keyframes sxk-history-pulse {
  0%, 100% {
    background: rgba(99, 102, 241, 0.08) !important;
  }
  50% {
    background: rgba(99, 102, 241, 0.16) !important;
  }
}

// 表格内单元格
// 关键：移除了 .sxk-history__cell-product / .sxk-history__cell-icon（去掉产品前小图标）
.sxk-history__channel-tag {
  margin-right: 4px;
  margin-bottom: 2px;
}
.sxk-history__cell-creator {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-weight: 500;
}
.sxk-history__cell-creator-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}
.sxk-history__status-dot {
  display: inline-block;
  width: 5px;
  height: 5px;
  border-radius: 50%;
  margin-right: 4px;
  background: currentColor;
  &.is-pass { background: #10b981; }
  &.is-warn { background: #f59e0b; }
}
.sxk-history__cell-feedback {
  display: inline-flex;
  gap: 2px;
}
.sxk-history__cell-actions {
  display: inline-flex;
  align-items: center;
  gap: 2px;
}

// 反馈 icon 按钮（自绘 SVG 拇指）
.sxk-history__icon-btn {
  width: 28px;
  height: 28px;
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

// 分页
.sxk-history__pager {
  margin-top: $spacing-lg;
  justify-content: flex-end;
}
</style>
