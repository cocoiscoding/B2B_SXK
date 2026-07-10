<!--
  神行库 · 生成历史
  对应需求文档 5.4（US016）：
    - 总条数
    - 搜索（产品名 / 模板名）+ 模板筛选
    - 表格：时间/产品/模板/状态/操作
    - 详情弹窗：查看 / 重新编辑此内容
-->
<template>
  <div class="sxk-history">
    <!-- ========== 顶部 ========== -->
    <basic-block>
      <div class="page-header">
        <div class="page-header__title">
          <h2>生成历史</h2>
          <p>共 <b>{{ total }}</b> 条记录</p>
        </div>
      </div>
    </basic-block>

    <!-- ========== 搜索 + 筛选 ========== -->
    <basic-block>
      <div class="search-bar">
        <el-input
          v-model="filters.keyword"
          placeholder="按产品名称 / 模板模糊搜索"
          clearable
          style="max-width: 360px"
          @keyup.enter="search"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>

        <el-select
          v-model="filters.template_id"
          placeholder="全部模板"
          clearable
          style="width: 240px"
          @change="search"
        >
          <el-option label="全部模板" value="" />
          <el-option
            v-for="tpl in templateOptions"
            :key="tpl.template_id"
            :label="tpl.name"
            :value="tpl.template_id"
          />
        </el-select>

        <el-select
          v-model="filters.status"
          placeholder="全部状态"
          clearable
          style="width: 140px"
          @change="search"
        >
          <el-option label="全部状态" value="" />
          <el-option label="已完成" value="success" />
          <el-option label="生成中" value="running" />
          <el-option label="失败" value="failed" />
          <el-option label="已取消" value="cancelled" />
        </el-select>

        <el-button type="primary" @click="search">搜索</el-button>
        <el-button @click="reset">重置</el-button>
      </div>
    </basic-block>

    <!-- ========== 表格 ========== -->
    <basic-block padding="none">
      <el-table
        ref="tableRef"
        :data="list"
        v-loading="loading"
        stripe
        :row-class-name="rowClassName"
        :empty-text="emptyText"
      >
        <el-table-column label="生成时间" width="200">
          <template #default="{ row }">
            <div>{{ formatDateTime(row.created_at) }}</div>
            <div class="text-sub">{{ relativeTime(row.created_at) }}</div>
          </template>
        </el-table-column>

        <el-table-column label="产品名称" min-width="180">
          <template #default="{ row }">
            <span :class="{ 'is-deleted': row.product.is_deleted }">
              {{ row.product.name }}
              <el-tag v-if="row.product.is_deleted" size="small" type="info" effect="plain">已删除</el-tag>
            </span>
          </template>
        </el-table-column>

        <el-table-column label="使用模板" min-width="180">
          <template #default="{ row }">
            {{ row.template.name }}
          </template>
        </el-table-column>

        <el-table-column label="耗时" width="120">
          <template #default="{ row }">
            <span v-if="row.duration_ms">{{ (row.duration_ms / 1000).toFixed(1) }}s</span>
            <span v-else>—</span>
          </template>
        </el-table-column>

        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)" effect="light" size="small">
              {{ statusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="onView(row)">查看</el-button>
            <el-button link type="primary" @click="onEdit(row)">重新编辑</el-button>
            <el-popconfirm
              title="确定删除这条历史吗？"
              confirm-button-text="删除"
              @confirm="onDelete(row)"
            >
              <template #reference>
                <el-button link type="danger">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="pager.page"
        v-model:page-size="pager.size"
        :total="total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next, jumper"
        background
        class="pager"
        @current-change="load"
        @size-change="load"
      />
    </basic-block>

    <!-- ========== 详情弹窗 ========== -->
    <history-detail-modal
      v-model="detailVisible"
      :generation-id="detailTargetId"
      @edit="goEdit"
    />
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import sxkApi from '@/mock/sxkApi'
import HistoryDetailModal from './components/history-detail-modal.vue'

const route = useRoute()
const router = useRouter()

// ========== 状态 ==========
const filters = reactive({ keyword: '', template_id: '', status: '' })
const list = ref([])
const total = ref(0)
const pager = reactive({ page: 1, size: 20 })
const loading = ref(false)
const templateOptions = ref([])

const detailVisible = ref(false)
const detailTargetId = ref(null)

// ========== 从首页"最近生成"跳转过来的高亮定位 ==========
// 首页点击某条记录 → URL 携带 query.gid → 历史表格高亮闪烁该行并滚动到位
const tableRef = ref(null)
const highlightGid = ref(route.query.gid || '')

// el-table row-class-name：给目标行打标记，便于 CSS 高亮闪烁
const rowClassName = ({ row }) => {
  return highlightGid.value && row.generation_id === highlightGid.value
    ? 'history-highlight-row'
    : ''
}

// 数据加载后，定位到 query.gid 对应行：滚动至可视区 + 闪烁 3 次（约 4s 后清除标记）
const scrollToHighlight = () => {
  if (!highlightGid.value) return
  nextTick(() => {
    const wrapper = tableRef.value?.$el?.querySelector('.el-table__body-wrapper')
    const targetRow = wrapper?.querySelector('.history-highlight-row')
    if (targetRow) {
      targetRow.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
    // 4 秒后清除高亮，恢复正常表格样式
    setTimeout(() => {
      highlightGid.value = ''
    }, 4000)
  })
}

// ========== 工具 ==========
const statusText = (s) =>
  ({ success: '已完成', running: '生成中', failed: '失败', cancelled: '已取消' })[s] || s

const statusTagType = (s) =>
  ({ success: 'success', running: 'warning', failed: 'danger', cancelled: 'info' })[s] || 'info'

const formatDateTime = (iso) => {
  const d = new Date(iso)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

const relativeTime = (iso) => {
  const d = new Date(iso)
  const diff = Date.now() - d.getTime()
  const min = Math.floor(diff / 60000)
  if (min < 1) return '刚刚'
  if (min < 60) return `${min} 分钟前`
  const hr = Math.floor(min / 60)
  if (hr < 24) return `${hr} 小时前`
  const day = Math.floor(hr / 24)
  if (day < 30) return `${day} 天前`
  return ''
}

const emptyText = computed(() =>
  filters.keyword || filters.template_id || filters.status
    ? '未找到匹配的历史记录'
    : '暂无生成历史'
)

// ========== 数据加载 ==========
const load = async () => {
  loading.value = true
  try {
    const res = await sxkApi.listHistory({
      page: pager.page,
      size: pager.size,
      keyword: filters.keyword,
      template_id: filters.template_id,
      status: filters.status
    })
    if (res.data) {
      list.value = res.data.items || []
      total.value = res.data.total || 0
      // 首页"最近生成"跳转过来时，定位并高亮目标行
      scrollToHighlight()
    }
  } catch (e) {
    console.error('[History] load failed', e)
    ElMessage.error('加载历史记录失败')
  } finally {
    loading.value = false
  }
}

const loadTemplates = async () => {
  try {
    // 仅取首屏足够多（mock 阶段直接拉全部；后端就绪后会自动分页）
    const res = await sxkApi.listTemplates({ page: 1, size: 100 })
    if (res.data) templateOptions.value = res.data.items || []
  } catch (e) {
    console.error('[History] loadTemplates failed', e)
  }
}

const search = () => {
  pager.page = 1
  load()
}

const reset = () => {
  filters.keyword = ''
  filters.template_id = ''
  filters.status = ''
  search()
}

// ========== 操作回调 ==========
const onView = (row) => {
  detailTargetId.value = row.generation_id
  detailVisible.value = true
}

const onEdit = (row) => {
  // BR-H-04：跳转内容生成页并携带 gid
  router.push({ path: '/generate/index', query: { gid: row.generation_id } })
}

const goEdit = (generationId) => {
  detailVisible.value = false
  router.push({ path: '/generate/index', query: { gid: generationId } })
}

const onDelete = async (row) => {
  try {
    const res = await sxkApi.removeHistory(row.generation_id)
    if (res.code === 0) {
      ElMessage.success('已删除')
      load()
    } else {
      ElMessage.error(res.msg || '删除失败')
    }
  } catch {
    // axios 拦截器已提示错误
  }
}

onMounted(() => {
  load()
  loadTemplates()
})
</script>

<style lang="scss" scoped>
.sxk-history {
  display: flex;
  flex-direction: column;
  gap: $spacing-md;
}

.page-header {
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

      b {
        color: $primary-color;
        margin: 0 $spacing-xs;
      }
    }
  }
}

.search-bar {
  display: flex;
  align-items: center;
  gap: $spacing-md;
  flex-wrap: wrap;
}

.text-sub {
  font-size: $font-size-xs;
  color: $text-secondary;
  margin-top: 2px;
}

.is-deleted {
  color: $text-secondary;
  text-decoration: line-through;
}

.pager {
  margin: $spacing-lg;
  justify-content: flex-end;
}

// ========== 从首页"最近生成"跳转过来的目标行高亮闪烁 ==========
// 用品牌色 #1A56DB 的浅色（blue-50 / blue-100）作为高亮底色，
// 闪烁 3 次后由 JS 清除 highlightGid 恢复常态。
// 注意：el-table 的 stripe 斑马纹会给 td.el-table__cell 设背景色，
// 因此高亮必须作用在 td 上并用 !important 覆盖。
:deep(.history-highlight-row td.el-table__cell) {
  background-color: $primary-color-light !important;   // blue-50 #eff6ff
  animation: sxk-history-row-flash 1.2s ease-in-out 3;
}

@keyframes sxk-history-row-flash {
  0%,
  100% {
    background-color: $primary-color-light !important;   // blue-50
  }
  50% {
    background-color: $primary-color-lighter !important; // blue-100，更明显
  }
}
</style>
