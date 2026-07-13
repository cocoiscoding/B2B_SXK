import { fileURLToPath, URL } from 'node:url'
import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'
import os from 'node:os'
import path from 'node:path'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const port = env.VITE_PORT || 52400
  const target = env.VITE_API_TARGET || 'http://localhost:8000'

  return {
    base: '/',
    // 关键修复：将 Vite 依赖缓存移出 node_modules，放到系统 temp 目录。
    // Windows Defender / 杀毒软件会实时扫描 node_modules，导致 Vite 写入
    // deps_temp_xxx/ 时触发 EBUSY (resource busy or locked) 错误。
    // 系统 temp 目录通常被 Defender 排除，可彻底避免文件锁冲突。
    cacheDir: path.join(os.tmpdir(), 'sxk-vite-cache'),
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url))
      },
      extensions: ['.mjs', '.js', '.ts', '.jsx', '.tsx', '.json', '.vue']
    },
    plugins: [
      vue(),
      AutoImport({
        resolvers: [ElementPlusResolver()]
      }),
      Components({
        // 仅按需注册 ElementPlus 组件；src/components/* 全部走显式 import，
        // 避免 basic-container / basic-block / iframe 等 main.vue 被推导为同名 Main 冲突。
        resolvers: [ElementPlusResolver()],
        dirs: [],
        deep: false,
        dts: false
      })
    ],
    // 关键修复：预声明所有 element-plus 子依赖，避免 Vite 在运行中
    // 发现新组件时触发重新打包（这是 EBUSY 的另一个触发点）。
    optimizeDeps: {
      include: [
        'vue',
        'vue-router',
        'pinia',
        'axios',
        'nprogress',
        'crypto-js',
        'js-base64',
        'js-cookie',
        'js-md5',
        'element-plus',
        'element-plus/dist/locale/zh-cn.mjs',
        'element-plus/es',
        '@element-plus/icons-vue',
        // 以下样式模块按需引入，预声明避免运行中发现新组件时重新打包
        'element-plus/es/components/base/style/css',
        'element-plus/es/components/button/style/css',
        'element-plus/es/components/form/style/css',
        'element-plus/es/components/form-item/style/css',
        'element-plus/es/components/input/style/css',
        'element-plus/es/components/row/style/css',
        'element-plus/es/components/col/style/css',
        'element-plus/es/components/icon/style/css',
        'element-plus/es/components/dropdown/style/css',
        'element-plus/es/components/dropdown-menu/style/css',
        'element-plus/es/components/dropdown-item/style/css',
        'element-plus/es/components/avatar/style/css',
        'element-plus/es/components/scrollbar/style/css',
        'element-plus/es/components/menu/style/css',
        'element-plus/es/components/sub-menu/style/css',
        'element-plus/es/components/menu-item/style/css',
        'element-plus/es/components/card/style/css',
        'element-plus/es/components/table/style/css',
        'element-plus/es/components/table-column/style/css',
        'element-plus/es/components/pagination/style/css',
        'element-plus/es/components/tag/style/css',
        'element-plus/es/components/dialog/style/css',
        'element-plus/es/components/tabs/style/css',
        'element-plus/es/components/tab-pane/style/css',
        'element-plus/es/components/tooltip/style/css',
        'element-plus/es/components/select/style/css',
        'element-plus/es/components/option/style/css',
        'element-plus/es/components/radio/style/css',
        'element-plus/es/components/radio-group/style/css',
        'element-plus/es/components/checkbox/style/css',
        'element-plus/es/components/checkbox-group/style/css',
        'element-plus/es/components/switch/style/css',
        'element-plus/es/components/date-picker/style/css',
        'element-plus/es/components/alert/style/css',
        'element-plus/es/components/loading/style/css',
        'element-plus/es/components/message-box/style/css',
        'element-plus/es/components/popconfirm/style/css',
        'element-plus/es/components/empty/style/css',
        'element-plus/es/components/divider/style/css',
        'element-plus/es/components/progress/style/css',
        'element-plus/es/components/badge/style/css',
        'element-plus/es/components/descriptions/style/css',
        'element-plus/es/components/descriptions-item/style/css',
        'element-plus/es/components/timeline/style/css',
        'element-plus/es/components/timeline-item/style/css',
        'element-plus/es/components/collapse/style/css',
        'element-plus/es/components/collapse-item/style/css',
        'element-plus/es/components/steps/style/css',
        'element-plus/es/components/step/style/css'
      ]
    },
    css: {
      preprocessorOptions: {
        scss: {
          additionalData: `@use "@/styles/variables.scss" as *;`
        }
      }
    },
    server: {
      // 关键修复：Windows 上绑定 0.0.0.0（通配地址）需要管理员权限，否则会
      // 触发 EACCES: permission denied。改为 127.0.0.1 可以正常启动且无需权限。
      // 如需局域网访问，临时改为 '0.0.0.0' 或以管理员身份运行。
      // host: '127.0.0.1',
      host: '0.0.0.0',
      port: Number(port),
      // 关键修复：Windows 上其他进程占用端口会触发 EACCES。
      // 当 strictPort=true 时 Vite 直接报错退出，导致开发体验极差。
      // 改为 strictPort=false，Vite 会自动尝试下一个可用端口 (52701, 52702, ...)。
      // 同时通过打印的端口号确保用户能知道实际访问地址。
      strictPort: false,
      open: false,
      cors: true,
      // 排除 node_modules 变化触发频繁的 fs.watch（另一个 Windows 上的性能杀手）
      watch: {
        ignored: ['**/node_modules/**', '**/.git/**', '**/dist/**']
      },
      proxy: {
        '/api': {
          target: target,
          changeOrigin: true
        }
      }
    },
    build: {
      outDir: 'dist',
      chunkSizeWarningLimit: 2000,
      rollupOptions: {
        output: {
          manualChunks: {
            vue: ['vue', 'vue-router', 'pinia'],
            element: ['element-plus', '@element-plus/icons-vue']
          }
        }
      }
    }
  }
})
