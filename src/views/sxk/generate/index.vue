<!--
  内容生成页（/generate/index）
  对应需求文档：5.3 内容生成 US009 ~ US013 / US017 / AC-13
  对应接口文档：4.6 触发生成 / 4.6.8 Agent 协作 / 4.6.3 版本内容 / 4.6.9 校验问题

  页面布局：
    ┌─────────────────────────────────────────────────────┐
    │  左栏（380px）       │  右栏（自适应，4 个 Tab）     │
    │  - 产品选择          │  T1: 内容编辑与调优            │
    │  - 场景选择          │  T2: Agent 协作过程            │
    │  - 动态参数表单       │  T3: 渠道适配预览              │
    │  - 立即生成          │  T4: 多版本对比                │
    └─────────────────────────────────────────────────────┘

  路由参数：
    ?gid=xxx    重新编辑历史内容（BR-H-04）
    ?scene=xxx  Dashboard 常用模板快捷进入
    ?tid=xxx    模板 ID 预选
-->
<template>
  <div class="sxk-generate" :class="{ 'is-empty': !currentGeneration }">
    <!-- ============================== 左栏：生成配置 ============================== -->
    <basic-block
      class="sxk-generate__config"
      hover-shadow
    >
      <template #header>
        <span class="sxk-generate__config-title">生成配置</span>
      </template>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-position="top"
        size="default"
        @submit.prevent
      >
        <!-- 1) 选择产品 -->
        <el-form-item label="选择产品" prop="product_id">
          <el-select
            v-model="form.product_id"
            placeholder="请选择产品"
            filterable
            clearable
            style="width: 100%"
            @change="onProductChange"
          >
            <el-option
              v-for="p in productOptions"
              :key="p.product_id"
              :label="p.name"
              :value="p.product_id"
              :disabled="p.is_deleted"
            >
              <span style="float: left">{{ p.name }}</span>
              <span style="float: right; color: #9ca3af; font-size: 12px">
                {{ p.category }}
              </span>
            </el-option>
          </el-select>
        </el-form-item>

        <!-- 2) 场景选择 -->
        <el-form-item label="内容场景" prop="scene_code">
          <el-radio-group v-model="form.scene_code" class="sxk-generate__scene">
            <el-radio-button
              v-for="s in scenes"
              :key="s.scene_code"
              :value="s.scene_code"
            >
              {{ s.name }}
            </el-radio-button>
          </el-radio-group>
        </el-form-item>

        <!-- 3) 动态参数：来自 sxkApi.getSceneSchemas() -->
        <template v-if="currentScene">
          <div class="sxk-generate__params-title">动态参数（{{ currentScene.name }}）</div>
          <el-form-item
            v-for="p in currentScene.params"
            :key="p.key"
            :label="p.label + (p.required ? ' *' : '')"
            :prop="`params.${p.key}`"
            :rules="p.required ? [{ required: true, message: `${p.label}为必填` }] : []"
          >
            <!-- enum：单选下拉 -->
            <el-select
              v-if="p.type === 'enum'"
              v-model="form.params[p.key]"
              :placeholder="`请选择${p.label}`"
              style="width: 100%"
            >
              <el-option
                v-for="opt in p.options"
                :key="opt"
                :label="opt"
                :value="opt"
              />
            </el-select>

            <!-- text：单行输入 -->
            <el-input
              v-else-if="p.type === 'text'"
              v-model="form.params[p.key]"
              :placeholder="`请输入${p.label}`"
              clearable
            />

            <!-- textarea：多行输入 -->
            <el-input
              v-else-if="p.type === 'textarea'"
              v-model="form.params[p.key]"
              type="textarea"
              :rows="3"
              :placeholder="`请输入${p.label}`"
            />

            <!-- 兜底 -->
            <el-input
              v-else
              v-model="form.params[p.key]"
              :placeholder="`请输入${p.label}`"
            />
          </el-form-item>
        </template>

        <!-- 4) 立即生成 -->
        <el-form-item>
          <el-button
            type="primary"
            class="sxk-generate__submit"
            :loading="triggering"
            @click="onTrigger"
          >
            <el-icon style="margin-right: 6px"><MagicStick /></el-icon>
            立即生成
          </el-button>
          <div class="sxk-generate__submit-tip">
            生成预计耗时 10 ~ 30 秒，可在右侧「Agent 协作」查看实时进度
          </div>
        </el-form-item>
      </el-form>
    </basic-block>

    <!-- ============================== 右栏：4 个 Tab ============================== -->
    <basic-block
      class="sxk-generate__main"
      hover-shadow
    >
      <template #header>
        <span>生成结果</span>
      </template>
      <template #aside>
        <template v-if="currentGeneration">
          <el-tag size="small" effect="plain" type="success">
            {{ currentGeneration.product.name }}
          </el-tag>
          <el-tag size="small" effect="plain" style="margin-left: 8px">
            {{ sceneName(currentGeneration.scene_code) }}
          </el-tag>
          <el-button
            size="small"
            link
            type="primary"
            style="margin-left: 8px"
            @click="resetAll"
          >
            <el-icon><Refresh /></el-icon>
            清空
          </el-button>
        </template>
      </template>

      <!-- 空状态：未生成任何内容 -->
      <div v-if="!currentGeneration" class="sxk-generate__empty">
        <el-empty description="尚未触发生成，请填写左侧表单后点击「立即生成」">
          <template #image>
            <div class="sxk-generate__empty-icon">
              <el-icon :size="48" color="#9ca3af"><MagicStick /></el-icon>
            </div>
          </template>
        </el-empty>
      </div>

      <!-- 4 个 Tab -->
      <el-tabs
        v-else
        v-model="activeTab"
        class="sxk-generate__tabs"
      >
        <!-- ============= Tab 1: 内容编辑与调优 ============= -->
        <el-tab-pane label="内容编辑与调优" name="edit">
          <div class="sxk-generate__edit">
            <!-- 工具栏 -->
            <div class="sxk-generate__toolbar">
              <el-button-group size="small">
                <el-button :icon="EditPen" @click="execCmd('bold')">加粗</el-button>
                <el-button :icon="EditPen" @click="execCmd('italic')">斜体</el-button>
                <el-button @click="execCmd('insertUnorderedList')">• 列表</el-button>
                <el-button @click="execCmd('insertOrderedList')">1. 列表</el-button>
                <el-button @click="execCmd('formatBlock', 'H2')">H2</el-button>
                <el-button @click="execCmd('formatBlock', 'H3')">H3</el-button>
              </el-button-group>

              <div class="sxk-generate__toolbar-right">
                <el-input
                  v-model="aiPrompt"
                  size="small"
                  placeholder="AI 局部微调，如：把开头改得更简洁"
                  style="width: 280px"
                  clearable
                />
                <el-button
                  size="small"
                  type="primary"
                  :loading="aiPolishing"
                  @click="onAiPolish"
                >
                  <el-icon><MagicStick /></el-icon>
                  AI 微调
                </el-button>
                <span class="sxk-generate__word-count">
                  字数：{{ wordCount }}
                </span>
              </div>
            </div>

            <!-- 编辑器 -->
            <div
              ref="editorRef"
              class="sxk-generate__editor"
              contenteditable="true"
              @input="onEditorInput"
              v-html="currentVersion?.content_html || ''"
            />

            <!-- 校验摘要 -->
            <div v-if="currentVersion?.validation_summary" class="sxk-generate__validation">
              <span class="sxk-generate__validation-label">校验摘要：</span>
              <el-tag
                v-if="currentVersion.validation_summary.error > 0"
                size="small"
                type="danger"
              >
                错误 {{ currentVersion.validation_summary.error }}
              </el-tag>
              <el-tag
                v-if="currentVersion.validation_summary.warn > 0"
                size="small"
                type="warning"
              >
                警告 {{ currentVersion.validation_summary.warn }}
              </el-tag>
              <el-tag
                v-if="currentVersion.validation_summary.info > 0"
                size="small"
                type="info"
              >
                提示 {{ currentVersion.validation_summary.info }}
              </el-tag>
              <el-tag
                v-if="currentVersion.validation_summary.passed"
                size="small"
                type="success"
              >
                通过
              </el-tag>
            </div>
          </div>
        </el-tab-pane>

        <!-- ============= Tab 2: Agent 协作过程 ============= -->
        <el-tab-pane label="Agent 协作过程" name="agent">
          <div class="sxk-generate__agent">
            <div class="sxk-generate__agent-head">
              <span class="sxk-generate__agent-title">
                {{ agentRunning ? '正在协作' : '协作已完成' }}
              </span>
              <el-button
                v-if="agentRunning"
                size="small"
                type="danger"
                plain
                @click="onCancelAgent"
              >
                取消生成
              </el-button>
            </div>

            <el-timeline class="sxk-generate__timeline">
              <el-timeline-item
                v-for="(r, idx) in agentRuns"
                :key="r.agent_code"
                :timestamp="r.duration_ms ? `${r.duration_ms} ms` : '执行中...'"
                :type="timelineType(r)"
                :hollow="r.status === 'pending'"
                size="large"
              >
                <template #dot>
                  <span class="sxk-generate__agent-dot" :class="`is-${r.status}`">
                    <el-icon><component :is="agentIcon(r.agent_code)" /></el-icon>
                  </span>
                </template>
                <div class="sxk-generate__agent-card">
                  <div class="sxk-generate__agent-card-head">
                    <span class="sxk-generate__agent-name">{{ r.agent_name }}</span>
                    <el-tag size="small" :type="agentTagType(r.status)">
                      {{ agentStatusLabel(r.status) }}
                    </el-tag>
                  </div>
                  <div class="sxk-generate__agent-desc">{{ r.description }}</div>

                  <!-- 思考链 -->
                  <details
                    v-if="r.thinking?.length"
                    class="sxk-generate__agent-thinking"
                  >
                    <summary>查看思考链（{{ r.thinking.length }} 步）</summary>
                    <ol>
                      <li v-for="(t, i) in r.thinking" :key="i">
                        <strong>{{ t.title }}</strong>
                        <div class="sxk-generate__agent-thinking-content">{{ t.detail }}</div>
                      </li>
                    </ol>
                  </details>

                  <!-- 输出摘要 -->
                  <div v-if="r.output_summary" class="sxk-generate__agent-output">
                    <el-icon color="#16a34a"><CircleCheck /></el-icon>
                    {{ r.output_summary }}
                  </div>
                </div>
                <el-divider v-if="idx < agentRuns.length - 1" />
              </el-timeline-item>
            </el-timeline>
          </div>
        </el-tab-pane>

        <!-- ============= Tab 3: 渠道适配预览 ============= -->
        <el-tab-pane label="渠道适配预览" name="channel">
          <div class="sxk-generate__channel">
            <el-radio-group v-model="channelKey" class="sxk-generate__channel-tabs">
              <el-radio-button label="wechat">微信公众号</el-radio-button>
              <el-radio-button label="linkedin">LinkedIn</el-radio-button>
              <el-radio-button label="ppt">内部 PPT</el-radio-button>
            </el-radio-group>

            <div class="sxk-generate__channel-stage">
              <!-- 微信公众号样机 -->
              <div v-if="channelKey === 'wechat'" class="sxk-generate__phone">
                <div class="sxk-generate__phone-bar">
                  <span>10:24</span>
                  <span>●●●●● 100%</span>
                </div>
                <div class="sxk-generate__phone-title">微信公众号 · 预览</div>
                <div class="sxk-generate__phone-content" v-html="wechatHtml" />
                <div class="sxk-generate__phone-foot">——— 完 ———</div>
              </div>

              <!-- LinkedIn 样机 -->
              <div v-else-if="channelKey === 'linkedin'" class="sxk-generate__linkedin">
                <div class="sxk-generate__linkedin-head">
                  <div class="sxk-generate__linkedin-avatar" />
                  <div>
                    <div class="sxk-generate__linkedin-name">{{ currentGeneration.product.name }} · 官方账号</div>
                    <div class="sxk-generate__linkedin-meta">1,234 followers · 刚刚</div>
                  </div>
                </div>
                <div class="sxk-generate__linkedin-content" v-html="linkedinHtml" />
                <div class="sxk-generate__linkedin-actions">
                  👍 鼓掌 &nbsp; 💬 评论 &nbsp; ↗ 转发
                </div>
              </div>

              <!-- PPT 样机 -->
              <div v-else class="sxk-generate__ppt">
                <div class="sxk-generate__ppt-page">
                  <div class="sxk-generate__ppt-title">
                    {{ currentGeneration.product.name }}
                  </div>
                  <div class="sxk-generate__ppt-subtitle">
                    {{ sceneName(currentGeneration.scene_code) }} · 内部汇报
                  </div>
                  <ul class="sxk-generate__ppt-bullets">
                    <li v-for="(line, i) in pptBullets" :key="i">{{ line }}</li>
                  </ul>
                  <div class="sxk-generate__ppt-foot">神行库 · 2026</div>
                </div>
              </div>
            </div>
          </div>
        </el-tab-pane>

        <!-- ============= Tab 4: 多版本对比 ============= -->
        <el-tab-pane label="多版本对比" name="compare">
          <div class="sxk-generate__compare">
            <el-row :gutter="12">
              <el-col
                v-for="v in versions"
                :key="v.version_key"
                :xs="24"
                :sm="12"
                :md="8"
              >
                <div
                  class="sxk-generate__compare-card"
                  :class="{ 'is-selected': currentGeneration.selected_version === v.version_key }"
                >
                  <div class="sxk-generate__compare-head">
                    <span class="sxk-generate__compare-name">{{ v.name }}</span>
                    <el-tag
                      v-if="v.is_recommended"
                      size="small"
                      type="success"
                      effect="dark"
                    >
                      推荐
                    </el-tag>
                  </div>
                  <div
                    class="sxk-generate__compare-preview"
                    v-html="v.content_html"
                  />
                  <div class="sxk-generate__compare-meta">
                    字数：{{ v.word_count }}
                  </div>
                  <el-button
                    type="primary"
                    :plain="currentGeneration.selected_version !== v.version_key"
                    size="small"
                    style="width: 100%; margin-top: 8px"
                    @click="onSelectVersion(v.version_key)"
                  >
                    {{ currentGeneration.selected_version === v.version_key ? '已选用' : '选用此版本' }}
                  </el-button>
                </div>
              </el-col>
            </el-row>
          </div>
        </el-tab-pane>
      </el-tabs>
    </basic-block>
  </div>
