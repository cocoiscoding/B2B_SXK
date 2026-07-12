<!--
  历史详情弹窗
  对齐项目弹窗规范（与 product-edit-modal / template-create-modal 等保持一致）：
    - 自定义头部（图标+标题+副标题+关闭按钮）
    - 可滚动 body
    - 自定义 footer
    - 全局覆盖 el-dialog 默认 padding
    - BEM 风格 class 前缀：hdm-*

  功能：
    - el-descriptions 描述列表（产品/场景/渠道/风格/时间/校验/反馈/创建人）
    - A/B 领先版本 Banner
    - 预览 / 编辑 切换
    - 各版本 Tab：Word 文档式预览 / 编辑表单 / 配图参考
    - 投票 + SEO 分析 + 保存修改
-->
<template>
  <el-dialog
    :model-value="modelValue"
    width="840px"
    top="5vh"
    :show-close="false"
    :close-on-click-modal="false"
    append-to-body
    class="hdm-dialog"
    @update:model-value="(v) => $emit('update:modelValue', v)"
    @open="load"
  >
    <!-- ========== 头部 ========== -->
  <template #header>
    <div class="hdm-head">
      <div class="hdm-head__left">
        <h3 class="hdm-head__title">
          <el-icon class="hdm-head__icon"><Document /></el-icon>
          历史详情
        </h3>
        <p v-if="data" class="hdm-head__sub">
          {{ data.product?.name || '已删除产品' }}
          <span v-if="data.scene_name">· {{ data.scene_name }}</span>
          <!-- <span v-if="data.created_at">· {{ formatDateTime(data.created_at) }}</span> -->
        </p>
      </div>
      <button class="hdm-head__close" @click="$emit('update:modelValue', false)">
        <el-icon :size="20"><Close /></el-icon>
      </button>
    </div>
  </template>

    <!-- ========== 可滚动内容区 ========== -->
    <div class="hdm-body" v-loading="loading">
      <template v-if="!loading && data">
        <!-- 描述列表 -->
        <el-descriptions :column="3" border class="hdm-desc">
          <el-descriptions-item label="产品">
            {{ data.product?.name || '已删除产品' }}
          </el-descriptions-item>
          <el-descriptions-item label="场景">
            {{ data.scene_name || data.scene_code || '—' }}
          </el-descriptions-item>
          <el-descriptions-item label="渠道">
            <el-tag
              v-for="ch in splitChannels(data.channel)"
              :key="ch"
              size="small"
              type="info"
              effect="light"
              class="hdm-channel-tag"
            >
              {{ ch }}
            </el-tag>
            <span v-if="!splitChannels(data.channel).length" class="hdm-muted">未标记</span>
          </el-descriptions-item>
          <el-descriptions-item label="风格">
            {{ data.style || '—' }}
          </el-descriptions-item>
          <el-descriptions-item label="生成时间">
            {{ formatDateTime(data.created_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="校验">
            <span
              class="hdm-status"
              :class="data.validated ? 'is-pass' : 'is-warn'"
            >
              <span class="hdm-status__dot" />
              <span class="hdm-status__text">
                {{ data.validated ? '校验通过' : '待完善' }}
              </span>
            </span>
          </el-descriptions-item>
          <!-- 整体反馈 -->
          <el-descriptions-item label="整体反馈" :span="3">
            <div class="hdm-feedback">
              <span
                class="hdm-status"
                :class="data.feedback === 'like' ? 'is-pass' : data.feedback === 'dislike' ? 'is-fail' : 'is-neutral'"
              >
                <span class="hdm-status__dot" />
                <span class="hdm-status__text">
                  {{
                    data.feedback === 'like'
                      ? '已点赞'
                      : data.feedback === 'dislike'
                        ? '已点踩'
                        : '未标记'
                  }}
                </span>
              </span>
              <el-button
                size="small"
                :type="data.feedback === 'like' ? 'success' : 'default'"
                :plain="data.feedback !== 'like'"
                style="margin-left: 4px"
                @click="onFeedback('like')"
              >
                <span style="font-weight: 600; margin-right: 2px">+1</span>
                <span>赞</span>
              </el-button>
              <el-button
                size="small"
                :type="data.feedback === 'dislike' ? 'danger' : 'default'"
                :plain="data.feedback !== 'dislike'"
                @click="onFeedback('dislike')"
              >
                <span style="font-weight: 600; margin-right: 2px">-1</span>
                <span>踩</span>
              </el-button>
            </div>
          </el-descriptions-item>
          <el-descriptions-item label="创建人">
            <span
              v-if="data.created_by"
              class="hdm-member"
              :style="{ color: memberColor(displayCreator()) }"
            >
              ● {{ displayCreator() }}
            </span>
            <span v-else class="hdm-muted">未标记</span>
          </el-descriptions-item>
        </el-descriptions>

        <!-- A/B 领先版本 Banner -->
        <div
          v-if="leadingVersion(data.versions)"
          class="hdm-leading"
        >
          <svg
            class="hdm-leading__trophy"
            viewBox="0 0 24 24"
            width="20"
            height="20"
            fill="currentColor"
            aria-hidden="true"
          >
            <path d="M19 5h-2V3H7v2H5c-1.1 0-2 .9-2 2v3c0 2.21 1.79 4 4 4v.5c0 1.93 1.57 3.5 3.5 3.5H11v2H7v2h10v-2h-4v-2h.5c1.93 0 3.5-1.57 3.5-3.5V14c2.21 0 4-1.79 4-4V7c0-1.1-.9-2-2-2zM5 10V7h2v4.82C5.84 11.4 5 10.3 5 10zm14 0c0 .3-.84 1.4-2 1.82V7h2v3z" />
          </svg>
          <span class="hdm-leading__title">
            A/B 领先版本：版本 {{ leadingVersion(data.versions).index }}
          </span>
          <span class="hdm-leading__pills">
            <span class="hdm-leading__pill is-like">
              <svg viewBox="0 0 24 24" width="12" height="12" fill="currentColor">
                <path d="M2 21h4V9H2v12zm20-11c0-1.1-.9-2-2-2h-6.31l.95-4.57.03-.32c0-.41-.17-.79-.44-1.06L13.17 1 7.59 6.59C7.22 6.95 7 7.45 7 8v10c0 1.1.9 2 2 2h9c.83 0 1.54-.5 1.84-1.22l3.02-7.05c.09-.23.14-.47.14-.73v-2z" />
              </svg>
              {{ leadingVersion(data.versions).votes?.like || 0 }}
            </span>
            <span class="hdm-leading__pill is-dislike">
              <svg viewBox="0 0 24 24" width="12" height="12" fill="currentColor">
                <path d="M22 3h-4v12h4V3zm-20 11c0 1.1.9 2 2 2h6.31l-.95 4.57-.03.32c0 .41.17.79.44 1.06L10.83 23l5.59-5.59c.36-.36.58-.86.58-1.41V6c0-1.1-.9-2-2-2H5c-.83 0-1.54.5-1.84 1.22L.14 12.27c-.09.23-.14.47-.14.73v2z" />
              </svg>
              {{ leadingVersion(data.versions).votes?.dislike || 0 }}
            </span>
          </span>
        </div>

        <!-- 预览/编辑切换 + 保存修改 -->
        <div class="hdm-bar">
          <span class="hdm-bar__title">
            版本内容（{{ data.versions?.length || 0 }} 个）
          </span>
          <div class="hdm-bar__actions">
            <el-button size="small" @click="editMode = !editMode">
              <el-icon><EditPen v-if="!editMode" /><View v-else /></el-icon>
              {{ editMode ? '预览' : '编辑' }}
            </el-button>
            <el-button
              v-if="editMode"
              size="small"
              type="primary"
              :loading="saving"
              @click="onSave"
            >
              保存修改
            </el-button>
          </div>
        </div>

        <!-- 多版本 Tab -->
        <el-tabs v-model="activeVersionIndex" type="card" class="hdm-tabs">
          <el-tab-pane
            v-for="(v, i) in data.versions"
            :key="v.version_key || v.index"
            :name="String(i)"
          >
            <template #label>
              <span class="hdm-tab-label">
                <span>版本 {{ v.index }}</span>
                <span class="hdm-tab-label__pills">
                  <span class="hdm-tab-label__pill is-like">
                    <svg viewBox="0 0 24 24" width="10" height="10" fill="currentColor">
                      <path d="M2 21h4V9H2v12zm20-11c0-1.1-.9-2-2-2h-6.31l.95-4.57.03-.32c0-.41-.17-.79-.44-1.06L13.17 1 7.59 6.59C7.22 6.95 7 7.45 7 8v10c0 1.1.9 2 2 2h9c.83 0 1.54-.5 1.84-1.22l3.02-7.05c.09-.23.14-.47.14-.73v-2z" />
                    </svg>
                    {{ v.votes?.like || 0 }}
                  </span>
                  <span class="hdm-tab-label__pill is-dislike">
                    <svg viewBox="0 0 24 24" width="10" height="10" fill="currentColor">
                      <path d="M22 3h-4v12h4V3zm-20 11c0 1.1.9 2 2 2h6.31l-.95 4.57-.03.32c0 .41.17.79.44 1.06L10.83 23l5.59-5.59c.36-.36.58-.86.58-1.41V6c0-1.1-.9-2-2-2H5c-.83 0-1.54.5-1.84 1.22L.14 12.27c-.09.23-.14.47-.14.73v2z" />
                    </svg>
                    {{ v.votes?.dislike || 0 }}
                  </span>
                </span>
              </span>
            </template>

            <!-- 编辑模式 -->
            <template v-if="editMode">
              <el-input v-model="v.title" style="margin-bottom: 8px">
                <template #prepend>标题</template>
              </el-input>
              <el-input
                type="textarea"
                :rows="10"
                v-model="v.body"
                class="hdm-edit-body"
              />
              <div v-if="v.images?.length" class="hdm-img-ref-list">
                <div class="hdm-img-ref-list__title">
                  配图（{{ v.images.length }} 张，预览时自动穿插在正文中）：
                </div>
                <span
                  v-for="(img, k) in v.images"
                  :key="k"
                  class="hdm-img-ref"
                >
                  <img :src="img.url" :alt="img.caption" />
                  {{ img.caption || ('配图 ' + (k + 1)) }}
                </span>
              </div>
            </template>

            <!-- 预览模式：Word 文档式 -->
            <template v-else>
              <div class="hdm-doc-page">
                <h1 class="hdm-doc-title">{{ v.title }}</h1>
                <div
                  class="hdm-doc-content markdown-body"
                  v-html="renderArticle(v.body, v.images, v.title)"
                />
              </div>
            </template>

            <!-- 投票胶囊条已移至全局底部 .hdm-vote-bar（fixed） -->
          </el-tab-pane>
        </el-tabs>
      </template>
      <div v-else-if="!loading" class="hdm-empty">
        <el-empty description="暂无数据" />
      </div>
    </div>

    <!-- ========== 底部固定点赞区（当前 tab 版本） ========== -->
    <div
      v-if="!loading && data && data.versions?.length"
      class="hdm-vote-bar"
    >
      <div class="hdm-vote-bar__left">
        <!-- <span class="hdm-vote-bar__label">当前版本（{{ currentVersion?.index }}）反馈：</span> -->
        <button
          class="hdm-vote__btn is-like"
          :class="{ 'is-active': votedDir(currentVersion) === 'like' }"
          @click="onVote(currentVersion, 'like')"
        >
          <span class="hdm-vote__icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" width="14" height="14">
              <path
                d="M2 21h4V9H2v12zm20-11c0-1.1-.9-2-2-2h-6.31l.95-4.57.03-.32c0-.41-.17-.79-.44-1.06L13.17 1 7.59 6.59C7.22 6.95 7 7.45 7 8v10c0 1.1.9 2 2 2h9c.83 0 1.54-.5 1.84-1.22l3.02-7.05c.09-.23.14-.47.14-.73v-2z"
                fill="currentColor"
              />
            </svg>
          </span>
          <span class="hdm-vote__label">赞</span>
          <span class="hdm-vote__num">{{ currentVersion?.votes?.like || 0 }}</span>
        </button>

        <span class="hdm-vote__sep" />
        <button
          class="hdm-vote__btn is-dislike"
          :class="{ 'is-active': votedDir(currentVersion) === 'dislike' }"
          @click="onVote(currentVersion, 'dislike')"
        >
          <span class="hdm-vote__icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" width="14" height="14">
              <path
                d="M22 3h-4v12h4V3zm-20 11c0 1.1.9 2 2 2h6.31l-.95 4.57-.03.32c0 .41.17.79.44 1.06L10.83 23l5.59-5.59c.36-.36.58-.86.58-1.41V6c0-1.1-.9-2-2-2H5c-.83 0-1.54.5-1.84 1.22L.14 12.27c-.09.23-.14.47-.14.73v2z"
                fill="currentColor"
              />
            </svg>
          </span>
          <span class="hdm-vote__label">踩</span>
          <span class="hdm-vote__num">{{ currentVersion?.votes?.dislike || 0 }}</span>
        </button>
      </div>
      <el-button link size="small" class="hdm-vote__seo" @click="onAnalyzeSeo(currentVersion)">
        <el-icon><Search /></el-icon>
        SEO 分析
      </el-button>
    </div>

    <!-- ========== 底部 ========== -->
    <template #footer>
      <div class="hdm-foot">
        <el-button @click="$emit('update:modelValue', false)">关闭</el-button>
        <el-button @click="onExport">导出</el-button>
        <el-button type="danger" :loading="deleting" @click="onDelete">删除</el-button>
        <el-button
          type="primary"
          @click="$emit('edit', data?.generation_id)"
        >
          重新编辑
        </el-button>
      </div>
    </template>

    <!-- SEO 分析弹窗 -->
    <el-dialog v-model="seoVisible" title="SEO 分析" width="560px" append-to-body>
      <div v-if="seoResult" class="hdm-seo">
        <div class="hdm-seo__score">
          <div class="hdm-seo__num" :style="{ color: seoScoreColor }">
            {{ seoResult.score }}
          </div>
          <div class="hdm-seo__tip">SEO 评分（满分 100）</div>
        </div>
        <div v-if="seoResult.keywords?.length" class="hdm-seo__keywords">
          <span class="hdm-seo__keywords-title">关键词：</span>
          <el-tag
            v-for="k in seoResult.keywords"
            :key="k"
            size="small"
            style="margin: 2px"
          >
            {{ k }}
          </el-tag>
        </div>
        <el-divider />
        <div
          v-for="(s, i) in seoResult.suggestions"
          :key="i"
          class="hdm-seo__item"
        >
          <el-tag
            :type="s.level === 'good' ? 'success' : s.level === 'warning' ? 'warning' : 'danger'"
            size="small"
          >
            {{ s.type }}
          </el-tag>
          <span class="hdm-seo__msg">{{ s.message }}</span>
        </div>
        <el-divider />
        <div class="hdm-seo__stats">
          标题 {{ seoResult.stats.title_length }} 字 · 正文
          {{ seoResult.stats.body_length }} 字 · 小标题
          {{ seoResult.stats.headings }} · 平均句长
          {{ seoResult.stats.avg_sentence_length }} 字
        </div>
        <div v-if="seoResult.stats.meta_description" class="hdm-seo__stats">
          建议 Meta：{{ seoResult.stats.meta_description }}
        </div>
      </div>
    </el-dialog>
  </el-dialog>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Close, Document, EditPen, View, Loading, Search } from '@element-plus/icons-vue'
import { sxkApi } from '@/mock/sxkApi'
import { renderArticle as renderArticleUtil } from '@/views/sxk/generate/md'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  generationId: { type: String, default: null },
  versionIndex: { type: Number, default: 0 }
})
const emit = defineEmits(['update:modelValue', 'edit', 'deleted', 'updated'])

