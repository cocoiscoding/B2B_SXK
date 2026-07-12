<!--
  神行库 · 首页（Dashboard）
  严格对齐原型 SXK.html page-dashboard：
    - 欢迎区（无卡片，h1 text-2xl font-bold text-gray-900 + 立即生成按钮）
    - 4 张统计卡片 grid（竖排：图标在上，标签/数值/副标签在下）
    - 常用模板 h3 + grid 3 列（竖排卡片：图标/标题/描述/标签）
    - 最近生成 h3 + 横向列表项（图标 + 标题副信息 + 状态标签）
  数据源：src/mock/sxkApi.js（后端就绪后无需改页面代码，sxkApi 切到 request() 即可）
-->
<template>
  <div class="sxk-dashboard">
    <!-- ========== 欢迎区（原型：无卡片背景，直接 section 内 flex justify-between） ========== -->
    <div class="welcome">
      <div class="welcome-text">
        <h2 class="welcome-title">欢迎回来，{{ welcomeName }}</h2>
        <p class="welcome-sub">今天是 {{ todayText }}，准备好创造精彩内容了吗？</p>
      </div>
      <!-- <el-button type="primary" size="large" class="welcome-btn" @click="goGenerate">
        <el-icon class="welcome-btn-icon"><MagicStick /></el-icon>
        <span>立即生成</span>
      </el-button> -->
    </div>

    <!-- ========== 任务进度条（US013：生成中任务，原型无此项，为业务需求保留） ========== -->
    <div v-if="stats.running_tasks > 0" class="progress-bar">
      <div class="progress-info">
        <el-icon class="rotating"><Loading /></el-icon>
        <span>当前有 {{ stats.running_tasks }} 个生成任务进行中…</span>
      </div>
      <el-button type="primary" link @click="goGenerate">查看进度</el-button>
    </div>

    <!-- ========== 4 张统计卡片（原型：grid lg:grid-cols-4 gap-6，竖排） ========== -->
    <el-row :gutter="24" class="stat-row">
      <el-col :xs="24" :sm="12" :md="6" v-for="card in statCards" :key="card.label">
        <div class="stat-card">
          <!-- 图标区（原型：w-12 h-12 bg-{color}-50 rounded-lg text-{color}-600） -->
          <div class="stat-icon" :style="{ color: card.color, backgroundColor: card.bg }">
            <el-icon><component :is="card.icon" /></el-icon>
          </div>
          <div class="stat-label">{{ card.label }}</div>
          <div class="stat-value">
            {{ card.value }}<span v-if="card.unit" class="stat-unit">{{ card.unit }}</span>
          </div>
          <div class="stat-sub">{{ card.sub }}</div>
        </div>
      </el-col>
    </el-row>

    <!-- ========== 常用场景模板（按生成历史使用次数聚合 top 3） ==========
         关键：首屏显示骨架屏（无 commonTemplates 兜底），load 完成后才显示真实数据 -->
    <div class="section-block">
      <h3 class="section-title">营销场景</h3>
      <!-- 加载中：骨架屏（避免看到 commonTemplates 旧数据） -->
      <el-row :gutter="24" v-if="!dataLoaded">
        <el-col :xs="24" :sm="12" :lg="8" v-for="i in 3" :key="`skeleton-${i}`">
          <div class="tpl-card tpl-card--skeleton">
            <div class="tpl-icon tpl-icon--skeleton"></div>
            <div class="tpl-name tpl-name--skeleton"></div>
            <div class="tpl-desc tpl-desc--skeleton"></div>
            <div class="tpl-tags">
              <span class="tpl-tag tpl-tag--skeleton"></span>
            </div>
          </div>
        </el-col>
      </el-row>
      <!-- 加载完成：显示真实聚合数据 -->
      <el-row :gutter="24" v-else-if="topScenesByUsage.length > 0">
        <el-col :xs="24" :sm="12" :lg="8" v-for="tpl in topScenesByUsage" :key="tpl.scene_code">
          <div class="tpl-card" @click="useCommonTemplate(tpl)">
            <!-- 图标（原型：w-12 h-12 bg-{color}-50 rounded-lg mb-4） -->
            <div class="tpl-icon" :style="{ color: tpl.color, backgroundColor: tpl.bg }">
              <el-icon><component :is="tpl.icon" /></el-icon>
            </div>
            <div class="tpl-name">{{ tpl.name }}</div>
            <div class="tpl-desc">
              <span v-if="tpl.use_count > 0">已使用 {{ tpl.use_count }} 次 · </span>
              {{ tpl.desc }}
            </div>
            <!-- 标签（原型：px-3 py-1 text-xs rounded-full） -->
            <div class="tpl-tags">
              <span
                v-for="tag in tpl.tags"
                :key="tag.text"
                class="tpl-tag"
                :style="tag.style"
              >{{ tag.text }}</span>
            </div>
          </div>
        </el-col>
      </el-row>
      <div v-else class="empty-tip">还没有常用场景，开始第一次生成吧</div>
    </div>

    <!-- ========== 最近生成（原型：h3 + space-y-4 横向列表项） ========== -->
    <div class="section-block">
      <h3 class="section-title">最近生成</h3>
      <div v-if="recentList.length === 0" class="empty-tip">暂无生成记录</div>
      <div v-else class="recent-list">
        <div
          v-for="item in recentList"
          :key="item.generation_id"
          class="recent-item"
          @click="goHistoryDetail(item)"
        >
          <!-- 图标（原型：w-12 h-12 bg-{color}-50 text-{color}-600 rounded-lg） -->
          <div class="recent-icon" :style="recentIconStyle(item)">
            <el-icon><component :is="recentIconComp(item)" /></el-icon>
          </div>
          <div class="recent-info">
            <div class="recent-title">{{ item.product.name }} · {{ item.template.name }}</div>
            <div class="recent-time">{{ item.template.name }} · {{ relativeTime(item.created_at) }}</div>
          </div>
          <el-tag
            :type="item.status === 'success' ? 'success' : 'warning'"
            size="small"
            effect="light"
            round
          >
            {{ statusText(item.status) }}
          </el-tag>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  MagicStick,
  Goods,
  Money,
  Timer,
  Document,
  Share,
  Loading,
  Calendar,
  Files
} from '@element-plus/icons-vue'
import sxkApi from '@/mock/sxkApi'