</template>

<script setup>
/**
 * 内容生成页 Script 逻辑
 *
 * 核心数据流：
 *   onTrigger()
 *     → sxkApi.triggerGeneration({product_id, scene_code, params})
 *     → sxkApi.getAgentRuns() 启动 Agent 仿真轮询
 *     → sxkApi.getGeneration() 拿版本清单
 *     → 默认展示 selected_version 对应的版本内容
 */
import { ref, reactive, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  MagicStick,
  Refresh,
  EditPen,
  CircleCheck,
  Search,
  Document,
  Picture,
  ChatLineRound,
  Connection,
  Aim,
  Histogram
} from '@element-plus/icons-vue'
import BasicBlock from '@/components/basic-block/main.vue'
import { sxkApi } from '@/mock/sxkApi'

// ---------- 路由与基础状态 ----------
const route = useRoute()
const router = useRouter()

// 触发状态
const triggering = ref(false)
// AI 局部微调状态
const aiPolishing = ref(false)
const aiPrompt = ref('')

// 表单引用
const formRef = ref(null)
// 编辑器 DOM 引用
const editorRef = ref(null)
// 编辑器当前内容
const editorContent = ref('')
// 当前激活 Tab
const activeTab = ref('edit')
// 渠道预览选中的样机
const channelKey = ref('wechat')

