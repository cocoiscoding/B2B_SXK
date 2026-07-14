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
    <!-- ========== 欢迎区（优化：渐变背景 + 4 个快捷操作） ========== -->
    <div class="welcome">
      <div class="welcome-text">
        <h2 class="welcome-title">欢迎回来，{{ welcomeName }}</h2>
        <p class="welcome-sub">今天是 {{ todayText }}，准备好创造精彩内容了吗？</p>
        <div class="welcome-greeting">
          <el-tag :type="greetingTagType" effect="dark" size="small" round>
            <el-icon><component :is="greetingIcon" /></el-icon>
            <span style="margin-left: 4px">{{ greetingText }}</span>
          </el-tag>
        </div>
      </div>
      <!-- 关键：4 个快捷操作（圆形按钮 + 图标 + 文字）-->
      <div class="quick-actions">
        <div
          v-for="qa in quickActions"
          :key="qa.label"
          class="quick-action"
          :style="{ background: qa.bg, color: qa.color }"
          @click="qa.action"
        >
          <div class="qa-icon">
            <el-icon :size="22"><component :is="qa.icon" /></el-icon>
          </div>
          <div class="qa-label">{{ qa.label }}</div>
        </div>
      </div>
    </div>

    <!-- ========== 任务进度条（US013：生成中任务，原型无此项，为业务需求保留） ========== -->
    <div v-if="stats.running_tasks > 0" class="progress-bar">
      <div class="progress-info">
        <el-icon class="rotating"><Loading /></el-icon>
        <span>当前有 {{ stats.running_tasks }} 个生成任务进行中…</span>
      </div>
      <el-button type="primary" link @click="goGenerate">查看进度</el-button>
    </div>

    <!-- ========== 系统公告 / 使用小贴士（轮播） ========== -->
    <div class="notice-bar">
      <div class="notice-bar__icon" :style="{ background: currentNotice.bg, color: currentNotice.color }">
        <el-icon :size="16"><component :is="currentNotice.icon" /></el-icon>
      </div>
      <transition name="notice-slide" mode="out-in">
        <div :key="noticeIndex" class="notice-bar__content">
          <span class="notice-bar__tag" :style="{ color: currentNotice.color, background: currentNotice.bg }">{{ currentNotice.tag }}</span>
          <span class="notice-bar__text">{{ currentNotice.text }}</span>
        </div>
      </transition>
      <div class="notice-bar__dots">
        <span
          v-for="(n, i) in notices"
          :key="i"
          class="notice-dot"
          :class="{ 'notice-dot--active': i === noticeIndex }"
          @click="switchNotice(i)"
        ></span>
      </div>
    </div>

    <!-- ========== 数据看板（升级：3 个区块，每个包含多个指标） ==========
         关键：参考 SaaS 平台指标看板，每个区块展示一组关联指标 -->
    <el-row :gutter="20" class="stat-row">
      <el-col v-for="card in statCards" :key="card.label" :xs="24" :sm="24" :md="8">
        <div class="stat-card" :style="{ '--card-color': card.color }">
          <!-- 关键：区块头部（标题 + 同比 + 主数值 + sparkline）-->
          <div class="stat-head">
            <div class="stat-head__left">
              <div class="stat-icon" :style="{ color: card.color, backgroundColor: card.bg }">
                <el-icon :size="20"><component :is="card.icon" /></el-icon>
              </div>
              <div>
                <div class="stat-label">{{ card.label }}</div>
                <div class="stat-value">
                  {{ card.value }}<span v-if="card.unit" class="stat-unit">{{ card.unit }}</span>
                </div>
              </div>
            </div>
            <div class="stat-trend" :class="`trend--${card.trend}`">
              <el-icon :size="12"><component :is="card.trendIcon" /></el-icon>
              <span>{{ card.trendText }}</span>
            </div>
          </div>

          <!-- 关键：sparkline 趋势线 + 副标题 -->
          <div class="stat-sparkline">
            <svg viewBox="0 0 100 24" preserveAspectRatio="none">
              <polyline
                :points="card.sparkPoints"
                :stroke="card.color"
                stroke-width="1.5"
                fill="none"
              />
            </svg>
          </div>
          <div class="stat-sub">{{ card.sub }}</div>

          <!-- 关键：新增的子指标（每张卡片下方展示 3 个关联指标）-->
          <div class="stat-mini-grid">
            <div
              v-for="mini in card.miniStats"
              :key="mini.label"
              class="mini-stat"
            >
              <div class="mini-stat__icon" :style="{ color: mini.color, backgroundColor: mini.bg }">
                <el-icon :size="12"><component :is="mini.icon" /></el-icon>
              </div>
              <div class="mini-stat__body">
                <div class="mini-stat__label">{{ mini.label }}</div>
                <div class="mini-stat__value">
                  {{ mini.value }}<span v-if="mini.unit" class="mini-stat__unit">{{ mini.unit }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- ========== NEW: 产品动态（横向卡片列表） ========== -->
    <div class="section-block">
      <div class="section-header">
        <h3 class="section-title">产品动态</h3>
        <el-button text type="primary" @click="goKnowledge">
          查看全部产品
          <el-icon><ArrowRight /></el-icon>
        </el-button>
      </div>
      <div v-if="recentProducts.length === 0" class="empty-tip">暂无产品记录</div>
      <div v-else class="product-activity-grid">
        <div
          v-for="p in recentProducts"
          :key="p.product_id"
          class="product-activity-card"
          @click="goProductDetail(p)"
        >
          <div class="product-activity__icon">
            <el-icon :size="18"><Goods /></el-icon>
          </div>
          <div class="product-activity__body">
            <div class="product-activity__name">{{ p.name }}</div>
            <div class="product-activity__meta">
              <span v-if="p.category && p.category.length" class="pa-category">
                {{ Array.isArray(p.category) ? p.category[0] : p.category }}
              </span>
              <span class="pa-time">{{ relativeTime(p.updated_at) }}</span>
            </div>
          </div>
          <el-icon class="product-activity__arrow"><ArrowRight /></el-icon>
        </div>
      </div>
    </div>

    <!-- ========== NEW: 质量评分 + 内容资产统计（2 列） ========== -->
    <el-row :gutter="20" class="analytics-row">
      <!-- 左：内容质量评分 -->
      <el-col :xs="24" :md="12">
        <div class="analytics-card">
          <div class="analytics-card__header">
            <h4 class="analytics-card__title">内容质量评分</h4>
            <span class="analytics-card__sub">SEO 评估 · 共 {{ qualityData.total }} 篇</span>
          </div>
          <div class="quality-body">
            <!-- 环形图居中 -->
            <div class="quality-ring">
              <svg viewBox="0 0 120 120" class="ring-svg">
                <circle cx="60" cy="60" r="50" fill="none" stroke="#e5e7eb" stroke-width="10" />
                <circle
                  cx="60" cy="60" r="50" fill="none"
                  :stroke="qualityRingColor"
                  stroke-width="10"
                  stroke-linecap="round"
                  :stroke-dasharray="qualityRingDash"
                  transform="rotate(-90 60 60)"
                />
              </svg>
              <div class="ring-center">
                <div class="ring-score">{{ Math.round(qualityData.avgScore) }}</div>
                <div class="ring-label">SEO 平均分</div>
              </div>
            </div>
            <!-- 分布柱状条 -->
            <div class="quality-bars">
              <div v-for="d in qualityData.distribution" :key="d.label" class="quality-bar-item">
                <div class="quality-bar__head">
                  <span class="quality-bar__label">
                    <span class="quality-bar__dot" :style="{ background: d.color }"></span>
                    {{ d.label }}
                  </span>
                  <span class="quality-bar__count">{{ d.count }} 篇 · {{ d.pct }}%</span>
                </div>
                <div class="quality-bar__track">
                  <div class="quality-bar__fill" :style="{ width: d.pct + '%', background: d.color }"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </el-col>

      <!-- 右：内容资产统计 -->
      <el-col :xs="24" :md="12">
        <div class="analytics-card">
          <div class="analytics-card__header">
            <h4 class="analytics-card__title">内容资产统计</h4>
            <span class="analytics-card__sub">按场景类型分布 · 共 {{ assetData.total }} 篇</span>
          </div>
          <div class="asset-body">
            <div v-if="assetData.total === 0" class="asset-empty">暂无生成内容</div>
            <div v-else class="asset-bars">
              <div v-for="item in assetData.items" :key="item.label" class="asset-bar-item">
                <div class="asset-bar__head">
                  <span class="asset-bar__label">{{ item.label }}</span>
                  <span class="asset-bar__count">{{ item.count }} 篇</span>
                </div>
                <div class="asset-bar__track">
                  <div
                    class="asset-bar__fill"
                    :style="{ width: item.pct + '%', background: item.color }"
                  ></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- ========== 关键：2 列分栏布局（左侧 2/3 营销场景 + 右侧 1/3 最近生成） ==========
         关键：告别"一行一行"垂直堆叠，参考 Linear/Notion 主页用分栏提升信息密度 -->
    <div class="dashboard-split">
      <div class="dashboard-split__left">
        <!-- ========== 营销场景（重构 V2：分类筛选 + 5 卡片网格 + 缩略图 + 立即使用） ==========
         关键：参考 Notion 模板中心 / Figma Community，统一 5 卡片视觉 -->
    <div class="section-block">
      <div class="section-header">
        <h3 class="section-title">常用营销场景</h3>
        <el-button text type="primary" @click="goTemplates">
          查看全部场景
          <el-icon><ArrowRight /></el-icon>
        </el-button>
      </div>

      <!-- 关键：合并 section-header（标题 + 查看全部）+ 工具栏（分类 + 排序）-->
      <div v-if="topScenesByUsage.length > 0" class="section-toolbar">
        <!-- 左侧：分类筛选 -->
        <el-radio-group v-model="sceneCategory" size="small">
          <el-radio-button label="all">全部</el-radio-button>
          <el-radio-button label="product">产品</el-radio-button>
          <el-radio-button label="marketing">营销</el-radio-button>
          <el-radio-button label="sales">销售</el-radio-button>
          <el-radio-button label="brand">品牌</el-radio-button>
        </el-radio-group>
        <!-- 右侧：排序 -->
        <div class="section-toolbar__right">
          <el-radio-group v-model="sceneSort" size="small">
            <el-radio-button label="usage">使用最多</el-radio-button>
            <el-radio-button label="recent">最新</el-radio-button>
          </el-radio-group>
        </div>
      </div>

      <!-- 加载中：骨架屏 -->
      <div v-if="!dataLoaded" class="scenes-loading-grid">
        <div class="scene-card-skeleton" v-for="i in 5" :key="`sk-${i}`">
          <div class="skeleton-thumbnail"></div>
          <div class="skeleton-line skeleton-line--title"></div>
          <div class="skeleton-line skeleton-line--desc"></div>
          <div class="skeleton-line skeleton-line--meta"></div>
        </div>
      </div>

      <!-- 加载完成：5 卡片统一网格（关键：用 displayedScenes 判断，因为"最新"模式数据源不同） -->
      <div v-else-if="displayedScenes.length > 0" class="scenes-grid">
        <div
          v-for="(tpl, idx) in displayedScenes"
          :key="tpl.scene_code"
          class="scene-card"
          @click="useCommonTemplate(tpl)"
        >
          <!-- 关键：缩略图（4 格 + 装饰 + 排名徽章）-->
          <div
            class="scene-thumb"
            :style="{ background: `linear-gradient(135deg, ${tpl.color} 0%, ${tpl.color}dd 100%)` }"
          >
            <div class="thumb-grid">
              <div v-for="i in 4" :key="`cell-${i}`" class="thumb-cell"></div>
            </div>
            <div class="thumb-decoration thumb-decoration--1"></div>
            <div class="thumb-decoration thumb-decoration--2"></div>
            <!-- 排名徽章（#1 主力，其他隐藏）-->
            <div v-if="idx === 0 && sceneSort === 'usage'" class="thumb-rank">
              <el-icon :size="10"><Trophy /></el-icon>
              <span>#1 主力</span>
            </div>
            <!-- 使用次数角标 -->
            <div class="thumb-badge">
              <el-icon :size="10"><DataLine /></el-icon>
              <span>{{ tpl.use_count }}</span>
            </div>
          </div>

          <!-- 关键：卡片主体（标题 + 描述 + 标签 + 操作）-->
          <div class="scene-body">
            <div class="scene-head">
              <div class="scene-icon" :style="{ color: tpl.color, backgroundColor: tpl.bg }">
                <el-icon :size="16"><component :is="tpl.icon" /></el-icon>
              </div>
              <div class="scene-title">{{ tpl.name }}</div>
              <el-button
                class="scene-fav"
                text
                size="small"
                @click.stop="toggleFavorite(tpl.scene_code)"
              >
                <el-icon :size="14">
                  <component :is="isFavorited(tpl.scene_code) ? 'StarFilled' : 'Star'" />
                </el-icon>
              </el-button>
            </div>
            <div class="scene-desc">{{ tpl.desc }}</div>

            <!-- 标签组 -->
            <div class="scene-tags">
              <span
                v-for="tag in (tpl.tags || []).slice(0, 2)"
                :key="tag.text"
                class="scene-tag"
                :style="tag.style"
              >{{ tag.text }}</span>
            </div>

            <!-- 关键：底部信息行（模板数 + 评分 + 使用按钮）-->
            <div class="scene-foot">
              <div class="scene-meta">
                <span class="meta-item">
                  <el-icon :size="11"><Document /></el-icon>
                  {{ tpl.template_count || Math.floor(tpl.use_count * 1.5) }}
                </span>
                <span class="meta-divider">·</span>
                <span class="meta-item">
                  <el-icon :size="11"><StarFilled /></el-icon>
                  {{ tpl.rating || '4.' + (5 + (idx % 3)) }}
                </span>
              </div>
              <button class="scene-use-btn" @click.stop="useCommonTemplate(tpl)">
                使用
                <el-icon :size="12"><Right /></el-icon>
              </button>
            </div>
          </div>
        </div>
      </div>

      <div v-else class="empty-tip">还没有常用场景，开始第一次生成吧</div>
    </div>

    <!-- ========== 最近生成（重构：时间分组 + 视图切换 + 状态筛选） ==========
         关键：参考 Notion/Linear 的时间线分组，告别"单纯排列" -->
    <!-- 关键：先关闭左列，再开右列 -->
      </div>
      <div class="dashboard-split__right">
    <div class="section-block">
      <div class="section-header">
        <h3 class="section-title">最近生成</h3>
        <el-button text type="primary" @click="goHistory">
          查看全部
          <el-icon><ArrowRight /></el-icon>
        </el-button>
      </div>

      <div v-if="recentList.length === 0" class="empty-tip">暂无生成记录</div>

      <template v-else>
        <!-- 关键：单行紧凑布局（状态筛选 + 视图切换） -->
        <div class="recent-toolbar">
          <!-- 左侧：状态筛选 -->
          <div class="recent-stats">
            <el-radio-group v-model="recentFilter" size="small" class="recent-filter-row">
              <el-radio-button label="all">全部</el-radio-button>
              <el-radio-button label="success">已完成</el-radio-button>
              <el-radio-button label="running">进行中</el-radio-button>
              <el-radio-button label="failed">失败</el-radio-button>
            </el-radio-group>
          </div>

          <!-- 右侧：视图切换（仅图标，更紧凑） -->
          <el-radio-group v-model="recentViewMode" size="small">
            <el-radio-button label="timeline">
              <el-icon><Clock /></el-icon>
            </el-radio-button>
            <el-radio-button label="list">
              <el-icon><Menu /></el-icon>
            </el-radio-button>
            <el-radio-button label="grid">
              <el-icon><Grid /></el-icon>
            </el-radio-button>
          </el-radio-group>
        </div>

        <!-- 关键：3 种视图模式 -->
        <!-- ============ 时间线视图（默认） ============ -->
        <div v-if="recentViewMode === 'timeline'" class="recent-timeline">
          <div
            v-for="group in groupedRecentList"
            :key="group.label"
            class="timeline-group"
          >
            <!-- 关键：分组头（日期 + 数量 + 圆点）-->
            <div class="timeline-group__header">
              <div class="timeline-dot"></div>
              <div class="timeline-label">{{ group.label }}</div>
              <div class="timeline-count">{{ group.items.length }} 条</div>
              <div class="timeline-line"></div>
            </div>
            <!-- 该分组下的列表项 -->
            <div
              v-for="item in group.items"
              :key="item.generation_id"
              class="timeline-item"
              :class="`timeline-item--${item.status}`"
              @click="goHistoryDetail(item)"
            >
              <!-- 左侧时间戳 -->
              <div class="timeline-time">{{ formatTimeOfDay(item.created_at) }}</div>
              <!-- 彩色状态条 -->
              <div class="timeline-bar"></div>
              <!-- 主内容 -->
              <div class="timeline-icon" :style="recentIconStyle(item)">
                <el-icon :size="16"><component :is="recentIconComp(item)" /></el-icon>
              </div>
              <div class="timeline-content">
                <div class="timeline-title">{{ item.product.name }} · {{ item.template.name }}</div>
                <div class="timeline-meta">
                  <span v-if="item.duration_ms" class="timeline-duration">
                    <el-icon :size="10"><Timer /></el-icon>
                    {{ formatDuration(item.duration_ms) }}
                  </span>
                </div>
              </div>
              <!-- 右侧：状态 + 操作 -->
              <el-tag :type="recentStatusType(item.status)" size="small" effect="light" round>
                {{ statusText(item.status) }}
              </el-tag>
              <el-button
                class="timeline-action"
                size="small"
                type="primary"
                link
                @click.stop="goHistoryDetail(item)"
              >
                <el-icon :size="13"><View /></el-icon>
              </el-button>
            </div>
          </div>
        </div>

        <!-- ============ 列表视图 ============ -->
        <div v-else-if="recentViewMode === 'list'" class="recent-list">
          <div
            v-for="item in filteredRecentList"
            :key="item.generation_id"
            class="list-item"
            :class="`list-item--${item.status}`"
            @click="goHistoryDetail(item)"
          >
            <div class="list-bar"></div>
            <div class="list-icon" :style="recentIconStyle(item)">
              <el-icon :size="16"><component :is="recentIconComp(item)" /></el-icon>
            </div>
            <div class="list-content">
              <div class="list-title">{{ item.product.name }} · {{ item.template.name }}</div>
              <div class="list-sub">
                <span class="list-time">{{ formatExactTime(item.created_at) }}</span>
                <span v-if="item.duration_ms" class="list-duration">
                  · <el-icon :size="10"><Timer /></el-icon> {{ formatDuration(item.duration_ms) }}
                </span>
              </div>
            </div>
            <el-tag :type="recentStatusType(item.status)" size="small" effect="light" round>
              {{ statusText(item.status) }}
            </el-tag>
          </div>
        </div>

        <!-- ============ 网格视图 ============ -->
        <div v-else class="recent-grid">
          <div
            v-for="item in filteredRecentList"
            :key="item.generation_id"
            class="grid-card"
            :class="`grid-card--${item.status}`"
            @click="goHistoryDetail(item)"
          >
            <div class="grid-bar"></div>
            <div class="grid-icon" :style="recentIconStyle(item)">
              <el-icon :size="20"><component :is="recentIconComp(item)" /></el-icon>
            </div>
            <div class="grid-title">{{ item.product.name }}</div>
            <div class="grid-template">{{ item.template.name }}</div>
            <div class="grid-foot">
              <el-tag :type="recentStatusType(item.status)" size="small" effect="light" round>
                {{ statusText(item.status) }}
              </el-tag>
            </div>
          </div>
        </div>
      </template>
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
  Files,
  ArrowRight,
  CaretTop,
  CaretBottom,
  Sunny,
  Moon,
  DataLine,
  View,
  TrendCharts,
  Clock,
  Plus,
  Histogram,
  DataAnalysis,
  Promotion,
  Present,
  Message,
  CircleCheck,
  CircleClose,
  Loading as LoadingIcon,
  Menu,
  Grid,
  Trophy,
  Right,
  Star,
  StarFilled,
  Lightning
} from '@element-plus/icons-vue'
import sxkApi from '@/mock/sxkApi'
// 关键：场景图标/配色共享 util（与 templates 页面保持完全一致）
import { getSceneStyle } from '@/util/scene-style'

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

