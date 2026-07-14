<template>
  <div class="lock-container">
    <div class="lock-box">
      <el-icon class="lock-icon">
        <Lock />
      </el-icon>
      <p class="lock-tip">
        屏幕已锁定
      </p>
      <el-input
        v-model="password"
        type="password"
        placeholder="请输入锁屏密码"
        style="width: 240px; margin-bottom: 16px"
        @keyup.enter="unlock"
      />
      <div>
        <el-button
          type="primary"
          @click="unlock"
        >
          解锁
        </el-button>
        <el-button @click="logout">
          退出登录
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { Lock } from '@element-plus/icons-vue'
import { useCommonStore } from '@/store/modules/common'
import { useUserStore } from '@/store/modules/user'

const router = useRouter()
const commonStore = useCommonStore()
const userStore = useUserStore()
const password = ref('')

const unlock = () => {
  if (password.value === commonStore.lockPasswd) {
    commonStore.clearLock()
    router.push('/')
  }
}

const logout = async () => {
  await userStore.logOut()
  router.push('/login')
}
</script>

<style lang="scss" scoped>
.lock-container {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100vh;
  background: #001529;

  .lock-box {
    text-align: center;
    color: #fff;

    .lock-icon {
      font-size: 80px;
      margin-bottom: 20px;
    }

    .lock-tip {
      font-size: 18px;
      margin-bottom: 20px;
    }
  }
}
</style>