// ========== 状态 ==========
const loading = ref(false)
const data = ref(null)
const editMode = ref(false)
const activeVersionIndex = ref('0')
const saving = ref(false)
const deleting = ref(false)

// SEO 弹窗
const seoVisible = ref(false)
const seoResult = ref(null)

// 当前用户（用于 votedDir 判定 + 创建人显示兜底）
const currentUser = ref(null)
try {
  const raw = localStorage.getItem('sxk-access-user') || sessionStorage.getItem('sxk-user')
  if (raw) currentUser.value = JSON.parse(raw)
} catch {
  /* ignore */
}

// 把后端返回的 created_by 规整为「人类可读用户名」
// 后端 history 表 SELECT 不到 created_by，但 orchestrator 会传 user["id"]（"u_xxx"）
// 这里把 user_id 形式（带 u_ 前缀的）回退为当前登录用户名
const isUserId = (s) => typeof s === 'string' && /^u_[a-f0-9]+$/i.test(s)
const displayCreator = (v) => {
  const cb = data.value?.created_by
  if (cb && !isUserId(cb)) return cb
  // user_id 形式或缺失 → 兜底用当前用户名
  return currentUser.value?.username || currentUser.value?.name || '当前用户'
}

// ========== 工具 ==========
const formatDateTime = (iso) => {
  if (!iso) return '—'
  const d = new Date(iso)
  if (isNaN(d.getTime())) return iso
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

const memberColor = (id) => {
  if (!id) return '#bbb'
  let hash = 0
  for (let i = 0; i < id.length; i++) {
    hash = (hash * 31 + id.charCodeAt(i)) & 0xffffffff
  }
  const colors = ['#1A56DB', '#16a34a', '#ea580c', '#9333ea', '#dc2626', '#0891b2', '#ca8a04']
  return colors[Math.abs(hash) % colors.length]
}

const leadingVersion = (versions) => {
  if (!versions || !versions.length) return null
  let best = null
  let bestNet = 0
  for (const v of versions) {
    const net = (v.votes?.like || 0) - (v.votes?.dislike || 0)
    if (net > bestNet) {
      bestNet = net
      best = v
    }
  }
  return best
}

/**
 * 关键：当前激活 tab 的版本（用于底部 fixed 点赞区）
 */
const currentVersion = computed(() => {
  if (!data.value?.versions?.length) return null
  const idx = Number(activeVersionIndex.value || 0)
  return data.value.versions[idx] || data.value.versions[0]
})

const renderArticle = (body, images, title) => {
  return renderArticleUtil(body || '', images || [], title || '')
}

const votedDir = (v) => {
  const id = currentUser.value?.username || currentUser.value?.id
  return (v.voters && id && v.voters[id]) || v._myVote || ''
}

const seoScoreColor = computed(() => {
  const s = seoResult.value?.score ?? 0
  return s >= 80 ? '#67c23a' : s >= 60 ? '#e6a23c' : '#f56c6c'
})

// ========== 数据加载 ==========
const load = async () => {
  if (!props.generationId) return
  loading.value = true
  try {
    const resp = await sxkApi.getGeneration(props.generationId)
    if (resp.code !== 0 || !resp.data) {
      ElMessage.error(resp.msg || '加载历史失败')
      return
    }
    data.value = resp.data
    const lead = leadingVersion(resp.data.versions)
    const leadIdx = lead
      ? resp.data.versions.findIndex((v) => v === lead)
      : 0
    activeVersionIndex.value = String(leadIdx >= 0 ? leadIdx : 0)
    editMode.value = false
  } catch (e) {
    ElMessage.error('加载历史失败：' + (e?.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

watch(
  () => [props.generationId, props.modelValue],
  ([id, visible]) => {
    if (id && visible) load()
  }
)

// ========== 操作 ==========
const onExport = async () => {
  if (!data.value?.generation_id) return
  try {
    await sxkApi.exportDocx(data.value.generation_id)
    ElMessage.success('已开始导出')
  } catch (e) {
    ElMessage.error('导出失败：' + (e?.message || '未知错误'))
  }
}

const onDelete = () => {
  if (!data.value) return
  ElMessageBox.confirm('确认删除该历史记录？删除后不可恢复。', '删除历史', {
    type: 'warning',
    confirmButtonText: '确认删除',
    cancelButtonText: '取消'
  })
    .then(async () => {
      deleting.value = true
      try {
        const resp = await sxkApi.removeHistory(data.value.generation_id)
        if (resp.code !== 0) {
          ElMessage.error(resp.msg || '删除失败')
          return
        }
        ElMessage.success('已删除')
        emit('deleted')
      } catch (e) {
        ElMessage.error('删除失败：' + (e?.message || '未知错误'))
      } finally {
        deleting.value = false
      }
    })
    .catch(() => {})
}

const onSave = async () => {
  if (!data.value) return
  saving.value = true
  try {
    const versions = (data.value.versions || []).map((v) => ({
      index: v.index,
      version_key: v.version_key,
      title: v.title,
      body: v.body,
      tags: v.tags,
      images: v.images,
      votes: v.votes,
      voters: v.voters
    }))
    const resp = await sxkApi.updateHistory(data.value.generation_id, { versions })
    if (resp.code !== 0) {
      ElMessage.error(resp.msg || '保存失败')
      return
    }
    data.value = resp.data
    emit('updated', resp.data)
    ElMessage.success('已保存修改')
    editMode.value = false
  } catch (e) {
    ElMessage.error('保存失败：' + (e?.message || '未知错误'))
  } finally {
    saving.value = false
  }
}

const onFeedback = async (fb) => {
  if (!data.value) return
  const next = data.value.feedback === fb ? '' : fb
  try {
    const resp = await sxkApi.setHistoryFeedback(data.value.generation_id, next)
    if (resp.code !== 0) {
      ElMessage.error(resp.msg || '操作失败')
      return
    }
    Object.assign(data.value, resp.data)
    ElMessage.success(next ? (next === 'like' ? '已点赞' : '已踩') : '已取消标记')
  } catch (e) {
    ElMessage.error('操作失败：' + (e?.message || '未知错误'))
  }
}

const onVote = async (v, dir) => {
  if (!data.value) return
  const cur = votedDir(v)
  const next = cur === dir ? '' : dir
  v.votes = v.votes || { like: 0, dislike: 0 }
  v.voters = v.voters || {}
  if (cur) v.votes[cur] = Math.max(0, v.votes[cur] - 1)
  if (next) v.votes[next] = (v.votes[next] || 0) + 1
  v._myVote = next
  try {
    const resp = await sxkApi.castVote(
      data.value.generation_id,
      v.index || v.version_key,
      next
    )
    if (resp.code !== 0) {
      if (cur) v.votes[cur] = (v.votes[cur] || 0) + 1
      if (next) v.votes[next] = Math.max(0, v.votes[next] - 1)
      v._myVote = cur
      ElMessage.error(resp.msg || '投票失败')
    }
  } catch (e) {
    if (cur) v.votes[cur] = (v.votes[cur] || 0) + 1
    if (next) v.votes[next] = Math.max(0, v.votes[next] - 1)
    v._myVote = cur
    ElMessage.error('投票失败：' + (e?.message || '未知错误'))
  }
}

const onAnalyzeSeo = async (v) => {
  try {
    const resp = await sxkApi.analyzeSeo({ title: v.title, body: v.body })
    if (resp.code !== 0) {
      ElMessage.error(resp.msg || 'SEO 分析失败')
      return
    }
    seoResult.value = resp.data
    seoVisible.value = true
  } catch (e) {
    ElMessage.error('SEO 分析失败：' + (e?.message || '未知错误'))
  }
}
</script>

<style lang="scss">
// ============================================================
// 全局覆盖：三段式固定布局（头部 / 中间滚动 / 底部点赞 + 底部按钮）
// ============================================================
.hdm-dialog {
  // 关键：禁用全局 .el-dialog__body 的 overflow-y: auto
  //       因为现在 .hdm-body 自己负责滚动
  .el-dialog__header {
    padding: 0;            // 让 .hdm-head 自带 padding
  }
  .el-dialog__body {
    // 关键：外层 body 不滚动（由 .hdm-body 自管）
    padding: 0;
    flex: 1;               // 关键：占满 head 与 footer 之间的空间
    min-height: 0;         // 允许收缩
    overflow: hidden;      // 关键：禁用外层滚动
    display: flex;         // 关键：让 .hdm-body 能 flex: 1 撑满
    flex-direction: column;
  }
  .el-dialog__footer {
    // 关键：恢复 padding，让 .hdm-foot 与弹窗底边有间距
    padding: 12px 24px 16px;
    border-top: 1px solid $border-light;
  }
}
</style>

<style lang="scss" scoped>
// ============================================================
// 历史详情弹窗 —— 样式与项目其他弹窗（pe-*/tcm-*）完全统一
// ============================================================

// ========== 头部（与 product-edit-modal 一致）==========
.hdm-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: $spacing-lg $spacing-lg $spacing-md;
  border-bottom: 1px solid $border-light;

  &__left {
    min-width: 0;
    flex: 1;
  }

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
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
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

// ========== 可滚动内容区（关键：自管滚动）==========
// 关键：现在 .hdm-body 自己负责滚动，由 .el-dialog__body 提供的 flex 父级计算高度
.hdm-body {
  padding: $spacing-lg;
  display: flex;
  flex-direction: column;
  gap: $spacing-md;
  // 关键：自管滚动（关键的三段式：head 固定 / body 滚 / vote-bar 固定）
  flex: 1 1 auto;           // 关键：占满 head / vote-bar 之间的空间
  min-height: 0;            // 关键：允许 flex 子项收缩（否则内容超出时不会滚动）
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
}

.hdm-empty {
  padding: $spacing-2xl 0;
}

// ========== 描述列表 ==========
.hdm-desc {
  margin-bottom: 0;
}

.hdm-muted {
  color: $text-placeholder;
  font-size: 13px;
}

.hdm-member {
  font-weight: 500;
  font-size: 13px;
}

// ========== 整体反馈 ==========
.hdm-feedback {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  min-height: 24px;
}

// ========== 状态点 + 文字胶囊（统一用于渠道 / 校验 / 反馈 / 创建人）==========
.hdm-status {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 2px 10px 2px 8px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 500;
  line-height: 1.6;
  background: $gray-100;
  color: $text-regular;
  border: 1px solid transparent;

  &__dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: currentColor;
    flex-shrink: 0;
  }
  &__text {
    line-height: 1;
  }

  // 校验通过：绿
  &.is-pass {
    background: #ecfdf5;
    color: #047857;
    border-color: #a7f3d0;
  }
  // 校验不通过：橙
  &.is-warn {
    background: #fffbeb;
    color: #b45309;
    border-color: #fde68a;
  }
  // 已点踩：红（语义最强）
  &.is-fail {
    background: #fef2f2;
    color: #b91c1c;
    border-color: #fecaca;
  }
  // 中性 / 未标记：灰
  &.is-neutral {
    background: $gray-100;
    color: $text-regular;
    border-color: $border-light;
  }
  // 蓝色（信息）：渠道用
  &.is-info {
    background: $primary-color-light;
    color: $primary-color;
    border-color: rgba(26, 86, 219, 0.2);
  }
}

// ========== 渠道标签（蓝、信息色）==========
.hdm-channel-tag {
  margin: 2px;
  font-weight: 500;
  // 略缩小圆角与字体以更紧凑
  padding: 1px 10px;
}

// ========== A/B 领先版本 Banner（自绘 SVG + 胶囊数字）==========
.hdm-leading {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  border-radius: $radius-md;
  background: linear-gradient(90deg, #ecfdf5 0%, #f0fdf4 100%);
  border: 1px solid #a7f3d0;
  color: #065f46;

  &__trophy {
    color: #ca8a04;
    flex-shrink: 0;
  }
  &__title {
    font-weight: 600;
    font-size: 14px;
    flex: 1;
  }
  &__pills {
    display: flex;
    align-items: center;
    gap: 6px;
  }
  &__pill {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 3px 8px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 600;
    line-height: 1;
    svg { display: block; }

    &.is-like {
      background: #d1fae5;
      color: #047857;
    }
    &.is-dislike {
      background: #fee2e2;
      color: #b91c1c;
    }
  }
}

// ========== 工具栏（预览/编辑切换）==========
.hdm-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 4px;
  border-bottom: 1px solid $border-light;

  &__title {
    font-size: 14px;
    font-weight: 600;
    color: $text-primary;
  }

  &__actions {
    display: flex;
    gap: 8px;
  }
}

// ========== 版本 Tab ==========
.hdm-tabs {
  :deep(.el-tabs__header) {
    margin-bottom: 0;
  }
  :deep(.el-tabs__content) {
    padding: 16px 0 0;
  }

  &__label-meta {
    display: none; // 已替换为 hdm-tab-label 胶囊
  }
}

// ========== Tab label 内嵌胶囊（自绘 SVG + 数字气泡）==========
.hdm-tab-label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  &__pills {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    margin-left: 4px;
  }
  &__pill {
    display: inline-flex;
    align-items: center;
    gap: 2px;
    padding: 1px 6px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 600;
    line-height: 1.3;
    svg { display: block; }

    &.is-like {
      background: rgba(103, 194, 58, 0.15);
      color: $success-color;
    }
    &.is-dislike {
      background: rgba(245, 108, 108, 0.15);
      color: $danger-color;
    }
  }
}

// ========== 编辑模式 ==========
.hdm-edit-body {
  :deep(.el-textarea__inner) {
    font-size: 13px;
    line-height: 1.85;
    font-family: inherit;
  }
}

.hdm-img-ref-list {
  font-size: 12px;
  color: $text-regular;
  margin: 8px 0 0;
  padding: 8px 10px;
  background: $bg-hover;
  border: 1px solid $border-light;
  border-radius: $radius-sm;

  &__title {
    margin-bottom: 4px;
  }
}
.hdm-img-ref {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  margin: 4px 10px 4px 0;
  img {
    width: 30px;
    height: 30px;
    object-fit: cover;
    border-radius: 4px;
    border: 1px solid $border-base;
  }
}

// ========== 投票 + SEO 工具栏（自绘胶囊形投票条）==========
.hdm-tools {
  display: none; // 已替换为 hdm-vote 自绘组件
}

.hdm-vote {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  margin-top: 12px;
  background: $bg-hover;
  border: 1px solid $border-light;
  border-radius: $radius-md;
  flex-wrap: wrap;

  &__btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 12px;
    border: 1px solid $border-base;
    background: $bg-card;
    color: $text-regular;
    border-radius: 999px;
    cursor: pointer;
    font-size: 13px;
    line-height: 1;
    transition: all 0.18s ease;
    user-select: none;

    &:hover {
      border-color: $primary-color-light;
      color: $primary-color;
    }

    &.is-like {
      &.is-active {
        background: $success-color;
        border-color: $success-color;
        color: #fff;
        box-shadow: 0 2px 6px rgba(103, 194, 58, 0.3);
      }
      .hdm-vote__icon { color: $success-color; }
      &.is-active .hdm-vote__icon { color: #fff; }
    }

    &.is-dislike {
      &.is-active {
        background: $danger-color;
        border-color: $danger-color;
        color: #fff;
        box-shadow: 0 2px 6px rgba(245, 108, 108, 0.3);
      }
      .hdm-vote__icon { color: $danger-color; }
      &.is-active .hdm-vote__icon { color: #fff; }
    }
  }
  &__icon {
    display: inline-flex;
    align-items: center;
    svg { display: block; }
  }
  &__label {
    font-weight: 500;
  }
  &__num {
    font-weight: 600;
    font-variant-numeric: tabular-nums;
    min-width: 16px;
    text-align: center;
  }
  &__sep {
    color: $border-base;
    font-size: 12px;
    user-select: none;
  }
  &__divider {
    flex: 0 0 1px;
    height: 18px;
    background: $border-light;
    margin: 0 4px;
  }
  &__seo {
    margin-left: auto;
  }
}

// ========== Word 文档式预览 ==========
.hdm-doc-page {
  background: $bg-card;
  max-width: 760px;
  margin: 0 auto;
  padding: 40px 48px;
  box-shadow: 0 2px 14px rgba(0, 0, 0, 0.08);
  border: 1px solid $border-light;
  border-radius: 2px;
  font-family: Georgia, "Times New Roman", "宋体", SimSun, serif;
  color: #1a1a1a;
  line-height: 1.85;
}
.hdm-doc-title {
  font-size: 25px;
  font-weight: 700;
  text-align: center;
  margin: 0 0 26px;
  line-height: 1.4;
  color: #1a1a1a;
}
.hdm-doc-content {
  font-size: 15.5px;
  :deep(h1) { font-size: 20px; margin: 22px 0 10px; font-weight: 700; }
  :deep(h2) { font-size: 18px; margin: 18px 0 8px; font-weight: 700; }
  :deep(h3) { font-size: 16px; margin: 14px 0 6px; font-weight: 700; }
  :deep(p) { margin: 10px 0; }
  :deep(ul), :deep(ol) { padding-left: 22px; margin: 8px 0; }
  :deep(blockquote) {
    border-left: 3px solid #bbb;
    color: #555;
    margin: 10px 0;
    padding: 4px 14px;
    background: #fafafa;
  }
  :deep(table) {
    border-collapse: collapse;
    width: 100%;
    margin: 10px 0;
    th, td {
      border: 1px solid #ccc;
      padding: 6px 10px;
      text-align: left;
    }
    th {
      background: #f5f5f5;
      font-weight: 700;
    }
  }
  :deep(.article-fig) {
    margin: 22px 0;
    text-align: center;
    img {
      max-width: 100%;
      max-height: 440px;
      object-fit: contain;
      border-radius: 4px;
      border: 1px solid $border-light;
      display: block;
      margin: 0 auto;
    }
    figcaption {
      font-size: 12.5px;
      color: #666;
      margin-top: 6px;
    }
  }
}

// ========== 底部固定点赞区（与 footer 上下相邻） ==========
.hdm-vote-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: $spacing-md;
  padding: 12px $spacing-lg;
  background: $bg-hover;
  border-top: 1px solid $border-light;
  flex-shrink: 0;        // 关键：作为 body 内的最后一个 flex item，保持 fixed 效果
  // 关键：自管边界，铺满 .el-dialog__body 宽度
  margin: 0 (-$spacing-lg);  // 抵消 .hdm-body 的 padding，让 bar 贴边铺满

  &__left {
    display: flex;
    align-items: center;
    gap: 12px;
    flex: 1;
    min-width: 0;
  }

  &__label {
    font-size: 12px;
    color: $text-secondary;
    font-weight: 500;
  }
}

// ========== 底部 ==========
.hdm-foot {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: $spacing-sm;
  // 关键：水平 padding 由 .el-dialog__footer 提供，此处不重复
  // 上下 padding 也不需要（由 .el-dialog__footer 提供）
  padding: 0;
}

// ========== SEO 弹窗 ==========
.hdm-seo {
  text-align: center;
  &__score { margin-bottom: $spacing-md; }
  &__num {
    font-size: 48px;
    font-weight: 700;
    line-height: 1;
  }
  &__tip {
    color: $text-placeholder;
    font-size: $font-size-sm;
    margin-top: 4px;
  }
  &__keywords {
    margin-bottom: 12px;
    text-align: left;
    &-title {
      font-size: 13px;
      color: $text-regular;
    }
  }
  &__item {
    padding: 8px 0;
    display: flex;
    align-items: flex-start;
    gap: 6px;
    text-align: left;
  }
  &__msg {
    margin-left: 8px;
    font-size: $font-size-sm;
    line-height: 1.6;
    text-align: left;
  }
  &__stats {
    font-size: $font-size-xs;
    color: $text-placeholder;
    text-align: left;
  }
}
</style>
