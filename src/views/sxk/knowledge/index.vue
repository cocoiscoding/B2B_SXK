<!--
  神行库 · 产品知识库
  对应需求文档 5.2（US001/002/003/004/005/006/018）：
    - 标题 + 添加/批量导入按钮
    - 搜索 + 分类筛选（BR-K-07/08）
    - 统计区（产品总数）
    - 卡片列表（最多展示 3 个卖点，BR-K-02）
    - 添加/编辑/删除/详情（5.2.3）
-->
<template>
  <div class="sxk-knowledge">
    <!-- ========== 顶部头：标题 + 按钮 ========== -->
    <basic-block>
      <div class="page-header">
        <div class="page-header__title">
          <h2>产品知识库</h2>
          <p>上传并解析产品文档，为 AI Agent 提供精准的事实依据</p>
        </div>
        <div class="page-header__actions">
          <el-button @click="onImport">
            <el-icon><Upload /></el-icon>
            <span>批量导入</span>
          </el-button>
          <el-button type="primary" @click="onAdd">
            <el-icon><Plus /></el-icon>
            <span>添加产品</span>
          </el-button>
        </div>
      </div>
    </basic-block>

    <!-- ========== 搜索 + 分类 ========== -->
    <basic-block>
      <div class="search-bar">
        <el-input
          v-model="filters.keyword"
          placeholder="按名称 / 分类 / 描述 / 卖点搜索（回车触发）"
          clearable
          style="max-width: 420px"
          @keyup.enter="search"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>

        <el-select
          v-model="filters.category"
          placeholder="全部分类"
          clearable
          style="width: 180px"
          @change="search"
        >
          <el-option label="全部分类" value="" />
          <el-option label="数据分析" value="数据分析" />
          <el-option label="CRM" value="CRM" />
          <el-option label="营销自动化" value="营销自动化" />
          <el-option label="其他" value="其他" />
        </el-select>

        <el-button type="primary" @click="search">搜索</el-button>
        <el-button @click="resetSearch">重置</el-button>

        <span class="stat-pill">共 <b>{{ total }}</b> 个产品</span>
      </div>
    </basic-block>

    <!-- ========== 统计卡片区（5.2.2）========== -->
    <!-- 用 CSS Grid auto-fit 让卡片数变化时自动平均铺满，不产生尾部空白 -->
    <div class="cat-grid" v-if="stats">
      <!-- 产品总数：品牌蓝高亮 -->
      <div class="cat-card cat-card--total">
        <div class="cat-card__icon">
          <el-icon><Box /></el-icon>
        </div>
        <div class="cat-card__body">
          <div class="cat-card__value">{{ stats.total }}</div>
          <div class="cat-card__label">产品总数</div>
        </div>
      </div>
      <!-- 各分类：按类目动态配色 -->
      <div
        v-for="cat in categoryStatList"
        :key="cat.name"
        class="cat-card"
        :style="cat.style"
      >
        <div class="cat-card__icon">
          <el-icon><component :is="cat.icon" /></el-icon>
        </div>
        <div class="cat-card__body">
          <div class="cat-card__value">{{ cat.count }}</div>
          <div class="cat-card__label">{{ cat.name }}</div>
        </div>
      </div>
    </div>

    <!-- ========== 产品列表 ========== -->
    <basic-block>
      <template #header>
        产品列表
        <el-tag v-if="filters.keyword" type="info" effect="plain" size="small" style="margin-left: 8px">
          关键词高亮：{{ filters.keyword }}
        </el-tag>
      </template>

      <div v-if="loading" class="loading">
        <el-icon class="rotating"><Loading /></el-icon>
        加载中...
      </div>

      <div v-else-if="list.length === 0" class="empty">
        <el-icon style="font-size: 48px; color: var(--el-text-color-placeholder)"><Search /></el-icon>
        <p>未找到匹配的产品</p>
      </div>

      <el-row :gutter="16" v-else>
        <el-col
          :xs="24"
          :sm="12"
          :md="8"
          :lg="6"
          v-for="item in list"
          :key="item.product_id"
        >
          <div class="product-card" :class="{ 'product-card--deleted': item.is_deleted }">
            <div class="product-card__head">
              <span class="product-name" v-html="highlight(item.name)" />
              <el-tag
                :type="categoryTagType(item.category)"
                effect="light"
                size="small"
              >
                {{ item.category }}
              </el-tag>
            </div>

            <div class="product-desc" v-html="highlight(item.description)" />

            <div class="selling-points">
              <el-tag
                v-for="sp in item.selling_points.slice(0, 3)"
                :key="sp"
                size="small"
                effect="plain"
                round
              >
                {{ sp }}
              </el-tag>
              <span
                v-if="item.selling_points.length > 3"
                class="selling-points__more"
              >
                +{{ item.selling_points.length - 3 }}
              </span>
            </div>

            <div class="product-card__foot">
              <span class="updated-at">
                更新于 {{ formatDate(item.updated_at) }}
              </span>
              <div class="actions">
                <el-button link type="primary" @click="onDetail(item)">查看</el-button>
                <el-button
                  link
                  type="primary"
                  :disabled="item.is_deleted"
                  @click="onEdit(item)"
                >编辑</el-button>
                <el-popconfirm
                  :title="`确定删除「${item.name}」吗？`"
                  confirm-button-text="确认删除"
                  @confirm="onDelete(item)"
                >
                  <template #reference>
                    <el-button
                      link
                      type="danger"
                      :disabled="item.is_deleted"
                    >删除</el-button>
                  </template>
                </el-popconfirm>
              </div>
            </div>
          </div>
        </el-col>
      </el-row>

      <!-- ========== 分页（BR-K-12） ========== -->
      <el-pagination
        v-model:current-page="pager.page"
        v-model:page-size="pager.size"
        :total="total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next, jumper"
        background
        class="pager"
        @current-change="loadList"
        @size-change="loadList"
      />
    </basic-block>

    <!-- ========== 弹窗：添加/编辑产品 ========== -->
    <product-edit-modal
      v-model="editVisible"
      :product-id="editTargetId"
      @saved="loadList"
    />

    <!-- ========== 弹窗：产品详情 ========== -->
    <el-dialog
      v-model="detailVisible"
      width="720px"
      top="6vh"
      destroy-on-close
      class="sxk-detail-dialog"
    >
      <template #header>
        <div class="detail-dialog__title">
          <el-icon class="title-icon"><Box /></el-icon>
          <span class="title-text">{{ detailTarget?.name || '产品详情' }}</span>
        </div>
      </template>

      <div v-if="detailTarget" class="product-detail">
        <!-- 顶部摘要条：分类 + 价格 + 更新时间 -->
        <div class="detail-summary">
          <div class="summary-item">
            <el-tag
              :type="categoryTagType(detailTarget.category)"
              effect="light"
              size="small"
            >{{ detailTarget.category || '未分类' }}</el-tag>
          </div>
          <div class="summary-item">
            <el-icon><Wallet /></el-icon>
            <span class="summary-label">价格</span>
            <span class="summary-value">{{ detailTarget.pricing || '—' }}</span>
          </div>
          <div class="summary-item">
            <el-icon><Clock /></el-icon>
            <span class="summary-label">更新</span>
            <span class="summary-value">{{ formatDate(detailTarget.updated_at) }}</span>
          </div>
        </div>

        <!-- 产品描述 -->
        <section class="detail-section">
          <div class="section-title">
            <el-icon><Document /></el-icon>
            <span>产品描述</span>
          </div>
          <p class="section-text">{{ detailTarget.description || '暂无描述' }}</p>
        </section>

        <!-- 功能特性（卡片式） -->
        <section class="detail-section" v-if="detailTarget.features?.length">
          <div class="section-title">
            <el-icon><Operation /></el-icon>
            <span>功能特性</span>
            <span class="section-count">{{ detailTarget.features.length }} 项</span>
          </div>
          <div class="feature-grid">
            <div
              v-for="(f, idx) in detailTarget.features"
              :key="f.name"
              class="feature-card"
            >
              <div class="feature-card__index">{{ idx + 1 }}</div>
              <div class="feature-card__body">
                <div class="feature-card__name">{{ f.name }}</div>
                <div class="feature-card__desc">{{ f.description || '—' }}</div>
              </div>
            </div>
          </div>
        </section>

        <!-- 目标客户 & 竞品（两列） -->
        <el-row :gutter="16">
          <el-col :span="12">
            <section class="detail-section">
              <div class="section-title">
                <el-icon><User /></el-icon>
                <span>目标客户</span>
              </div>
              <div v-if="detailTarget.target_customers?.length" class="tag-group">
                <el-tag
                  v-for="t in detailTarget.target_customers"
                  :key="t"
                  type="info"
                  effect="plain"
                >{{ t }}</el-tag>
              </div>
              <span v-else class="empty-text">暂无</span>
            </section>
          </el-col>
          <el-col :span="12">
            <section class="detail-section">
              <div class="section-title">
                <el-icon><Aim /></el-icon>
                <span>竞品</span>
              </div>
              <div v-if="detailTarget.competitors?.length" class="tag-group">
                <el-tag
                  v-for="c in detailTarget.competitors"
                  :key="c"
                  type="warning"
                  effect="plain"
                >{{ c }}</el-tag>
              </div>
              <span v-else class="empty-text">暂无</span>
            </section>
          </el-col>
        </el-row>

        <!-- 核心卖点 -->
        <section class="detail-section" v-if="detailTarget.selling_points?.length">
          <div class="section-title">
            <el-icon><Star /></el-icon>
            <span>核心卖点</span>
          </div>
          <div class="tag-group">
            <el-tag
              v-for="s in detailTarget.selling_points"
              :key="s"
              type="success"
              effect="light"
            >{{ s }}</el-tag>
          </div>
        </section>

        <!-- 元信息 -->
        <section class="detail-section detail-section--meta">
          <div class="section-title">
            <el-icon><InfoFilled /></el-icon>
            <span>元信息</span>
          </div>
          <div class="meta-grid">
            <div class="meta-item">
              <span class="meta-label">产品ID</span>
              <span class="meta-value">{{ detailTarget.product_id }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-label">创建时间</span>
              <span class="meta-value">{{ formatDate(detailTarget.created_at) }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-label">状态</span>
              <span class="meta-value">
                <el-tag :type="detailTarget.is_deleted ? 'danger' : 'success'" size="small" effect="plain">
                  {{ detailTarget.is_deleted ? '已下线' : '在售' }}
                </el-tag>
              </span>
            </div>
          </div>
        </section>
      </div>

      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
        <el-button
          type="primary"
          :disabled="detailTarget?.is_deleted"
          @click="onDetailEdit"
        >编辑此产品</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, markRaw, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Upload, Search, Loading, Box, Wallet, Clock, Document, Operation, User, Aim, Star, InfoFilled, TrendCharts, Connection, Promotion, MoreFilled } from '@element-plus/icons-vue'
import sxkApi from '@/mock/sxkApi'
import ProductEditModal from './components/product-edit-modal.vue'

// ========== 状态 ==========
const filters = reactive({ keyword: '', category: '' })
const list = ref([])
const total = ref(0)
const pager = reactive({ page: 1, size: 20 })
const loading = ref(false)
const stats = ref(null)

const editVisible = ref(false)
const editTargetId = ref(null)
const detailVisible = ref(false)
const detailTarget = ref(null)

// ========== 分类 → 图标 / 配色映射 ==========
// 每个分类对应独特图标和主题色，让统计卡片有视觉区分度
const categoryMeta = (cat) => {
  const map = {
    '数据分析': { icon: TrendCharts, color: '#2563eb', bg: '#eff6ff' },   // blue-600 / blue-50
    'CRM': { icon: Connection, color: '#16a34a', bg: '#f0fdf4' },          // green-600 / green-50
    '营销自动化': { icon: Promotion, color: '#9333ea', bg: '#faf5ff' },     // purple-600 / purple-50
    '其他': { icon: MoreFilled, color: '#475569', bg: '#f8fafc' }          // slate-600 / slate-50
  }
  return map[cat] || { icon: Box, color: '#475569', bg: '#f8fafc' }
}

// ========== 计算属性：分类统计卡片列表 ==========
const categoryStatList = computed(() => {
  if (!stats.value?.by_category) return []
  return Object.entries(stats.value.by_category).map(([name, count]) => {
    const meta = categoryMeta(name)
    return {
      name,
      count,
      icon: markRaw(meta.icon),
      // 通过 CSS 自定义属性把颜色注入到 :style，供 .cat-card__icon 使用
      style: { '--cat-color': meta.color, '--cat-bg': meta.bg }
    }
  })
})

// ========== 工具方法 ==========
const categoryTagType = (cat) =>
  ({ 数据分析: 'primary', CRM: 'success', 营销自动化: 'warning', 其他: 'info' })[cat] || 'info'

const formatDate = (iso) => {
  const d = new Date(iso)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

/**
 * BR-K-08：命中关键词在名称/描述中加 <mark> 高亮
 */
const highlight = (text) => {
  if (!text || !filters.keyword) return text || ''
  const kw = filters.keyword
  // 用正则匹配，正则元字符转义
  const escaped = kw.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  const re = new RegExp(escaped, 'gi')
  return String(text).replace(re, (m) => `<mark>${m}</mark>`)
}

// ========== 数据加载 ==========
const loadList = async () => {
  loading.value = true
  const res = await sxkApi.listProducts({
    page: pager.page,
    size: pager.size,
    keyword: filters.keyword,
    category: filters.category
  })
  if (res.data) {
    list.value = res.data.items || []
    total.value = res.data.total || 0
  }
  loading.value = false
}

const loadStats = async () => {
  const res = await sxkApi.getProductStats()
  if (res.data) stats.value = res.data
}

const search = () => {
  pager.page = 1
  loadList()
}

const resetSearch = () => {
  filters.keyword = ''
  filters.category = ''
  search()
}

// ========== 操作回调 ==========
const onAdd = () => {
  editTargetId.value = null
  editVisible.value = true
}

const onEdit = (item) => {
  // F1-2 / US003：编辑现有产品
  editTargetId.value = item.product_id
  editVisible.value = true
}

// 从详情弹窗直接跳到编辑（关闭详情，打开编辑）
const onDetailEdit = () => {
  if (!detailTarget.value) return
  editTargetId.value = detailTarget.value.product_id
  detailVisible.value = false
  editVisible.value = true
}

const onDetail = async (item) => {
  // F1-5 / US006：只读详情
  const res = await sxkApi.getProduct(item.product_id)
  if (res.data) {
    detailTarget.value = res.data
    detailVisible.value = true
  } else {
    ElMessage.error(res.msg || '加载详情失败')
  }
}

const onDelete = async (item) => {
  // F1-2 / US004 / BR-K-06：软删除
  const res = await sxkApi.removeProduct(item.product_id)
  if (res.code === 0) {
    ElMessage.success('已删除')
    loadList()
    loadStats()
  } else {
    ElMessage.error(res.msg || '删除失败')
  }
}

const onImport = () => {
  // US018：批量导入。mock 阶段提示后端待联调，避免误操作
  ElMessage.info('批量导入功能将在后端就绪后开放（US018）')
}

onMounted(() => {
  loadList()
  loadStats()
})
</script>

<style lang="scss" scoped>
.sxk-knowledge {
  display: flex;
  flex-direction: column;
  gap: $spacing-md;
}

// ========== 页面头部 ==========
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;

  &__title {
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
  }

  &__actions {
    display: flex;
    gap: $spacing-sm;
  }
}

// ========== 搜索栏 ==========
.search-bar {
  display: flex;
  align-items: center;
  gap: $spacing-md;
  flex-wrap: wrap;
}

.stat-pill {
  margin-left: auto;
  font-size: $font-size-sm;
  color: $text-regular;

  b {
    color: $primary-color;
    font-size: $font-size-lg;
    margin: 0 $spacing-xs;
  }
}

// ========== 统计卡片（分类配色） ==========
// Grid auto-fit：卡片数变化时自动平均铺满，不产生尾部空白
.cat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: $spacing-md;
  margin-bottom: $spacing-lg;
}