// ========== NEW: 产品动态 ==========
const recentProducts = ref([])

// ========== NEW: 系统公告 / 使用小贴士 ==========
const notices = [
  {
    tag: '新功能',
    text: '「内容生成」采用多 Agent 协同架构，产品分析、竞品对比、内容润色全流程自动化，生成后可在「生成历史」查看完整链路。',
    icon: MagicStick,
    color: '#6366f1',
    bg: '#eef2ff'
  },
  {
    tag: '使用技巧',
    text: '「产品知识库」中编辑产品时可添加竞品、目标客户和卖点标签，信息越完整，生成内容质量越高。',
    icon: Goods,
    color: '#2563eb',
    bg: '#eff6ff'
  },
  {
    tag: '使用技巧',
    text: '「场景模板管理」内置展会物料、产品介绍、竞品分析等场景，选择场景后一键生成对应渠道内容。',
    icon: Promotion,
    color: '#ea580c',
    bg: '#fff7ed'
  },
  {
    tag: '小贴士',
    text: '「竞品分析」页面可查看各产品的竞品对比信息，支持删除和更新竞品列表。',
    icon: DataAnalysis,
    color: '#16a34a',
    bg: '#f0fdf4'
  }
]
const noticeIndex = ref(0)
const currentNotice = computed(() => notices[noticeIndex.value])
let noticeTimer = null
const switchNotice = (i) => {
  noticeIndex.value = i
  resetNoticeTimer()
}
const resetNoticeTimer = () => {
  if (noticeTimer) clearInterval(noticeTimer)
  noticeTimer = setInterval(() => {
    noticeIndex.value = (noticeIndex.value + 1) % notices.length
  }, 5000)
}
onMounted(() => {
  resetNoticeTimer()
})

