<!--
  神行库 · 竞品分析
  对应 Phase D：
  - 左侧：产品列表（点击切换）
  - 右侧：选中产品的竞品列表（来自 /api/products/{pid}/competitors）
  - 支持删除竞品
-->
<template>
  <div class="sxk-competitors">
    <!-- 顶部欢迎条：与首页风格一致 -->
    <div class="sxk-page-welcome">
      <div class="sxk-page-welcome__left">
        <h2 class="sxk-page-welcome__title">竞品分析</h2>
        <p class="sxk-page-welcome__desc">查看每个产品的竞品情报，支持删除</p>
      </div>
    </div>

    <div class="layout">
      <!-- 左侧：产品列表 -->
      <basic-block class="layout__left">
        <div class="product-list">
          <div class="product-list__title">产品（{{ productList.length }}）</div>
          <el-input
            v-model="productKeyword"
            placeholder="筛选产品"
            clearable
            size="small"
            class="product-list__search"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          <el-scrollbar class="product-list__scroll">
            <div
              v-for="p in filteredProducts"
              :key="p.product_id"
              class="product-item"
              :class="{ 'is-active': selectedId === p.product_id }"
              @click="selectProduct(p)"
            >
              <el-icon class="product-item__icon"><Box /></el-icon>
              <div class="product-item__info">
                <div class="product-item__name">{{ p.name }}</div>
                <div class="product-item__cat">
                  {{ Array.isArray(p.category) ? p.category.join(' / ') : p.category }}
                </div>
              </div>
            </div>
            <div v-if="!filteredProducts.length" class="product-list__empty">
              没有匹配的产品
            </div>
          </el-scrollbar>
        </div>
      </basic-block>

      <!-- 右侧：竞品列表 -->
      <basic-block class="layout__right">
        <div v-if="!selectedId" class="empty-state">
          <el-icon :size="48" color="#94a3b8"><Aim /></el-icon>
          <p>请从左侧选择一个产品</p>
        </div>
        <div v-else class="competitor-list" v-loading="loading">
          <div class="competitor-list__head">
            <div>
              <div class="competitor-list__title">
                {{ selectedProduct?.name }} · 竞品
              </div>
              <div class="competitor-list__sub">
                共 {{ competitorList.length }} 个竞品
              </div>
            </div>
            <el-button
              :loading="reanalyzing"
              size="small"
              @click="onReanalyze"
            >
              <el-icon><Refresh /></el-icon>
              <span>重新分析</span>
            </el-button>
          </div>

          <div v-if="!competitorList.length" class="competitor-list__empty">
            该产品暂无竞品数据
          </div>

          <div
            v-for="comp in competitorList"
            :key="comp.name"
            class="comp-card"
          >
            <div class="comp-card__head">
              <div class="comp-card__name">
                <el-icon class="comp-card__icon"><Aim /></el-icon>
                {{ comp.name }}
              </div>
              <el-popconfirm
                :title="`确认删除「${comp.name}」？`"
                @confirm="removeCompetitor(comp)"
              >
                <template #reference>
                  <el-button link type="danger" size="small">删除</el-button>
                </template>
              </el-popconfirm>
            </div>
            <div class="comp-card__score">
              <el-rate
                :model-value="comp.score || 0"
                disabled
                :show-text="false"
                :show-score="false"
              />
              <span class="comp-card__score-text">{{ (comp.score || 0).toFixed(1) }}</span>
            </div>
            <div class="comp-card__summary">{{ comp.summary || '暂无摘要' }}</div>
            <div class="comp-card__meta">
              来源：{{ comp.source || 'heuristic' }} ·
              更新：{{ formatTime(comp.last_updated) }}
            </div>
          </div>
        </div>
      </basic-block>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { Aim, Box, Refresh, Search } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import sxkApi from '@/mock/sxkApi'

const productList = ref([])
const productKeyword = ref('')
const selectedId = ref(null)
const selectedProduct = ref(null)
const competitorList = ref([])
const loading = ref(false)
const reanalyzing = ref(false)  // 重新分析加载状态

const filteredProducts = computed(() => {
  const kw = productKeyword.value.trim().toLowerCase()
  if (!kw) return productList.value
  return productList.value.filter(
    (p) =>
      (p.name || '').toLowerCase().includes(kw) ||
      (Array.isArray(p.category)
        ? p.category.join(',').toLowerCase()
        : (p.category || '').toLowerCase()
      ).includes(kw)
  )
})

const formatTime = (iso) => {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleString('zh-CN', { hour12: false })
  } catch {
    return iso
  }
}

const loadProducts = async () => {
  try {
    const res = await sxkApi.listProducts({ page: 1, size: 100 })
    if (res.data) {
      productList.value = res.data.items || []
      // 默认选中第一个
      if (productList.value.length && !selectedId.value) {
        selectProduct(productList.value[0])
      }
    }
  } catch (e) {
    ElMessage.error('加载产品失败：' + (e.message || e))
  }
}