// ========== 响应式数据 ==========
const router = useRouter()
// 欢迎区用户名（来自 mock 用户；如已登录展示用户 store 数据）
const welcomeName = ref('营销专家')
const todayText = computed(() => {
  const d = new Date()
  return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日`
})

const stats = ref({
  product_count: 0,
  monthly_generation_count: 0,
  avg_score: 0,
  avg_duration_ms: 0,
  running_tasks: 0
})

const recentList = ref([])

// ========== 4 张统计卡片（严格对齐原型 SXK.html） ==========
// 配色：blue-50/blue-600、green-50/green-600、orange-50/orange-600、indigo-50/indigo-600
// 结构：图标(上) + 标签(sm gray-500) + 数值(3xl bold gray-900) + 副标签(xs gray-400)
const statCards = computed(() => [
  {
    label: '产品知识库',
    value: stats.value.product_count,
    sub: '已录入产品',
    icon: Goods,
    color: '#2563eb',                          // Tailwind blue-600
    bg: '#eff6ff'                              // Tailwind blue-50
  },
  {
    label: '本月生成',
    value: stats.value.monthly_generation_count,
    sub: '营销内容',
    icon: Document,
    color: '#16a34a',                          // Tailwind green-600
    bg: '#f0fdf4'                              // Tailwind green-50
  },
  // {
  //   label: '平均评分',
  //   value: stats.value.avg_score || '—',
  //   unit: stats.value.avg_score ? '分' : '',
  //   sub: '内容质量',
  //   icon: Money,
  //   color: '#ea580c',                          // Tailwind orange-600
  //   bg: '#fff7ed'                              // Tailwind orange-50
  // },
  {
    label: '平均耗时',
    value: stats.value.avg_duration_ms ? (stats.value.avg_duration_ms / 1000).toFixed(0) : '—',
    unit: stats.value.avg_duration_ms ? '秒' : '',
    sub: '生成速度',
    icon: Timer,
    color: '#4f46e5',                          // Tailwind indigo-600
    bg: '#eef2ff'                              // Tailwind indigo-50
  }
])

// ========== 场景元信息映射（用于最近生成列表项的图标/配色） ==========
// 对齐原型：产品→blue、竞品→orange、渠道→green
// 同时支持 mock 格式 (product_intro/competitor/channel_adapt) 和后端格式 (S001-S006)
const SCENE_META = {
  // mock 格式
  product_intro: { icon: Document, color: '#2563eb', bg: '#eff6ff' },
  competitor: { icon: Money, color: '#ea580c', bg: '#fff7ed' },
  channel_adapt: { icon: Share, color: '#16a34a', bg: '#f0fdf4' },
  email: { icon: Document, color: '#9333ea', bg: '#faf5ff' },
  event: { icon: Calendar, color: '#dc2626', bg: '#fee2e2' },
  other: { icon: Files, color: '#6b7280', bg: '#f3f4f6' },
  // 后端预置场景 (S001-S006 对应 B2B-SXK-FastApi/app/seed_data.py SEED_SCENARIOS)
  S001: { icon: Document, color: '#2563eb', bg: '#eff6ff' },  // 线下展会物料
  S002: { icon: Document, color: '#2563eb', bg: '#eff6ff' },  // 产品介绍文案
  S003: { icon: Money, color: '#ea580c', bg: '#fff7ed' },     // 竞品对比分析报告
  S004: { icon: Document, color: '#16a34a', bg: '#f0fdf4' },  // 客户案例包装
  S005: { icon: Share, color: '#dc2626', bg: '#fee2e2' },     // 演讲 PPT 大纲
  S006: { icon: Share, color: '#9333ea', bg: '#faf5ff' }      // 社交媒体帖子
}
const getSceneMeta = (sceneCode) => SCENE_META[sceneCode] || SCENE_META.product_intro

const recentIconComp = (item) => getSceneMeta(item.template?.scene_code).icon
const recentIconStyle = (item) => {
  const m = getSceneMeta(item.template?.scene_code)
  return { color: m.color, backgroundColor: m.bg }
}

// ========== 常用模板（对齐原型 grid 3 列竖排卡片） ==========
// 配色对齐原型：产品介绍 blue-600、竞品对比 orange-600、多渠道 green-600
const commonTemplates = [
  {
    template_id: 't_intro_professional',
    name: '产品介绍文案',
    desc: '快速生成官网首页banner、产品介绍等营销文案，支持多种风格',
    icon: Document,
    color: '#2563eb',                          // blue-600
    bg: '#eff6ff',                             // blue-50
    tags: [
      { text: '官网', style: { color: '#2563eb', backgroundColor: '#eff6ff' } },
      { text: '营销', style: { color: '#6b7280', backgroundColor: '#f3f4f6' } },
      { text: '文案', style: { color: '#6b7280', backgroundColor: '#f3f4f6' } }
    ],
    scene_code: 'product_intro'
  },
  {
    template_id: 't_competitor_objective',
    name: '竞品对比报告',
    desc: '自动生成结构化竞品对比报告，包含功能对比、差异化卖点、话术建议',
    icon: Money,
    color: '#ea580c',                          // orange-600
    bg: '#fff7ed',                             // orange-50
    tags: [
      { text: '竞品', style: { color: '#ea580c', backgroundColor: '#fff7ed' } },
      { text: '分析', style: { color: '#6b7280', backgroundColor: '#f3f4f6' } },
      { text: '报告', style: { color: '#6b7280', backgroundColor: '#f3f4f6' } }
    ],
    scene_code: 'competitor'
  },
  {
    template_id: 't_channel_adapt',
    name: '多渠道内容适配',
    desc: '一键将内容适配到微信公众号、LinkedIn、内部培训PPT等多个渠道',
    icon: Share,
    color: '#16a34a',                          // green-600
    bg: '#f0fdf4',                             // green-50
    tags: [
      { text: '多渠道', style: { color: '#16a34a', backgroundColor: '#f0fdf4' } },
      { text: '适配', style: { color: '#6b7280', backgroundColor: '#f3f4f6' } },
      { text: '分发', style: { color: '#6b7280', backgroundColor: '#f3f4f6' } }
    ],
    scene_code: 'channel_adapt'
  }
]

// ========== 工具 ==========
const relativeTime = (iso) => {
  const d = new Date(iso)
  const diff = Date.now() - d.getTime()
  const min = Math.floor(diff / 60000)
  if (min < 1) return '刚刚'
  if (min < 60) return `${min}分钟前`
  const hr = Math.floor(min / 60)
  if (hr < 24) return `${hr}小时前`
  const day = Math.floor(hr / 24)
  if (day < 30) return `${day}天前`
  return d.toLocaleDateString('zh-CN')
}

const statusText = (s) =>
  ({
    success: '已完成',
    running: '生成中',
    failed: '失败',
    cancelled: '已取消'
  })[s] || s

// ========== 跳转方法（与 router name 解耦，靠 path 防重构破坏） ==========
const goGenerate = () => router.push('/generate/index')

// 点击"最近生成"某项 → 跳转到"生成历史"页面并定位到对应行（携带 generation_id）
const goHistoryDetail = (item) => {
  router.push({ path: '/history/index', query: { gid: item.generation_id } })
}

const useCommonTemplate = (tpl) => {
  // 关键：跳转到"场景模板管理"，并通过 query 携带 scene_code，
  //       让目标页面自动打开该场景的详情弹窗（而非仅停留在列表）
  router.push({
    path: '/templates/index',
    query: { openDetail: tpl.scene_code }
  })
}

// ========== 常用场景模板：按生成历史使用次数聚合 top 3 ==========
// 关键：首屏显示骨架屏，load 完成后聚合真实数据
// 降级：history 加载失败 / 数据不足 3 条 → 使用 commonTemplates 补齐
const dataLoaded = ref(false)             // 数据是否已加载（控制骨架屏切换）
const recentListForStats = ref([])        // 仅用于聚合 scene_code，不渲染到 UI
const sceneCodeToName = ref({})           // 来自 getTemplateMeta 的 scene_code → 名称 映射

/**
 * 聚合规则：
 *   1. 按 scene_code 分组
 *   2. 每组 count = history 中该 scene_code 出现的次数
 *   3. 按 count 降序
 *   4. 取前 3
 *   5. 不足 3 条时用 commonTemplates 补齐
 */
const topScenesByUsage = computed(() => {
  // 聚合 history 中 scene_code 出现次数
  const counts = new Map()
  for (const item of (recentListForStats.value || [])) {
    const code = item.scene_code
    if (!code) continue
    counts.set(code, (counts.get(code) || 0) + 1)
  }

  // 按次数降序，取前 3
  const sorted = [...counts.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3)

  // 转为展示卡片结构
  const aggregated = sorted.map(([code, count]) => {
    const meta = getSceneMeta(code)
    const name = sceneCodeToName.value[code] || (code)  // 降级显示 code
    // tags 优先使用常见标签，否则空
    const tag = (() => {
      if (code === 'product_intro' || code === 'S001' || code === 'S002') {
        return { text: '文案', style: { color: '#6b7280', backgroundColor: '#f3f4f6' } }
      }
      if (code === 'competitor' || code === 'S003') {
        return { text: '分析', style: { color: '#6b7280', backgroundColor: '#f3f4f6' } }
      }
      if (code === 'channel_adapt' || code === 'S005' || code === 'S006') {
        return { text: '渠道', style: { color: '#6b7280', backgroundColor: '#f3f4f6' } }
      }
      if (code === 'email') {
        return { text: '邮件', style: { color: '#9333ea', backgroundColor: '#faf5ff' } }
      }
      if (code === 'event' || code === 'S001') {
        return { text: '活动', style: { color: '#dc2626', backgroundColor: '#fee2e2' } }
      }
      return { text: '模板', style: { color: '#6b7280', backgroundColor: '#f3f4f6' } }
    })()
    return {
      scene_code: code,
      name,
      use_count: count,
      desc: '基于真实使用历史推荐',
      icon: meta.icon,
      color: meta.color,
      bg: meta.bg,
      tags: [tag]
    }
  })

  // 不足 3 条时用 commonTemplates 补齐（仅作为推荐项，use_count=0）
  if (aggregated.length < 3) {
    const existingCodes = new Set(aggregated.map((s) => s.scene_code))
    for (const tpl of commonTemplates) {
      if (aggregated.length >= 3) break
      if (existingCodes.has(tpl.scene_code)) continue
      aggregated.push({
        ...tpl,
        use_count: 0,
        desc: tpl.desc + '（推荐）'
      })
    }
  }
  return aggregated
})

// ========== 数据加载 ==========
const load = async () => {
  try {
    // 并行加载：首页统计 + 最近 3 条 + 当前用户 + 全量 history(用于聚合) + 场景元数据
    const [statRes, recentRes, userRes, historyRes, metaRes] = await Promise.allSettled([
      sxkApi.getDashboardStats(),
      sxkApi.getRecentGenerations(3),
      sxkApi.getCurrentUser(),
      // 关键：取尽可能多的 history 用于聚合常用场景（size 100 覆盖常用场景）
      sxkApi.listHistory({ page: 1, size: 100 }),
      sxkApi.getTemplateMeta()
    ])
    if (statRes.status === 'fulfilled' && statRes.value?.data) stats.value = statRes.value.data
    if (recentRes.status === 'fulfilled' && recentRes.value?.data) recentList.value = recentRes.value.data.items || []
    if (userRes.status === 'fulfilled' && userRes.value?.data) welcomeName.value = userRes.value.data.username || '营销专家'
    // 聚合：scene_code 使用次数
    if (historyRes.status === 'fulfilled' && historyRes.value?.data) {
      const items = historyRes.value.data.items || historyRes.value.data || []
      recentListForStats.value = Array.isArray(items) ? items : []
      // ========== 关键：前端兜底计算"平均耗时" ==========
      // 场景：后端 getDashboardStats 可能没提供 avg_duration_ms（兼容老接口）
      //       或提供的值为 0/无效，此时前端用 history.agent_trace 自行计算
      // 数据源：每条 history.agent_trace（JSON 数组，元素含 duration_ms）
      if (!stats.value.avg_duration_ms) {
        const durations = []
        for (const h of recentListForStats.value) {
          const trace = h && h.agent_trace
          if (!Array.isArray(trace) || trace.length === 0) continue
          const total = trace.reduce((sum, step) => {
            const d = step && step.duration_ms
            return sum + (typeof d === 'number' && d > 0 ? d : 0)
          }, 0)
          if (total > 0) durations.push(total)
        }
        if (durations.length > 0) {
          stats.value = {
            ...stats.value,
            avg_duration_ms: Math.round(
              durations.reduce((a, b) => a + b, 0) / durations.length
            )
          }
        }
      }
      // ===============================================
    }
    // 场景元数据：scene_code → 名称
    if (metaRes.status === 'fulfilled' && metaRes.value?.data) {
      const sceneCodes = metaRes.value.data.scene_codes || []
      const map = {}
      for (const sc of sceneCodes) {
        if (sc && sc.code) map[sc.code] = sc.name || sc.code
      }
      sceneCodeToName.value = map
    }
    // 关键：所有数据加载完成后切换为聚合数据
    // 仍显示 commonTemplates 作为兜底（首屏已显示）
    dataLoaded.value = true
  } catch (e) {
    console.error('[Dashboard] load failed', e)
    ElMessage.error('加载数据失败，请检查网络或重新登录')
    // 失败时也标记为已加载（保持显示 commonTemplates）
    dataLoaded.value = true
  }
}

onMounted(load)
</script>

<style lang="scss" scoped>
// 整体容器：space-y-6（24px 行间距，对齐原型 section space-y-6）
.sxk-dashboard {
  display: flex;
  flex-direction: column;
  gap: $spacing-xl;              // 24px（原型 space-y-6）
}

// ========== 欢迎区（原型：flex justify-between items-center，无卡片背景） ==========
.welcome {
  display: flex;
  align-items: center;
  justify-content: space-between;

  .welcome-title {
    margin: 0;
    font-size: 24px;             // 原型 text-2xl
    font-weight: 700;            // 原型 font-bold
    color: $gray-900;            // 原型 text-gray-900
    line-height: 1.3;
  }

  .welcome-sub {
    margin: 4px 0 0;
    font-size: $font-size-sm;    // 原型 text-sm
    color: $text-secondary;      // 原型 text-gray-500
  }

  // 立即生成按钮（原型：bg-[#1A56DB] px-6 py-3 rounded-md font-semibold shadow-sm）
  .welcome-btn {
    font-weight: 600;
    :deep(.welcome-btn-icon) {
      margin-right: $spacing-sm;
    }
  }
}

// ========== 任务进度条（US013，原型无，业务保留） ==========
.progress-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: $spacing-md $spacing-lg;
  background: linear-gradient(90deg, $primary-color-light, $bg-card);
  border: 1px solid $border-base;
  border-radius: $radius-lg;

  .progress-info {
    display: flex;
    align-items: center;
    gap: $spacing-sm;
    font-size: $font-size-sm;
    color: $text-regular;

    .rotating {
      animation: sxkRotating 1s linear infinite;
      color: $primary-color;
    }
  }
}

// ========== 统计卡片（原型：bg-white rounded-lg border-gray-200 shadow-sm p-5 hover:shadow-md） ==========
.stat-row {
  margin-bottom: 0;
}

.stat-card {
  background: $bg-card;
  border: 1px solid $border-base;        // border-gray-200
  border-radius: $radius-lg;             // rounded-lg
  box-shadow: $shadow-sm;                // shadow-sm
  padding: 20px;                         // 原型 p-5
  transition: $transition-base;
  margin-bottom: $spacing-lg;            // 行内间距（配合 el-row gutter）

  &:hover {
    box-shadow: $shadow-md;              // hover:shadow-md
  }

  // 图标（原型：w-12 h-12 bg-{color}-50 rounded-lg，mb-4）
  .stat-icon {
    width: 48px;
    height: 48px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: $radius-lg;
    font-size: 24px;                     // text-2xl
    margin-bottom: $spacing-lg;
  }

  // 标签（原型：text-sm text-gray-500 mb-1）
  .stat-label {
    font-size: $font-size-sm;
    color: $text-secondary;              // text-gray-500
    margin-bottom: 4px;
  }

  // 数值（原型：text-3xl font-bold text-gray-900）
  .stat-value {
    font-size: 30px;                     // text-3xl ≈ 30px
    font-weight: 700;
    color: $gray-900;                    // text-gray-900
    line-height: 1.1;

    .stat-unit {
      font-size: $font-size-base;        // 原型 text-base
      font-weight: 600;
      margin-left: 2px;
    }
  }

  // 副标签（原型：text-xs text-gray-400 mt-1）
  .stat-sub {
    font-size: $font-size-xs;
    color: $text-placeholder;            // text-gray-400
    margin-top: 4px;
  }
}

// ========== section 标题（原型：text-xl font-bold text-gray-900 mb-4） ==========
.section-block {
  display: flex;
  flex-direction: column;
}

.section-title {
  margin: 0 0 $spacing-lg;
  font-size: $font-size-xl;              // text-xl
  font-weight: 700;                      // font-bold
  color: $gray-900;                      // text-gray-900
}

// ========== 常用模板卡片（原型：竖排 + border-2 hover:border-blue-500） ==========
.tpl-card {
  background: $bg-card;
  border: 2px solid transparent;
  border-radius: $radius-lg;
  box-shadow: $shadow-sm;
  padding: 20px;                         // p-5
  cursor: pointer;
  transition: $transition-base;
  margin-bottom: $spacing-lg;

  &:hover {
    border-color: $primary-color;        // hover:border-blue-500（用品牌色）
    box-shadow: $shadow-md;
  }

  // 图标（原型：w-12 h-12 rounded-lg mb-4 text-3xl）
  .tpl-icon {
    width: 48px;
    height: 48px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: $radius-lg;
    font-size: 30px;                     // text-3xl
    margin-bottom: $spacing-lg;
  }

  // 标题（原型：text-lg font-semibold text-gray-900 mb-2）
  .tpl-name {
    font-size: $font-size-lg;            // text-lg
    font-weight: 600;                    // font-semibold
    color: $gray-900;
    margin-bottom: $spacing-sm;
  }

  // 描述（原型：text-sm text-gray-500 mb-4）
  .tpl-desc {
    font-size: $font-size-sm;
    color: $text-secondary;
    margin-bottom: $spacing-lg;
    line-height: 1.5;
  }

  // 标签组（原型：flex flex-wrap gap-2）
  .tpl-tags {
    display: flex;
    flex-wrap: wrap;
    gap: $spacing-sm;
  }

  // 单个标签（原型：px-3 py-1 text-xs rounded-full）
  .tpl-tag {
    padding: 4px 12px;
    font-size: $font-size-xs;
    border-radius: $radius-round;        // rounded-full
    line-height: 1.2;
  }

  // ========== 骨架屏（加载中占位，避免看到 commonTemplates 旧数据） ==========
  &--skeleton {
    cursor: default;
    pointer-events: none;
  }
}

// ========== 骨架屏元素样式（关键：动画 + 灰色占位） ==========
@keyframes skeleton-shimmer {
  0% { background-position: -200px 0; }
  100% { background-position: calc(200px + 100%) 0; }
}

.tpl-icon--skeleton,
.tpl-name--skeleton,
.tpl-desc--skeleton,
.tpl-tag--skeleton {
  background: linear-gradient(
    90deg,
    #f0f0f0 0%,
    #f8f8f8 50%,
    #f0f0f0 100%
  );
  background-size: 200px 100%;
  animation: skeleton-shimmer 1.5s ease-in-out infinite;
  color: transparent !important;
  border-radius: $radius-md;
}

.tpl-icon--skeleton {
  width: 48px;
  height: 48px;
}

.tpl-name--skeleton {
  width: 60%;
  height: 18px;
  margin-bottom: 12px;
}

.tpl-desc--skeleton {
  width: 90%;
  height: 14px;
  margin-bottom: 8px;
}

.tpl-tag--skeleton {
  width: 40px;
  height: 18px;
  display: inline-block;
}

// ========== 最近生成列表（原型：space-y-4 横向卡片） ==========
.recent-list {
  display: flex;
  flex-direction: column;
  gap: $spacing-md;                      // space-y-4
}

.recent-item {
  display: flex;
  align-items: center;
  gap: $spacing-md;                      // space-x-4
  padding: 20px;                         // p-5
  background: $bg-card;
  border: 1px solid $border-base;
  border-radius: $radius-lg;
  box-shadow: $shadow-sm;
  cursor: pointer;
  transition: $transition-base;

  &:hover {
    box-shadow: $shadow-md;              // hover:shadow-md
  }

  // 图标（原型：w-12 h-12 rounded-lg text-2xl）
  .recent-icon {
    width: 48px;
    height: 48px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: $radius-lg;
    font-size: 24px;
    flex-shrink: 0;
  }

  .recent-info {
    flex: 1;
    min-width: 0;

    // 标题（原型：font-semibold text-gray-900）
    .recent-title {
      font-size: $font-size-base;
      font-weight: 600;
      color: $gray-900;
    }

    // 副信息（原型：text-xs text-gray-500 mt-1）
    .recent-time {
      font-size: $font-size-xs;
      color: $text-secondary;
      margin-top: 4px;
    }
  }
}

.empty-tip {
  padding: $spacing-2xl 0;
  text-align: center;
  color: $text-secondary;
  font-size: $font-size-sm;
}
</style>