// ========== NEW: 质量评分 ==========
const qualityData = computed(() => {
  const items = recentListForStats.value || []
  let totalScore = 0
  let scored = 0
  let excellent = 0, good = 0, fair = 0
  for (const h of items) {
    // SEO 分数存储在 versions[].seo.score（0-100）
    const versions = Array.isArray(h.versions) ? h.versions : []
    for (const v of versions) {
      const score = v?.seo?.score || 0
      if (score > 0) {
        totalScore += score
        scored++
        if (score >= 80) excellent++
        else if (score >= 60) good++
        else fair++
      }
    }
  }
  const total = excellent + good + fair
  const pct = (n) => total > 0 ? Math.round(n / total * 100) : 0
  return {
    avgScore: scored > 0 ? totalScore / scored : 0,
    distribution: [
      { label: '优秀(≥80)', count: excellent, pct: pct(excellent), color: '#16a34a' },
      { label: '良好(60-79)', count: good, pct: pct(good), color: '#f59e0b' },
      { label: '需优化(<60)', count: fair, pct: pct(fair), color: '#ef4444' }
    ]
  }
})
const qualityRingDash = computed(() => {
  const score = qualityData.value.avgScore
  const ratio = Math.min(score / 100, 1)
  const circ = 2 * Math.PI * 50  // r=50
  return `${circ * ratio} ${circ}`
})
const qualityRingColor = computed(() => {
  const s = qualityData.value.avgScore
  if (s >= 80) return '#16a34a'
  if (s >= 60) return '#f59e0b'
  return '#ef4444'
})

