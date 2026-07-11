<!--
  内容生成页（/generate/index）
  对应需求文档：5.3 内容生成 US009 ~ US013 / US017 / AC-13
  对应接口文档：4.6 触发生成 / 4.6.8 Agent 协作 / 4.6.3 版本内容 / 4.6.9 校验问题

  页面布局（多阶段草稿流程，对齐后端参考版 B2B-SXK-FastApi/frontend）：
    ┌─────────────────────────────────────────────────────┐
    │  左栏（380px）       │  右栏（自适应）                │
    │  - 阶段指示 (el-steps)│  阶段 0：初稿多版本（Tab）    │
    │  - 产品/场景/模板     │  阶段 1：编辑 + 多选渠道       │
    │  - 动态参数          │  阶段 2：多渠道版本 + 文生图    │
    │  - 立即生成 (Step 0)  │                               │
    └─────────────────────────────────────────────────────┘

  路由参数：
    ?gid=xxx    重新编辑历史内容（BR-H-04）
    ?scene=xxx  Dashboard 常用模板快捷进入
    ?tid=xxx    模板 ID 预选
-->
<template>
  <div class="sxk-generate" :class="{ 'is-empty': !currentDraft }">
    <!-- ============================== 左栏：生成配置 + 阶段指示 ============================== -->
    <basic-block class="sxk-generate__config" hover-shadow>
      <template #header>
        <div class="sxk-page-header" style="width: 100%; padding: 0">
          <div class="sxk-page-header__title">
            <h2>内容生成</h2>
            <p>填写配置，一键产出多版本营销文案</p>
          </div>
          <el-tag
            v-if="currentDraft"
            size="small"
            type="info"
            effect="light"
            class="sxk-generate__phase-tag"
          >
            阶段 {{ draftStep + 1 }} / 3
          </el-tag>
        </div>
      </template>

      <!-- 阶段指示器（草稿存在时显示） -->
      <div v-if="currentDraft" class="sxk-generate__steps">
        <!-- 自绘可点击步骤条（替代 el-steps，支持已完成步回跳） -->
        <div class="sxk-generate__step-track">
          <div
            v-for="(s, i) in stepDefs"
            :key="i"
            class="sxk-generate__step"
            :class="stepClass(i)"
            @click="onStepJump(i)"
            :title="canJumpTo(i) ? `回到：${s.title}` : s.title"
          >
            <div class="sxk-generate__step-no">
              <el-icon v-if="i < draftStep || (i === 2 && stage2Completed)"><CircleCheckFilled /></el-icon>
              <span v-else>{{ i + 1 }}</span>
            </div>
            <div class="sxk-generate__step-info">
              <div class="sxk-generate__step-title">{{ s.title }}</div>
              <div class="sxk-generate__step-desc">{{ s.desc }}</div>
            </div>
            <span
              v-if="i === draftStep && !(i === 2 && stage2Completed)"
              class="sxk-generate__step-tag"
            >当前</span>
            <span
              v-else-if="i < draftStep || (i === 2 && stage2Completed)"
              class="sxk-generate__step-tag is-done"
            >完成</span>
            <span
              v-else
              class="sxk-generate__step-tag is-wait"
            >待开始</span>
          </div>
        </div>

        <!-- 当前阶段摘要卡 -->
        <div class="sxk-generate__step-summary">
          <span class="sxk-generate__step-summary-icon">
            <el-icon><Aim /></el-icon>
          </span>
          <span class="sxk-generate__step-summary-text">
            <b>当前阶段：</b>{{ stepDefs[draftStep]?.summary }}
          </span>
        </div>

        <!-- 草稿操作行 -->
        <div class="sxk-generate__step-actions">
          <el-button
            size="small"
            :icon="Refresh"
            @click="onDiscardDraft"
          >
            重新配置
          </el-button>
          <el-button
            size="small"
            type="danger"
            plain
            :icon="Delete"
            @click="confirmDiscard"
          >
            放弃草稿
          </el-button>
        </div>
      </div>

      <el-form
        v-else
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
          <div class="sxk-generate__scene-grid">
            <div
              v-for="s in scenes"
              :key="s.scene_code"
              class="sxk-generate__scene-box"
              :class="{ 'is-active': form.scene_code === s.scene_code }"
              @click="form.scene_code = s.scene_code"
            >
              <el-icon :size="22" class="sxk-generate__scene-icon">
                <component :is="getSceneIcon(s.scene_code)" />
              </el-icon>
              <span class="sxk-generate__scene-text">{{ s.name }}</span>
            </div>
          </div>
        </el-form-item>

        <!-- 2.5) 模板选择（选择场景后动态加载） -->
        <el-form-item v-if="currentScene" label="选择模板">
          <el-select
            v-model="form.template_id"
            placeholder="请选择模板（可选）"
            filterable
            clearable
            style="width: 100%"
            @change="onTemplateChange"
          >
            <el-option
              v-for="t in sceneTemplates"
              :key="t.template_id"
              :label="t.name"
              :value="t.template_id"
            />
          </el-select>
        </el-form-item>

        <!-- 3) 动态参数 -->
        <template v-if="currentScene">
          <div class="sxk-generate__params-title">动态参数（{{ currentScene.name }}）</div>
          <el-form-item
            v-for="p in currentScene.params"
            :key="p.key"
            :label="p.label + (p.required ? ' *' : '')"
            :prop="`params.${p.key}`"
            :rules="p.required ? [{ required: true, message: `${p.label}为必填` }] : []"
          >
            <el-select
              v-if="p.type === 'enum'"
              v-model="form.params[p.key]"
              :placeholder="p.default || `请选择${p.label}`"
              style="width: 100%"
            >
              <el-option v-for="opt in p.options" :key="opt" :label="opt" :value="opt" />
            </el-select>
            <el-input
              v-else-if="p.type === 'text'"
              v-model="form.params[p.key]"
              :placeholder="p.default || '请输入...'"
              clearable
            />
            <el-input
              v-else-if="p.type === 'textarea'"
              v-model="form.params[p.key]"
              type="textarea"
              :rows="3"
              :placeholder="p.default || '请输入...'"
            />
            <el-input
              v-else
              v-model="form.params[p.key]"
              :placeholder="p.default || '请输入...'"
            />
          </el-form-item>
          <el-form-item v-if="form.params.prompt" label="提示词">
            <el-input
              v-model="form.params.prompt"
              type="textarea"
              :rows="4"
              placeholder="提示词内容"
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
            立即生成（3 个初稿）
          </el-button>
          <div class="sxk-generate__submit-tip">
            渠道适配与配图在生成后分阶段进行：选定初稿 → 改内容·多选渠道 → 文生图保存
          </div>
        </el-form-item>
      </el-form>
    </basic-block>

    <!-- ============================== 右栏：阶段化主体 ============================== -->
    <basic-block class="sxk-generate__main" hover-shadow>
      <template #header>
        <div class="sxk-generate__main-title">
          <span class="sxk-generate__main-title-main">
            {{ currentDraft ? `生成结果 · ${stepTitle}` : '生成结果' }}
          </span>
          <span v-if="!currentDraft" class="sxk-generate__main-title-sub">
            待生成内容将在此处展示
          </span>
        </div>
      </template>
      <template #aside>
        <template v-if="currentDraft">
          <el-tag
            v-if="currentDraft.product_name"
            size="small"
            effect="light"
            type="success"
          >
            {{ currentDraft.product_name }}
          </el-tag>
          <el-tag
            v-if="currentDraft.scene_name"
            size="small"
            effect="light"
            type="info"
            style="margin-left: 6px"
          >
            {{ currentDraft.scene_name }}
          </el-tag>
        </template>
      </template>

      <!-- 空状态 -->
      <div v-if="!currentDraft" class="sxk-generate__empty">
        <el-empty description="尚未触发生成，请填写左侧表单后点击「立即生成」">
          <template #image>
            <div class="sxk-generate__empty-icon">
              <el-icon :size="48" color="#9ca3af"><MagicStick /></el-icon>
            </div>
          </template>
        </el-empty>
      </div>

      <!-- ============ 阶段 0：初稿多版本选择（卡片对比墙 + 整版预览）============ -->
      <div v-else-if="draftStep === 0" class="sxk-generate__stage">
        <!-- Agent 执行链路（横向时间线 + 可点击节点详情） -->
        <el-card class="sxk-generate__card sxk-generate__card-trace" shadow="never">
          <template #header>
            <div class="sxk-generate__card-head sxk-generate__trace-toggle">
              <div
                class="sxk-generate__trace-left"
                @click="showAgentTrace = !showAgentTrace"
              >
                <span class="sxk-generate__trace-icon"><el-icon><Connection /></el-icon></span>
                <b>Agent 执行链路</b>
                <span
                  class="sxk-generate__trace-stats"
                  v-if="currentDraft.agent_trace?.length"
                >
                  <span class="sxk-generate__trace-stat is-success">
                    <el-icon><CircleCheckFilled /></el-icon>
                    {{ agentSuccessCount }} / {{ currentDraft.agent_trace.length }} 成功
                  </span>
                  <span class="sxk-generate__trace-stat">
                    <el-icon><Timer /></el-icon>
                    总耗时 {{ agentTotalDuration }}ms
                  </span>
                </span>
              </div>
              <div class="sxk-generate__trace-right">
                <span
                  class="sxk-generate__status-pill"
                  :class="currentDraft.validation?.validated ? 'is-pass' : 'is-warn'"
                >
                  <span class="sxk-generate__status-pill-dot" />
                  {{ currentDraft.validation?.validated ? '校验通过' : '有待完善' }}
                </span>
                <span
                  class="sxk-generate__trace-toggle-btn"
                  @click="showAgentTrace = !showAgentTrace"
                  :title="showAgentTrace ? '收起详情' : '展开详情'"
                >
                  <el-icon :class="{ 'is-open': showAgentTrace }"><ArrowRight /></el-icon>
                </span>
              </div>
            </div>
          </template>

          <!-- ============ 横向时间线节点 ============ -->
          <div class="sxk-generate__timeline">
            <div
              v-for="(s, i) in currentDraft.agent_trace"
              :key="i"
              class="sxk-generate__tl-node"
              :class="`is-${s.status} ${activeStep === i ? 'is-active' : ''}`"
              @click="activeStep = activeStep === i ? -1 : i"
              :title="`${s.agent} · ${s.duration_ms}ms`"
            >
              <div class="sxk-generate__tl-dot">
                <el-icon v-if="s.status === 'success'"><CircleCheckFilled /></el-icon>
                <el-icon v-else-if="s.status === 'warning'"><WarningFilled /></el-icon>
                <el-icon v-else-if="s.status === 'error'"><CircleCloseFilled /></el-icon>
                <span v-else class="sxk-generate__tl-dot-num">{{ i + 1 }}</span>
              </div>
              <div class="sxk-generate__tl-info">
                <div class="sxk-generate__tl-name">{{ shortAgentName(s.agent) }}</div>
                <div class="sxk-generate__tl-time">{{ s.duration_ms }}ms</div>
              </div>
              <span
                v-if="i < currentDraft.agent_trace.length - 1"
                class="sxk-generate__tl-line"
              />
            </div>
          </div>

          <!-- ============ 当前选中节点详情 ============ -->
          <transition name="sxk-fade">
            <div
              v-if="showAgentTrace && currentDraft.agent_trace[activeStep]"
              class="sxk-generate__tl-detail"
            >
              <div
                v-for="(s, i) in currentDraft.agent_trace"
                v-show="activeStep === i"
                :key="`detail-${i}`"
                class="sxk-generate__tl-detail-card"
                :class="`is-${s.status}`"
              >
                <div class="sxk-generate__tl-detail-head">
                  <span class="sxk-generate__tl-detail-idx">步骤 {{ i + 1 }}</span>
                  <span class="sxk-generate__tl-detail-name">{{ s.agent }}</span>
                  <el-tag
                    size="small"
                    :type="s.status === 'success' ? 'success' : s.status === 'warning' ? 'warning' : 'danger'"
                    effect="light"
                  >
                    <el-icon style="margin-right: 3px">
                      <CircleCheckFilled v-if="s.status === 'success'" />
                      <WarningFilled v-else />
                    </el-icon>
                    {{ STATUS_LABEL[s.status] }}
                  </el-tag>
                  <span class="sxk-generate__tl-detail-time">
                    <el-icon><Timer /></el-icon>
                    {{ s.duration_ms }}ms
                  </span>
                </div>
                <div class="sxk-generate__tl-detail-msg">
                  {{ s.message }}
                </div>
                <div class="sxk-generate__tl-detail-foot">
                  <el-button
                    size="small"
                    link
                    type="primary"
                    @click="copyAgentMsg(s.message)"
                  >
                    <el-icon><CopyDocument /></el-icon>
                    复制消息
                  </el-button>
                  <el-button
                    v-if="i > 0"
                    size="small"
                    link
                    type="info"
                    @click="activeStep = i - 1"
                  >
                    <el-icon><ArrowLeft /></el-icon>
                    上一步
                  </el-button>
                  <el-button
                    v-if="i < currentDraft.agent_trace.length - 1"
                    size="small"
                    link
                    type="info"
                    @click="activeStep = i + 1"
                  >
                    下一步
                    <el-icon><ArrowRight /></el-icon>
                  </el-button>
                </div>
              </div>
            </div>
          </transition>

          <!-- ============ 折叠时：摘要信息条 ============ -->
          <div v-if="!showAgentTrace" class="sxk-generate__tl-collapsed">
            <span v-if="currentDraft.validation?.issues?.length" class="sxk-generate__tl-collapsed-warn">
              <el-icon><WarningFilled /></el-icon>
              {{ currentDraft.validation.issues.length }} 个待优化项
            </span>
            <!-- "所有 Agent 步骤已完成"提示默认隐藏（避免与时间线节点信息重复） -->
            <span v-else-if="false" class="sxk-generate__tl-collapsed-ok">
              <el-icon><CircleCheckFilled /></el-icon>
              所有 Agent 步骤已完成
            </span>
            <!-- <el-link type="primary" :underline="false">
              点击展开时间线
              <el-icon><ArrowDown /></el-icon>
            </el-link> -->
          </div>
        </el-card>

        <!-- 版本对比墙 + 当前预览 -->
        <el-card class="sxk-generate__card" shadow="never">
          <template #header>
            <div class="sxk-generate__card-head">
              <div class="sxk-generate__card-head-left">
                <b>初稿对比</b>
                <span class="sxk-generate__card-tip">
                  点击下方任一卡片预览完整内容，满意后点击「选定」进入下一步
                </span>
              </div>
              <el-button size="small" :loading="triggering" @click="onRegenerateDraft">
                <el-icon><Refresh /></el-icon>
                重新生成
              </el-button>
            </div>
          </template>

          <!-- 版本对比卡片墙 -->
          <div class="sxk-generate__version-grid">
            <div
              v-for="v in currentDraft.draft_versions"
              :key="v.index"
              class="sxk-generate__version-card"
              :class="{ 'is-selected': String(v.index) === draftVersionIndex }"
              @click="draftVersionIndex = String(v.index)"
            >
              <div class="sxk-generate__version-card-head">
                <span class="sxk-generate__version-card-radio">
                  <span
                    class="sxk-generate__radio-dot"
                    :class="{ 'is-checked': String(v.index) === draftVersionIndex }"
                  />
                </span>
                <span class="sxk-generate__version-card-no">版本 {{ v.index }}</span>
                <el-tag
                  v-if="String(v.index) === draftVersionIndex"
                  size="small"
                  type="primary"
                  effect="light"
                  class="sxk-generate__version-card-tag"
                >
                  当前查看
                </el-tag>
              </div>
              <div class="sxk-generate__version-card-title">
                {{ v.title || ('版本 ' + v.index) }}
              </div>
              <div class="sxk-generate__version-card-meta">
                <span class="sxk-generate__version-card-stat">
                  <el-icon><Document /></el-icon>
                  {{ v.body?.length || 0 }} 字
                </span>
                <span class="sxk-generate__version-card-stat">
                  <el-icon><CollectionTag /></el-icon>
                  {{ v.tags?.length || 0 }} 标签
                </span>
              </div>
            </div>
          </div>

          <!-- 当前版本完整预览 -->
          <div
            v-for="v in currentDraft.draft_versions"
            v-show="String(v.index) === draftVersionIndex"
            :key="`preview-${v.index}`"
            class="sxk-generate__version-preview"
          >
            <div class="sxk-generate__doc-page">
              <h1 class="sxk-generate__doc-title">{{ v.title }}</h1>
              <div
                class="sxk-generate__doc-content markdown-body"
                v-html="renderArticle(v.body, v.images, v.title)"
              />
              <div v-if="v.tags?.length" class="sxk-generate__doc-tags">
                <el-tag
                  v-for="t in v.tags"
                  :key="t"
                  size="small"
                  type="info"
                  effect="light"
                  style="margin: 2px"
                >
                  #{{ t }}
                </el-tag>
              </div>
            </div>
            <div class="sxk-generate__stage-foot">
              <span class="sxk-generate__stage-foot-tip">
                <el-icon><InfoFilled /></el-icon>
                确认无误后点击「选定此版本」进入多渠道适配
              </span>
              <el-button
                type="primary"
                size="small"
                @click="onSelectDraftVersion(v)"
                :loading="selectingDraft"
              >
                选定此版本 →
              </el-button>
            </div>
          </div>
        </el-card>
      </div>

      <!-- ============ 阶段 1：编辑选定内容 + 多选渠道 ============ -->
      <div v-else-if="draftStep === 1" class="sxk-generate__stage">
        <el-row :gutter="16">
          <!-- 左侧：编辑选定内容 -->
          <el-col :span="16">
            <el-card class="sxk-generate__card" shadow="never">
              <template #header>
                <div class="sxk-generate__card-head">
                  <b>编辑选定内容</b>
                  <span class="sxk-generate__card-tip">
                    改动标题与正文，确认后进入多渠道适配
                  </span>
                </div>
              </template>
              <div class="sxk-generate__edit-title">
                <el-input
                  v-model="draftEditingVersion.title"
                  placeholder="文案标题"
                  size="large"
                >
                  <template #prepend>标题</template>
                </el-input>
              </div>
              <div class="sxk-generate__edit-body">
                <div class="sxk-generate__edit-body-head">
                  <span>正文</span>
                  <span class="sxk-generate__edit-body-cnt">{{ bodyCharCount }} 字</span>
                </div>
                <el-input
                  type="textarea"
                  v-model="draftEditingVersion.body"
                  :autosize="{ minRows: 16, maxRows: 26 }"
                  resize="vertical"
                />
              </div>
              <div v-if="draftEditingVersion.tags?.length" class="sxk-generate__edit-tags">
                <el-tag
                  v-for="t in draftEditingVersion.tags"
                  :key="t"
                  size="small"
                  style="margin: 2px"
                >
                  {{ t }}
                </el-tag>
              </div>
            </el-card>
          </el-col>

          <!-- 右侧：渠道多选 -->
          <el-col :span="8">
            <el-card class="sxk-generate__card sxk-generate__channel-pane" shadow="never">
              <template #header>
                <div class="sxk-generate__card-head">
                  <div class="sxk-generate__channel-pane-head">
                    <b>发布渠道</b>
                    <span class="sxk-generate__card-tip">可多选</span>
                  </div>
                  <span class="sxk-generate__channel-count">
                    已选 {{ selectedChannels.length }} / {{ channelOptions.length }}
                  </span>
                </div>
              </template>
              <!-- 渠道列表（独立滚动区域） -->
              <div class="sxk-generate__channel-scroll">
                <el-checkbox-group v-model="selectedChannels" class="sxk-generate__channel-list">
                  <el-checkbox
                    v-for="ch in channelOptions"
                    :key="ch.name"
                    :value="ch.name"
                    :class="['sxk-generate__channel-item', { 'is-checked': selectedChannels.includes(ch.name) }]"
                  >
                    <!-- 自定义内容：包含虚拟勾选框 + 文案 -->
                    <div class="sxk-generate__channel-content">
                      <!-- 虚拟勾选框（视觉上替代 el-checkbox 原生方框） -->
                      <span
                        class="sxk-generate__channel-check"
                        :class="{ 'is-checked': selectedChannels.includes(ch.name) }"
                      >
                        <el-icon v-if="selectedChannels.includes(ch.name)"><Check /></el-icon>
                      </span>
                      <div class="sxk-generate__channel-info">
                        <div class="sxk-generate__channel-name">{{ ch.display_name }}</div>
                        <div class="sxk-generate__channel-meta">
                          {{ ch.tone }} · {{ ch.format }}
                        </div>
                      </div>
                    </div>
                  </el-checkbox>
                </el-checkbox-group>
              </div>
              <!-- 底部 CTA：sticky 始终可见 -->
              <div class="sxk-generate__channel-foot">
                <el-button
                  type="primary"
                  size="large"
                  class="sxk-generate__channel-submit"
                  @click="onAdapt"
                  :loading="adaptingDraft"
                  :disabled="!selectedChannels.length"
                >
                  <el-icon v-if="!adaptingDraft"><Right /></el-icon>
                  {{ adaptingDraft ? '适配中...' : '确认适配（' + selectedChannels.length + ' 个渠道）' }}
                </el-button>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>

      <!-- ============ 阶段 2：多渠道适配（卡片对比墙 + 预览/编辑）============ -->
      <div v-else class="sxk-generate__stage">
        <el-card class="sxk-generate__card" shadow="never">
          <template #header>
            <div class="sxk-generate__card-head">
              <div class="sxk-generate__card-head-left">
                <b>多渠道适配</b>
                <span class="sxk-generate__card-tip">
                  共 {{ currentDraft.versions?.length || 0 }} 个渠道 · 已配图
                  {{ adaptedCount }} / {{ currentDraft.versions?.length || 0 }}
                </span>
              </div>
              <!-- 阶段 2 顶部操作组（按状态动态展示） -->
              <div class="sxk-generate__stage2-actions">
                <!-- 始终可用：仅导出（无需配图）-->
                <el-button
                  size="small"
                  :icon="Download"
                  :loading="exportingDraft"
                  @click="onExport"
                >
                  {{ exportingDraft ? '导出中' : '导出' }}
                </el-button>
                <!-- 重新配图（完成后可再次生成）-->
                <!-- <el-button
                  v-if="currentDraft.history_id && !finalizingDraft"
                  size="small"
                  type="warning"
                  plain
                  :icon="Refresh"
                  @click="onFinalize"
                >
                  重新配图
                </el-button> -->
                <!-- 主 CTA：生成配图并保存 -->
                <el-button
                  v-if="!currentDraft.history_id"
                  size="default"
                  type="primary"
                  @click="onFinalize"
                  :loading="finalizingDraft"
                >
                  <el-icon v-if="!finalizingDraft"><Picture /></el-icon>
                  {{ finalizingDraft ? '文生图中...' : '生成配图并保存' }}
                </el-button>
                <el-button
                  v-else
                  size="default"
                  type="success"
                  disabled
                >
                  <el-icon><CircleCheckFilled /></el-icon>
                  已保存到历史
                </el-button>
              </div>
            </div>
          </template>

          <!-- 渠道对比卡（横向） -->
          <div class="sxk-generate__version-grid sxk-generate__channel-wall">
            <div
              v-for="v in currentDraft.versions"
              :key="v.index"
              class="sxk-generate__version-card"
              :class="{
                'is-selected': String(v.index) === adaptVersionIndex,
                'is-finalized': v.images?.length > 0
              }"
              @click="adaptVersionIndex = String(v.index)"
            >
              <div class="sxk-generate__version-card-head">
                <span class="sxk-generate__version-card-radio">
                  <span
                    class="sxk-generate__radio-dot"
                    :class="{ 'is-checked': String(v.index) === adaptVersionIndex }"
                  />
                </span>
                <span class="sxk-generate__version-card-no">
                  {{ v.channel || `渠道 ${v.index}` }}
                </span>
                <span
                  class="sxk-generate__version-card-tag"
                  :class="versionStatusClass(v)"
                >
                  <el-icon v-if="v.images?.length > 0"><Picture /></el-icon>
                  <el-icon v-else-if="finalizingDraft"><Loading /></el-icon>
                  <el-icon v-else><Clock /></el-icon>
                  {{ versionStatusText(v) }}
                </span>
              </div>
              <div class="sxk-generate__version-card-meta">
                <span class="sxk-generate__version-card-stat">
                  <el-icon><Document /></el-icon>
                  {{ v.body?.length || 0 }} 字
                </span>
                <span class="sxk-generate__version-card-stat">
                  <el-icon><Picture /></el-icon>
                  {{ v.images?.length || 0 }} 图
                </span>
                <span class="sxk-generate__version-card-stat">
                  <el-icon><Star /></el-icon>
                  {{ (v.votes?.like || 0) - (v.votes?.dislike || 0) }}
                </span>
              </div>
            </div>
          </div>

          <!-- 当前渠道预览/编辑 -->
          <div
            v-for="v in currentDraft.versions"
            v-show="String(v.index) === adaptVersionIndex"
            :key="`preview-${v.index}`"
            class="sxk-generate__version-preview"
          >
            <!-- 顶部工具栏 -->
            <div class="sxk-generate__channel-toolbar">
              <div class="sxk-generate__channel-toolbar-left">
                <span class="sxk-generate__channel-name-lg">
                  {{ v.channel || `渠道 ${v.index}` }}
                </span>
                <span class="sxk-generate__channel-meta-inline">
                  <el-tag v-if="v.channel" size="small" effect="plain" type="info">
                    {{ v.channel }}
                  </el-tag>
                  <span>{{ v.body?.length || 0 }} 字</span>
                  <span>·</span>
                  <span>{{ v.images?.length || 0 }} 图</span>
                </span>
              </div>
              <el-radio-group v-model="genEditMode" size="small" class="sxk-generate__mode-switch">
                <el-radio-button :value="false">
                  <el-icon><View /></el-icon>
                  预览
                </el-radio-button>
                <el-radio-button :value="true">
                  <el-icon><Edit /></el-icon>
                  编辑
                </el-radio-button>
              </el-radio-group>
            </div>

            <!-- 预览 -->
            <div v-if="!genEditMode" class="sxk-generate__doc-page">
              <h1 class="sxk-generate__doc-title">{{ v.title }}</h1>
              <div
                class="sxk-generate__doc-content markdown-body"
                v-html="renderArticle(v.body, v.images, v.title)"
              />
              <div v-if="v.tags?.length" class="sxk-generate__doc-tags">
                <el-tag
                  v-for="t in v.tags"
                  :key="t"
                  size="small"
                  type="info"
                  effect="light"
                  style="margin: 2px"
                >
                  #{{ t }}
                </el-tag>
              </div>
            </div>

            <!-- 编辑 -->
            <div v-else class="sxk-generate__edit-area">
              <div class="sxk-generate__edit-title">
                <el-input v-model="v.title" size="large" placeholder="文案标题">
                  <template #prepend>标题</template>
                </el-input>
              </div>
              <div class="sxk-generate__edit-body">
                <div class="sxk-generate__edit-body-head">
                  <span>正文</span>
                  <span class="sxk-generate__edit-body-cnt">{{ (v.body || '').length }} 字</span>
                </div>
                <el-input
                  type="textarea"
                  v-model="v.body"
                  :autosize="{ minRows: 12, maxRows: 22 }"
                  resize="vertical"
                />
              </div>
              <div v-if="v.images?.length" class="sxk-generate__img-ref-list">
                <div class="sxk-generate__img-ref-head">
                  <el-icon><Picture /></el-icon>
                  配图参考（{{ v.images.length }} 张，预览时自动穿插在正文中）
                </div>
                <div class="sxk-generate__img-ref-grid">
                  <div
                    v-for="(img, i) in v.images"
                    :key="i"
                    class="sxk-generate__img-ref-item"
                  >
                    <img :src="img.url" :alt="img.caption" />
                    <span class="sxk-generate__img-ref-cap">
                      {{ img.caption || `配图 ${i + 1}` }}
                    </span>
                  </div>
                </div>
              </div>
              <div v-else class="sxk-generate__img-ref-empty">
                <el-icon><PictureFilled /></el-icon>
                <span>暂无配图，点击右上「生成配图并保存」可自动配图</span>
              </div>
            </div>

            <!-- 操作按钮：👍/👎 A/B 投票 + SEO 分析 -->
            <div class="sxk-generate__version-tools">
              <span class="sxk-generate__tools-tip">
                <el-icon><InfoFilled /></el-icon>
                对当前渠道版本进行反馈，或查看 SEO 优化建议
              </span>
              <div class="sxk-generate__tools-actions">
                <!-- ============ 反馈组：👍/👎 投票 ============ -->
                <div class="sxk-generate__tools-group">
                  <span class="sxk-generate__tools-group-label">反馈</span>
                  <button
                    class="sxk-generate__vote-btn is-like"
                    :class="{ 'is-active': votedDir(v) === 'like' }"
                    @click="onCastVote(v)"
                    :title="votedDir(v) === 'like' ? '取消点赞' : '点赞'"
                  >
                    <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
                      <path d="M2 21h4V9H2v12zm20-11c0-1.1-.9-2-2-2h-6.31l.95-4.57.03-.32c0-.41-.17-.79-.44-1.06L13.17 1 7.59 6.59C7.22 6.95 7 7.45 7 8v10c0 1.1.9 2 2 2h9c.83 0 1.54-.5 1.84-1.22l3.02-7.05c.09-.23.14-.47.14-.73v-2z" />
                    </svg>
                    <span class="sxk-generate__vote-num">{{ v.votes?.like || 0 }}</span>
                  </button>
                  <button
                    class="sxk-generate__vote-btn is-dislike"
                    :class="{ 'is-active': votedDir(v) === 'dislike' }"
                    @click="onCastVote(v, 'dislike')"
                    :title="votedDir(v) === 'dislike' ? '取消点踩' : '点踩'"
                  >
                    <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
                      <path d="M22 3h-4v12h4V3zm-20 11c0 1.1.9 2 2 2h6.31l-.95 4.57-.03.32c0 .41.17.79.44 1.06L10.83 23l5.59-5.59c.36-.36.58-.86.58-1.41V6c0-1.1-.9-2-2-2H5c-.83 0-1.54.5-1.84 1.22L.14 12.27c-.09.23-.14.47-.14.73v2z" />
                    </svg>
                    <span class="sxk-generate__vote-num">{{ v.votes?.dislike || 0 }}</span>
                  </button>
                </div>

                <!-- ============ 分析组：SEO 分析 ============ -->
                <div class="sxk-generate__tools-group">
                  <span class="sxk-generate__tools-group-label">分析</span>
                  <el-button
                    size="small"
                    type="primary"
                    plain
                    @click="onAnalyzeSeo(v)"
                  >
                    <el-icon><Search /></el-icon>
                    SEO 分析
                  </el-button>
                </div>

                <!-- ============ 重做组：重新生成本渠道配图（已完成才出现）============ -->
                <!-- <div v-if="currentDraft.history_id && !finalizingDraft" class="sxk-generate__tools-group">
                  <span class="sxk-generate__tools-group-label">重做</span>
                  <el-tooltip
                    content="仅对当前选中渠道重新生成配图（不覆盖其他渠道）"
                    placement="top"
                  >
                    <el-button
                      class="sxk-generate__tools-regen"
                      size="small"
                      text
                      bg
                      :icon="Refresh"
                      @click="onRegenerateCurrentChannel(v)"
                      :loading="regeneratingChannelIdx === v.index"
                    >
                      重配本渠道
                    </el-button>
                  </el-tooltip>
                </div> -->
              </div>
            </div>
          </div>

        </el-card>
      </div>
    </basic-block>

    <!-- ============ 流程结束弹窗（页面级）============ -->
    <el-dialog
      v-model="doneDrawerVisible"
      width="380px"
      :show-close="false"
      :close-on-click-modal="false"
      align-center
      append-to-body
      custom-class="sxk-generate__done-dialog"
    >
      <div v-if="currentDraft" class="sxk-generate__done-drawer">
        <div class="sxk-generate__done-bg" />
        <div class="sxk-generate__done-body">
          <!-- 右上角关闭按钮（在白色 body 区域，不在绿色背景上） -->
          <button
            class="sxk-generate__done-close"
            aria-label="关闭"
            @click="onStayHere"
          >
            <el-icon><Close /></el-icon>
          </button>
          <div class="sxk-generate__done-icon">
            <el-icon><CircleCheckFilled /></el-icon>
          </div>
          <h2 class="sxk-generate__done-title">多渠道适配已完成</h2>

          <!-- 一行紧凑的元信息 chip（取代 3 张统计卡） -->
          <div class="sxk-generate__done-meta">
            <span class="sxk-generate__done-meta-chip">
              <el-icon><Document /></el-icon>
              {{ currentDraft.history_id }}
            </span>
            <span class="sxk-generate__done-meta-divider">·</span>
            <span class="sxk-generate__done-meta-text">
              {{ currentDraft.versions?.length || 0 }} 渠道
            </span>
            <span class="sxk-generate__done-meta-divider">·</span>
            <span class="sxk-generate__done-meta-text">
              {{ totalImages }} 配图
            </span>
            <span class="sxk-generate__done-meta-divider">·</span>
            <span class="sxk-generate__done-meta-text">
              +{{ totalNetVotes }} 票
            </span>
          </div>

          <div class="sxk-generate__done-actions">
            <el-button
              type="primary"
              size="large"
              class="sxk-generate__done-btn sxk-generate__done-btn--primary"
              @click="onGoHistory"
            >
              <el-icon><View /></el-icon>
              查看完整历史
            </el-button>
            <el-button
              size="large"
              plain
              class="sxk-generate__done-btn"
              @click="onStartNew"
            >
              <el-icon><MagicStick /></el-icon>
              开始新创作
            </el-button>
          </div>
        </div>
      </div>
      <template #footer>
        <span></span>
      </template>
    </el-dialog>

    <!-- SEO 分析弹窗 -->
    <el-dialog
      v-model="seoVisible"
      width="640px"
      align-center
      :show-close="true"
      custom-class="sxk-generate__seo-dialog"
    >
      <template #header>
        <div class="sxk-generate__seo-header">
          <div class="sxk-generate__seo-header-icon">
            <el-icon><DataAnalysis /></el-icon>
          </div>
          <div class="sxk-generate__seo-header-text">
            <div class="sxk-generate__seo-header-title">SEO 智能分析</div>
            <div class="sxk-generate__seo-header-sub" v-if="seoTarget">
              {{ seoTarget.channel }} · {{ seoTarget.title || '未命名版本' }}
            </div>
          </div>
        </div>
      </template>
      <div v-if="seoResult" v-loading="seoLoading" class="sxk-generate__seo">
        <!-- ============ 评分主卡 ============ -->
        <div class="sxk-generate__seo-hero">
          <!-- 左侧：环形评分 -->
          <div class="sxk-generate__seo-ring">
            <svg viewBox="0 0 120 120" class="sxk-generate__seo-ring-svg">
              <circle
                cx="60"
                cy="60"
                r="50"
                class="sxk-generate__seo-ring-bg"
                stroke-width="10"
                fill="none"
              />
              <circle
                cx="60"
                cy="60"
                r="50"
                class="sxk-generate__seo-ring-fg"
                :stroke="seoScoreColor"
                stroke-width="10"
                fill="none"
                :stroke-dasharray="circProgress(seoResult.score).length"
                :stroke-dashoffset="circProgress(seoResult.score).offset"
                stroke-linecap="round"
                transform="rotate(-90 60 60)"
              />
            </svg>
            <div class="sxk-generate__seo-ring-text">
              <div class="sxk-generate__seo-ring-num" :style="{ color: seoScoreColor }">
                {{ seoResult.score }}
              </div>
              <div class="sxk-generate__seo-ring-tip">/100</div>
            </div>
          </div>
          <!-- 右侧：评分等级 + 关键词 + 维度统计 -->
          <div class="sxk-generate__seo-side">
            <div class="sxk-generate__seo-grade" :style="{ background: seoScoreColor + '15', color: seoScoreColor }">
              {{ seoScoreGrade }}
            </div>
            <!-- 维度统计胶囊 -->
            <div class="sxk-generate__seo-dimstats">
              <div class="sxk-generate__seo-dimstat is-good">
                <el-icon><CircleCheckFilled /></el-icon>
                <span class="sxk-generate__seo-dimstat-num">{{ seoDimCount('good') }}</span>
                <span class="sxk-generate__seo-dimstat-label">良好</span>
              </div>
              <div class="sxk-generate__seo-dimstat is-warn">
                <el-icon><WarningFilled /></el-icon>
                <span class="sxk-generate__seo-dimstat-num">{{ seoDimCount('warning') }}</span>
                <span class="sxk-generate__seo-dimstat-label">警告</span>
              </div>
              <div class="sxk-generate__seo-dimstat is-bad">
                <el-icon><CircleCloseFilled /></el-icon>
                <span class="sxk-generate__seo-dimstat-num">{{ seoDimCount('danger') }}</span>
                <span class="sxk-generate__seo-dimstat-label">错误</span>
              </div>
            </div>
            <!-- 关键词 -->
            <div v-if="seoResult.keywords?.length" class="sxk-generate__seo-kw">
              <span class="sxk-generate__seo-kw-label">关键词</span>
              <el-tag
                v-for="(k, idx) in seoResult.keywords"
                :key="k"
                size="small"
                effect="light"
                :type="idx === 0 ? 'primary' : 'info'"
                class="sxk-generate__seo-kw-tag"
              >
                #{{ k }}
              </el-tag>
            </div>
          </div>
        </div>

        <!-- ============ 维度分析卡（4 维）============ -->
        <div class="sxk-generate__seo-dims">
          <div
            v-for="dim in seoDimensions"
            :key="dim.key"
            class="sxk-generate__seo-dim"
            :class="['is-' + dim.level]"
          >
            <div class="sxk-generate__seo-dim-head">
              <el-icon class="sxk-generate__seo-dim-icon">
                <component :is="dim.iconComp" />
              </el-icon>
              <span class="sxk-generate__seo-dim-name">{{ dim.name }}</span>
              <span
                class="sxk-generate__seo-dim-score"
                :style="{ color: dim.scoreColor }"
              >
                {{ dim.score }} 分
              </span>
            </div>
            <div class="sxk-generate__seo-dim-meta">
              <span>{{ dim.meta }}</span>
            </div>
            <el-progress
              :percentage="dim.score / dim.max * 100"
              :color="dim.scoreColor"
              :show-text="false"
              :stroke-width="4"
              class="sxk-generate__seo-dim-bar"
            />
          </div>
        </div>

        <!-- ============ 优化建议列表 ============ -->
        <div class="sxk-generate__seo-section">
          <div class="sxk-generate__seo-section-title">
            <el-icon><Aim /></el-icon>
            优化建议
          </div>
          <div class="sxk-generate__seo-suggestions">
            <div
              v-for="(s, i) in seoResult.suggestions"
              :key="i"
              class="sxk-generate__seo-suggestion"
              :class="['is-' + s.level]"
            >
              <div class="sxk-generate__seo-suggestion-status">
                <el-icon v-if="s.level === 'good'"><CircleCheckFilled /></el-icon>
                <el-icon v-else-if="s.level === 'warning'"><WarningFilled /></el-icon>
                <el-icon v-else><CircleCloseFilled /></el-icon>
              </div>
              <div class="sxk-generate__seo-suggestion-body">
                <div class="sxk-generate__seo-suggestion-type">
                  {{ seoTypeLabel(s.type) }}
                </div>
                <div class="sxk-generate__seo-suggestion-msg">
                  {{ s.message }}
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- ============ Meta 描述建议 ============ -->
        <div v-if="seoResult.stats.meta_description" class="sxk-generate__seo-section">
          <div class="sxk-generate__seo-section-title">
            <el-icon><Document /></el-icon>
            建议 Meta 描述
            <el-button
              size="small"
              text
              type="primary"
              @click="onCopyMeta"
            >
              <el-icon><CopyDocument /></el-icon>
              复制
            </el-button>
          </div>
          <div class="sxk-generate__seo-meta">
            {{ seoResult.stats.meta_description }}
          </div>
        </div>
      </div>
      <template #footer>
        <div class="sxk-generate__seo-footer">
          <span class="sxk-generate__seo-footer-tip">
            建议将得分提升至 80+ 后再发布
          </span>
          <el-button @click="seoVisible = false">关闭</el-button>
          <el-button
            v-if="seoResult"
            type="primary"
            :icon="Refresh"
            @click="onReanalyze"
          >
            重新分析
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
/**
 * 内容生成页 Script 逻辑
 *
 * 多阶段草稿流程（与后端参考版 B2B-SXK-FastApi/frontend 对齐）：
 *   阶段 0：createDraft → 展示 3 个初稿 → 选定一个版本 → 阶段 1
 *   阶段 1：编辑 title/body + 多选渠道 → adapt → 阶段 2
 *   阶段 2：多渠道版本展示 → 文生图 → finalize → 落 history
 *
 * 草稿状态机：stage ∈ draft | editing | adapted | done
 * 持久化：localStorage['sxk-draft-id']，刷新自动恢复
 */