// ---------- 表单数据 ----------
// 注意：params 是动态字段（来自 schema），用 reactive 包裹便于字段增删
const form = reactive({
  product_id: '',
  scene_code: 'product_intro',
  params: {}
})

const rules = {
  product_id: [{ required: true, message: '请选择产品', trigger: 'change' }],
  scene_code: [{ required: true, message: '请选择场景', trigger: 'change' }]
}

// ---------- 元数据：场景 / 产品下拉 ----------
const scenes = ref([]) // 来自 sxkApi.getSceneSchemas().scenes
const productOptions = ref([])

// ---------- 生成的运行态 ----------
const currentGeneration = ref(null) // 最近一次生成的元数据 + versions
const currentVersion = ref(null)    // 当前选中的版本（含 content_html / validation_summary）
const versions = computed(() => currentGeneration.value?.versions || [])

// Agent 协作运行态
const agentRuns = ref([])
const agentRunning = ref(false)
let agentTimer = null

// 计算属性：当前场景 schema
const currentScene = computed(() =>
  scenes.value.find((s) => s.scene_code === form.scene_code)
)

// 计算属性：编辑器字数（粗略，去 HTML 标签）
const wordCount = computed(() => {
  const text = (editorContent.value || '').replace(/<[^>]+>/g, '').trim()
  if (!text) return 0
  // 中英文混合：CJK 字符按字计，英文按词计
  const cjk = (text.match(/[一-龥]/g) || []).length
  const en = (text.replace(/[一-龥]/g, ' ').match(/[A-Za-z]+/g) || []).length
  return cjk + en
})