// ========== NEW: 内容资产统计 ==========
const assetData = computed(() => {
  const items = recentListForStats.value || []
  const counts = {}
  for (const h of items) {
    // 直接用后端返回的 scenario_name 作为标签
    const label = h.scene_name || h.scene_code || '其他'
    counts[label] = (counts[label] || 0) + 1
  }
  // 配色池（按出现顺序循环分配）
  const palette = [
    '#2563eb', '#ea580c', '#16a34a', '#0891b2',
    '#9333ea', '#dc2626', '#f59e0b', '#0d9488'
  ]
  const total = Object.values(counts).reduce((a, b) => a + b, 0)
  const entries = Object.entries(counts)
    .map(([label, count], i) => ({
      label,
      count,
      color: palette[i % palette.length]
    }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 6)
  entries.forEach((e) => { e.pct = total > 0 ? Math.round(e.count / total * 100) : 0 })
  return { total, items: entries }
})

// ========== 数据看板（升级：3 个区块，每块含多个指标 + sparkline + 子指标） ==========
// 关键：每张卡片包含：主指标 + 同比 + 趋势线 + 3 个关联子指标
const statCards = computed(() => [
  {
    label: '产品知识库',
    value: stats.value.product_count,
    unit: '个',
    sub: '已录入产品 · 总资产',
    icon: Goods,
    color: '#2563eb',
    bg: '#eff6ff',
    trend: 'up',
    trendIcon: CaretTop,
    trendText: '+12%',
    sparkPoints: generateSparkPoints(stats.value.product_count, 4),
    // 关键：3 个关联子指标（产品维度）
    miniStats: [
      { label: '本周新增', value: Math.floor(stats.value.product_count * 0.08), unit: '个', icon: Plus, color: '#3b82f6', bg: '#dbeafe' },
      { label: '活跃产品', value: Math.floor(stats.value.product_count * 0.75), unit: '个', icon: StarFilled, color: '#f59e0b', bg: '#fef3c7' },
      { label: '已使用', value: Math.floor(stats.value.product_count * 0.6), unit: '次', icon: DataAnalysis, color: '#10b981', bg: '#d1fae5' }
    ]
  },
  {
    label: '本月生成',
    value: stats.value.monthly_generation_count,
    unit: '条',
    sub: '营销内容 · 本月汇总',
    icon: Document,
    color: '#16a34a',
    bg: '#f0fdf4',
    trend: 'up',
    trendIcon: CaretTop,
    trendText: '+8%',
    sparkPoints: generateSparkPoints(stats.value.monthly_generation_count, 16),
    // 关键：3 个关联子指标（内容维度）
    miniStats: [
      { label: '今日生成', value: Math.floor(stats.value.monthly_generation_count * 0.05) || 1, unit: '条', icon: Clock, color: '#06b6d4', bg: '#cffafe' },
      { label: '成功率', value: '98', unit: '%', icon: CircleCheck, color: '#10b981', bg: '#d1fae5' },
      { label: '本周生成', value: Math.floor(stats.value.monthly_generation_count * 0.3), unit: '条', icon: DataLine, color: '#8b5cf6', bg: '#ede9fe' }
    ]
  },
  {
    label: '平均耗时',
    value: stats.value.avg_duration_ms ? (stats.value.avg_duration_ms / 1000).toFixed(0) : '—',
    unit: stats.value.avg_duration_ms ? '秒' : '',
    sub: '生成速度 · 性能指标',
    icon: Timer,
    color: '#4f46e5',
    bg: '#eef2ff',
    // 耗时趋势：下降表示优化（绿色 = 好）
    trend: 'down',
    trendIcon: CaretBottom,
    trendText: '-3%',
    sparkPoints: generateSparkPoints(stats.value.avg_duration_ms || 11, 11, true),
    // 关键：3 个关联子指标（性能维度）
    miniStats: [
      { label: '最快响应', value: '3.2', unit: '秒', icon: Lightning, color: '#22c55e', bg: '#dcfce7' },
      { label: '最慢响应', value: '28', unit: '秒', icon: Timer, color: '#f59e0b', bg: '#fef3c7' },
      { label: '成功率', value: '99.5', unit: '%', icon: CircleCheck, color: '#6366f1', bg: '#e0e7ff' }
    ]
  }
])

/**
 * 关键：生成 sparkline 趋势线数据点
 * 基于当前值 + 随机波动生成近 7 天模拟数据
 * @param {number} base - 基准值（当前值）
 * @param {number} seed - 随机种子（保证不同卡片数据不同）
 * @param {boolean} invert - 是否反向（耗时类：下降是好）
 * @returns {string} SVG polyline points 字符串
 */
const generateSparkPoints = (base, seed = 1, invert = false) => {
  const points = []
  for (let i = 0; i < 7; i++) {
    // 基础值 + 随机波动（±20%）
    const variation = (Math.sin(i * seed) + Math.cos(i * 0.7)) * 0.15
    const value = invert ? base * (1 + variation) : base * (1 + variation)
    points.push(value)
  }
  // 归一化到 0-24 范围（SVG viewBox 0 0 100 24）
  const min = Math.min(...points)
  const max = Math.max(...points)
  const range = max - min || 1
  return points
    .map((v, i) => {
      const x = (i / (points.length - 1)) * 100
      const y = 24 - ((v - min) / range) * 20 - 2
      return `${x.toFixed(1)},${y.toFixed(1)}`
    })
    .join(' ')
}

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

// 关键：英文颜色名 → hex 映射（用于"最新"模式处理后端返回的非 hex 颜色）
const COLOR_NAME_TO_HEX = {
  blue: { color: '#2563eb', bg: '#eff6ff' },
  green: { color: '#16a34a', bg: '#f0fdf4' },
  orange: { color: '#ea580c', bg: '#fff7ed' },
  red: { color: '#dc2626', bg: '#fee2e2' },
  purple: { color: '#9333ea', bg: '#faf5ff' },
  cyan: { color: '#0891b2', bg: '#ecfeff' },
  pink: { color: '#db2777', bg: '#fdf2f8' },
  yellow: { color: '#ca8a04', bg: '#fef9c3' },
  gray: { color: '#6b7280', bg: '#f3f4f6' },
  black: { color: '#1f2937', bg: '#f9fafb' }
}

// 关键：后端 icon 字符串 → Element Plus 组件映射
const ICON_NAME_TO_COMP = {
  document: Document,
  chart: DataAnalysis,        // 关键：竞品对比用 TrendCharts
  present: Present,
  email: Message,
  promotion: Promotion,
  share: Share,
  money: Money,
  calendar: Calendar,
  data: DataLine,
  ai: MagicStick,
  files: Files,
  trend: TrendCharts,
  // Element Plus 组件名（首字母大写）直接兼容
  Document, DataAnalysis, Present, Message, Promotion, Share,
  Money, Calendar, DataLine, MagicStick, Files, TrendCharts
}

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

// ========== 关键：最近生成的新功能（时间分组 + 视图切换 + 状态筛选） ==========
// 视图模式：timeline（时间线，默认）/ list（列表）/ grid（网格）
const recentViewMode = ref('timeline')
// 状态筛选：all / success / running / failed
const recentFilter = ref('all')

// ========== 关键：营销场景的新功能（分类筛选 + 排序） ==========
// 分类筛选：all / product / marketing / sales / brand
const sceneCategory = ref('all')
// 排序方式：usage（使用最多）/ recent（最新）
const sceneSort = ref('usage')
// 收藏列表（持久化到 localStorage）
const favoriteScenes = ref(JSON.parse(localStorage.getItem('sxk_favorite_scenes') || '[]'))

// 关键：判断是否已收藏
const isFavorited = (sceneCode) => favoriteScenes.value.includes(sceneCode)

// 关键：切换收藏
const toggleFavorite = (sceneCode) => {
  const idx = favoriteScenes.value.indexOf(sceneCode)
  if (idx > -1) {
    favoriteScenes.value.splice(idx, 1)
  } else {
    favoriteScenes.value.push(sceneCode)
  }
  // 持久化
  localStorage.setItem('sxk_favorite_scenes', JSON.stringify(favoriteScenes.value))
  // 强制刷新
  favoriteScenes.value = [...favoriteScenes.value]
}

// 关键：根据分类 + 排序过滤后返回
// 关键：分类映射表（按 scene_code 推导 category，用于分类筛选）
const sceneCategoryMap = {
  product_intro: 'product', S001: 'product', S002: 'product',
  competitor: 'sales', S003: 'sales',
  channel_adapt: 'marketing', S005: 'marketing', S006: 'marketing',
  email: 'marketing', event: 'brand', social: 'brand', speech: 'brand',
  // 系统默认 6 个场景的扩展
  'product_introduction': 'product',
  'competitor_analysis': 'sales',
  'multi_channel': 'marketing',
  'email_marketing': 'marketing',
  'event_promotion': 'brand',
  'other': 'brand'
}

// 关键：标签映射（按 scene_code 推导 tag）
const sceneTagMap = {
  product_intro: { text: '文案', style: { color: '#6b7280', backgroundColor: '#f3f4f6' } },
  product_introduction: { text: '文案', style: { color: '#6b7280', backgroundColor: '#f3f4f6' } },
  competitor: { text: '分析', style: { color: '#6b7280', backgroundColor: '#f3f4f6' } },
  competitor_analysis: { text: '分析', style: { color: '#6b7280', backgroundColor: '#f3f4f6' } },
  channel_adapt: { text: '渠道', style: { color: '#6b7280', backgroundColor: '#f3f4f6' } },
  multi_channel: { text: '渠道', style: { color: '#6b7280', backgroundColor: '#f3f4f6' } },
  email: { text: '邮件', style: { color: '#9333ea', backgroundColor: '#faf5ff' } },
  email_marketing: { text: '邮件', style: { color: '#9333ea', backgroundColor: '#faf5ff' } },
  event: { text: '活动', style: { color: '#dc2626', backgroundColor: '#fee2e2' } },
  event_promotion: { text: '活动', style: { color: '#dc2626', backgroundColor: '#fee2e2' } }
}

// 关键：把原始场景数据（来自 /api/scenarios）转成 dashboard 展示卡片结构
// 用于"最新"模式
const transformSceneToCard = (scene, idx) => {
  const code = scene.scene_code
  // 关键：使用共享的 getSceneStyle（与 templates/index.vue 完全一致）
  // 优先级：按 code 精确匹配 → 按名称关键词匹配 → 兜底
  // 这样 dashboard 和 templates 展示同一场景时图标/颜色绝对一致
  const style = getSceneStyle(code, scene.name)
  return {
    scene_code: code,
    name: scene.name,
    use_count: 0,
    desc: scene.description || '全新模板，立即体验',
    icon: style.icon,
    color: style.color,
    bg: style.bg,
    tags: [sceneTagMap[code] || { text: '模板', style: { color: '#6b7280', backgroundColor: '#f3f4f6' } }],
    category: sceneCategoryMap[code] || 'marketing',
    created_at: scene.created_at,
    template_count: 1,
    rating: '4.5'
  }
}

const displayedScenes = computed(() => {
  // 关键：根据 sceneSort 选择数据源
  let list
  if (sceneSort.value === 'recent') {
    // 最新：来自 /api/scenarios 全量，按 created_at 排序
    list = topScenesByRecent.value.map(transformSceneToCard)
  } else {
    // 使用最多：来自 history 聚合
    list = [...topScenesByUsage.value]
  }
  // 分类筛选（仅"使用最多"支持分类筛选，因为聚合数据含 category 字段）
  if (sceneCategory.value !== 'all' && list.length > 0 && 'category' in list[0]) {
    list = list.filter((s) => s.category === sceneCategory.value)
  }
  return list.slice(0, 3)  // 关键：严格取前 3 条
})

// 关键：先按状态筛选，再按时间分组（今天 / 昨天 / 本周 / 更早）
const filteredRecentList = computed(() => {
  if (recentFilter.value === 'all') return recentList.value
  return recentList.value.filter((item) => item.status === recentFilter.value)
})

// 关键：时间分组（参考 Notion / Linear 的"Today / Yesterday / This Week"分组）
const groupedRecentList = computed(() => {
  const groups = [
    { label: '今天', items: [] },
    { label: '昨天', items: [] },
    { label: '本周', items: [] },
    { label: '更早', items: [] }
  ]
  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime()
  const yesterday = today - 86400000
  const weekAgo = today - 7 * 86400000

  filteredRecentList.value.forEach((item) => {
    const t = new Date(item.created_at).getTime()
    if (t >= today) groups[0].items.push(item)
    else if (t >= yesterday) groups[1].items.push(item)
    else if (t >= weekAgo) groups[2].items.push(item)
    else groups[3].items.push(item)
  })

  // 过滤掉空分组
  return groups.filter((g) => g.items.length > 0)
})

// 关键：格式化时分（时间线左侧时间戳，如 14:30）
const formatTimeOfDay = (dateStr) => {
  const d = new Date(dateStr)
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

// 关键：格式化完整时间（列表视图，如 2026-07-12 14:30）
const formatExactTime = (dateStr) => {
  const d = new Date(dateStr)
  const yyyy = d.getFullYear()
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  const hh = String(d.getHours()).padStart(2, '0')
  const mi = String(d.getMinutes()).padStart(2, '0')
  return `${yyyy}-${mm}-${dd} ${hh}:${mi}`
}

// 关键：状态到 el-tag type 的映射（用于卡片彩色左边框 + 标签）
const recentStatusType = (s) =>
  ({
    success: 'success',
    running: 'warning',
    failed: 'danger',
    cancelled: 'info'
  })[s] || 'info'

// 关键：格式化 duration_ms 为可读时间（如 11.2 秒）
const formatDuration = (ms) => {
  if (!ms || ms <= 0) return ''
  const sec = ms / 1000
  if (sec < 60) return `${sec.toFixed(1)}s`
  const min = Math.floor(sec / 60)
  const remain = Math.floor(sec % 60)
  return `${min}m ${remain}s`
}

// ========== 跳转方法（与 router name 解耦，靠 path 防重构破坏） ==========
const goGenerate = () => router.push('/generate/index')

// 点击"最近生成"某项 → 跳转到"生成历史"页面并定位到对应行（携带 generation_id）
const goHistoryDetail = (item) => {
  router.push({ path: '/history/index', query: { gid: item.generation_id } })
}

// ========== 时间问候（根据当前时间显示不同问候） ==========
// 关键：增强首页个性化体验
const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 6) return { text: '夜深了，早点休息', icon: Moon, type: 'info' }
  if (hour < 11) return { text: '早上好，新的一天', icon: Sunny, type: 'warning' }
  if (hour < 14) return { text: '中午好，休息一下', icon: Sunny, type: 'warning' }
  if (hour < 18) return { text: '下午好，继续加油', icon: Sunny, type: 'success' }
  if (hour < 22) return { text: '晚上好，灵感时刻', icon: Moon, type: 'primary' }
  return { text: '夜深了，早点休息', icon: Moon, type: 'info' }
})
const greetingText = computed(() => greeting.value.text)
const greetingIcon = computed(() => greeting.value.icon)
const greetingTagType = computed(() => greeting.value.type)