import { ref, reactive, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  MagicStick,
  Refresh,
  ArrowRight,
  Download,
  Search,
  Picture,
  Box,
  TrendCharts,
  Share,
  Promotion,
  Message,
  Document,
  Aim,
  CircleCheckFilled,
  Delete,
  InfoFilled,
  Connection,
  Timer,
  WarningFilled,
  CollectionTag,
  CircleCloseFilled,
  CopyDocument,
  ArrowLeft,
  ArrowDown,
  Right,
  Loading,
  Clock,
  Star,
  View,
  Edit,
  PictureFilled,
  EditPen,
  Folder,
  DataAnalysis,
  Files,
  Reading,
  Close,
  Check
} from '@element-plus/icons-vue'
import BasicBlock from '@/components/basic-block/main.vue'
import { sxkApi } from '@/mock/sxkApi'
import { renderMarkdown, renderArticle as renderArticleUtil } from './md'

// ---------- 路由与基础状态 ----------
const route = useRoute()
const router = useRouter()

// 触发状态
const triggering = ref(false)
const selectingDraft = ref(false)
const adaptingDraft = ref(false)
const finalizingDraft = ref(false)
// 重新生成当前渠道配图（loading 状态）
const regeneratingChannelIdx = ref(null)
// 阶段 2 是否已完成（保存到历史后置 true，刷新"多渠道适配"步骤状态为"完成"）
const stage2Completed = ref(false)

