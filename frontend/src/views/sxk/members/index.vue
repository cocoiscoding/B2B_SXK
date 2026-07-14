<!--
  神行库 · 成员管理
  对应 Phase C（核心功能：列表/新增/编辑/删除）
  - 仅管理员可访问（permission.js 的 requiresAdmin 守卫）
  - 调用 sxkApi.listMembers / createMember / updateMember / removeMember
-->
<template>
  <div class="sxk-members">
    <!-- ========== 顶部欢迎条：与首页风格一致 ========== -->
    <div class="sxk-page-welcome">
      <div class="sxk-page-welcome__left">
        <h2 class="sxk-page-welcome__title">
          成员管理
        </h2>
        <p class="sxk-page-welcome__desc">
          管理团队成员的账号、昵称和角色权限（仅管理员）
        </p>
      </div>
      <div class="sxk-page-welcome__actions">
        <el-button
          type="primary"
          @click="onAdd"
        >
          <el-icon><Plus /></el-icon>
          <span>添加成员</span>
        </el-button>
      </div>
    </div>

    <!-- ========== 成员表格 ========== -->
    <basic-block>
      <el-table
        v-loading="loading"
        :data="list"
        border
        stripe
        class="members-table"
        empty-text="暂无成员"
      >
        <el-table-column
          label="昵称"
          min-width="160"
        >
          <template #default="{ row }">
            <div class="member-name">
              <span
                class="member-color"
                :style="{ background: row.color || '#3b82f6' }"
              />
              <span>{{ row.name || row.username }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column
          prop="username"
          label="用户名"
          min-width="140"
        />
        <el-table-column
          prop="email"
          label="邮箱"
          min-width="200"
        />
        <el-table-column
          label="角色"
          width="100"
        >
          <template #default="{ row }">
            <el-tag
              v-if="row.is_admin"
              type="danger"
              size="small"
            >
              管理员
            </el-tag>
            <el-tag
              v-else
              size="small"
              type="info"
            >
              普通成员
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column
          prop="created_at"
          label="创建时间"
          min-width="180"
        >
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column
          label="操作"
          width="180"
          fixed="right"
        >
          <template #default="{ row }">
            <el-button
              link
              type="primary"
              @click="onEdit(row)"
            >
              编辑
            </el-button>
            <el-popconfirm
              :title="`确认删除「${row.name || row.username}」？`"
              @confirm="onDelete(row)"
            >
              <template #reference>
                <el-button
                  link
                  type="danger"
                >
                  删除
                </el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </basic-block>

    <!-- ========== 成员编辑弹窗 ========== -->
    <member-edit-modal
      v-model="editVisible"
      :member-id="editTargetId"
      @saved="loadList"
    />
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import sxkApi from '@/mock/sxkApi'
import MemberEditModal from './components/member-edit-modal.vue'

const list = ref([])
const loading = ref(false)
const editVisible = ref(false)
const editTargetId = ref(null)

const formatTime = (iso) => {
  if (!iso) return ''
  try {
    const d = new Date(iso)
    return d.toLocaleString('zh-CN', { hour12: false })
  } catch {
    return iso
  }
}

const loadList = async () => {
  loading.value = true
  try {
    const res = await sxkApi.listMembers()
    if (res.code === 0) {
      list.value = res.data || []
    } else {
      ElMessage.error(res.msg || '加载成员失败')
    }
  } catch (e) {
    console.error('[Members] loadList failed', e)
    ElMessage.error('加载成员失败：' + (e.message || e))
  } finally {
    loading.value = false
  }
}

const onAdd = () => {
  editTargetId.value = null
  editVisible.value = true
}

const onEdit = (row) => {
  editTargetId.value = row.id
  editVisible.value = true
}

const onDelete = async (row) => {
  try {
    const res = await sxkApi.removeMember(row.id)
    if (res.code === 0) {
      ElMessage.success('已删除')
      loadList()
    } else {
      ElMessage.error(res.msg || '删除失败')
    }
  } catch (e) {
    // axios 拦截器已提示
  }
}

onMounted(() => {
  loadList()
})
</script>

<style lang="scss" scoped>
.sxk-members {
  padding: $spacing-md 0;
}

// ========== 页面头部（已迁移到 .sxk-page-welcome，参考 common.scss） ==========
// 关键：删除了旧的 .page-header，使用全局 .sxk-page-welcome 组件

.members-table {
  margin-top: 0;
}

.member-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.member-color {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
  box-shadow: 0 0 0 2px rgba(0, 0, 0, 0.04);
}
</style>
