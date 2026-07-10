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
      <el-button type="primary" size="large" class="welcome-btn" @click="goGenerate">
        <el-icon class="welcome-btn-icon"><MagicStick /></el-icon>
        <span>立即生成</span>
      </el-button>
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

    <!-- ========== 常用模板（原型：h3 + grid lg:grid-cols-3 gap-6 竖排卡片） ========== -->
    <div class="section-block">
      <h3 class="section-title">常用模板</h3>
      <el-row :gutter="24">
        <el-col :xs="24" :sm="12" :lg="8" v-for="tpl in commonTemplates" :key="tpl.template_id">
          <div class="tpl-card" @click="useCommonTemplate(tpl)">
            <!-- 图标（原型：w-12 h-12 bg-{color}-50 rounded-lg mb-4） -->
            <div class="tpl-icon" :style="{ color: tpl.color, backgroundColor: tpl.bg }">
              <el-icon><component :is="tpl.icon" /></el-icon>
            </div>
            <div class="tpl-name">{{ tpl.name }}</div>
            <div class="tpl-desc">{{ tpl.desc }}</div>
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
  Loading
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
  {
    label: '平均评分',
    value: stats.value.avg_score || '—',
    unit: stats.value.avg_score ? '分' : '',
    sub: '内容质量',
    icon: Money,
    color: '#ea580c',                          // Tailwind orange-600
    bg: '#fff7ed'                              // Tailwind orange-50
  },
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
const SCENE_META = {
  product_intro: { icon: Document, color: '#2563eb', bg: '#eff6ff' },
  competitor: { icon: Money, color: '#ea580c', bg: '#fff7ed' },
  channel_adapt: { icon: Share, color: '#16a34a', bg: '#f0fdf4' }
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
  ElMessage.success(`已预设场景「${tpl.name}」`)
  router.push({ path: '/generate/index', query: { scene: tpl.scene_code } })
}

// ========== 数据加载 ==========
const load = async () => {
  try {
    // 并行加载：首页统计 + 最近 3 条 + 当前用户
    const [statRes, recentRes, userRes] = await Promise.allSettled([
      sxkApi.getDashboardStats(),
      sxkApi.getRecentGenerations(3),
      sxkApi.getCurrentUser()
    ])
    if (statRes.status === 'fulfilled' && statRes.value?.data) stats.value = statRes.value.data
    if (recentRes.status === 'fulfilled' && recentRes.value?.data) recentList.value = recentRes.value.data.items || []
    if (userRes.status === 'fulfilled' && userRes.value?.data) welcomeName.value = userRes.value.data.username || '营销专家'
  } catch (e) {
    console.error('[Dashboard] load failed', e)
    ElMessage.error('加载数据失败，请检查网络或重新登录')
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