// Agent 链路
const showAgentTrace = ref(true)   // 默认展开（时间线节点本身已展示关键信息，详情按需展开）
const activeStep = ref(-1)         // 当前选中的时间线节点索引（-1 = 未选）
// 状态映射
const STATUS_LABEL = {
  success: '成功',
  warning: '警告',
  error: '失败',
  pending: '等待'
}
// Agent 名缩写（去掉 "Agent" 后缀）
const shortAgentName = (name) => String(name || '').replace(/Agent$/i, '').trim() || name

// 阶段 2 渠道版本状态/分类
const adaptedCount = computed(() => {
  return (currentDraft.value?.versions || []).filter((v) => v.images?.length > 0).length
})
const versionStatusClass = (v) => {
  if (v.images?.length > 0) return 'is-done'
  if (finalizingDraft.value) return 'is-running'
  return 'is-pending'
}
const versionStatusText = (v) => {
  if (v.images?.length > 0) return '已配图'
  if (finalizingDraft.value) return '配图中'
  return '待开始'
}
// 完成卡统计
const totalImages = computed(() => {
  return (currentDraft.value?.versions || []).reduce(
    (sum, v) => sum + (v.images?.length || 0), 0
  )
})
const totalNetVotes = computed(() => {
  return (currentDraft.value?.versions || []).reduce(
    (sum, v) => sum + ((v.votes?.like || 0) - (v.votes?.dislike || 0)), 0
  )
})
// 完成态按钮跳转
const onGoHistory = () => {
  doneDrawerVisible.value = false
  if (currentDraft.value?.history_id) {
    // 携带 openDetail 参数，跳转后由 history 列表页自动打开该条详情弹窗
    router.push({
      path: '/history/index',
      query: {
        openDetail: currentDraft.value.history_id,
        highlight: currentDraft.value.history_id
      }
    })
  } else {
    router.push('/history/index')
  }
}
const onStartNew = () => {
  doneDrawerVisible.value = false
  ElMessageBox.confirm(
    '开始新创作将清空当前草稿与表单，确定继续？',
    '开始新创作',
    { type: 'warning', confirmButtonText: '开始新创作', cancelButtonText: '取消' }
  )
    .then(() => {
      onDiscardDraft()
    })
    .catch(() => {})
}
const onStayHere = () => {
  // 关闭按钮：仅关闭弹窗，不弹提示（用户主动关闭不应被打断）
  doneDrawerVisible.value = false
}
// 显式关闭（保留原 onStayHere 的语义以防别处调用）
const onCloseDialog = () => {
  doneDrawerVisible.value = false
}
// 复制消息
const copyAgentMsg = async (msg) => {
  try {
    await navigator.clipboard.writeText(msg || '')
    ElMessage.success('已复制到剪贴板')
  } catch {
    ElMessage.warning('复制失败，请手动复制')
  }
}
// 阶段 2 预览/编辑切换
const genEditMode = ref(false)
// SEO 弹窗
const seoVisible = ref(false)
const seoResult = ref(null)
const seoLoading = ref(false)
// 当前正在分析的渠道版本（弹窗标题展示）
const seoTarget = ref(null)
// 图标名 → 组件映射（供 SEO 维度动态渲染）
const iconMap = {
  EditPen,
  Document,
  Files,
  Reading,
  DataAnalysis,
  Aim
}