const selectProduct = (p) => {
  selectedId.value = p.product_id
  selectedProduct.value = p
}

watch(selectedId, async (newId) => {
  if (!newId) {
    competitorList.value = []
    return
  }
  loading.value = true
  try {
    const res = await sxkApi.listCompetitors(newId)
    if (res.code === 0) {
      competitorList.value = res.data || []
    } else {
      ElMessage.error(res.msg || '加载竞品失败')
    }
  } catch (e) {
    ElMessage.error('加载竞品失败：' + (e.message || e))
  } finally {
    loading.value = false
  }
})

const removeCompetitor = async (comp) => {
  try {
    const res = await sxkApi.removeCompetitor(selectedId.value, comp.name)
    if (res.code === 0) {
      ElMessage.success('已删除')
      competitorList.value = competitorList.value.filter((c) => c.name !== comp.name)
    } else {
      ElMessage.error(res.msg || '删除失败')
    }
  } catch (e) {
    // axios 拦截器已提示
  }
}

// 重新分析竞品（Phase D 增强）
// 后端无独立 /competitors/analyze 端点，重新分析由 content_generate 阶段触发。
// 这里提供 UI 让用户提示"需生成新内容" —— 避免误以为有独立端点
const onReanalyze = async () => {
  reanalyzing.value = true
  try {
    // 真实链路：此处应 POST /api/products/{id}/competitors/analyze（后端目前无独立端点）
    // 折中：直接调 listCompetitors 重新拉取最新数据
    const res = await sxkApi.listCompetitors(selectedId.value)
    reanalyzing.value = false
    if (res.code === 0) {
      competitorList.value = res.data || []
      if (!competitorList.value.length) {
        ElMessage.info('当前产品暂无竞品数据。请在「内容生成」阶段生成竞品分析后再次查看。')
      } else {
        ElMessage.success('已刷新竞品列表')
      }
    } else {
      ElMessage.error(res.msg || '刷新失败')
    }
  } catch (e) {
    reanalyzing.value = false
  }
}

onMounted(() => {
  loadProducts()
})
</script>

<style lang="scss" scoped>
.sxk-competitors {
  padding: $spacing-md 0;
}

// ========== 页面头部（已迁移到 .sxk-page-welcome，参考 common.scss） ==========
// 关键：删除了旧的 .page-header，使用全局 .sxk-page-welcome 组件

.layout {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: $spacing-md;
  margin-top: $spacing-md;

  &__left {
    align-self: flex-start;
  }
}

.product-list {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 240px);
  min-height: 360px;

  &__title {
    font-size: 14px;
    font-weight: 600;
    color: $text-primary;
    margin-bottom: $spacing-sm;
  }

  &__search {
    margin-bottom: $spacing-sm;
  }

  &__scroll {
    flex: 1;
    margin-right: -8px;
    padding-right: 8px;
  }

  &__empty {
    text-align: center;
    color: $text-placeholder;
    padding: $spacing-md;
    font-size: 13px;
  }
}

.product-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: $radius-md;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: 4px;

  &:hover {
    background: $bg-hover;
  }

  &.is-active {
    background: rgba(59, 130, 246, 0.08);
    border-left: 3px solid $primary-color;
  }

  &__icon {
    color: $primary-color;
    font-size: 18px;
    flex-shrink: 0;
  }

  &__info {
    flex: 1;
    min-width: 0;
  }

  &__name {
    font-size: 14px;
    font-weight: 500;
    color: $text-primary;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  &__cat {
    font-size: 12px;
    color: $text-secondary;
    margin-top: 2px;
  }
}

.empty-state {
  text-align: center;
  padding: 80px 0;
  color: $text-placeholder;
  p {
    margin: $spacing-sm 0 0;
    font-size: 14px;
  }
}

.competitor-list {
  &__head {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    margin-bottom: $spacing-md;
  }

  &__title {
    font-size: 16px;
    font-weight: 600;
    color: $text-primary;
  }

  &__sub {
    font-size: 12px;
    color: $text-secondary;
    margin-top: 4px;
  }

  &__empty {
    text-align: center;
    color: $text-placeholder;
    padding: $spacing-xl;
    font-size: 14px;
  }
}

.comp-card {
  border: 1px solid $border-light;
  border-radius: $radius-md;
  padding: $spacing-md;
  margin-bottom: $spacing-sm;
  transition: all 0.2s;
  background: $bg-card;

  &:hover {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
    border-color: $primary-color-light;
  }

  &__head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
  }

  &__name {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 15px;
    font-weight: 600;
    color: $text-primary;
  }

  &__icon {
    color: #ef4444;
  }

  &__score {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
  }

  &__score-text {
    font-size: 13px;
    color: $text-secondary;
    font-weight: 500;
  }

  &__summary {
    font-size: 13px;
    color: $text-secondary;
    line-height: 1.5;
    margin-bottom: 6px;
  }

  &__meta {
    font-size: 12px;
    color: $text-placeholder;
  }
}
</style>