// ---------- 初始化 ----------
onMounted(async () => {
  // 1) 拉取产品下拉
  try {
    const resp = await sxkApi.listProducts({ size: 100 })
    productOptions.value = resp.data.items || []
  } catch (e) {
    productOptions.value = []
  }

  // 2) 拉取场景 schema
  try {
    const resp = await sxkApi.getSceneSchemas()
    scenes.value = resp.data.scenes || []
  } catch (e) {
    scenes.value = []
  }

  // 3) 处理路由 query
  const { gid, scene, tid } = route.query
  if (scene) form.scene_code = String(scene)
  if (tid) form.template_id = String(tid) // 暂存，供后续触发时透传给 params
  if (gid) {
    // 重新编辑历史内容：拉取历史并填充
    await loadHistoryAsContext(String(gid))
  } else {
    // 应用场景默认参数
    applySceneDefaults()
  }
})

onBeforeUnmount(() => {
  stopAgentPolling()
})

// 监听场景切换：重置动态参数
watch(
  () => form.scene_code,
  () => applySceneDefaults()
)

// ---------- 业务方法 ----------

/**
 * 应用当前场景的默认参数到 form.params
 * （每次切换场景都执行，避免遗留字段造成校验噪声）
 */
function applySceneDefaults() {
  if (!currentScene.value) return
  const next = {}
  for (const p of currentScene.value.params) {
    next[p.key] = p.default ?? ''
  }
  form.params = next
}

/**
 * 产品切换：清空一些只与产品强相关的字段
 */
function onProductChange() {
  // 暂不需要特殊处理，仅占位
}

/**
 * 场景中文名映射
 */
function sceneName(code) {
  const m = {
    product_intro: '产品介绍',
    competitor: '竞品分析',
    channel_adapt: '渠道适配',
    email: '邮件营销',
    event: '活动宣传',
    other: '其他'
  }
  return m[code] || code
}

/**
 * 触发生成主流程
 */
async function onTrigger() {
  // 1) 表单校验
  if (!formRef.value) return
  try {
    await formRef.value.validate()
  } catch (e) {
    return
  }

  triggering.value = true
  try {
    // 2) 调用触发生成
    const resp = await sxkApi.triggerGeneration({
      product_id: form.product_id,
      scene_code: form.scene_code,
      params: form.params
    })
    if (resp.code !== 0) {
      ElMessage.error(resp.msg || '触发生成失败')
      return
    }
    const generationId = resp.data.generation_id

    // 3) 拉取完整生成记录（含 versions）
    const detailResp = await sxkApi.getGeneration(generationId)
    if (detailResp.code !== 0) {
      ElMessage.error(detailResp.msg || '获取生成详情失败')
      return
    }
    currentGeneration.value = detailResp.data

    // 4) 加载当前版本的详情（含 validation_summary）
    const selVer = currentGeneration.value.selected_version || 'A'
    await loadVersion(generationId, selVer)

    // 5) 启动 Agent 协作轮询（视觉演示用，生产可换 WebSocket/SSE）
    startAgentPolling(generationId, currentGeneration.value.scene_code)

    // 6) 默认激活"编辑" Tab
    activeTab.value = 'edit'

    ElMessage.success('生成完成')
  } catch (e) {
    console.error('[Generate] trigger failed', e)
    ElMessage.error('触发生成失败：' + (e?.message || '未知错误'))
  } finally {
    triggering.value = false
  }
}