// 草稿状态
const currentDraft = ref(null)
// 阶段 0/1/2 的激活 Tab
const draftVersionIndex = ref('1')
const adaptVersionIndex = ref('1')
// 完成态抽屉（必须在 currentDraft 之后声明，因为 watch 依赖它）
const doneDrawerVisible = ref(false)
// 监听 history_id 变化自动打开抽屉（每次新保存时触发）
watch(
  () => currentDraft.value?.history_id,
  (newId, oldId) => {
    if (newId && newId !== oldId) {
      doneDrawerVisible.value = true
    }
  }
)

// 阶段 1：编辑中的版本（深拷贝 selected_version）
const draftEditingVersion = ref(null)
// 阶段 1：选中的渠道数组
const selectedChannels = ref([])

// 表单引用
const formRef = ref(null)

// ---------- 表单数据 ----------
const form = reactive({
  product_id: '',
  scene_code: 'product_intro',
  template_id: '',
  params: {}
})

const rules = {
  product_id: [{ required: true, message: '请选择产品', trigger: 'change' }],
  scene_code: [{ required: true, message: '请选择场景', trigger: 'change' }]
}

// ---------- 元数据：场景 / 产品 / 模板 / 渠道 ----------
const scenes = ref([])
const productOptions = ref([])
const sceneTemplates = ref([])
const channelOptions = ref([])

// ---------- 阶段步骤配置（用于步骤条 / 摘要）----------
const stepDefs = [
  {
    title: '生成初稿',
    desc: '检索 · 生成 · 校验',
    summary: '选择 1 个最符合预期的初稿，进入下一步'
  },
  {
    title: '渠道适配',
    desc: '选版改内容 · 多选渠道',
    summary: '编辑选定初稿，并选择发布渠道'
  },
  {
    title: '多渠道适配',
    desc: '文生图 · 保存',
    summary: '为各渠道生成配图，并保存到生成历史'
  }
]

const stepClass = (i) => ({
  // 阶段 2 完成时也标记为 done（视觉上显示为绿色对勾）
  'is-done': i < draftStep.value || (i === 2 && stage2Completed.value),
  'is-active': i === draftStep.value && !(i === 2 && stage2Completed.value),
  'is-wait': i > draftStep.value && !(i === 2 && stage2Completed.value),
  'is-clickable': canJumpTo(i)
})

const canJumpTo = (i) => {
  // 已完成的步骤可以点击回退（便于修改初稿）
  // 阶段 2 已完成时也不允许再"跳回"（已完成的工作不应被覆盖）
  if (i === 2 && stage2Completed.value) return false
  return i < draftStep.value && currentDraft.value
}

const onStepJump = (i) => {
  if (!canJumpTo(i)) return
  // 仅支持回退到阶段 0（已选定草稿进入 1/2 后，要回 0 需要保存当前版本）
  ElMessage.info(`已切回：${stepDefs[i].title}`)
  draftStep.value = i
}

const confirmDiscard = () => {
  ElMessageBox.confirm(
    '放弃当前草稿后，所有阶段进度将丢失，确定继续？',
    '放弃草稿',
    { type: 'warning', confirmButtonText: '确定放弃', cancelButtonText: '取消' }
  )
    .then(() => onDiscardDraft())
    .catch(() => {})
}

const SCENE_ICON_MAP = {
  product_intro: Box,
  competitor: TrendCharts,
  channel_adapt: Share,
  email: Message,
  event: Promotion,
  other: Document
}
function getSceneIcon(sceneCode) {
  return SCENE_ICON_MAP[sceneCode] || Document
}

// ---------- 计算属性 ----------
const currentScene = computed(() =>
  scenes.value.find((s) => s.scene_code === form.scene_code)
)

const draftStep = computed(() => {
  const s = currentDraft.value?.stage
  if (!s || s === 'draft') return 0
  if (s === 'editing') return 1
  return 2 // adapted / done
})

const stepTitle = computed(() => {
  return ['生成初稿', '编辑与渠道', '多渠道适配'][draftStep.value]
})

const bodyCharCount = computed(() => (draftEditingVersion.value?.body || '').length)

// Agent 链路统计（用于头部总览）
const agentSuccessCount = computed(() => {
  const trace = currentDraft.value?.agent_trace || []
  return trace.filter((s) => s.status === 'success').length
})
const agentTotalDuration = computed(() => {
  const trace = currentDraft.value?.agent_trace || []
  return trace.reduce((sum, s) => sum + (s.duration_ms || 0), 0)
})

const seoScoreColor = computed(() => {
  const s = seoResult.value?.score ?? 0
  return s >= 80 ? '#16a34a' : s >= 60 ? '#f59e0b' : '#ef4444'
})

// 评分等级（优秀/良好/待优化）
const seoScoreGrade = computed(() => {
  const s = seoResult.value?.score ?? 0
  if (s >= 90) return '优秀'
  if (s >= 80) return '良好'
  if (s >= 60) return '合格'
  if (s >= 40) return '待优化'
  return '较差'
})

// 4 个分析维度
const seoDimensions = computed(() => {
  if (!seoResult.value) return []
  const { stats, suggestions } = seoResult.value
  const findLevel = (type) => {
    const s = (suggestions || []).find((x) => x.type === type)
    return s?.level || 'good'
  }
  // 颜色辅助
  const colorFor = (lvl) =>
    lvl === 'good' ? '#16a34a' : lvl === 'warning' ? '#f59e0b' : '#ef4444'
  // 各维度满分
  const items = [
    { key: 'title', name: '标题', max: 25, meta: `${stats.title_length} 字（建议 15~30）`, icon: 'EditPen' },
    { key: 'body', name: '正文', max: 30, meta: `${stats.body_length} 字（建议 200~1500）`, icon: 'Document' },
    { key: 'structure', name: '结构', max: 20, meta: `${stats.headings} 个小节（建议 ≥2）`, icon: 'Files' },
    { key: 'readability', name: '易读', max: 25, meta: `平均句长 ${stats.avg_sentence_length} 字（建议 10~35）`, icon: 'Reading' }
  ]
  return items.map((it) => {
    const level = findLevel(it.key)
    const score = level === 'good' ? it.max : level === 'warning' ? Math.round(it.max * 0.5) : 0
    return {
      ...it,
      level,
      score,
      scoreColor: colorFor(level),
      iconComp: iconMap[it.icon] || 'EditPen'
    }
  })
})

// 维度数量统计
function seoDimCount(level) {
  if (!seoResult.value?.suggestions) return 0
  return seoResult.value.suggestions.filter((s) => s.level === level).length
}

// 维度类型 label
const typeLabelMap = {
  title: '标题',
  body: '正文',
  structure: '结构',
  readability: '可读性'
}
function seoTypeLabel(type) {
  return typeLabelMap[type] || type
}

// 环形进度计算
function circProgress(score) {
  const C = 2 * Math.PI * 50 // 圆周长 ≈ 314.16
  const percent = Math.max(0, Math.min(100, score)) / 100
  const length = C.toFixed(2)
  const offset = (C * (1 - percent)).toFixed(2)
  return { length, offset }
}

// 重新分析
async function onReanalyze() {
  if (!seoTarget.value) return
  await onAnalyzeSeo(seoTarget.value)
}

// 复制 Meta 描述
async function onCopyMeta() {
  const txt = seoResult.value?.stats?.meta_description
  if (!txt) return
  try {
    await navigator.clipboard.writeText(txt)
    ElMessage.success('Meta 描述已复制')
  } catch {
    ElMessage.warning('复制失败，请手动选择复制')
  }
}

// ---------- Markdown / 文章式渲染 ----------
function renderArticle(body, images, title) {
  return renderArticleUtil(body || '', images || [], title || '')
}

// ---------- 初始化 ----------
const DRAFT_STORAGE_KEY = 'sxk-draft-id'

onMounted(async () => {
  // 1) 拉取基础数据
  const tasks = [
    loadProductOptions(),
    loadSceneSchemas(),
    loadChannels()
  ]
  await Promise.allSettled(tasks)

  // 2) 处理路由 query
  const { gid, scene, tid } = route.query
  if (scene) form.scene_code = String(scene)
  if (tid) form.template_id = String(tid)

  // 3) 恢复草稿（优先级最高：先看 gid，再看 localStorage）
  if (gid) {
    await loadHistoryAsContext(String(gid))
  } else {
    const savedDraftId = localStorage.getItem(DRAFT_STORAGE_KEY)
    if (savedDraftId) {
      try {
        await loadDraft(savedDraftId)
      } catch {
        localStorage.removeItem(DRAFT_STORAGE_KEY)
      }
    }
    if (!currentDraft.value) {
      applySceneDefaults()
      await loadSceneTemplates()
      if (tid) await onTemplateChange(String(tid))
    }
  }
})

onBeforeUnmount(() => {
  // 草稿持久化由 sxkApi 内部管理；此处无需清理
})

// 监听场景切换
watch(
  () => form.scene_code,
  () => {
    if (currentDraft.value) return // 草稿进行中不要重置表单
    applySceneDefaults()
    loadSceneTemplates()
  }
)

// ---------- 业务方法：基础数据加载 ----------
async function loadProductOptions() {
  try {
    const resp = await sxkApi.listProducts({ size: 100 })
    productOptions.value = resp.data?.items || []
  } catch {
    productOptions.value = []
  }
}

async function loadSceneSchemas() {
  try {
    const resp = await sxkApi.getSceneSchemas()
    scenes.value = resp.data?.scenes || []
  } catch {
    scenes.value = []
  }
}

async function loadChannels() {
  try {
    const resp = await sxkApi.listChannels()
    channelOptions.value = resp.data || []
  } catch {
    channelOptions.value = []
  }
}

function applySceneDefaults() {
  if (!currentScene.value) return
  const next = {}
  for (const p of currentScene.value.params) {
    next[p.key] = ''
  }
  form.params = next
}

async function loadSceneTemplates() {
  if (!form.scene_code) {
    sceneTemplates.value = []
    return
  }
  try {
    const resp = await sxkApi.listTemplates({ page: 1, size: 100, scene_code: form.scene_code })
    sceneTemplates.value = resp.data?.items || []
  } catch {
    sceneTemplates.value = []
  }
}

async function onTemplateChange(templateId) {
  if (!templateId) {
    if (form.params.prompt) delete form.params.prompt
    return
  }
  try {
    const resp = await sxkApi.getTemplate(templateId, form.scene_code)
    if (resp.code === 0 && resp.data) {
      form.params.prompt = resp.data.prompt || ''
    }
  } catch {
    /* 失败不阻塞 */
  }
}

function onProductChange() {
  /* 占位 */
}

// ---------- 业务方法：阶段 0 → 1 → 2 ----------
async function onTrigger() {
  if (!formRef.value) return
  try {
    await formRef.value.validate()
  } catch {
    return
  }
  triggering.value = true
  try {
    const resp = await sxkApi.createDraft({
      product_id: form.product_id,
      scene_code: form.scene_code,
      template_id: form.template_id,
      style: '专业严谨',
      params: form.params
    })
    if (resp.code !== 0) {
      ElMessage.error(resp.msg || '创建草稿失败')
      return
    }
    currentDraft.value = resp.data
    draftVersionIndex.value = '1'
    activeStep.value = -1
    showAgentTrace.value = false
    localStorage.setItem(DRAFT_STORAGE_KEY, resp.data.id)
    ElMessage.success('已生成 ' + (resp.data.draft_versions?.length || 0) + ' 个初稿')
  } catch (e) {
    ElMessage.error('创建草稿失败：' + (e?.message || '未知错误'))
  } finally {
    triggering.value = false
  }
}

async function onRegenerateDraft() {
  if (!currentDraft.value) return
  triggering.value = true
  try {
    const resp = await sxkApi.regenerateDraft(currentDraft.value.id)
    if (resp.code !== 0) {
      ElMessage.error(resp.msg || '重新生成失败')
      return
    }
    currentDraft.value = resp.data
    draftVersionIndex.value = '1'
    ElMessage.success('已重新生成初稿')
  } catch (e) {
    ElMessage.error('重新生成失败：' + (e?.message || '未知错误'))
  } finally {
    triggering.value = false
  }
}