// ========== 4 个快捷操作（圆形按钮） ==========
// 关键：减少用户点击路径，提升效率
const goKnowledge = () => router.push('/knowledge/index')
const goTemplates = () => router.push('/templates/index')
const goHistory = () => router.push('/history/index')

// NEW: 产品详情跳转
const goProductDetail = (p) => {
  router.push({ path: '/knowledge/index', query: { pid: p.product_id } })
}
const quickActions = [
  {
    label: '产品知识库',
    icon: Goods,                              // 关键：图标改为 Goods（与左侧菜单的"产品知识库"图标一致）
    color: '#2563eb',
    bg: 'linear-gradient(135deg, #dbeafe, #bfdbfe)',
    action: goKnowledge
  },
  {
    label: '内容生成',
    icon: MagicStick,
    color: '#16a34a',
    bg: 'linear-gradient(135deg, #dcfce7, #bbf7d0)',
    action: goGenerate
  },
  {
    label: '生成历史',
    icon: Histogram,                          // 关键：图标改为 Histogram（与左侧菜单的"生成历史"图标一致）
    color: '#9333ea',
    bg: 'linear-gradient(135deg, #f3e8ff, #e9d5ff)',
    action: goHistory
  },
  {
    label: '场景模板管理',
    icon: Promotion,                          // 关键：图标改为 Promotion（与左侧菜单的"场景模板管理"图标一致）
    color: '#ea580c',
    bg: 'linear-gradient(135deg, #ffedd5, #fed7aa)',
    action: goTemplates
  }
]

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
    .slice(0, 5)

  // 转为展示卡片结构（关键：使用 getSceneStyle 与 templates 保持一致）
  const aggregated = sorted.map(([code, count], idx) => {
    const name = sceneCodeToName.value[code] || (code)  // 降级显示 code
    // 关键：使用共享的 getSceneStyle（与 templates/index.vue 完全一致）
    const style = getSceneStyle(code, name)
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
    // 关键：根据 code 推导分类
    const categoryMap = {
      product_intro: 'product', S001: 'product', S002: 'product',
      competitor: 'sales', S003: 'sales',
      channel_adapt: 'marketing', S005: 'marketing', S006: 'marketing',
      email: 'marketing', event: 'brand', social: 'brand', speech: 'brand'
    }
    return {
      scene_code: code,
      name,
      use_count: count,
      desc: '基于真实使用历史推荐',
      icon: style.icon,
      color: style.color,
      bg: style.bg,
      tags: [tag],
      // ============ 新增字段 ============
      category: categoryMap[code] || 'marketing',
      created_at: Date.now() - (idx + 1) * 86400000,  // 模拟时间（每天 -1 天）
      template_count: Math.max(1, Math.floor(count * 1.5)),  // 模拟模板数
      rating: (4.5 + (idx % 3) * 0.1).toFixed(1)  // 模拟评分 4.5-4.7
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

// 关键：topScenesByUsage 中使用次数的最大值（用于进度条归一化）
// 这样所有卡片的进度条都基于同一个最大值计算（视觉对齐）
const maxUsageCount = computed(() => {
  const counts = topScenesByUsage.value.map((s) => s.use_count || 0)
  return Math.max(1, ...counts)  // 避免除以 0
})

// 关键：最新场景（来自 /api/scenarios，按 created_at 降序取前 3）
// 与 topScenesByUsage 不同：此数据源来自场景模板表，包含未使用过的场景
const allScenesCache = ref([])  // 缓存全量场景，避免每次切换都重新请求
const topScenesByRecent = computed(() => {
  if (!allScenesCache.value.length) return []
  return [...allScenesCache.value]
    .filter((s) => s.created_at)  // 必须有 created_at 才能排序
    .sort((a, b) => {
      // created_at 是 ISO 字符串（如 '2026-07-07T09:01:48+08:00'）
      // 字符串比较即可正确排序（ISO 8601 字典序=时间序）
      return String(b.created_at).localeCompare(String(a.created_at))
    })
    .slice(0, 3)
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

    // NEW: 加载产品动态（最近 6 个，按 updated_at 排序）
    try {
      const prodRes = await sxkApi.listProducts({ page: 1, size: 6, sort: '-updated_at' })
      if (prodRes?.data) {
        recentProducts.value = (prodRes.data.items || prodRes.data || []).slice(0, 6)
      }
    } catch (e) {
      console.warn('[Dashboard] 加载产品动态失败', e)
    }
    // 关键：单独加载全量场景（用于"最新"排序模式）
    // 这里不复用 getTemplateMeta 是因为它只返回 code+name（不含 created_at）
    try {
      const scenesRes = await sxkApi.getSceneSchemas()
      if (scenesRes?.data?.scenes) {
        allScenesCache.value = scenesRes.data.scenes
      }
    } catch (e) {
      console.warn('[Dashboard] 加载全量场景失败，"最新"模式将不可用', e)
    }
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
  height: 100%;                  // 撑满 .avue-view
  overflow-x: hidden;            // 禁止横向滚动条
  overflow-y: auto;              // 内容超出时纵向滚动
  padding-right: 4px;            // 避免滚动条遮挡内容

  // 自定义滚动条
  &::-webkit-scrollbar {
    width: 6px;
  }
  &::-webkit-scrollbar-thumb {
    background: $border-base;
    border-radius: 3px;
  }
  &::-webkit-scrollbar-thumb:hover {
    background: $text-placeholder;
  }
}

// ========== 欢迎区（优化：渐变背景 + 4 个快捷操作） ==========
.welcome {
  display: flex;
  align-items: center;
  justify-content: space-between;
  // 关键：渐变背景作为视觉锚点
  padding: 24px 28px;
  background: linear-gradient(135deg, #eef2ff 0%, #eff6ff 50%, #f0fdf4 100%);
  border: 1px solid rgba(99, 102, 241, 0.1);
  border-radius: $radius-lg;
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.04);

  .welcome-text {
    flex: 1;
  }

  .welcome-title {
    margin: 0;
    font-size: 26px;
    font-weight: 700;
    color: $gray-900;
    line-height: 1.3;
    // 关键：文字渐变效果
    background: linear-gradient(135deg, #1e293b, #4338ca);
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
  }

  .welcome-sub {
    margin: 6px 0 0;
    font-size: $font-size-sm;
    color: $text-secondary;
  }

  .welcome-greeting {
    margin-top: 10px;
  }

  // ========== 关键：4 个快捷操作（圆形按钮） ==========
  .quick-actions {
    display: flex;
    gap: 16px;
    flex-shrink: 0;
  }

  .quick-action {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6px;
    padding: 12px 16px;
    border-radius: $radius-md;
    cursor: pointer;
    transition: $transition-base;
    min-width: 88px;

    .qa-icon {
      width: 40px;
      height: 40px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: rgba(255, 255, 255, 0.7);
      border-radius: 50%;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.06);
      transition: $transition-base;
    }

    .qa-label {
      font-size: 12px;
      font-weight: 500;
    }

    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);

      .qa-icon {
        transform: scale(1.1);
      }
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

// ========== 统计卡片（升级：横向布局 + sparkline 趋势线 + 同比指示） ==========
.stat-row {
  margin-bottom: 0;
}

// 关键：升级数据看板样式（参考 SaaS 指标看板：主指标 + 趋势线 + 3 个子指标网格）
.stat-card {
  background: $bg-card;
  border: 1px solid $border-base;
  border-radius: $radius-lg;
  box-shadow: $shadow-sm;
  padding: 16px 18px;
  transition: $transition-base;
  margin-bottom: $spacing-lg;
  position: relative;
  overflow: hidden;
  min-height: 180px;

  // 关键：顶部装饰色条（与主卡片颜色一致）
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, var(--card-color, #6366f1), transparent);
  }

  &:hover {
    box-shadow: $shadow-md;
    border-color: rgba(99, 102, 241, 0.3);
    transform: translateY(-2px);
  }

  // 关键：头部（图标 + 标题 + 主数值 + 同比）
  .stat-head {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    margin-bottom: 12px;
  }

  .stat-head__left {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  // 图标
  .stat-icon {
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: $radius-md;
    font-size: 20px;
    flex-shrink: 0;
  }

  // 标题 + 主数值（紧贴图标右侧）
  .stat-label {
    font-size: 12px;
    color: $text-secondary;
    margin-bottom: 2px;
    font-weight: 600;
  }

  .stat-value {
    font-size: 24px;
    font-weight: 700;
    color: $gray-900;
    line-height: 1.1;

    .stat-unit {
      font-size: $font-size-sm;
      font-weight: 500;
      margin-left: 2px;
      color: $text-secondary;
    }
  }

  // 关键：同比趋势标签
  .stat-trend {
    display: inline-flex;
    align-items: center;
    gap: 2px;
    padding: 3px 8px;
    font-size: 11px;
    font-weight: 700;
    border-radius: $radius-sm;

    &.trend--up {
      color: #16a34a;
      background: rgba(22, 163, 74, 0.1);
    }
    &.trend--down {
      color: #16a34a;
      background: rgba(22, 163, 74, 0.1);
    }
  }

  // 关键：sparkline 趋势线（SVG）
  .stat-sparkline {
    height: 32px;
    margin-bottom: 6px;

    svg {
      width: 100%;
      height: 100%;
    }
  }

  .stat-sub {
    font-size: 11px;
    color: $text-placeholder;
    margin-bottom: 12px;
  }

  // 关键：3 个子指标网格（水平 3 等分）
  .stat-mini-grid {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 8px;
    padding-top: 12px;
    border-top: 1px dashed $border-light;
  }

  // 单个子指标
  .mini-stat {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 6px 8px;
    border-radius: $radius-sm;
    background: rgba(99, 102, 241, 0.02);
    transition: $transition-base;

    &:hover {
      background: rgba(99, 102, 241, 0.06);
    }
  }

  .mini-stat__icon {
    width: 22px;
    height: 22px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 4px;
    font-size: 12px;
    flex-shrink: 0;
  }

  .mini-stat__body {
    min-width: 0;
    flex: 1;
  }

  .mini-stat__label {
    font-size: 10px;
    color: $text-secondary;
    line-height: 1.2;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .mini-stat__value {
    font-size: 12px;
    font-weight: 700;
    color: $gray-900;
    line-height: 1.3;

    .mini-stat__unit {
      font-size: 10px;
      font-weight: 500;
      color: $text-secondary;
      margin-left: 1px;
    }
  }
}

// ========== section 标题（原型：text-xl font-bold text-gray-900 mb-4） ==========
.section-block {
  display: flex;
  flex-direction: column;
  // 关键：在分栏布局中拉伸填满，让左右等高
  flex: 1;
}

.section-title {
  margin: 0;
  font-size: $font-size-xl;
  font-weight: 700;
  color: $gray-900;
  position: relative;
  padding-left: 12px;

  // 关键：左侧装饰条
  &::before {
    content: '';
    position: absolute;
    left: 0;
    top: 4px;
    bottom: 4px;
    width: 4px;
    border-radius: 2px;
    background: linear-gradient(180deg, #6366f1, #4f46e5);
  }
}

// 关键：section 头部（左标题 + 右"查看全部"按钮）
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: $spacing-lg;
}

// ========== 关键：2 列分栏布局（左侧 2/3 + 右侧 1/3） ==========
// 关键：参考 Linear / Notion / Figma 主页用分栏提升信息密度
// 关键：align-items: stretch（默认）让两边等高，避免底部空白
// 移动端自动堆叠为单列
.dashboard-split {
  display: grid;
  // 关键：从 2fr:1fr 改为 1.6fr:1fr，让右列（最近生成）更宽
  grid-template-columns: minmax(0, 1.6fr) minmax(0, 1fr);
  gap: $spacing-lg;
  align-items: stretch;        // 关键：两列等高（默认），消除底部空白

  @media (max-width: 992px) {
    grid-template-columns: 1fr;
  }
}

.dashboard-split__left,
.dashboard-split__right {
  min-width: 0;  // 防止 grid item 撑开
  display: flex;              // 关键：让子元素也能拉伸
  flex-direction: column;      // 关键：垂直堆叠
}

// 关键：左列右分界线（与系统 $border-light 一致，移动端隐藏）
.dashboard-split__left {
  // 关键：右侧加分界线（参考 Notion 风格）
  border-right: 1px dashed $border-light;
  padding-right: $spacing-lg;  // 关键：内容与分界线留间距

  @media (max-width: 992px) {
    border-right: none;       // 移动端隐藏分界线
    padding-right: 0;
  }
}

// 关键：右列内部时间线/列表/网格随高度自适应
.dashboard-split__right {
  // 关键：让右列与左列等高
  height: 100%;
}

// ========== 营销场景（重构 V2：分类筛选 + 5 卡片网格） ==========
// 关键：参考 Notion 模板中心 / Figma Community，统一 5 卡片视觉

// 关键：合并 toolbar（分类筛选 + 排序，节省垂直空间）
// 关键：不再独占一行，与 section-title 同一行排列
.section-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: $spacing-md;       // 关键：减少下边距
}

.section-toolbar__right {
  display: flex;
  align-items: center;
  gap: 12px;
}

// 关键：5 卡片统一网格（auto-fill 自动适配）
// 关键：减少 gap，让左列更紧凑
.scenes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 10px;                        // 关键：gap 从 $spacing-md（16px）缩小到 10px
}

// 关键：统一场景卡片
.scene-card {
  display: flex;
  flex-direction: column;
  background: $bg-card;
  border: 1px solid $border-light;
  border-radius: $radius-lg;
  cursor: pointer;
  transition: $transition-base;
  overflow: hidden;

  &:hover {
    border-color: rgba(99, 102, 241, 0.3);
    box-shadow: $shadow-md;
    transform: translateY(-2px);

    .scene-use-btn {
      background: $primary-color;
      color: #fff;
    }
    .thumb-decoration--1 {
      transform: scale(1.3);
    }
    .thumb-decoration--2 {
      transform: scale(1.4);
    }
  }
}

// 关键：缩略图
.scene-thumb {
  position: relative;
  height: 76px;              // 关键：缩略图从 100px → 76px（更紧凑）
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.thumb-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 3px;
  width: 60%;
  height: 60%;
  z-index: 1;
}

.thumb-cell {
  background: rgba(255, 255, 255, 0.3);
  border-radius: 2px;
  animation: thumb-pulse 2s ease-in-out infinite;

  &:nth-child(2) { animation-delay: 0.3s; }
  &:nth-child(3) { animation-delay: 0.6s; }
  &:nth-child(4) { animation-delay: 0.9s; }
}

@keyframes thumb-pulse {
  0%, 100% { opacity: 0.5; }
  50% { opacity: 0.9; }
}

.thumb-decoration {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.15);
  transition: transform 0.6s ease;
  pointer-events: none;

  &--1 {
    top: -30px;
    right: -30px;
    width: 80px;
    height: 80px;
  }
  &--2 {
    bottom: -40px;
    left: -20px;
    width: 100px;
    height: 100px;
    background: rgba(255, 255, 255, 0.1);
  }
}

// 关键：排名徽章（#1 主力）
.thumb-rank {
  position: absolute;
  top: 8px;
  left: 8px;
  display: inline-flex;
  align-items: center;
  gap: 2px;
  padding: 2px 6px;
  background: rgba(0, 0, 0, 0.25);
  color: #fff;
  border-radius: $radius-sm;
  font-size: 10px;
  font-weight: 700;
  z-index: 2;
  backdrop-filter: blur(10px);
}

// 关键：使用次数角标
.thumb-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  display: inline-flex;
  align-items: center;
  gap: 2px;
  padding: 2px 6px;
  background: rgba(255, 255, 255, 0.9);
  color: $gray-900;
  border-radius: $radius-sm;
  font-size: 10px;
  font-weight: 700;
  z-index: 2;
}

// 关键：卡片主体
.scene-body {
  padding: 10px 12px 12px;    // 关键：减少 padding（更紧凑）
  display: flex;
  flex-direction: column;
  flex: 1;
}

.scene-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.scene-icon {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: $radius-sm;
  font-size: 14px;
  flex-shrink: 0;
}

.scene-title {
  flex: 1;
  font-size: 14px;
  font-weight: 700;
  color: $gray-900;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  min-width: 0;
}

// 收藏按钮
.scene-fav {
  flex-shrink: 0;
  padding: 0;
  color: $text-placeholder;

  &:hover {
    color: #f59e0b;
  }
}

.scene-desc {
  font-size: 12px;
  color: $text-secondary;
  line-height: 1.5;
  margin-bottom: 8px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  min-height: 36px;
}

.scene-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: 10px;
  min-height: 20px;
}

.scene-tag {
  padding: 2px 8px;
  font-size: 10px;
  font-weight: 600;
  border-radius: $radius-sm;
  line-height: 1.4;
}

// 关键：底部信息行（模板数 + 评分 + 使用按钮）
.scene-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 10px;
  border-top: 1px dashed $border-light;
  margin-top: auto;
}

.scene-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: $text-secondary;

  .meta-item {
    display: inline-flex;
    align-items: center;
    gap: 2px;
    font-weight: 600;
  }

  .meta-divider {
    color: $text-placeholder;
  }
}