.cat-card {
  display: flex;
  align-items: center;
  gap: $spacing-md;
  padding: $spacing-lg;
  background: $bg-card;
  border: 1px solid $border-base;
  border-radius: $radius-lg;
  box-shadow: $shadow-sm;
  transition: $transition-base;
  cursor: default;

  &:hover {
    transform: translateY(-2px);
    box-shadow: $shadow-hover;
    border-color: var(--cat-color, $primary-color);
  }

  &__icon {
    flex-shrink: 0;
    width: 44px;
    height: 44px;
    border-radius: $radius-md;
    background: var(--cat-bg, $primary-color-light);
    color: var(--cat-color, $primary-color);
    font-size: 22px;
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
    color: $gray-900;
    line-height: 1.2;
  }

  &__label {
    font-size: $font-size-sm;
    color: $text-secondary;
    margin-top: 2px;
  }

  // 产品总数卡片：品牌蓝强调
  &--total {
    .cat-card__icon {
      background: $primary-color-light;
      color: $primary-color;
    }
    .cat-card__value {
      color: $primary-color;
    }
  }
}

// ========== 产品卡片 ==========
.product-card {
  margin-bottom: $spacing-lg;
  padding: $spacing-lg;
  background: $bg-card;
  border: 1px solid $border-base;
  border-radius: $radius-lg;
  transition: $transition-base;
  min-height: 220px;
  display: flex;
  flex-direction: column;

  &:hover {
    border-color: $primary-color;
    transform: translateY(-2px);
    box-shadow: $shadow-hover;
  }

  &--deleted {
    opacity: 0.55;
    background: $bg-hover;
  }

  &__head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: $spacing-sm;

    .product-name {
      font-size: $font-size-lg;
      font-weight: 600;
      color: $text-primary;
      flex: 1;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      margin-right: $spacing-sm;
    }
  }

  .product-desc {
    font-size: $font-size-sm;
    color: $text-regular;
    line-height: 1.5;
    margin-bottom: $spacing-md;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .selling-points {
    display: flex;
    flex-wrap: wrap;
    gap: $spacing-xs;
    align-items: center;
    min-height: 24px;
    margin-bottom: $spacing-md;

    &__more {
      font-size: $font-size-xs;
      color: $text-secondary;
    }
  }

  &__foot {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding-top: $spacing-md;
    border-top: 1px solid $border-light;
    margin-top: auto;

    .updated-at {
      font-size: $font-size-xs;
      color: $text-secondary;
    }

    .actions {
      display: flex;
      gap: $spacing-xs;
    }
  }
}