async function onSelectDraftVersion(v) {
  if (!currentDraft.value) return
  selectingDraft.value = true
  try {
    const resp = await sxkApi.selectDraftVersion(currentDraft.value.id, v)
    if (resp.code !== 0) {
      ElMessage.error(resp.msg || '选定失败')
      return
    }
    currentDraft.value = resp.data
    draftEditingVersion.value = JSON.parse(JSON.stringify(resp.data.selected_version || v))
    selectedChannels.value = []
    ElMessage.success('已选定，进入渠道适配')
  } catch (e) {
    ElMessage.error('选定失败：' + (e?.message || '未知错误'))
  } finally {
    selectingDraft.value = false
  }
}

async function onAdapt() {
  if (!currentDraft.value) return
  if (!selectedChannels.value.length) {
    ElMessage.warning('请至少选择一个渠道')
    return
  }
  adaptingDraft.value = true
  try {
    // 先把 step1 的编辑写回 selected_version
    await sxkApi.selectDraftVersion(currentDraft.value.id, draftEditingVersion.value)
    // 再做多渠道适配
    const resp = await sxkApi.adaptDraft(currentDraft.value.id, selectedChannels.value)
    if (resp.code !== 0) {
      ElMessage.error(resp.msg || '适配失败')
      return
    }
    currentDraft.value = resp.data
    adaptVersionIndex.value = '1'
    ElMessage.success('已适配 ' + selectedChannels.value.length + ' 个渠道')
  } catch (e) {
    ElMessage.error('适配失败：' + (e?.message || '未知错误'))
  } finally {
    adaptingDraft.value = false
  }
}

async function onFinalize() {
  if (!currentDraft.value) return
  finalizingDraft.value = true
  try {
    const resp = await sxkApi.finalizeDraft(currentDraft.value.id)
    if (resp.code !== 0) {
      ElMessage.error(resp.msg || '保存失败')
      return
    }
    currentDraft.value = resp.data
    // 标记阶段 2 已完成（让步骤条"多渠道适配"显示为"完成"）
    stage2Completed.value = true
    ElMessage.success('配图完成，已保存到历史记录')
  } catch (e) {
    ElMessage.error('保存失败：' + (e?.message || '未知错误'))
  } finally {
    finalizingDraft.value = false
  }
}

/**
 * 重新生成当前渠道的配图
 * 后端目前没有单渠道配图接口，但只对已保存的草稿进行「替换」语义
 */
async function onRegenerateCurrentChannel(version) {
  if (!version || !currentDraft.value) return
  regeneratingChannelIdx.value = version.index
  try {
    // 二次确认：避免误触
    try {
      await ElMessageBox.confirm(
        `确认要重新生成「${version.channel}」渠道的配图吗？\n\n本操作仅替换当前渠道的配图，其他渠道不受影响。`,
        '重新生成配图',
        {
          type: 'warning',
          confirmButtonText: '确认重配',
          cancelButtonText: '取消'
        }
      )
    } catch {
      return // 用户取消
    }
    // 调用后端 finalize 重新生成所有渠道配图
    // 注意：当前后端是全渠道重新配图，"仅本渠道"是前端 UI 承诺
    const resp = await sxkApi.finalizeDraft(currentDraft.value.id)
    if (resp.code !== 0) {
      ElMessage.error(resp.msg || '重配失败')
      return
    }
    currentDraft.value = resp.data
    ElMessage.success(`「${version.channel}」渠道配图已重新生成`)
  } catch (e) {
    if (e !== 'cancel' && e?.message !== 'cancel') {
      ElMessage.error('重配失败：' + (e?.message || '未知错误'))
    }
  } finally {
    regeneratingChannelIdx.value = null
  }
}

function onDiscardDraft() {
  ElMessageBox.confirm('确认放弃当前草稿？已生成的内容将不会保存。', '放弃草稿', {
    type: 'warning',
    confirmButtonText: '确认放弃',
    cancelButtonText: '继续编辑'
  })
    .then(() => {
      currentDraft.value = null
      draftEditingVersion.value = null
      selectedChannels.value = []
      localStorage.removeItem(DRAFT_STORAGE_KEY)
      ElMessage.info('已放弃草稿')
    })
    .catch(() => {})
}

async function loadDraft(draftId) {
  const resp = await sxkApi.getDraft(draftId)
  if (resp.code !== 0) {
    throw new Error(resp.msg || '草稿不存在')
  }
  currentDraft.value = resp.data
  if (resp.data.selected_version) {
    draftEditingVersion.value = JSON.parse(JSON.stringify(resp.data.selected_version))
  }
  selectedChannels.value = [...(resp.data.channels || [])]
}

// ---------- 业务方法：辅助功能 ----------
async function loadHistoryAsContext(gid) {
  try {
    const resp = await sxkApi.getGeneration(gid)
    if (resp.code !== 0) {
      ElMessage.warning('该历史记录不存在')
      return
    }
    const gen = resp.data
    form.product_id = gen.product?.product_id || ''
    form.scene_code = gen.scene_code || 'product_intro'
    // 从历史记录重建为「草稿」：当作已选定版本，跳到阶段 1
    currentDraft.value = {
      id: 'from_history_' + gid,
      product_id: gen.product?.product_id,
      product_name: gen.product?.name,
      scene_code: gen.scene_code,
      scene_name: gen.scene_name,
      style: gen.style,
      stage: 'adapted', // 直接跳到阶段 2
      draft_versions: gen.versions,
      selected_version: gen.versions[0],
      versions: gen.versions,
      channels: [],
      agent_trace: [],
      validation: { validated: gen.validated, issues: [] },
      history_id: gid
    }
    draftVersionIndex.value = '1'
    adaptVersionIndex.value = '1'
  } catch (e) {
    console.error('[Generate] load history failed', e)
  }
}

// 导出中状态（防止重复点击）
const exportingDraft = ref(false)

async function onExport() {
  if (!currentDraft.value?.history_id) {
    ElMessage.warning('当前内容尚未保存到历史，无法导出')
    return
  }
  if (exportingDraft.value) return
  exportingDraft.value = true
  try {
    await sxkApi.exportDocx(currentDraft.value.history_id)
    ElMessage.success('已开始导出，可在浏览器下载目录查看')
  } catch (e) {
    ElMessage.error('导出失败：' + (e?.message || '未知错误'))
  } finally {
    exportingDraft.value = false
  }
}

// A/B 投票：按版本投票，同方向再点 = 取消
function votedDir(v) {
  // 简单实现：用 voters 对象存当前用户投票
  return v._myVote || ''
}
async function onCastVote(v, dir = 'like') {
  if (!currentDraft.value?.history_id) {
    ElMessage.info('保存到历史记录后才能投票')
    return
  }
  const cur = v._myVote || ''
  const next = cur === dir ? '' : dir
  // 乐观更新
  v.votes = v.votes || { like: 0, dislike: 0 }
  v.voters = v.voters || {}
  if (cur) v.votes[cur] = Math.max(0, v.votes[cur] - 1)
  if (next) v.votes[next] = (v.votes[next] || 0) + 1
  v._myVote = next
  try {
    await sxkApi.castVote(currentDraft.value.history_id, v.index, next)
  } catch (e) {
    // 回滚
    if (cur) v.votes[cur] = (v.votes[cur] || 0) + 1
    if (next) v.votes[next] = Math.max(0, v.votes[next] - 1)
    v._myVote = cur
    ElMessage.error('投票失败：' + (e?.message || '未知错误'))
  }
}

async function onAnalyzeSeo(v) {
  try {
    // 记录分析目标（弹窗标题展示）
    seoTarget.value = { channel: v.channel, title: v.title, body: v.body }
    seoLoading.value = true
    // 首次打开弹窗，loading 才有意义
    if (!seoVisible.value) {
      seoResult.value = null
      seoVisible.value = true
    }
    const resp = await sxkApi.analyzeSeo({ title: v.title, body: v.body })
    if (resp.code !== 0) {
      ElMessage.error(resp.msg || 'SEO 分析失败')
      return
    }
    seoResult.value = resp.data
  } catch (e) {
    ElMessage.error('SEO 分析失败：' + (e?.message || '未知错误'))
  } finally {
    seoLoading.value = false
  }
}

// 给 md 工具方法的引用（避免 import 警告）
void renderMarkdown
</script>

<style lang="scss" scoped>
// ============================================================
// 内容生成页样式 —— 全部使用全局设计 Token
// 结构：1) 主框架 2) 阶段指示 3) 场景网格 4) 版本 Tab
//       5) Word 文档式展示  6) 编辑区  7) 渠道多选  8) SEO
// ============================================================

// ---------- 主框架 ----------
.sxk-generate {
  display: flex;
  gap: $spacing-md;
  align-items: stretch;

  @media (max-width: 1100px) {
    flex-direction: column;
  }
}

// ---------- 左栏：生成配置 + 阶段指示 ----------
.sxk-generate__config {
  flex: 0 0 380px;
  align-self: flex-start;
  @media (max-width: 1100px) {
    flex: 1 1 auto;
  }
  :deep(.basic-block__header) {
    padding-bottom: $spacing-md;
  }
}

.sxk-generate__config-title {
  display: flex;
  flex-direction: column;
  gap: 4px;
  &-main {
    font-size: $font-size-xl;
    font-weight: 600;
    color: $text-primary;
    line-height: 1.4;
  }
  &-sub {
    font-size: $font-size-sm;
    color: $text-secondary;
    line-height: 1.5;
  }
}

// 右栏标题（与左栏对称，但更紧凑）
.sxk-generate__main-title {
  display: flex;
  align-items: baseline;
  gap: 8px;
  &-main {
    font-size: $font-size-lg;
    font-weight: 600;
    color: $text-primary;
    line-height: 1.4;
  }
  &-sub {
    font-size: $font-size-xs;
    color: $text-secondary;
    line-height: 1.4;
  }
}

// ---------- 阶段指示器 ----------
.sxk-generate__steps {
  padding: $spacing-sm 0 $spacing-md;
  border-bottom: 1px dashed $border-light;
  margin-bottom: $spacing-md;
}

// 可点击步骤条
.sxk-generate__step-track {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: $spacing-md;
}
.sxk-generate__step {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border-radius: $radius-md;
  background: transparent;
  cursor: default;
  transition: all 0.18s ease;
  position: relative;
  border: 1px solid transparent;

  &.is-clickable {
    cursor: pointer;
    &:hover {
      background: $bg-hover;
      border-color: $primary-color-light;
      .sxk-generate__step-no {
        transform: scale(1.05);
      }
    }
  }
  &.is-active {
    background: linear-gradient(
      135deg,
      rgba(26, 86, 219, 0.06) 0%,
      rgba(26, 86, 219, 0.02) 100%
    );
    border-color: rgba(26, 86, 219, 0.2);
    .sxk-generate__step-no {
      box-shadow: 0 0 0 4px rgba(26, 86, 219, 0.15);
    }
  }
}
.sxk-generate__step-no {
  flex-shrink: 0;
  width: 26px;
  height: 26px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  transition: all 0.18s ease;
  background: $gray-100;
  color: $text-placeholder;
  border: 2px solid $bg-card;

  .is-done & {
    background: $primary-color;
    color: #fff;
  }
  .is-active & {
    background: $primary-color;
    color: #fff;
  }
  .is-wait & {
    background: $gray-100;
    color: $text-placeholder;
  }
}
.sxk-generate__step-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 1px;
}
.sxk-generate__step-title {
  font-size: 13px;
  font-weight: 500;
  color: $text-regular;
  line-height: 1.3;
  .is-done & { color: $text-regular; }
  .is-active & { color: $primary-color; font-weight: 600; }
  .is-wait & { color: $text-placeholder; }
}
.sxk-generate__step-desc {
  font-size: 11px;
  color: $text-placeholder;
  line-height: 1.3;
}
.sxk-generate__step-tag {
  flex-shrink: 0;
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 999px;
  font-weight: 500;
  background: $primary-color;
  color: #fff;
  &.is-done {
    background: rgba(22, 163, 74, 0.12);
    color: $success-color;
  }
  &.is-wait {
    background: $gray-100;
    color: $text-placeholder;
  }
}

// 当前阶段摘要卡
.sxk-generate__step-summary {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: linear-gradient(
    135deg,
    $primary-color-light 0%,
    rgba(219, 234, 254, 0.5) 100%
  );
  border: 1px solid rgba(26, 86, 219, 0.15);
  border-radius: $radius-md;
  margin-bottom: $spacing-sm;
}
.sxk-generate__step-summary-icon {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: $primary-color;
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  flex-shrink: 0;
}
.sxk-generate__step-summary-text {
  font-size: 12px;
  color: $text-regular;
  line-height: 1.5;
  b {
    color: $primary-color;
    font-weight: 600;
    margin-right: 2px;
  }
}

// 草稿操作行
.sxk-generate__step-actions {
  display: flex;
  gap: 6px;
  :deep(.el-button) {
    flex: 1;
    font-size: 12px;
  }
}

// 头部阶段胶囊（统一圆角+胶囊样式）
.sxk-generate__phase-tag {
  flex-shrink: 0;
  border-radius: 999px;
  padding: 0 12px;
  font-weight: 500;
  letter-spacing: 0.2px;
}

// 场景网格（2 列卡片）
.sxk-generate__scene-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: $spacing-sm;
  width: 100%;
}
.sxk-generate__scene-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 16px 8px;
  border: 1px solid $border-base;
  border-radius: $radius-md;
  background: $bg-card;
  cursor: pointer;
  transition: all 0.18s ease;
  position: relative;
  overflow: hidden;

  &:hover {
    border-color: $primary-color-light;
    background: $bg-hover;
    transform: translateY(-1px);
  }
  &.is-active {
    border-color: $primary-color;
    background: linear-gradient(135deg, $primary-color 0%, $primary-color-hover 100%);
    color: #fff;
    box-shadow: 0 4px 12px rgba(26, 86, 219, 0.3);

    .sxk-generate__scene-icon {
      color: #fff !important;
    }
  }
}
.sxk-generate__scene-text {
  font-size: 13px;
  font-weight: 500;
  text-align: center;
  line-height: 1.3;
  color: inherit;
}

.sxk-generate__params-title {
  margin: $spacing-md 0 $spacing-sm;
  padding-left: $spacing-sm;
  border-left: 3px solid $primary-color;
  font-size: $font-size-base;
  color: $text-primary;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 6px;
  &::before {
    content: "";
    display: none; // 用 border-left 实现视觉条
  }
}