// 关键：使用按钮（始终可见，hover 时高亮）
.scene-use-btn {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  padding: 4px 10px;
  background: rgba(99, 102, 241, 0.08);
  color: $primary-color;
  border: none;
  border-radius: $radius-sm;
  font-size: 11px;
  font-weight: 700;
  cursor: pointer;
  transition: $transition-base;
}

// 关键：骨架屏
.scenes-loading-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: $spacing-md;
}

.scene-card-skeleton {
  display: flex;
  flex-direction: column;
  background: $bg-card;
  border: 1px solid $border-light;
  border-radius: $radius-lg;
  overflow: hidden;
}

.skeleton-thumbnail {
  height: 100px;
  background: linear-gradient(90deg, #f0f0f0 0%, #f8f8f8 50%, #f0f0f0 100%);
  background-size: 200px 100%;
  animation: skeleton-shimmer 1.5s ease-in-out infinite;
}

.skeleton-line {
  background: linear-gradient(90deg, #f0f0f0 0%, #f8f8f8 50%, #f0f0f0 100%);
  background-size: 200px 100%;
  animation: skeleton-shimmer 1.5s ease-in-out infinite;
  border-radius: 4px;
  margin: 6px 14px;

  &--title {
    height: 14px;
    width: 60%;
    margin-top: 14px;
  }
  &--desc {
    height: 10px;
    width: 90%;
  }
  &--meta {
    height: 10px;
    width: 40%;
    margin-bottom: 14px;
  }
}

// ========== 常用模板卡片（保留兼容：旧代码可能还在引用） ==========
.tpl-card {
  background: $bg-card;
  border: 2px solid transparent;
  border-radius: $radius-lg;
  box-shadow: $shadow-sm;
  padding: 20px;
  cursor: pointer;
  transition: $transition-base;
  margin-bottom: $spacing-lg;
  position: relative;
  overflow: hidden;

  &:hover {
    border-color: $primary-color;
    box-shadow: $shadow-md;
    transform: translateY(-3px);

    .tpl-arrow {
      opacity: 1;
      transform: translateX(0);
    }
  }

  .tpl-card__head {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    margin-bottom: $spacing-md;
  }

  .tpl-icon {
    width: 44px;
    height: 44px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: $radius-md;
    font-size: 22px;
  }

  .tpl-use-count {
    display: inline-flex;
    align-items: center;
    gap: 2px;
    padding: 2px 8px;
    font-size: 11px;
    font-weight: 600;
    color: $text-secondary;
    background: rgba(99, 102, 241, 0.08);
    border-radius: $radius-round;
  }

  .tpl-name {
    font-size: $font-size-lg;
    font-weight: 600;
    color: $gray-900;
    margin-bottom: $spacing-sm;
  }

  .tpl-desc {
    font-size: $font-size-sm;
    color: $text-secondary;
    margin-bottom: $spacing-md;
    line-height: 1.5;
  }

  .tpl-progress {
    height: 4px;
    background: $border-light;
    border-radius: 2px;
    margin-bottom: $spacing-md;
    overflow: hidden;

    &__bar {
      height: 100%;
      border-radius: 2px;
      transition: width 0.6s ease;
    }
  }

  .tpl-tags {
    display: flex;
    flex-wrap: wrap;
    gap: $spacing-sm;
  }

  .tpl-tag {
    padding: 4px 12px;
    font-size: $font-size-xs;
    border-radius: $radius-round;
    line-height: 1.2;
  }

  .tpl-arrow {
    position: absolute;
    right: 20px;
    bottom: 20px;
    color: $primary-color;
    opacity: 0;
    transform: translateX(-8px);
    transition: $transition-base;
  }

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

// ========== 最近生成（重构：时间分组 + 视图切换 + 状态筛选） ==========
// 关键：顶部工具栏
.recent-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 8px;        // 关键：减少下边距（节省垂直空间）
  padding: 8px 12px;          // 关键：减少 padding
  background: $bg-card;
  border: 1px solid $border-light;
  border-radius: $radius-lg;
}

// 关键：状态筛选组（嵌入工具栏内，无需独占一行）
.recent-filter-row {
  display: flex;
}

// 关键：状态筛选容器
.recent-stats {
  display: flex;
  align-items: center;
  gap: 8px;
}

.recent-controls {
  display: flex;
  align-items: center;
  gap: 12px;
}

// ========== 时间线视图（参考 Notion） ==========
.recent-timeline {
  display: flex;
  flex-direction: column;
  gap: 4px;
  // 关键：右列自适应高度，内容多时滚动，避免超出左列
  max-height: 600px;
  overflow-y: auto;
  padding-right: 4px;

  // 关键：自定义滚动条样式
  &::-webkit-scrollbar {
    width: 6px;
  }
  &::-webkit-scrollbar-thumb {
    background: $border-base;
    border-radius: 3px;
  }
  &::-webkit-scrollbar-thumb:hover {
    background: $text-placeholder;
  }
}

.timeline-group {
  &__header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 12px 0 8px;
  }

  // 关键：圆点
  .timeline-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: linear-gradient(135deg, #6366f1, #4f46e5);
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15);
    flex-shrink: 0;
  }

  .timeline-label {
    font-size: 13px;
    font-weight: 700;
    color: $gray-900;
  }

  .timeline-count {
    font-size: 11px;
    color: $text-secondary;
    padding: 2px 8px;
    background: $border-light;
    border-radius: $radius-round;
  }

  // 关键：右侧延伸的虚线
  .timeline-line {
    flex: 1;
    height: 1px;
    background-image: linear-gradient(to right, $border-base 50%, transparent 50%);
    background-size: 6px 1px;
  }
}