/**
 * 加载某版本详情到 currentVersion
 */
async function loadVersion(generationId, versionKey) {
  const resp = await sxkApi.getVersionContent(generationId, versionKey)
  if (resp.code !== 0) {
    ElMessage.error(resp.msg || '加载版本失败')
    return
  }
  currentVersion.value = resp.data
  editorContent.value = resp.data.content_html || ''
}

/**
 * 从历史记录重新进入（BR-H-04）
 */
async function loadHistoryAsContext(gid) {
  try {
    const resp = await sxkApi.getGeneration(gid)
    if (resp.code !== 0) {
      ElMessage.warning('该历史记录不存在，已重置为空白态')
      applySceneDefaults()
      return
    }
    currentGeneration.value = resp.data
    const selVer = resp.data.selected_version || 'A'
    await loadVersion(gid, selVer)
    startAgentPolling(gid, resp.data.scene_code)
    // 回填表单（便于二次修改参数）
    form.product_id = resp.data.product?.product_id || ''
    form.scene_code = resp.data.scene_code || 'product_intro'
    if (resp.data.params) {
      form.params = { ...resp.data.params }
    } else {
      applySceneDefaults()
    }
    activeTab.value = 'edit'
  } catch (e) {
    console.error('[Generate] load history failed', e)
  }
}

/**
 * 选用某个版本
 */
async function onSelectVersion(versionKey) {
  if (!currentGeneration.value) return
  const resp = await sxkApi.selectVersion(currentGeneration.value.generation_id, versionKey)
  if (resp.code !== 0) {
    ElMessage.error(resp.msg || '选用失败')
    return
  }
  currentGeneration.value.selected_version = versionKey
  // 同步切换编辑 Tab 中的内容
  await loadVersion(currentGeneration.value.generation_id, versionKey)
  // 替换编辑器内容
  await nextTick()
  if (editorRef.value) editorRef.value.innerHTML = currentVersion.value?.content_html || ''
  ElMessage.success(`已选用版本 ${versionKey}`)
}

/**
 * 编辑器：执行原生 document.execCommand 命令
 * （轻量 contenteditable，演示阶段够用；生产可替换为 Tiptap / Quill）
 */
function execCmd(cmd, value = null) {
  document.execCommand(cmd, false, value)
  if (editorRef.value) {
    editorContent.value = editorRef.value.innerHTML
  }
}

function onEditorInput(e) {
  editorContent.value = e.target.innerHTML
}

/**
 * AI 局部微调：mock 实现，实际应调用 sxkApi.tuneContent()
 */
async function onAiPolish() {
  if (!aiPrompt.value.trim()) {
    ElMessage.warning('请输入微调指令')
    return
  }
  aiPolishing.value = true
  // 模拟 800ms 耗时
  await new Promise((r) => setTimeout(r, 800))
  aiPolishing.value = false
  ElMessage.success(`已应用微调：${aiPrompt.value}`)
  aiPrompt.value = ''
}

// ---------- Agent 协作轮询 ----------
function startAgentPolling(generationId, sceneCode) {
  stopAgentPolling()
  agentRunning.value = true

  // 初始：所有节点设为 pending
  sxkApi.getAgentRuns(generationId, sceneCode).then((resp) => {
    if (resp.code === 0) {
      agentRuns.value = (resp.data.runs || []).map((r) => ({
        ...r,
        status: 'pending',
        duration_ms: null
      }))
      // 每 1.2s 把下一个节点标记为 running → success
      let i = 0
      const tick = () => {
        if (i >= agentRuns.value.length) {
          agentRunning.value = false
          return
        }
        const cur = agentRuns.value[i]
        cur.status = 'running'
        agentTimer = setTimeout(() => {
          cur.status = 'success'
          cur.duration_ms = 1500 + Math.floor(Math.random() * 2500)
          i += 1
          tick()
        }, 1200)
      }
      tick()
    }
  })
}

function stopAgentPolling() {
  if (agentTimer) {
    clearTimeout(agentTimer)
    agentTimer = null
  }
  agentRunning.value = false
}

function onCancelAgent() {
  ElMessageBox.confirm('确认取消当前生成任务？', '取消生成', {
    type: 'warning',
    confirmButtonText: '确认取消',
    cancelButtonText: '继续生成'
  })
    .then(() => {
      stopAgentPolling()
      agentRuns.value.forEach((r) => {
        if (r.status === 'pending' || r.status === 'running') {
          r.status = 'failed'
        }
      })
      ElMessage.info('已取消生成任务')
    })
    .catch(() => {})
}

// ---------- Agent 状态辅助 ----------
function agentIcon(code) {
  const map = {
    retrieval: Search,
    generation: EditPen,
    channel_adapt: Connection,
    validation: CircleCheck,
    competitor_analysis: Histogram
  }
  return map[code] || Document
}
function agentStatusLabel(s) {
  return {
    pending: '等待',
    running: '执行中',
    success: '完成',
    failed: '失败'
  }[s] || s
}
function agentTagType(s) {
  return {
    pending: 'info',
    running: 'warning',
    success: 'success',
    failed: 'danger'
  }[s] || 'info'
}
function timelineType(r) {
  return {
    pending: 'info',
    running: 'warning',
    success: 'success',
    failed: 'danger'
  }[r.status] || 'info'
}