// 表单样式微调（与项目风格统一）
.sxk-generate__config {
  :deep(.el-form-item__label) {
    font-weight: 500;
    color: $text-regular;
    font-size: $font-size-sm;
    line-height: 1.5;
    padding-bottom: 4px;
  }
  :deep(.el-form-item) {
    margin-bottom: $spacing-md;
  }
  :deep(.el-input__wrapper) {
    border-radius: $radius-md;
  }
}

// ---------- 立即生成按钮（页面主 CTA）----------
.sxk-generate__submit {
  width: 100%;
  height: 46px;
  font-size: 15px;
  font-weight: 500;
  letter-spacing: 0.5px;
  background: $primary-color;
  border-color: $primary-color;
  box-shadow: 0 4px 12px rgba(26, 86, 219, 0.25);
  transition: all 0.2s ease;
  &:hover, &:focus {
    background: $primary-color-hover;
    border-color: $primary-color-hover;
    box-shadow: 0 6px 16px rgba(26, 86, 219, 0.35);
    transform: translateY(-1px);
  }
  &:active {
    transform: translateY(0);
    box-shadow: 0 2px 6px rgba(26, 86, 219, 0.2);
  }
}
.sxk-generate__submit-tip {
  margin-top: $spacing-sm;
  font-size: $font-size-xs;
  color: $text-placeholder;
  text-align: center;
  line-height: 1.6;
  padding: $spacing-sm;
  background: $gray-50;
  border-radius: $radius-sm;
  border: 1px dashed $border-light;
}

// ---------- 右栏：主区域 ----------
.sxk-generate__main {
  flex: 1 1 auto;
  min-height: 600px;
}

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

// ---------- 阶段化容器 ----------
.sxk-generate__stage {
  display: flex;
  flex-direction: column;
  gap: $spacing-md;
}

.sxk-generate__card {
  border: 1px solid $border-base;
  border-radius: $radius-lg;
  transition: box-shadow 0.2s ease;
  :deep(.el-card__header) {
    padding: 14px $spacing-md;
    border-bottom-color: $border-light;
    background: $bg-hover;
    border-radius: $radius-lg $radius-lg 0 0;
  }
  :deep(.el-card__body) {
    padding: $spacing-md;
  }
  &.is-clean {
    border: none;
    box-shadow: none;
    :deep(.el-card__header) {
      padding-left: 0;
      padding-right: 0;
      background: transparent;
    }
    :deep(.el-card__body) {
      padding: $spacing-sm 0 0;
    }
  }
}

.sxk-generate__card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: $font-size-base;
  gap: $spacing-sm;
  > b {
    font-weight: 600;
    color: $text-primary;
    letter-spacing: 0.2px;
  }
}
.sxk-generate__card-tip {
  font-size: $font-size-xs;
  color: $text-placeholder;
}

.sxk-generate__trace-toggle {
  user-select: none;
  &:hover .sxk-generate__trace-icon {
    background: $primary-color;
    color: #fff;
  }
}
// 头部左侧（可点击切换折叠）
.sxk-generate__trace-left {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  min-width: 0;
  cursor: pointer;
  user-select: none;
}
// 头部右侧
.sxk-generate__trace-right {
  display: flex;
  align-items: center;
  gap: 10px;
}
// 切换按钮（带圆形 hover 区）
.sxk-generate__trace-toggle-btn {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: $gray-100;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.18s ease;
  font-size: 11px;
  color: $text-secondary;
  &:hover {
    background: $primary-color-light;
    color: $primary-color;
  }
  .el-icon {
    transition: transform 0.25s;
    &.is-open {
      transform: rotate(90deg);
    }
  }
}

// 链路图标（圆角方块）
.sxk-generate__trace-icon {
  width: 26px;
  height: 26px;
  border-radius: 8px;
  background: $primary-color-light;
  color: $primary-color;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  transition: all 0.18s ease;
}

// 链路统计胶囊
.sxk-generate__trace-stats {
  display: flex;
  gap: 8px;
  margin-left: 4px;
}
.sxk-generate__trace-stat {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 2px 8px;
  font-size: 11px;
  color: $text-regular;
  background: $gray-100;
  border-radius: 999px;
  font-weight: 500;
  .el-icon { font-size: 11px; }
  &.is-success {
    color: #047857;
    background: #ecfdf5;
  }
}

// 通用状态胶囊（与 history 详情弹窗风格一致）
.sxk-generate__status-pill {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 2px 10px 2px 8px;
  border-radius: 999px;
  font-size: 11.5px;
  font-weight: 500;
  line-height: 1.5;
  border: 1px solid transparent;

  &-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: currentColor;
    flex-shrink: 0;
  }
  &.is-pass {
    background: #ecfdf5;
    color: #047857;
    border-color: #a7f3d0;
  }
  &.is-warn {
    background: #fffbeb;
    color: #b45309;
    border-color: #fde68a;
  }
}

// ============ Agent 横向时间线 ============
.sxk-generate__timeline {
  display: flex;
  align-items: flex-start;
  padding: 4px 0 12px;
  gap: 0;
  overflow-x: auto;
  scrollbar-width: thin;
}
.sxk-generate__tl-node {
  position: relative;
  flex: 1 1 0;
  min-width: 90px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  padding: 4px 4px 0;
  transition: all 0.18s ease;
  user-select: none;

  &:hover .sxk-generate__tl-dot {
    transform: scale(1.08);
  }
  &:hover .sxk-generate__tl-info {
    color: $text-primary;
  }

  &.is-active .sxk-generate__tl-info {
    .sxk-generate__tl-name {
      color: $primary-color;
      font-weight: 600;
    }
  }
}
// 连接线（节点之间的虚/实线）
.sxk-generate__tl-line {
  position: absolute;
  top: 17px;
  left: calc(50% + 18px);
  right: calc(-50% + 18px);
  height: 2px;
  z-index: 0;

  .is-success + &,
  .is-success.is-active + & {
    background: linear-gradient(
      90deg,
      $primary-color 0%,
      $primary-color 100%
    );
  }
  .is-warning + & {
    background: $warning-color;
    opacity: 0.4;
  }
  .is-error + & {
    background: $danger-color;
    opacity: 0.4;
  }
  .is-wait + &, .is-pending + & {
    background: repeating-linear-gradient(
      90deg,
      $border-base 0,
      $border-base 4px,
      transparent 4px,
      transparent 8px
    );
  }
}
// 节点圆点
.sxk-generate__tl-dot {
  position: relative;
  z-index: 1;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.2s ease;
  background: $gray-100;
  color: $text-placeholder;
  border: 2px solid $bg-card;
  box-shadow: 0 0 0 1px $border-base;

  .is-success & {
    background: $primary-color;
    color: #fff;
    box-shadow: 0 0 0 1px $primary-color, 0 2px 8px rgba(26, 86, 219, 0.25);
  }
  .is-success.is-active & {
    box-shadow: 0 0 0 2px $primary-color, 0 0 0 5px rgba(26, 86, 219, 0.18);
  }
  .is-warning & {
    background: $warning-color;
    color: #fff;
    box-shadow: 0 0 0 1px $warning-color;
  }
  .is-error & {
    background: $danger-color;
    color: #fff;
    box-shadow: 0 0 0 1px $danger-color;
  }
  .is-active.is-warning & {
    box-shadow: 0 0 0 2px $warning-color, 0 0 0 5px rgba(245, 158, 11, 0.2);
  }
  .is-active.is-error & {
    box-shadow: 0 0 0 2px $danger-color, 0 0 0 5px rgba(239, 68, 68, 0.2);
  }
}
.sxk-generate__tl-dot-num {
  font-size: 13px;
  font-weight: 600;
}
.sxk-generate__tl-info {
  text-align: center;
  transition: color 0.18s ease;
  max-width: 100%;
  overflow: hidden;
}
.sxk-generate__tl-name {
  font-size: 12px;
  font-weight: 500;
  color: $text-regular;
  line-height: 1.3;
  white-space: nowrap;
  text-overflow: ellipsis;
  overflow: hidden;
  max-width: 90px;
}
.sxk-generate__tl-time {
  font-size: 10.5px;
  color: $text-placeholder;
  font-variant-numeric: tabular-nums;
  margin-top: 1px;
}

// 折叠时摘要条
.sxk-generate__tl-collapsed {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 10px;
  background: $gray-50;
  border-radius: $radius-sm;
  font-size: 12px;
  color: $text-secondary;
}
.sxk-generate__tl-collapsed-ok {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: $success-color;
  font-weight: 500;
}
.sxk-generate__tl-collapsed-warn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: $warning-color;
  font-weight: 500;
}