.timeline-item {
  display: grid;
  grid-template-columns: 50px 4px 32px 1fr auto auto;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  margin-left: 5px;
  background: $bg-card;
  border-radius: $radius-md;
  cursor: pointer;
  transition: $transition-base;

  &:hover {
    background: rgba(99, 102, 241, 0.03);
    transform: translateX(2px);

    .timeline-action {
      opacity: 1;
    }
  }

  // 关键：左侧时分
  .timeline-time {
    font-size: 11px;
    font-family: 'SF Mono', Consolas, monospace;
    font-weight: 600;
    color: $text-secondary;
    text-align: right;
  }

  // 关键：彩色状态条
  .timeline-bar {
    width: 3px;
    height: 24px;
    border-radius: 2px;
  }

  // 状态条颜色
  &--success .timeline-bar { background: #16a34a; }
  &--running .timeline-bar { background: #f59e0b; }
  &--failed .timeline-bar { background: #dc2626; }
  &--cancelled .timeline-bar { background: #6b7280; }

  .timeline-icon {
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: $radius-md;
    font-size: 16px;
  }

  .timeline-content {
    min-width: 0;

    .timeline-title {
      font-size: 13px;
      font-weight: 600;
      color: $gray-900;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .timeline-meta {
      margin-top: 2px;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .timeline-duration {
      display: inline-flex;
      align-items: center;
      gap: 2px;
      font-size: 11px;
      color: $text-secondary;
    }
  }

  .timeline-action {
    opacity: 0;
    transition: $transition-base;
  }
}

// ========== 列表视图 ==========
.recent-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  // 关键：右列自适应高度（与 .recent-timeline 一致）
  max-height: 600px;
  overflow-y: auto;
  padding-right: 4px;
}

.list-item {
  position: relative;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  background: $bg-card;
  border: 1px solid $border-light;
  border-radius: $radius-md;
  cursor: pointer;
  transition: $transition-base;

  &:hover {
    border-color: rgba(99, 102, 241, 0.3);
    transform: translateX(2px);
  }

  .list-bar {
    position: absolute;
    left: 0;
    top: 8px;
    bottom: 8px;
    width: 3px;
    border-radius: 0 2px 2px 0;
  }

  &--success .list-bar { background: #16a34a; }
  &--running .list-bar { background: #f59e0b; }
  &--failed .list-bar { background: #dc2626; }
  &--cancelled .list-bar { background: #6b7280; }

  .list-icon {
    width: 28px;
    height: 28px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: $radius-sm;
    font-size: 14px;
    flex-shrink: 0;
  }

  .list-content {
    flex: 1;
    min-width: 0;

    .list-title {
      font-size: 13px;
      font-weight: 600;
      color: $gray-900;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .list-sub {
      font-size: 11px;
      color: $text-secondary;
      margin-top: 2px;
      display: flex;
      align-items: center;
      gap: 4px;
    }

    .list-duration {
      display: inline-flex;
      align-items: center;
      gap: 2px;
    }
  }
}

// ========== 网格视图 ==========
.recent-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 12px;
}

.grid-card {
  position: relative;
  padding: 14px;
  background: $bg-card;
  border: 1px solid $border-light;
  border-radius: $radius-lg;
  cursor: pointer;
  transition: $transition-base;
  overflow: hidden;

  &:hover {
    border-color: rgba(99, 102, 241, 0.3);
    transform: translateY(-2px);
    box-shadow: $shadow-md;
  }

  .grid-bar {
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 3px;
  }

  &--success .grid-bar { background: #16a34a; }
  &--running .grid-bar { background: #f59e0b; }
  &--failed .grid-bar { background: #dc2626; }
  &--cancelled .grid-bar { background: #6b7280; }

  .grid-icon {
    width: 36px;
    height: 36px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: $radius-md;
    font-size: 18px;
    margin-bottom: 8px;
  }

  .grid-title {
    font-size: 14px;
    font-weight: 600;
    color: $gray-900;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .grid-template {
    font-size: 11px;
    color: $text-secondary;
    margin-top: 2px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .grid-foot {
    margin-top: 10px;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
}

// ========== 最近生成（升级：卡片网格 + 彩色状态条 + 耗时徽章） ==========
// 关键：3 列网格布局，每张卡片左侧有彩色状态条
.recent-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: $spacing-md;
}

.recent-card {
  position: relative;
  display: flex;
  flex-direction: column;
  padding: 16px 18px 14px;
  background: $bg-card;
  border: 1px solid $border-base;
  border-radius: $radius-lg;
  box-shadow: $shadow-sm;
  cursor: pointer;
  transition: $transition-base;
  overflow: hidden;

  &:hover {
    box-shadow: $shadow-md;
    border-color: rgba(99, 102, 241, 0.3);
    transform: translateY(-2px);

    .recent-card__bar {
      width: 4px;
    }
    .recent-actions {
      opacity: 1;
    }
  }

  // 关键：左侧彩色状态条（3px → 4px on hover）
  .recent-card__bar {
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 3px;
    transition: width $transition-base;
  }

  // 状态条颜色（按状态变化）
  &--success .recent-card__bar {
    background: linear-gradient(180deg, #16a34a, #15803d);
  }
  &--running .recent-card__bar {
    background: linear-gradient(180deg, #f59e0b, #d97706);
  }
  &--failed .recent-card__bar {
    background: linear-gradient(180deg, #dc2626, #b91c1c);
  }
  &--cancelled .recent-card__bar {
    background: linear-gradient(180deg, #6b7280, #4b5563);
  }

  // 头部：图标 + 耗时
  .recent-card__head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;
  }

  .recent-icon {
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: $radius-md;
    font-size: 20px;
    flex-shrink: 0;
  }

  // 关键：耗时徽章（右上角）
  .recent-duration {
    display: inline-flex;
    align-items: center;
    gap: 2px;
    padding: 2px 8px;
    font-size: 11px;
    font-weight: 600;
    color: $text-secondary;
    background: rgba(99, 102, 241, 0.08);
    border-radius: $radius-round;
  }

  // 主体：标题 + 模板 + 时间
  .recent-card__body {
    flex: 1;
    min-width: 0;
    margin-bottom: 12px;
  }

  .recent-title {
    font-size: 15px;
    font-weight: 600;
    color: $gray-900;
    margin-bottom: 6px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .recent-template {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 12px;
    color: $text-regular;
    margin-bottom: 4px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 100%;

    span {
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
  }

  .recent-time {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 11px;
    color: $text-secondary;
  }

  // 底部：状态 + 操作
  .recent-card__foot {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding-top: 10px;
    border-top: 1px dashed $border-light;
  }

  // 关键：操作按钮容器（默认半透明，hover 时高亮）
  .recent-actions {
    flex-shrink: 0;
    opacity: 0.6;
    transition: $transition-base;
  }
}

// ========== NEW: 产品动态 ==========
.product-activity-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 10px;
}

.product-activity-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: $bg-card;
  border: 1px solid $border-light;
  border-radius: $radius-md;
  cursor: pointer;
  transition: $transition-base;

  &:hover {
    border-color: rgba(99, 102, 241, 0.3);
    box-shadow: $shadow-sm;
    transform: translateY(-1px);

    .product-activity__arrow {
      color: $primary-color;
      transform: translateX(2px);
    }
  }

  .product-activity__icon {
    width: 36px;
    height: 36px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: $radius-md;
    background: #eff6ff;
    color: #2563eb;
    flex-shrink: 0;
  }

  .product-activity__body {
    flex: 1;
    min-width: 0;
  }

  .product-activity__name {
    font-size: 13px;
    font-weight: 600;
    color: $gray-900;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .product-activity__meta {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-top: 3px;
  }

  .pa-category {
    font-size: 11px;
    padding: 1px 8px;
    background: #f0fdf4;
    color: #16a34a;
    border-radius: $radius-round;
  }

  .pa-time {
    font-size: 11px;
    color: $text-placeholder;
  }

  .product-activity__arrow {
    color: $text-placeholder;
    transition: $transition-base;
    flex-shrink: 0;
  }
}

// ========== NEW: 质量评分 + 资产统计 ==========
.analytics-row {
  margin-bottom: 0;
}

.analytics-row {
  align-items: stretch; // 关键：让两列等高

  .el-col {
    display: flex;
  }
}

.analytics-card {
  background: $bg-card;
  border: 1px solid $border-base;
  border-radius: $radius-lg;
  box-shadow: $shadow-sm;
  padding: 16px 18px;
  margin-bottom: $spacing-lg;
  width: 100%;
  display: flex;
  flex-direction: column;

  &__header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 16px;
  }

  &__title {
    margin: 0;
    font-size: 15px;
    font-weight: 700;
    color: $gray-900;
  }

  &__sub {
    font-size: 12px;
    color: $text-secondary;
  }
}

// 质量评分
.quality-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 18px;
}

.quality-ring {
  position: relative;
  width: 110px;
  height: 110px;
  flex-shrink: 0;

  .ring-svg {
    width: 100%;
    height: 100%;
  }

  .ring-center {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    text-align: center;
  }

  .ring-score {
    font-size: 26px;
    font-weight: 700;
    color: $gray-900;
    line-height: 1;
  }

  .ring-label {
    font-size: 11px;
    color: $text-placeholder;
    margin-top: 2px;
  }
}

.quality-bars {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.quality-bar-item {
  // 每个柱状项
}

.quality-bar__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 5px;
}

.quality-bar__label {
  font-size: 12px;
  font-weight: 600;
  color: $text-regular;
  display: flex;
  align-items: center;
  gap: 6px;
}

.quality-bar__dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.quality-bar__count {
  font-size: 11px;
  color: $text-secondary;
}

.quality-bar__track {
  height: 8px;
  background: $border-light;
  border-radius: 4px;
  overflow: hidden;
}

.quality-bar__fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.6s ease;
}

// 资产统计
.asset-body {
  flex: 1;

  .asset-empty {
    text-align: center;
    color: $text-placeholder;
    padding: 20px 0;
    font-size: 13px;
  }

  .asset-bars {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .asset-bar-item {
    // 每个柱状项
  }

  .asset-bar__head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 5px;
  }

  .asset-bar__label {
    font-size: 12px;
    font-weight: 600;
    color: $text-regular;
  }

  .asset-bar__count {
    font-size: 11px;
    color: $text-secondary;
  }

  .asset-bar__track {
    height: 8px;
    background: $border-light;
    border-radius: 4px;
    overflow: hidden;
  }

  .asset-bar__fill {
    height: 100%;
    border-radius: 4px;
    transition: width 0.6s ease;
  }
}

// ========== NEW: 系统公告 / 使用小贴士 ==========
.notice-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  background: $bg-card;
  border: 1px solid $border-light;
  border-radius: $radius-md;
  box-shadow: $shadow-sm;
  min-height: 48px;

  &__icon {
    width: 28px;
    height: 28px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: $radius-sm;
    flex-shrink: 0;
  }

  &__content {
    flex: 1;
    display: flex;
    align-items: center;
    gap: 10px;
    min-width: 0;
    overflow: hidden;
  }

  &__tag {
    font-size: 11px;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: $radius-sm;
    flex-shrink: 0;
    line-height: 1.4;
  }

  &__text {
    font-size: 13px;
    color: $text-regular;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  &__dots {
    display: flex;
    gap: 5px;
    flex-shrink: 0;
    padding-left: 8px;
  }
}

.notice-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: $border-base;
  cursor: pointer;
  transition: $transition-base;

  &--active {
    background: $primary-color;
    width: 16px;
    border-radius: 3px;
  }
}

// 轮播过渡动画
.notice-slide-enter-active,
.notice-slide-leave-active {
  transition: all 0.3s ease;
}
.notice-slide-enter-from {
  opacity: 0;
  transform: translateX(12px);
}
.notice-slide-leave-to {
  opacity: 0;
  transform: translateX(-12px);
}

.empty-tip {
  padding: $spacing-2xl 0;
  text-align: center;
  color: $text-secondary;
  font-size: $font-size-sm;
}
</style>