// ---------- 渠道预览：基于当前版本 HTML 做轻度改写 ----------
const wechatHtml = computed(() => wrapHtmlForWechat(currentVersion.value?.content_html))
const linkedinHtml = computed(() => wrapHtmlForLinkedin(currentVersion.value?.content_html))
const pptBullets = computed(() => extractBullets(currentVersion.value?.content_html))

// 以下两个函数中的内联样式为运行时字符串拼接（注入 v-html），无法使用 SCSS 变量
// 色值需与 styles/variables.scss 中的 token 保持一致：
//   #2563eb = $primary-color / #1f2937 = $text-primary
function wrapHtmlForWechat(html) {
  if (!html) return ''
  // 微信公众号：段落间增加 1.6em 行高
  return html
    .replace(/<p>/g, '<p style="margin: 0 0 14px; line-height: 1.75; color: #1f2937;">')
    .replace(/<h2>/g, '<h2 style="font-size: 18px; color: #2563eb; margin: 16px 0 8px;">')
    .replace(/<h3>/g, '<h3 style="font-size: 16px; color: #1f2937; margin: 12px 0 6px;">')
}

function wrapHtmlForLinkedin(html) {
  if (!html) return ''
  // LinkedIn：短句优先，每段不超过 3 行
  return html
    .replace(/<p>/g, '<p style="margin: 0 0 10px; line-height: 1.55; color: #1f2937; font-size: 14px;">')
    .replace(/<h2>/g, '<p style="font-weight: 700; margin: 8px 0;">')
    .replace(/<\/h2>/g, '</p>')
    .replace(/<h3>/g, '<p style="font-weight: 600; margin: 6px 0;">')
    .replace(/<\/h3>/g, '</p>')
}

function extractBullets(html) {
  if (!html) return []
  // 简单抽取：把 <p>/<h2>/<h3> 转成要点行
  const tmp = html
    .replace(/<h2[^>]*>(.*?)<\/h2>/gi, '◆ $1')
    .replace(/<h3[^>]*>(.*?)<\/h3>/gi, '▸ $1')
    .replace(/<p[^>]*>(.*?)<\/p>/gi, '$1')
    .replace(/<li[^>]*>(.*?)<\/li>/gi, '• $1')
    .replace(/<[^>]+>/g, '')
    .split(/\n+/)
    .map((s) => s.trim())
    .filter(Boolean)
    .slice(0, 8)
  return tmp
}

// ---------- 重置 ----------
function resetAll() {
  currentGeneration.value = null
  currentVersion.value = null
  agentRuns.value = []
  stopAgentPolling()
  editorContent.value = ''
  router.replace({ path: '/generate/index' })
}
</script>

<style lang="scss" scoped>
// ============================================================
// 内容生成页样式 —— 全部使用全局设计 Token（styles/variables.scss）
// 结构：1) 主框架 2) 左栏配置 3) Tab1 编辑 4) Tab2 Agent
//       5) Tab3 渠道样机（微信/LinkedIn/PPT） 6) Tab4 多版本对比
// ============================================================

// ---------- 主框架 ----------
.sxk-generate {
  display: flex;
  gap: $spacing-md;
  align-items: stretch;

  // 窄屏：左右栏上下堆叠
  @media (max-width: 1100px) {
    flex-direction: column;
  }
}

// ---------- 左栏：生成配置 ----------
.sxk-generate__config {
  flex: 0 0 380px;
  align-self: flex-start;
  position: sticky;
  top: $spacing-md;
  max-height: calc(100vh - 100px);
  overflow-y: auto;

  @media (max-width: 1100px) {
    position: static;
    flex: 1 1 auto;
    max-height: none;
  }
}

.sxk-generate__config-title {
  font-size: $font-size-lg;
  font-weight: 600;
  color: $text-primary;
}