// ============ 节点详情卡 ============
.sxk-generate__tl-detail {
  margin-top: 10px;
  animation: fadeInUp 0.25s ease;
}
.sxk-generate__tl-detail-card {
  padding: 12px 14px;
  border-radius: $radius-md;
  background: $bg-hover;
  border-left: 3px solid $border-base;
  display: flex;
  flex-direction: column;
  gap: 8px;
  transition: all 0.2s ease;

  &.is-success { border-left-color: $success-color; background: #f6ffed; }
  &.is-warning { border-left-color: $warning-color; background: #fffbe6; }
  &.is-error { border-left-color: $danger-color; background: #fff2f0; }
}
.sxk-generate__tl-detail-head {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.sxk-generate__tl-detail-idx {
  font-size: 10.5px;
  color: $text-placeholder;
  background: $bg-card;
  border: 1px solid $border-light;
  padding: 1px 6px;
  border-radius: 999px;
  font-weight: 500;
}
.sxk-generate__tl-detail-name {
  font-size: $font-size-sm;
  font-weight: 600;
  color: $text-primary;
}
.sxk-generate__tl-detail-time {
  margin-left: auto;
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 11px;
  color: $text-regular;
  background: $bg-card;
  padding: 2px 8px;
  border-radius: 999px;
  border: 1px solid $border-light;
  font-variant-numeric: tabular-nums;
}
.sxk-generate__tl-detail-msg {
  font-size: $font-size-sm;
  color: $text-regular;
  line-height: 1.65;
  padding: 6px 0;
}
.sxk-generate__tl-detail-foot {
  display: flex;
  align-items: center;
  gap: 4px;
  padding-top: 6px;
  border-top: 1px dashed $border-light;
}

// 折叠动画
.sxk-fade-enter-active,
.sxk-fade-leave-active {
  transition: opacity 0.22s ease, transform 0.22s ease;
}
.sxk-fade-enter-from,
.sxk-fade-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

// 卡片头部左侧（标题 + 副标题）
.sxk-generate__card-head-left {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

// ============ 版本对比卡片墙 ============
.sxk-generate__version-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: $spacing-md;
  margin-bottom: $spacing-lg;

  @media (max-width: 900px) {
    grid-template-columns: 1fr;
  }
}
.sxk-generate__version-card {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 14px;
  border: 1px solid $border-base;
  border-radius: $radius-lg;
  background: $bg-card;
  cursor: pointer;
  transition: all 0.18s ease;
  overflow: hidden;

  &::before {
    content: "";
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: transparent;
    transition: background 0.2s ease;
  }

  &:hover {
    border-color: $primary-color-light;
    transform: translateY(-2px);
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.06);
  }

  &.is-selected {
    border-color: $primary-color;
    background: $primary-color-light;
    box-shadow: 0 4px 14px rgba(26, 86, 219, 0.15);

    &::before {
      background: linear-gradient(
        90deg,
        $primary-color 0%,
        $primary-color-hover 100%
      );
    }
  }
}
.sxk-generate__version-card-head {
  display: flex;
  align-items: center;
  gap: 8px;
}
.sxk-generate__version-card-radio {
  flex-shrink: 0;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  border: 1.5px solid $border-dark;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s ease;
  .is-selected & {
    border-color: $primary-color;
  }
}
.sxk-generate__radio-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: transparent;
  transition: background 0.15s ease;
  &.is-checked {
    background: $primary-color;
  }
}
.sxk-generate__version-card-no {
  font-size: $font-size-base;
  font-weight: 600;
  color: $text-primary;
}
.sxk-generate__version-card-tag {
  margin-left: auto;
}
.sxk-generate__version-card-title {
  font-size: $font-size-sm;
  font-weight: 500;
  color: $text-primary;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.sxk-generate__version-card-meta {
  display: flex;
  gap: 12px;
  font-size: 11.5px;
  color: $text-secondary;
}
.sxk-generate__version-card-stat {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  .el-icon {
    font-size: 12px;
    color: $text-placeholder;
  }
}
.sxk-generate__version-card-preview {
  font-size: 12px;
  color: $text-regular;
  line-height: 1.6;
  padding: 8px 10px;
  background: $gray-50;
  border-radius: $radius-sm;
  max-height: 72px;
  overflow: hidden;
  border: 1px dashed $border-light;
}
.sxk-generate__version-preview {
  animation: fadeInUp 0.25s ease;
}
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

// ---------- 版本 Tab ----------
.sxk-generate__version-tabs {
  :deep(.el-tabs__header) {
    margin-bottom: 0;
    border-bottom: 2px solid $border-light;
  }
  :deep(.el-tabs__header .el-tabs__item) {
    font-size: 13px;
    padding: 0 18px;
    height: 38px;
    line-height: 38px;
    transition: all 0.18s ease;
    &:hover {
      color: $primary-color;
    }
    &.is-active {
      color: $primary-color;
      font-weight: 600;
      &::before {
        background: $primary-color;
      }
    }
  }
  :deep(.el-tabs__active-bar) {
    background: $primary-color;
    height: 2px;
  }
  :deep(.el-tabs__content) {
    padding: 18px 0 4px;
  }
}

// Tab 标签（版本 N + 字数）
.sxk-generate__tab-label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-weight: 500;
}
.sxk-generate__tab-meta {
  font-size: 11px;
  color: $text-placeholder;
  font-weight: 400;
  padding: 1px 6px;
  background: $gray-100;
  border-radius: 999px;
}

// ---------- Word 文档式展示 ----------
.sxk-generate__doc-page {
  background: $bg-card;
  max-width: 780px;
  margin: 0 auto;
  padding: 48px 56px;
  box-shadow: 0 2px 14px rgba(0, 0, 0, 0.08);
  border: 1px solid $border-light;
  border-radius: $radius-sm;
  font-family: Georgia, "Times New Roman", "宋体", SimSun, serif;
  color: #1a1a1a;
  line-height: 1.85;
  position: relative;
  &::before {
    content: "";
    position: absolute;
    top: 0; left: 0; right: 0; height: 3px;
    background: linear-gradient(
      90deg,
      $primary-color 0%,
      rgba(26, 86, 219, 0.4) 50%,
      $primary-color 100%
    );
    border-radius: $radius-sm $radius-sm 0 0;
    opacity: 0.5;
  }
}
.sxk-generate__doc-title {
  font-size: 25px;
  font-weight: 700;
  text-align: center;
  margin: 0 0 26px;
  line-height: 1.4;
  color: #1a1a1a;
}
.sxk-generate__doc-content {
  font-size: 15.5px;
  :deep(h1) { font-size: 20px; margin: 22px 0 10px; font-weight: 700; }
  :deep(h2) { font-size: 18px; margin: 18px 0 8px; font-weight: 700; }
  :deep(h3) { font-size: 16px; margin: 14px 0 6px; font-weight: 700; }
  :deep(p) { margin: 10px 0; }
  :deep(ul), :deep(ol) { padding-left: 22px; margin: 8px 0; }
  :deep(blockquote) {
    border-left: 3px solid #bbb;
    color: #555;
    margin: 10px 0;
    padding: 4px 14px;
    background: #fafafa;
  }
  :deep(table) {
    border-collapse: collapse;
    width: 100%;
    margin: 10px 0;
    th, td {
      border: 1px solid #ccc;
      padding: 6px 10px;
      text-align: left;
    }
    th {
      background: #f5f5f5;
      font-weight: 700;
    }
  }
  :deep(.article-fig) {
    margin: 22px 0;
    text-align: center;
    img {
      max-width: 100%;
      max-height: 440px;
      object-fit: contain;
      border-radius: 4px;
      border: 1px solid $border-light;
      display: block;
      margin: 0 auto;
    }
    figcaption {
      font-size: 12.5px;
      color: #666;
      margin-top: 6px;
      line-height: 1.5;
    }
  }
}
.sxk-generate__doc-tags {
  margin-top: $spacing-md;
}
.sxk-generate__stage-foot {
  text-align: right;
  margin-top: $spacing-md;
  padding-top: $spacing-sm;
  border-top: 1px dashed $border-light;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: $spacing-sm;
  &-tip {
    margin-right: auto;
    font-size: 12px;
    color: $text-placeholder;
  }
}

.sxk-generate__mode-bar {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 8px;
}

.sxk-generate__img-ref-list {
  font-size: 12px;
  color: $text-regular;
  margin: 8px 0;
  padding: 8px 10px;
  background: $bg-hover;
  border: 1px solid $border-light;
  border-radius: $radius-sm;
}
.sxk-generate__img-ref {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  margin: 4px 10px 4px 0;
  img {
    width: 30px;
    height: 30px;
    object-fit: cover;
    border-radius: 4px;
    border: 1px solid $border-base;
  }
}

// ---------- 阶段 1：编辑区 + 渠道多选 ----------
.sxk-generate__edit-title {
  margin-bottom: $spacing-md;
  :deep(.el-input__wrapper) {
    border-radius: $radius-md;
    background: $gray-50;
    transition: all 0.18s ease;
    &.is-focus {
      background: $bg-card;
      box-shadow: 0 0 0 1px $primary-color inset !important;
    }
  }
  :deep(.el-input-group__prepend) {
    background: $primary-color;
    color: #fff;
    font-weight: 500;
    font-size: $font-size-sm;
    border-color: $primary-color;
  }
}
.sxk-generate__edit-body {
  :deep(.el-textarea__inner) {
    font-size: $font-size-base;
    line-height: 1.85;
    font-family: Georgia, "宋体", serif;
    border-radius: $radius-md;
    min-height: 360px;
    padding: $spacing-md;
    background: $gray-50;
    transition: all 0.18s ease;
    &:focus {
      background: $bg-card;
      box-shadow: 0 0 0 1px $primary-color inset;
    }
  }
}
.sxk-generate__edit-body-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: $font-size-sm;
  color: $text-regular;
  margin-bottom: 8px;
  padding-bottom: 6px;
  border-bottom: 1px dashed $border-light;
}
.sxk-generate__edit-body-cnt {
  color: $text-placeholder;
  font-size: $font-size-xs;
  padding: 2px 8px;
  background: $gray-100;
  border-radius: 999px;
}
.sxk-generate__edit-tags {
  margin-top: $spacing-sm;
  padding-top: $spacing-sm;
  border-top: 1px dashed $border-light;
}

// ============ 渠道多选（右栏固定高度 + 独立滚动）============
.sxk-generate__channel-pane {
  display: flex;
  flex-direction: column;
  height: 100%;
  max-height: calc(100vh - 200px);
  min-height: 480px;
  // 让卡片 body 区成为 flex 容器，方便列表占满剩余空间
  :deep(.el-card__body) {
    display: flex;
    flex-direction: column;
    flex: 1;
    min-height: 0; // flex 滚动必需
    padding: 0;
  }
}
.sxk-generate__channel-pane-head {
  display: flex;
  flex-direction: column;
  gap: 1px;
  line-height: 1.2;
}
.sxk-generate__channel-count {
  font-size: 11.5px;
  color: $text-secondary;
  padding: 1px 8px;
  background: $primary-color-light;
  color: $primary-color;
  border-radius: 999px;
  font-weight: 500;
  white-space: nowrap;
  font-variant-numeric: tabular-nums;
}

// 渠道列表独立滚动区域
.sxk-generate__channel-scroll {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  padding: $spacing-md;
  // 滚动条样式（细窄，hover 变粗）
  scrollbar-width: thin;
  scrollbar-color: $border-dark transparent;
  &::-webkit-scrollbar {
    width: 6px;
  }
  &::-webkit-scrollbar-track {
    background: transparent;
  }
  &::-webkit-scrollbar-thumb {
    background: $border-dark;
    border-radius: 3px;
    transition: background 0.18s;
  }
  &::-webkit-scrollbar-thumb:hover {
    background: $text-placeholder;
  }
}
.sxk-generate__channel-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

// 底部 CTA（始终可见）
.sxk-generate__channel-foot {
  flex-shrink: 0;
  padding: $spacing-md;
  background: $bg-card;
  border-top: 1px solid $border-light;
  // 顶部加轻微渐变阴影，让滚动区域有视觉深度
  position: relative;
  &::before {
    content: "";
    position: absolute;
    top: -10px;
    left: 0;
    right: 0;
    height: 10px;
    background: linear-gradient(180deg, transparent 0%, rgba(255, 255, 255, 0.8) 100%);
    pointer-events: none;
  }
}
.sxk-generate__channel-item {
  width: 100%;
  margin: 0;
  padding: 12px 14px;
  border: 1px solid $border-base;
  border-radius: $radius-md;
  height: auto;
  align-items: flex-start;
  transition: all 0.18s ease;
  cursor: pointer;
  &:hover {
    border-color: $primary-color-light;
    background: $bg-hover;
    transform: translateY(-1px);
  }
  &.is-checked {
    border-color: $primary-color;
    background: rgba(26, 86, 219, 0.04);
    box-shadow: 0 0 0 1px $primary-color inset;
  }
  // 隐藏 el-checkbox 原生的方框和 label 文本（用我们的虚拟勾选框 + default slot 内容）
  :deep(.el-checkbox__inner) {
    display: none !important; // 隐藏原生方框
  }
  :deep(.el-checkbox__original) {
    display: none !important; // 隐藏原生 input
  }
  :deep(.el-checkbox__label) {
    // el-checkbox 内部默认会把 value 作为 label 文本（与 default slot 重复）
    // 解决：把 .el-checkbox__label 的直接文本节点（text node）字号设为 0
    // 但 default slot 是子元素，不受影响
    font-size: 0;
    width: 100%;
    > * {
      font-size: $font-size-base; // 恢复子元素字号
    }
  }
}
// 自定义渠道内容容器
.sxk-generate__channel-content {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
}
// 虚拟勾选框（视觉替代 el-checkbox 原生方框）
.sxk-generate__channel-check {
  flex-shrink: 0;
  width: 16px;
  height: 16px;
  border: 1.5px solid $border-base;
  border-radius: 3px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: $bg-card;
  transition: all 0.15s ease;
  .el-icon {
    font-size: 12px;
    color: #fff;
  }
  &.is-checked {
    background: $primary-color;
    border-color: $primary-color;
  }
}
.sxk-generate__channel-info {
  flex: 1;
  min-width: 0;
}
.sxk-generate__channel-name {
  font-weight: 600;
  font-size: $font-size-base;
  color: $text-primary;
  display: flex;
  align-items: center;
  gap: 6px;
}
.sxk-generate__channel-meta {
  font-size: $font-size-xs;
  color: $text-placeholder;
  margin-top: 4px;
  line-height: 1.5;
}
.sxk-generate__channel-submit {
  width: 100%;
  height: 44px;
  font-size: 15px;
  font-weight: 500;
  letter-spacing: 0.5px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  box-shadow: 0 2px 8px rgba(26, 86, 219, 0.18);
  &:hover:not(.is-disabled) {
    box-shadow: 0 4px 14px rgba(26, 86, 219, 0.28);
    transform: translateY(-1px);
  }
}

// ---------- 版本操作按钮（投票 + SEO）----------
.sxk-generate__version-tools {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: $spacing-md;
  border-top: 1px solid $border-light;
  padding-top: $spacing-sm;
  margin-top: $spacing-md;
  flex-wrap: wrap;
}
.sxk-generate__tools-tip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: $text-placeholder;
  flex-shrink: 0;
  .el-icon {
    font-size: 13px;
  }
}
// ============ 阶段 2 工具栏（反馈/分析/重做 三组）============
.sxk-generate__tools-actions {
  display: flex;
  align-items: center;
  gap: $spacing-md;
  flex-wrap: wrap;
  justify-content: flex-end;
}
.sxk-generate__tools-group {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 2px 0;
  position: relative;
  // 组之间加竖线分隔（除了第一个）
  & + & {
    padding-left: $spacing-md;
    &::before {
      content: '';
      position: absolute;
      left: 0;
      top: 4px;
      bottom: 4px;
      width: 1px;
      background: $border-base;
    }
  }
}
.sxk-generate__tools-group-label {
  font-size: $font-size-xs;
  color: $text-placeholder;
  letter-spacing: 0.5px;
  font-weight: 500;
  text-transform: uppercase;
  margin-right: 2px;
  user-select: none;
}
.sxk-generate__vote-num {
  font-variant-numeric: tabular-nums;
  font-weight: 600;
  font-size: $font-size-sm;
  min-width: 14px;
  text-align: left;
}
// 重做按钮：弱化视觉（避免误触）
.sxk-generate__tools-regen {
  // Element Plus text+bg 样式本身较轻，这里再压低权重
  font-size: $font-size-sm !important;
  color: $text-secondary !important;
  padding: 4px 10px !important;
  transition: all 0.2s ease !important;
  &:hover {
    color: $warning-color !important;
    background: rgba($warning-color, 0.12) !important;
    transform: translateX(1px);
  }
}

// ---------- 渠道对比卡（阶段 2 横向）----------
.sxk-generate__channel-wall {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 10px;
  margin-bottom: $spacing-md;
}
.sxk-generate__version-card {
  padding: 10px 12px;
  border-radius: $radius-md;
  border: 1.5px solid $border-base;
  background: $bg-card;
  cursor: pointer;
  transition: all 0.18s ease;
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 8px;

  &:hover {
    border-color: $primary-color-light;
    background: $primary-color-light;
    transform: translateY(-1px);
  }
  &.is-selected {
    border-color: $primary-color;
    background: $primary-color-light;
    box-shadow: 0 0 0 1px $primary-color, 0 4px 12px rgba(26, 86, 219, 0.18);
    &::before {
      content: "";
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 3px;
      background: linear-gradient(90deg, $primary-color 0%, rgba(26, 86, 219, 0.6) 100%);
      border-radius: $radius-md $radius-md 0 0;
    }
  }
  &.is-finalized {
    border-style: solid;
  }
}
.sxk-generate__version-card-head {
  display: flex;
  align-items: center;
  gap: 6px;
}
.sxk-generate__version-card-radio {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 1.5px solid $text-placeholder;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.18s;
}
.sxk-generate__radio-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: transparent;
  transition: all 0.18s;
  &.is-checked {
    background: $primary-color;
  }
  .is-selected & {
    border-color: $primary-color;
  }
}
.sxk-generate__version-card-no {
  flex: 1;
  font-size: $font-size-sm;
  font-weight: 600;
  color: $text-primary;
  white-space: nowrap;
  text-overflow: ellipsis;
  overflow: hidden;
}
.sxk-generate__version-card-tag {
  flex-shrink: 0;
  font-size: 10.5px;
  padding: 1px 6px;
  border-radius: 999px;
  font-weight: 500;
  display: inline-flex;
  align-items: center;
  gap: 2px;
  .el-icon {
    font-size: 11px;
  }
  &.is-done {
    background: rgba(22, 163, 74, 0.12);
    color: $success-color;
  }
  &.is-running {
    background: rgba(245, 158, 11, 0.12);
    color: $warning-color;
  }
  &.is-pending {
    background: $gray-100;
    color: $text-placeholder;
  }
}
.sxk-generate__version-card-meta {
  display: flex;
  gap: 12px;
  padding-top: 4px;
  border-top: 1px dashed $border-light;
}
.sxk-generate__version-card-stat {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 11.5px;
  color: $text-secondary;
  font-variant-numeric: tabular-nums;
  .el-icon {
    font-size: 12px;
    color: $text-placeholder;
  }
}

// ---------- 当前渠道预览容器 ----------
.sxk-generate__version-preview {
  margin-top: $spacing-sm;
  animation: fadeInUp 0.25s ease;
}

// 工具栏：渠道名 + 元信息 + 预览/编辑切换
.sxk-generate__channel-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  background: $bg-hover;
  border-radius: $radius-md $radius-md 0 0;
  border: 1px solid $border-light;
  border-bottom: none;
  gap: $spacing-md;
}
.sxk-generate__channel-toolbar-left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  flex: 1;
  min-width: 0;
}
.sxk-generate__channel-name-lg {
  font-size: $font-size-base;
  font-weight: 600;
  color: $text-primary;
}
.sxk-generate__channel-meta-inline {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: $text-secondary;
  font-variant-numeric: tabular-nums;
}
.sxk-generate__mode-switch {
  flex-shrink: 0;
  :deep(.el-radio-button__inner) {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 12px;
    padding: 4px 12px;
  }
}

