<template>
  <div class="workbench">
    <el-row :gutter="16">
      <el-col :span="24">
        <basic-block>
          <div class="welcome">
            <h2>欢迎使用管理系统</h2>
            <p>这是一个基于 Vue3 + Element Plus 的管理系统框架</p>
          </div>
        </basic-block>
      </el-col>
    </el-row>
    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :xs="24" :sm="12" :md="6" v-for="card in cards" :key="card.title">
        <basic-block>
          <div class="stat-card">
            <el-icon class="stat-icon" :style="{ color: card.color }">
              <component :is="card.icon" />
            </el-icon>
            <div class="stat-info">
              <div class="stat-value">{{ card.value }}</div>
              <div class="stat-label">{{ card.title }}</div>
            </div>
          </div>
        </basic-block>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { User, Document, Bell, DataLine } from '@element-plus/icons-vue'

const cards = [
  { title: '用户总数', value: '1,024', icon: User, color: '#409eff' },
  { title: '文档数量', value: '512', icon: Document, color: '#67c23a' },
  { title: '通知消息', value: '8', icon: Bell, color: '#e6a23c' },
  { title: '数据统计', value: '99%', icon: DataLine, color: '#f56c6c' }
]
</script>

<style lang="scss" scoped>
.welcome {
  text-align: center;
  padding: 40px 0;

  h2 {
    margin: 0 0 12px;
    color: #303133;
  }

  p {
    color: #909399;
    font-size: 14px;
  }
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;

  .stat-icon {
    font-size: 48px;
  }

  .stat-info {
    .stat-value {
      font-size: 28px;
      font-weight: 600;
    }

    .stat-label {
      font-size: 14px;
      color: #909399;
    }
  }
}
</style>