// ========== 加载 / 空状态（复用全局 sxkRotating 动画） ==========
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

.pager {
  margin-top: $spacing-lg;
  justify-content: flex-end;
}

// ========== 详情弹窗 ==========
// 自定义标题栏（图标 + 产品名）
.sxk-detail-dialog {
  :deep(.detail-dialog__title) {
    display: flex;
    align-items: center;
    gap: $spacing-sm;

    .title-icon {
      font-size: 20px;
      color: $primary-color;
    }

    .title-text {
      font-size: $font-size-lg;
      font-weight: 700;
      color: $gray-900;
    }
  }
}

.product-detail {
  display: flex;
  flex-direction: column;
  gap: $spacing-lg;

  // 顶部摘要条：分类 / 价格 / 更新时间
  .detail-summary {
    display: flex;
    align-items: center;
    gap: $spacing-xl;
    padding: $spacing-md $spacing-lg;
    background: $bg-page;
    border-radius: $radius-md;

    .summary-item {
      display: flex;
      align-items: center;
      gap: $spacing-xs;
      font-size: $font-size-sm;

      .el-icon {
        color: $text-secondary;
      }

      .summary-label {
        color: $text-secondary;
      }

      .summary-value {
        color: $text-primary;
        font-weight: 500;
      }
    }
  }

  // 区块通用
  .detail-section {
    display: flex;
    flex-direction: column;
    gap: $spacing-sm;

    .section-title {
      display: flex;
      align-items: center;
      gap: $spacing-xs;
      font-size: $font-size-base;
      font-weight: 600;
      color: $gray-900;

      .el-icon {
        color: $primary-color;
        font-size: 16px;
      }

      .section-count {
        margin-left: $spacing-xs;
        font-size: $font-size-xs;
        font-weight: 400;
        color: $text-secondary;
      }
    }

    .section-text {
      margin: 0;
      font-size: $font-size-sm;
      color: $text-regular;
      line-height: 1.6;
    }
  }

  // 功能特性卡片网格
  .feature-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: $spacing-sm;
  }

  .feature-card {
    display: flex;
    align-items: flex-start;
    gap: $spacing-sm;
    padding: $spacing-md;
    border: 1px solid $border-base;
    border-radius: $radius-md;
    background: $bg-card;
    transition: $transition-base;

    &:hover {
      border-color: $primary-color;
      box-shadow: 0 2px 8px rgba(26, 86, 219, 0.08);
    }

    &__index {
      flex-shrink: 0;
      width: 24px;
      height: 24px;
      border-radius: $radius-round;
      background: $primary-color-light;
      color: $primary-color;
      font-size: $font-size-xs;
      font-weight: 700;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    &__body {
      flex: 1;
      min-width: 0;
    }

    &__name {
      font-size: $font-size-sm;
      font-weight: 600;
      color: $text-primary;
      margin-bottom: 2px;
    }

    &__desc {
      font-size: $font-size-xs;
      color: $text-secondary;
      line-height: 1.5;
    }
  }

  .tag-group {
    display: flex;
    flex-wrap: wrap;
    gap: $spacing-xs;
  }

  .empty-text {
    font-size: $font-size-sm;
    color: $text-placeholder;
  }

  // 元信息
  &--meta {
    padding-top: $spacing-md;
    border-top: 1px dashed $border-base;

    .meta-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: $spacing-md;
    }

    .meta-item {
      display: flex;
      flex-direction: column;
      gap: 4px;

      .meta-label {
        font-size: $font-size-xs;
        color: $text-secondary;
      }

      .meta-value {
        font-size: $font-size-sm;
        color: $text-primary;
        word-break: break-all;
      }
    }
  }
}

// 关键词高亮统一由 common.scss 的全局 mark 选择器控制（yellow-200 / yellow-900），
// 此处不再重复定义，避免与全局色值冲突。
</style>