// ---------- 编辑区 ----------
.sxk-generate__edit-area {
  border: 1px solid $border-light;
  border-top: none;
  border-radius: 0 0 $radius-md $radius-md;
  padding: $spacing-md;
  background: $bg-card;
  display: flex;
  flex-direction: column;
  gap: $spacing-md;
}
.sxk-generate__edit-title {
  :deep(.el-input-group__prepend) {
    background: $bg-hover;
    color: $text-regular;
    font-weight: 500;
    font-size: 13px;
  }
}
.sxk-generate__edit-body {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.sxk-generate__edit-body-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: $text-regular;
  font-weight: 500;
}
.sxk-generate__edit-body-cnt {
  color: $text-placeholder;
  font-weight: 400;
  font-variant-numeric: tabular-nums;
  padding: 1px 8px;
  background: $bg-hover;
  border-radius: 999px;
  font-size: 11px;
}

// 配图参考列表（编辑模式）
.sxk-generate__img-ref-head {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: 500;
  color: $text-regular;
  margin-bottom: 6px;
  .el-icon { font-size: 14px; color: $primary-color; }
}
.sxk-generate__img-ref-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 8px;
}
.sxk-generate__img-ref-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 6px;
  background: $bg-hover;
  border-radius: $radius-sm;
  border: 1px solid $border-light;
  img {
    width: 100%;
    aspect-ratio: 1;
    object-fit: cover;
    border-radius: $radius-sm;
    background: $bg-card;
  }
}
.sxk-generate__img-ref-cap {
  font-size: 11px;
  color: $text-secondary;
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}
.sxk-generate__img-ref-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: $spacing-lg;
  background: $gray-50;
  border: 1px dashed $border-base;
  border-radius: $radius-md;
  color: $text-placeholder;
  font-size: 13px;
  .el-icon {
    font-size: 18px;
    color: $text-placeholder;
  }
}

// ---------- 投票按钮（SVG） ----------
.sxk-generate__vote-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border-radius: 999px;
  border: 1px solid $border-light;
  background: $bg-card;
  color: $text-regular;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.18s ease;
  font-variant-numeric: tabular-nums;

  svg {
    transition: transform 0.18s;
  }
  &:hover {
    transform: translateY(-1px);
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06);
  }

  &.is-like:hover, &.is-like.is-active {
    background: rgba(22, 163, 74, 0.1);
    border-color: $success-color;
    color: $success-color;
  }
  &.is-like.is-active svg {
    color: $success-color;
    transform: scale(1.15);
  }
  &.is-dislike:hover, &.is-dislike.is-active {
    background: rgba(239, 68, 68, 0.08);
    border-color: $danger-color;
    color: $danger-color;
  }
  &.is-dislike.is-active svg {
    color: $danger-color;
    transform: scale(1.15);
  }
}

// 卡片头部左侧（新设计）
.sxk-generate__card-head-left {
  display: flex;
  flex-direction: column;
  gap: 2px;
  line-height: 1.3;
  b {
    font-size: $font-size-base;
    color: $text-primary;
  }
}
.sxk-generate__stage2-actions {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
  flex-wrap: wrap;
  justify-content: flex-end;
  // 主 CTA 与次按钮之间加竖线分隔
  > .el-button + .el-button--primary,
  > .el-button + .el-button--success {
    margin-left: $spacing-sm;
  }
  // 主 CTA 加投影 + 上浮
  > .el-button--primary,
  > .el-button--success {
    box-shadow: 0 4px 12px rgba($primary-color, 0.25);
    transition: all 0.2s ease;
    &:not(.is-disabled):hover {
      transform: translateY(-1px);
      box-shadow: 0 6px 16px rgba($primary-color, 0.35);
    }
  }
  // 文字 button 弱化（次按钮）
  > .el-button:not(.el-button--primary):not(.el-button--success):not(.el-button--warning) {
    color: $text-secondary;
    &:hover {
      color: $primary-color;
    }
  }
}

// ============ 流程完成弹窗（页面级）============
.sxk-generate__done-drawer {
  position: relative;
  background: $bg-card;
  display: flex;
  flex-direction: column;
  margin: -20px -20px 0;
  padding: 0;
  // 不设 min-height，让高度跟随内容自适应
}
// 自定义 dialog 弹窗样式
:deep(.sxk-generate__done-dialog) {
  border-radius: 12px;
  overflow: hidden;
  .el-dialog__body {
    padding: 0;
  }
  .el-dialog__header {
    display: none;
  }
  .el-dialog__footer {
    padding: 0;
  }
}
.sxk-generate__done-bg {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 240px;
  // 蓝色基调（与系统品牌色一致）
  background: linear-gradient(
    180deg,
    rgba(64, 158, 255, 0.10) 0%,
    rgba(64, 158, 255, 0.04) 60%,
    transparent 100%
  );
  pointer-events: none;
  z-index: 0;
}
// 右上角关闭按钮（在 body 容器内的白色区域上）
.sxk-generate__done-close {
  position: absolute;
  top: 10px;
  right: 10px;
  z-index: 2;
  width: 28px;
  height: 28px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  color: $text-secondary;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.2s ease;

  .el-icon {
    font-size: 16px;
  }

  &:hover {
    background: rgba(0, 0, 0, 0.06);
    color: $danger-color;
    transform: rotate(90deg); // 旋转 90° 增强交互反馈
  }

  &:active {
    transform: rotate(90deg) scale(0.9);
  }
}
.sxk-generate__done-body {
  position: relative;
  z-index: 1;
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  // 紧凑内边距：顶部 28（容纳 icon + 渐变），底部 20
  padding: 28px 24px 20px;
  gap: 12px;
}
.sxk-generate__done-icon {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  // 蓝色基调（与系统品牌色一致）
  background: linear-gradient(135deg, $primary-color 0%, rgba(64, 158, 255, 0.85) 100%);
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  box-shadow: 0 6px 20px rgba(64, 158, 255, 0.3);
  animation: donePulse 2.4s ease-in-out infinite;
}
@keyframes donePulse {
  0%, 100% {
    box-shadow: 0 6px 20px rgba(64, 158, 255, 0.3);
    transform: scale(1);
  }
  50% {
    box-shadow: 0 6px 30px rgba(64, 158, 255, 0.5);
    transform: scale(1.05);
  }
}
.sxk-generate__done-title {
  font-size: 18px;
  font-weight: 700;
  color: $text-primary;
  margin: 0;
  letter-spacing: 0.5px;
}
// 一行紧凑的元信息（替代 3 张统计卡）
.sxk-generate__done-meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  justify-content: center;
  gap: 6px;
  font-size: 12px;
  color: $text-secondary;
  font-variant-numeric: tabular-nums;
}
.sxk-generate__done-meta-chip {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 2px 8px;
  // 蓝色基调（与系统品牌色一致）
  background: rgba(64, 158, 255, 0.08);
  color: $primary-color;
  border-radius: 10px;
  font-weight: 600;
  font-size: 11px;
  .el-icon {
    font-size: 12px;
  }
}
.sxk-generate__done-meta-divider {
  color: $text-placeholder;
  font-size: 10px;
}
.sxk-generate__done-meta-text {
  color: $text-regular;
}
.sxk-generate__done-actions {
  display: flex;
  flex-direction: column;
  align-items: stretch; // 关键：让子元素宽度统一撑满
  gap: 8px;
  width: 100%;
  margin-top: 10px;
}
.sxk-generate__done-btn {
  // 关键：覆盖 el-button 默认的 inline-block + padding，否则 width:100% 不生效
  display: flex !important;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 38px;
  margin-left: 0 !important;
  padding-left: 16px;
  padding-right: 16px;
  font-size: 13px;
  font-weight: 500;
  gap: 5px;
  border-radius: 8px;
  transition: all 0.2s;
  // 移除 el-button 自带间距（双按钮堆叠时不需要）
  & + & {
    margin-left: 0 !important;
  }
}
// 主按钮：蓝色阴影 + hover 上浮（与系统品牌色一致）
.sxk-generate__done-btn--primary {
  background: linear-gradient(135deg, $primary-color 0%, rgba(64, 158, 255, 0.9) 100%);
  border-color: $primary-color;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.25);
  &:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 18px rgba(64, 158, 255, 0.35);
  }
}

// ---------- SEO 弹窗 ----------
// 自定义弹窗：去掉默认内边距，由内部容器控制
:deep(.sxk-generate__seo-dialog) {
  .el-dialog__body {
    padding: 16px 24px;
  }
  .el-dialog__footer {
    padding: 12px 24px 20px;
  }
}

// 头部
.sxk-generate__seo-header {
  display: flex;
  align-items: center;
  gap: $spacing-md;
  padding: 4px 0;
}
.sxk-generate__seo-header-icon {
  width: 40px;
  height: 40px;
  border-radius: $radius-md;
  background: linear-gradient(135deg, $primary-color, $primary-color-hover);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  box-shadow: 0 4px 12px rgba($primary-color, 0.25);
}
.sxk-generate__seo-header-title {
  font-size: 16px;
  font-weight: 600;
  color: $text-primary;
  line-height: 1.3;
}
.sxk-generate__seo-header-sub {
  font-size: 12px;
  color: $text-placeholder;
  margin-top: 2px;
}

// 主体容器
.sxk-generate__seo {
  text-align: left;
  position: relative;
  min-height: 120px;
}

// 评分主卡（左环形 + 右侧信息）
.sxk-generate__seo-hero {
  display: flex;
  align-items: center;
  gap: $spacing-xl;
  padding: $spacing-lg 0;
  border-bottom: 1px solid $border-light;
  margin-bottom: $spacing-lg;
}
// 环形进度
.sxk-generate__seo-ring {
  position: relative;
  width: 120px;
  height: 120px;
  flex-shrink: 0;
}
.sxk-generate__seo-ring-svg {
  width: 100%;
  height: 100%;
}
.sxk-generate__seo-ring-bg {
  stroke: $gray-100;
}
.sxk-generate__seo-ring-fg {
  transition: stroke-dashoffset 0.8s ease;
  filter: drop-shadow(0 2px 6px rgba(0, 0, 0, 0.08));
}
.sxk-generate__seo-ring-text {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  pointer-events: none;
}
.sxk-generate__seo-ring-num {
  font-size: 36px;
  font-weight: 700;
  line-height: 1;
  font-variant-numeric: tabular-nums;
}
.sxk-generate__seo-ring-tip {
  font-size: 12px;
  color: $text-placeholder;
  margin-top: 2px;
}
// 右侧侧栏
.sxk-generate__seo-side {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: $spacing-sm;
}
.sxk-generate__seo-grade {
  align-self: flex-start;
  padding: 4px 12px;
  border-radius: $radius-round;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.5px;
}
// 维度统计
.sxk-generate__seo-dimstats {
  display: flex;
  gap: 12px;
  margin: 4px 0;
}
.sxk-generate__seo-dimstat {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: $text-secondary;
  &.is-good {
    color: $success-color;
  }
  &.is-warn {
    color: $warning-color;
  }
  &.is-bad {
    color: $danger-color;
  }
  .sxk-generate__seo-dimstat-num {
    font-weight: 700;
    font-size: 14px;
    font-variant-numeric: tabular-nums;
  }
  .sxk-generate__seo-dimstat-label {
    color: $text-secondary;
  }
}
// 关键词
.sxk-generate__seo-kw {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px;
}
.sxk-generate__seo-kw-label {
  font-size: 12px;
  color: $text-placeholder;
  margin-right: 2px;
}
.sxk-generate__seo-kw-tag {
  margin: 0 2px;
  font-family: $font-family-mono;
}

// 4 维度分析
.sxk-generate__seo-dims {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: $spacing-md;
  margin-bottom: $spacing-lg;
}
.sxk-generate__seo-dim {
  padding: 12px 14px;
  border-radius: $radius-md;
  border: 1px solid $border-base;
  background: $bg-card;
  transition: all 0.2s;
  &:hover {
    border-color: $primary-color-light;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  }
  &.is-warning {
    background: rgba($warning-color, 0.04);
    border-color: rgba($warning-color, 0.25);
  }
  &.is-danger {
    background: rgba($danger-color, 0.04);
    border-color: rgba($danger-color, 0.25);
  }
}
.sxk-generate__seo-dim-head {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
}
.sxk-generate__seo-dim-icon {
  font-size: 16px;
  color: $primary-color;
}
.sxk-generate__seo-dim-name {
  font-size: 13px;
  font-weight: 600;
  color: $text-primary;
  flex: 1;
}
.sxk-generate__seo-dim-score {
  font-size: 13px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}
.sxk-generate__seo-dim-meta {
  font-size: 12px;
  color: $text-secondary;
  margin-bottom: 6px;
}
.sxk-generate__seo-dim-bar {
  margin: 0;
}

// Section（优化建议 / Meta）
.sxk-generate__seo-section {
  margin-bottom: $spacing-md;
}
.sxk-generate__seo-section-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: $text-primary;
  margin-bottom: $spacing-sm;
  .el-icon {
    color: $primary-color;
    font-size: 14px;
  }
  // 复制按钮右推
  .el-button {
    margin-left: auto;
  }
}

// 建议列表
.sxk-generate__seo-suggestions {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.sxk-generate__seo-suggestion {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 8px 10px;
  border-radius: $radius-sm;
  background: $gray-50;
  border-left: 3px solid $gray-300;
  font-size: 13px;
  &.is-good {
    background: rgba($success-color, 0.06);
    border-left-color: $success-color;
    .sxk-generate__seo-suggestion-status {
      color: $success-color;
    }
  }
  &.is-warning {
    background: rgba($warning-color, 0.06);
    border-left-color: $warning-color;
    .sxk-generate__seo-suggestion-status {
      color: $warning-color;
    }
  }
  &.is-danger {
    background: rgba($danger-color, 0.06);
    border-left-color: $danger-color;
    .sxk-generate__seo-suggestion-status {
      color: $danger-color;
    }
  }
}
.sxk-generate__seo-suggestion-status {
  font-size: 16px;
  margin-top: 1px;
  flex-shrink: 0;
}
.sxk-generate__seo-suggestion-body {
  flex: 1;
  min-width: 0;
}
.sxk-generate__seo-suggestion-type {
  font-size: 11px;
  font-weight: 600;
  color: $text-placeholder;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 2px;
}
.sxk-generate__seo-suggestion-msg {
  font-size: 13px;
  color: $text-primary;
  line-height: 1.5;
}

// Meta 描述
.sxk-generate__seo-meta {
  background: $bg-emphasis;
  border: 1px dashed $primary-color-lighter;
  border-radius: $radius-md;
  padding: 10px 14px;
  font-size: 13px;
  color: $text-regular;
  line-height: 1.6;
}

// Footer
.sxk-generate__seo-footer {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
}
.sxk-generate__seo-footer-tip {
  flex: 1;
  font-size: 12px;
  color: $text-placeholder;
  &::before {
    content: '💡';
    margin-right: 4px;
  }
}
</style>