// 场景单选按钮组：允许换行
.sxk-generate__scene {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

// 动态参数小标题：左侧品牌色竖线（与 dashboard页/toolbar 风格一致）
.sxk-generate__params-title {
  margin: $spacing-md 0 $spacing-sm;
  font-size: $font-size-sm;
  color: $text-regular;
  font-weight: 500;
  border-left: 3px solid $primary-color;
  padding-left: $spacing-sm;
}

.sxk-generate__submit {
  width: 100%;
  height: 42px;
  font-size: 15px;
}

.sxk-generate__submit-tip {
  margin-top: $spacing-sm;
  font-size: $font-size-xs;
  color: $text-placeholder;
  text-align: center;
  line-height: 1.5;
}

// ---------- 右栏：主区域 ----------
.sxk-generate__main {
  flex: 1 1 auto;
  min-height: 600px;
}

// 空状态
.sxk-generate__empty {
  padding: 80px 0;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.sxk-generate__empty-icon {
  width: 80px;
  height: 80px;
  border-radius: $radius-round;
  background: $gray-100;
  display: flex;
  align-items: center;
  justify-content: center;
}

.sxk-generate__tabs {
  :deep(.el-tabs__header) {
    margin-bottom: $spacing-md;
  }
}

// ==================== Tab 1: 内容编辑与调优 ====================
.sxk-generate__edit {
  display: flex;
  flex-direction: column;
  gap: $spacing-sm;
}

// 工具栏：浅灰背景，与编辑器分离
.sxk-generate__toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: $spacing-sm;
  background: $bg-hover;
  border-radius: $radius-md;
}

.sxk-generate__toolbar-right {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
}

.sxk-generate__word-count {
  font-size: $font-size-xs;
  color: $text-regular;
}

// contenteditable 编辑器
.sxk-generate__editor {
  min-height: 360px;
  max-height: 480px;
  overflow-y: auto;
  padding: $spacing-lg $spacing-xl;
  border: 1px solid $border-base;
  border-radius: $radius-md;
  background: $bg-card;
  font-size: $font-size-base;
  line-height: 1.8;
  color: $text-primary;
  transition: $transition-base;

  &:focus {
    outline: none;
    border-color: $primary-color;
    box-shadow: 0 0 0 3px rgba(26, 86, 219, 0.12); // 品牌色 #1A56DB 光晕
  }

  :deep(h2) {
    font-size: $font-size-xl;
    margin: $spacing-lg 0 $spacing-sm;
    color: $text-primary;
  }
  :deep(h3) {
    font-size: $font-size-lg;
    margin: $spacing-md 0 6px;
    color: $text-regular;
  }
  :deep(p) {
    margin: 0 0 $spacing-md;
  }
}

// 校验摘要
.sxk-generate__validation {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: $spacing-sm $spacing-md;
  background: $bg-hover;
  border-radius: $radius-md;
  font-size: $font-size-xs;
}
.sxk-generate__validation-label {
  color: $text-regular;
  font-weight: 500;
}

// ==================== Tab 2: Agent 协作过程 ====================
.sxk-generate__agent {
  padding: $spacing-xs $spacing-xs 0 0;
}

// 头部横幅：品牌浅蓝渐变（对齐 token，全程品牌蓝系，不混入紫色）
.sxk-generate__agent-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: $spacing-md;
  padding: 10px $spacing-lg;
  background: linear-gradient(135deg, #{$primary-color-light} 0%, #{$primary-color-lighter} 100%);
  border-radius: $radius-md;
}

.sxk-generate__agent-title {
  font-weight: 600;
  color: $primary-color;
}

.sxk-generate__timeline {
  padding-left: $spacing-sm;
}

// 时间轴节点圆点（按状态着色）
.sxk-generate__agent-dot {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: $radius-round;
  background: $primary-color-lighter;
  color: $primary-color;
  transition: $transition-base;

  &.is-success {
    background: #dcfce7; // success-50（浅绿）
    color: $success-color;
  }
  &.is-running {
    background: #fef3c7; // warning-50（浅黄）
    color: $warning-color;
    animation: agentPulse 1.2s ease-in-out infinite;
  }
  &.is-failed {
    background: #fee2e2; // danger-50（浅红）
    color: $danger-color;
  }
}

// Agent 卡片
.sxk-generate__agent-card {
  background: $bg-card;
  border: 1px solid $border-light;
  border-radius: $radius-lg;
  padding: $spacing-md $spacing-lg;
  transition: $transition-base;
}

.sxk-generate__agent-card-head {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
  margin-bottom: $spacing-xs;
}

.sxk-generate__agent-name {
  font-weight: 600;
  color: $text-primary;
  font-size: $font-size-base;
}

.sxk-generate__agent-desc {
  font-size: $font-size-sm;
  color: $text-regular;
  margin-bottom: 6px;
}

// 思考链（折叠面板）
.sxk-generate__agent-thinking {
  margin-top: 6px;
  font-size: $font-size-sm;
  color: $gray-700;
  summary {
    cursor: pointer;
    color: $primary-color;
    user-select: none;
    padding: $spacing-xs 0;
  }
  ol {
    padding-left: 18px;
    margin: 6px 0 0;
    li {
      margin-bottom: $spacing-sm;
    }
  }
}
.sxk-generate__agent-thinking-content {
  margin-top: 2px;
  color: $text-regular;
  line-height: 1.6;
}

// 输出摘要：浅绿背景
.sxk-generate__agent-output {
  display: flex;
  align-items: center;
  gap: $spacing-xs;
  margin-top: 6px;
  padding: 6px 10px;
  background: #f0fdf4;
  border-radius: $radius-sm;
  color: #15803d; // success-700（浅底深字保证对比度）
  font-size: $font-size-sm;
}

// ==================== Tab 3: 渠道适配预览 ====================
.sxk-generate__channel {
  display: flex;
  flex-direction: column;
  gap: $spacing-md;
}

.sxk-generate__channel-tabs {
  align-self: flex-start;
}

// 样机舞台：浅渐变背景
.sxk-generate__channel-stage {
  background: linear-gradient(180deg, #{$bg-hover} 0%, #{$primary-color-light} 100%);
  border-radius: $radius-lg;
  padding: $spacing-xl;
  display: flex;
  justify-content: center;
}

// ---------- 微信公众号样机 ----------
.sxk-generate__phone {
  width: 340px;
  background: $bg-card;
  border-radius: 16px; // 手机外壳大圆角（保留原值，无对应 token）
  box-shadow: $shadow-lg;
  padding: $spacing-md 14px 18px;
  font-family: $font-family-base;
}
.sxk-generate__phone-bar {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: $text-placeholder;
  padding: $spacing-xs 0 $spacing-md;
}
.sxk-generate__phone-title {
  font-size: $font-size-lg;
  font-weight: 700;
  color: $text-primary;
  padding-bottom: $spacing-md;
  border-bottom: 1px solid $border-light;
  margin-bottom: $spacing-md;
}
.sxk-generate__phone-content {
  font-size: $font-size-base;
  color: $text-primary;
  line-height: 1.85;
  max-height: 420px;
  overflow-y: auto;
}
.sxk-generate__phone-foot {
  text-align: center;
  color: $text-placeholder;
  font-size: $font-size-xs;
  margin-top: $spacing-lg;
}

// ---------- LinkedIn 样机 ----------
.sxk-generate__linkedin {
  width: 480px;
  background: $bg-card;
  border-radius: 10px; // 卡片中圆角（保留原值）
  box-shadow: $shadow-lg;
  padding: $spacing-lg $spacing-xl;
}
.sxk-generate__linkedin-head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: $spacing-md;
}
// 头像：品牌蓝深浅渐变（同色系，不混入 indigo）
.sxk-generate__linkedin-avatar {
  width: 44px;
  height: 44px;
  border-radius: $radius-round;
  background: linear-gradient(135deg, #{$primary-color} 0%, #{$primary-color-hover} 100%);
}
.sxk-generate__linkedin-name {
  font-size: $font-size-base;
  font-weight: 600;
  color: $text-primary;
}
.sxk-generate__linkedin-meta {
  font-size: 11px;
  color: $text-regular;
}
.sxk-generate__linkedin-content {
  font-size: $font-size-base;
  color: $text-primary;
  line-height: 1.6;
  max-height: 360px;
  overflow-y: auto;
  margin-bottom: $spacing-md;
}
.sxk-generate__linkedin-actions {
  border-top: 1px solid $border-light;
  padding-top: $spacing-sm;
  font-size: $font-size-sm;
  color: $text-regular;
}

// ---------- PPT 样机 ----------
.sxk-generate__ppt {
  width: 560px;
}
.sxk-generate__ppt-page {
  aspect-ratio: 16 / 9;
  background: linear-gradient(135deg, #{$bg-card} 0%, #{$gray-100} 100%);
  border: 1px solid $border-base;
  border-radius: $radius-md;
  padding: 36px 48px;
  display: flex;
  flex-direction: column;
  box-shadow: $shadow-lg;
}
// PPT 标题：品牌色 + 品牌色下划线（视觉强对比）
.sxk-generate__ppt-title {
  font-size: 28px; // PPT 大标题（保留原值，超出 token 范围）
  font-weight: 700;
  color: $primary-color;
  border-bottom: 3px solid $primary-color;
  padding-bottom: $spacing-sm;
}
.sxk-generate__ppt-subtitle {
  margin-top: 6px;
  font-size: $font-size-base;
  color: $text-regular;
}
.sxk-generate__ppt-bullets {
  margin-top: $spacing-xl;
  flex: 1;
  padding-left: 20px;
  font-size: $font-size-lg;
  color: $text-primary;
  line-height: 1.9;
  li {
    margin-bottom: $spacing-sm;
  }
}
.sxk-generate__ppt-foot {
  text-align: right;
  font-size: $font-size-xs;
  color: $text-placeholder;
  margin-top: $spacing-sm;
}

// ==================== Tab 4: 多版本对比 ====================
.sxk-generate__compare-card {
  border: 1px solid $border-base;
  border-radius: $radius-lg;
  padding: 14px;
  background: $bg-card;
  height: 100%;
  display: flex;
  flex-direction: column;
  transition: $transition-base;

  &:hover {
    border-color: $border-dark;
  }

  // 选中态：品牌色边框 + 品牌色光晕
  &.is-selected {
    border-color: $primary-color;
    box-shadow: 0 0 0 2px rgba(26, 86, 219, 0.18); // 品牌色 #1A56DB
  }
}

.sxk-generate__compare-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: $spacing-sm;
}

.sxk-generate__compare-name {
  font-weight: 600;
  color: $text-primary;
}

// 预览区：浅灰底，限制高度
.sxk-generate__compare-preview {
  flex: 1;
  min-height: 220px;
  max-height: 260px;
  overflow-y: auto;
  font-size: $font-size-sm;
  color: $gray-700;
  line-height: 1.7;
  background: $bg-hover;
  border-radius: $radius-sm;
  padding: 10px $spacing-md;
}

.sxk-generate__compare-meta {
  font-size: $font-size-xs;
  color: $text-placeholder;
  text-align: right;
  margin-top: 6px;
}

// Agent 运行节点呼吸动画（仅此页使用，未抽到 common.scss）
@keyframes agentPulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.08); }
}
</style>