<!--
  内容生成页（/generate/index）
  对应需求文档：5.3 内容生成 US009 ~ US013 / US017 / AC-13
  对应接口文档：4.6 触发生成 / 4.6.8 Agent 协作 / 4.6.3 版本内容 / 4.6.9 校验问题

  页面布局（多阶段草稿流程，对齐后端参考版 B2B-SXK-FastApi/frontend）：
    ┌─────────────────────────────────────────────────────┐
    │  左栏（380px）       │  右栏（自适应）                │
    │  - 阶段指示 (el-steps)│  阶段 0：初稿多版本（Tab）    │
    │  - 产品/场景/模板     │  阶段 1：编辑 + 多选渠道       │
    │  - 动态参数          │  阶段 2：多渠道版本 + 保存      │
    │  - 立即生成 (Step 0)  │                               │
    └─────────────────────────────────────────────────────┘

  路由参数：
    ?gid=xxx    重新编辑历史内容（BR-H-04）
    ?scene=xxx  Dashboard 常用模板快捷进入
    ?tid=xxx    模板 ID 预选
-->
<template>
  <div
    class="sxk-generate"
    :class="{ 'is-empty': !currentDraft }"
  >
    <!-- ============================== 生成中 Loading 覆盖层 ============================== -->
    <transition name="gen-loading-fade">
      <div
        v-if="genLoadingVisible"
        class="sxk-gen-loading"
      >
        <div class="sxk-gen-loading__card">
          <!-- 动画图标 -->
          <div class="sxk-gen-loading__icon">
            <div class="sxk-gen-loading__orb" />
            <div class="sxk-gen-loading__pulse" />
          </div>
          <!-- 标题 -->
          <h3 class="sxk-gen-loading__title">
            {{ genLoadingTitle }}
          </h3>
          <p class="sxk-gen-loading__sub">
            {{ genLoadingSub }}
          </p>
          <!-- 步骤指示 -->
          <div class="sxk-gen-loading__steps">
            <div
              v-for="(s, i) in genLoadingSteps"
              :key="i"
              class="sxk-gen-loading__step"
              :class="s.state"
            >
              <span class="sxk-gen-loading__step-dot" />
              <span class="sxk-gen-loading__step-name">{{ s.label }}</span>
            </div>
          </div>
          <!-- 已生成版本实时预览（每完成一个版本就显示一个，不等全部完成） -->
          <div
            v-if="liveVersions.length > 0 && triggering && !currentDraft"
            class="sxk-gen-loading__versions"
          >
            <div
              v-for="v in liveVersions"
              :key="v.index"
              class="sxk-gen-loading__version"
            >
              <div class="sxk-gen-loading__version-head">
                <span class="sxk-gen-loading__version-no">版本 {{ v.index }}</span>
                <span class="sxk-gen-loading__version-title">{{ v.title || ('版本 ' + v.index) }}</span>
                <span class="sxk-gen-loading__version-stat">{{ v.body?.length || 0 }} 字</span>
              </div>
              <div class="sxk-gen-loading__version-body">{{ v.body }}</div>
            </div>
          </div>
        </div>
      </div>
    </transition>
    <!-- ============================== 顶部欢迎条（与其他页面一致） ============================== -->
    <div
      v-if="configPanelVisible"
      class="sxk-page-welcome"
    >
      <div class="sxk-page-welcome__left">
        <h2 class="sxk-page-welcome__title">
          内容生成
        </h2>
        <p class="sxk-page-welcome__desc">
          填写配置，一键产出多版本营销文案
        </p>
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

    <!-- ============================== 左栏：生成配置（首次访问无草稿时全宽撑满） ============================== -->
    <basic-block
      v-if="configPanelVisible && !currentDraft"
      class="sxk-generate__config"
      hover-shadow
    >
      <!-- 阶段指示器（草稿存在时显示） -->
      <div
        v-if="currentDraft"
        class="sxk-generate__steps"
      >
        <!-- 自绘可点击步骤条（替代 el-steps，支持已完成步回跳） -->
        <div class="sxk-generate__step-track">
          <div
            v-for="(s, i) in stepDefs"
            :key="i"
            class="sxk-generate__step"
            :class="stepClass(i)"
            :title="canJumpTo(i) ? `回到：${s.title}` : s.title"
            @click="onStepJump(i)"
          >
            <div class="sxk-generate__step-no">
              <el-icon v-if="i < draftStep || (i === 2 && stage2Completed)">
                <CircleCheckFilled />
              </el-icon>
              <span v-else>{{ i + 1 }}</span>
            </div>
            <div class="sxk-generate__step-info">
              <div class="sxk-generate__step-title">
                {{ s.title }}
              </div>
              <div class="sxk-generate__step-desc">
                {{ s.desc }}
              </div>
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
        class="sxk-generate__form"
        @submit.prevent
      >
        <!-- ============ 卡片 1：基础配置（产品 + 模板 并排） ============ -->
        <div class="sxk-form-card">
          <div class="sxk-form-card__head">
            <span class="sxk-form-card__bar" />
            <span class="sxk-form-card__title">基础配置</span>
            <span class="sxk-form-card__desc">先选择产品，再选择场景模板</span>
          </div>
          <div class="sxk-form-card__body">
            <el-form-item
              label="选择产品"
              prop="product_id"
              class="sxk-form-card__col"
            >
              <el-select
                v-model="form.product_id"
                placeholder="请选择产品"
                filterable
                clearable
                class="sxk-generate__form-full"
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
          </div>
        </div>

        <!-- ============ 卡片 2：内容场景（全宽网格） ============ -->
        <div class="sxk-form-card">
          <div class="sxk-form-card__head">
            <span class="sxk-form-card__bar" />
            <span class="sxk-form-card__title">内容场景</span>
            <span class="sxk-form-card__desc">选择本次生成内容的目标场景</span>
          </div>
          <div class="sxk-form-card__body">
            <el-form-item
              label="选择场景"
              prop="scene_code"
            >
              <div class="sxk-generate__scene-grid">
                <div
                  v-for="s in scenes"
                  :key="s.scene_code"
                  class="sxk-generate__scene-box"
                  :class="{ 'is-active': form.scene_code === s.scene_code }"
                  :style="{
                    '--scene-bg': getSceneStyle(s.scene_code, s.name).bg,
                    '--scene-color': getSceneStyle(s.scene_code, s.name).color
                  }"
                  @click="form.scene_code = s.scene_code"
                >
                  <el-icon
                    :size="22"
                    class="sxk-generate__scene-icon"
                  >
                    <component :is="getSceneStyle(s.scene_code, s.name).icon" />
                  </el-icon>
                  <span class="sxk-generate__scene-text">{{ s.name }}</span>
                </div>
              </div>
            </el-form-item>

            <!-- 关键：选择模板（移到内容场景下方） -->
            <el-form-item
              v-if="currentScene"
              prop="template_id"
              :rules="[{ required: true, message: '请选择模板', trigger: 'change' }]"
            >
              <template #label>
                <span>选择模板</span>
              </template>
              <el-select
                v-model="form.template_id"
                placeholder="请选择模板"
                filterable
                clearable
                class="sxk-generate__form-full"
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
          </div>
        </div>

        <!-- ============ 卡片 3：动态参数（4 栏紧凑布局，一屏全显） ============ -->
        <template v-if="currentScene">
          <div class="sxk-form-card sxk-form-card--params-compact">
            <div class="sxk-form-card__head sxk-form-card__head--compact">
              <span class="sxk-form-card__bar" />
              <span class="sxk-form-card__title">动态参数（{{ currentScene.name }}）</span>
              <span class="sxk-form-card__desc">带 * 为必填项</span>
            </div>
            <div class="sxk-form-card__body sxk-form-card__body--compact">
              <div class="sxk-form-compact">
                <template
                  v-for="p in currentScene.params"
                  :key="p.key"
                >
                  <!-- word_count 参数已由下方统一的"正文字数上限"输入框处理，此处跳过避免重复 -->
                  <div
                    v-if="p.key === 'word_count'"
                    style="display: none"
                  />
                  <!-- 枚举：label + chip 同行（compact） -->
                  <div
                    v-else-if="p.type === 'enum' && p.options && p.options.length"
                    class="sxk-field sxk-field--enum"
                  >
                    <span class="sxk-field__label">
                      <i
                        v-if="p.required"
                        class="sxk-field__required"
                      >*</i>
                      {{ p.label || p.key }}
                    </span>
                    <div class="sxk-field__chips">
                      <button
                        v-for="opt in p.options"
                        :key="opt"
                        type="button"
                        class="sxk-param-chip sxk-param-chip--compact"
                        :class="{ 'is-active': form.params[p.key] === opt }"
                        @click="form.params[p.key] = opt"
                      >
                        {{ opt }}
                      </button>
                    </div>
                  </div>
                  <!-- 文本：label + input 同行 -->
                  <div
                    v-else-if="p.type === 'text'"
                    class="sxk-field sxk-field--text"
                  >
                    <span class="sxk-field__label">
                      <i
                        v-if="p.required"
                        class="sxk-field__required"
                      >*</i>
                      {{ p.label || p.key }}
                    </span>
                    <el-input
                      v-model="form.params[p.key]"
                      :placeholder="p.default || '请输入'"
                      :maxlength="p.maxLength || 100"
                      show-word-limit
                      clearable
                      size="default"
                    />
                  </div>
                  <!-- 长文本：label + textarea 同行（紧凑 1 行） -->
                  <div
                    v-else-if="p.type === 'textarea'"
                    class="sxk-field sxk-field--textarea"
                  >
                    <span class="sxk-field__label">
                      <i
                        v-if="p.required"
                        class="sxk-field__required"
                      >*</i>
                      {{ p.label || p.key }}
                    </span>
                    <el-input
                      v-model="form.params[p.key]"
                      type="textarea"
                      :autosize="{ minRows: 1, maxRows: 3 }"
                      :placeholder="p.default || '请输入'"
                      :maxlength="p.maxLength || 500"
                      show-word-limit
                    />
                  </div>
                  <!-- 默认：text -->
                  <div
                    v-else
                    class="sxk-field sxk-field--text"
                  >
                    <span class="sxk-field__label">
                      <i
                        v-if="p.required"
                        class="sxk-field__required"
                      >*</i>
                      {{ p.label || p.key }}
                    </span>
                    <el-input
                      v-model="form.params[p.key]"
                      :placeholder="p.default || '请输入'"
                      :maxlength="p.maxLength || 100"
                      show-word-limit
                      clearable
                    />
                  </div>
                </template>
              </div>
            </div>
          </div>
        </template>

        <!-- ============ 提示词（选场景后显示，根据所选模板回填，可编辑） ============ -->
        <div
          v-if="currentScene"
          class="sxk-form-card sxk-form-card--prompt"
        >
          <div class="sxk-form-card__head sxk-form-card__head--compact">
            <span class="sxk-form-card__bar" />
            <span class="sxk-form-card__title">提示词</span>
            <span class="sxk-form-card__desc">根据所选模板自动回填，可按需调整</span>
          </div>
          <div class="sxk-form-card__body sxk-form-card__body--compact">
            <el-input
              v-model="form.params.prompt"
              type="textarea"
              :autosize="{ minRows: 3, maxRows: 8 }"
              placeholder="例如：'请用第一人称' / '结尾加一句号召' / '突出 AI 风控和毫秒级风险识别'"
              :maxlength="500"
              show-word-limit
              clearable
            />
          </div>
        </div>

        <!-- ============ 字数限制（统一输入框，所有场景通用） ============ -->
        <div
          v-if="currentScene"
          class="sxk-form-card sxk-form-card--compact"
        >
          <div class="sxk-form-card__head sxk-form-card__head--compact">
            <span class="sxk-form-card__bar" />
            <span class="sxk-form-card__title">正文字数上限</span>
            <span class="sxk-form-card__desc">0 表示不限制，生成后超出会被标记</span>
          </div>
          <div class="sxk-form-card__body sxk-form-card__body--compact">
            <el-input-number
              v-model="form.word_limit"
              :min="0"
              :max="5000"
              :step="100"
              controls-position="right"
              style="width: 200px"
            />
          </div>
        </div>

        <!-- ============ 卡片 4：提交 ============ -->
        <div class="sxk-form-card sxk-form-card--submit">
          <div class="sxk-generate__submit-area">
            <el-button
              type="primary"
              class="sxk-generate__submit"
              :loading="triggering"
              @click="onTrigger"
            >
              <el-icon style="margin-right: 6px">
                <MagicStick />
              </el-icon>
              立即生成（3 个初稿）
            </el-button>
            <div class="sxk-generate__submit-tip">
              生成后分三个阶段进行：选定初稿 → 改内容·选渠道 → 保存历史
            </div>
          </div>
        </div>
      </el-form>
    </basic-block>

    <!-- ============================== 当有草稿时：左栏（config） + 右栏（result）水平排列 ============================== -->
    <div
      v-if="currentDraft"
      class="sxk-generate__body"
    >
      <basic-block
        v-if="configPanelVisible"
        class="sxk-generate__config"
        hover-shadow
      >
        <!-- 阶段指示器（草稿存在时显示） -->
        <div class="sxk-generate__steps">
          <!-- 自绘可点击步骤条（替代 el-steps，支持已完成步回跳） -->
          <div class="sxk-generate__step-track">
            <div
              v-for="(s, i) in stepDefs"
              :key="i"
              class="sxk-generate__step"
              :class="stepClass(i)"
              :title="canJumpTo(i) ? `回到：${s.title}` : s.title"
              @click="onStepJump(i)"
            >
              <div class="sxk-generate__step-no">
                <el-icon v-if="i < draftStep || (i === 2 && stage2Completed)">
                  <CircleCheckFilled />
                </el-icon>
                <span v-else>{{ i + 1 }}</span>
              </div>
              <div class="sxk-generate__step-info">
                <div class="sxk-generate__step-title">
                  {{ s.title }}
                </div>
                <div class="sxk-generate__step-desc">
                  {{ s.desc }}
                </div>
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
      </basic-block>

      <basic-block
        v-if="currentDraft"
        class="sxk-generate__main"
        hover-shadow
      >
        <template #header>
          <div class="sxk-generate__main-title">
            <span class="sxk-generate__main-title-main">
              {{ currentDraft ? `生成结果 · ${stepTitle}` : '生成结果' }}
            </span>
            <span
              v-if="!currentDraft"
              class="sxk-generate__main-title-sub"
            >
              待生成内容将在此处展示
            </span>
          </div>
          <!-- 阶段子标题（draft 存在时显示当前阶段的目标/操作） -->
          <div
            v-if="currentDraft"
            class="sxk-generate__main-subtitle"
          >
            <el-icon class="sxk-generate__main-subtitle-icon">
              <Aim />
            </el-icon>
            <span class="sxk-generate__main-subtitle-text">
              {{ stageSubtitleText }}
            </span>
          </div>
          <!-- 三阶段分段指示（segmented） -->
          <div
            v-if="currentDraft"
            class="sxk-generate__main-segments"
          >
            <div
              v-for="(s, i) in stepDefs"
              :key="i"
              class="sxk-generate__main-segment"
              :class="{
                'is-active': i === draftStep,
                'is-done': i < draftStep || (i === 2 && stage2Completed),
                'is-disabled': i > draftStep && !(i === 2 && stage2Completed)
              }"
              @click="onStepJump(i)"
            >
              <span class="sxk-generate__main-segment-no">
                <el-icon v-if="i < draftStep || (i === 2 && stage2Completed)"><CircleCheckFilled /></el-icon>
                <span v-else>{{ i + 1 }}</span>
              </span>
              <span class="sxk-generate__main-segment-title">{{ s.title }}</span>
              <span class="sxk-generate__main-segment-desc">{{ s.desc }}</span>
            </div>
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

        <!-- 空状态：分步进度 + 智能提示（替代原空状态） -->
        <div
          v-if="!currentDraft"
          class="sxk-generate__guide"
        >
          <!-- 顶部欢迎 -->
          <div class="sxk-generate__guide-hero">
            <el-icon
              :size="48"
              color="#1A56DB"
            >
              <MagicStick />
            </el-icon>
            <h3 class="sxk-generate__guide-title">
              AI 智能文案生成
            </h3>
            <p class="sxk-generate__guide-subtitle">
              填写左侧表单，AI 将自动生成多版本文案供您选择
            </p>
          </div>

          <!-- 分步进度 -->
          <div class="sxk-generate__guide-steps">
            <div class="sxk-generate__guide-step is-active">
              <div class="sxk-generate__guide-step-no">
                1
              </div>
              <div class="sxk-generate__guide-step-body">
                <div class="sxk-generate__guide-step-title">
                  填写配置
                </div>
                <div class="sxk-generate__guide-step-desc">
                  选择产品和场景模板
                </div>
              </div>
            </div>
            <div class="sxk-generate__guide-step">
              <div class="sxk-generate__guide-step-no">
                2
              </div>
              <div class="sxk-generate__guide-step-body">
                <div class="sxk-generate__guide-step-title">
                  智能生成
                </div>
                <div class="sxk-generate__guide-step-desc">
                  AI 一次产出 3 个版本
                </div>
              </div>
            </div>
            <div class="sxk-generate__guide-step">
              <div class="sxk-generate__guide-step-no">
                3
              </div>
              <div class="sxk-generate__guide-step-body">
                <div class="sxk-generate__guide-step-title">
                  编辑发布
                </div>
                <div class="sxk-generate__guide-step-desc">
                  编辑选定，多渠道分发
                </div>
              </div>
            </div>
          </div>

          <!-- 底部小贴士 -->
          <div class="sxk-generate__guide-tips">
            <div class="sxk-generate__guide-tip-title">
              <el-icon><InfoFilled /></el-icon>
              <span>使用小贴士</span>
            </div>
            <ul class="sxk-generate__guide-tip-list">
              <li>填写动态参数时，尽量详细描述目标受众</li>
              <li>不同场景模板适配不同行业，优先选择匹配项</li>
              <li>生成后可对比 3 个版本，选择最佳继续编辑</li>
            </ul>
          </div>
        </div>

        <!-- ============ 阶段 0：初稿多版本选择（卡片对比墙 + 整版预览）============ -->
        <div
          v-else-if="draftStep === 0"
          class="sxk-generate__stage"
        >
          <!-- 阶段标题 hero（已注释，由右栏 segmented 替代） -->
          <!--
        <div class="sxk-generate__stage-hero">
          <div class="sxk-generate__stage-hero-no">1</div>
          <div class="sxk-generate__stage-hero-info">
            <div class="sxk-generate__stage-hero-title">{{ stepDefs[0].title }}</div>
            <div class="sxk-generate__stage-hero-desc">{{ stepDefs[0].summary }}</div>
          </div>
        </div>
        -->
          <!-- 主体两栏：左侧 Agent 链路（窄/竖向） + 右侧 初稿对比 + 预览（主区） -->
          <el-row
            :gutter="16"
            class="sxk-generate__stage0-row"
          >
            <el-col
              :xs="24"
              :sm="8"
              :md="7"
              :lg="6"
            >
              <!-- Agent 执行链路（横向时间线 + 可点击节点详情） -->
              <el-card
                class="sxk-generate__card sxk-generate__card-trace is-scrollable"
                shadow="never"
                :style="cardScrollStyle"
              >
                <template #header>
                  <div class="sxk-generate__card-head sxk-generate__trace-toggle">
                    <div
                      class="sxk-generate__trace-left"
                      @click="showAgentTrace = !showAgentTrace"
                    >
                      <span class="sxk-generate__trace-icon"><el-icon><Connection /></el-icon></span>
                      <b>Agent 执行链路</b>
                      <span
                        v-if="currentDraft.agent_trace?.length || liveCurrentAgent"
                        class="sxk-generate__trace-stats"
                      >
                        <span class="sxk-generate__trace-stat is-success">
                          <el-icon><CircleCheckFilled /></el-icon>
                          {{ currentDraft.agent_trace?.length || 0 }} 步
                        </span>
                        <span
                          v-if="liveCurrentAgent"
                          class="sxk-generate__trace-stat is-running"
                        >
                          <el-icon class="is-spin"><Loading /></el-icon>
                          {{ liveCurrentAgent }} 执行中
                        </span>
                      </span>
                    </div>
                    <div class="sxk-generate__trace-right">
                      <span
                        class="sxk-generate__trace-toggle-btn"
                        :title="showAgentTrace ? '收起详情' : '展开详情'"
                        @click="showAgentTrace = !showAgentTrace"
                      >
                        <el-icon :class="{ 'is-open': showAgentTrace }"><ArrowRight /></el-icon>
                      </span>
                    </div>
                  </div>
                </template>

                <!-- ============ 横向时间线节点（详情已融合到每个节点内，节点不可点击） ============ -->
                <div class="sxk-generate__timeline">
                  <!-- 已完成步骤：来自 currentDraft.agent_trace
                 设计：每个节点直接显示详情（agent名 + 耗时 + 消息），节点本身不可点击 -->
                  <div
                    v-for="(s, i) in currentDraft.agent_trace"
                    :key="`agent-${i}`"
                    class="sxk-generate__tl-node"
                    :class="`is-${s.status}`"
                  >
                    <div class="sxk-generate__tl-dot">
                      <el-icon v-if="s.status === 'success'">
                        <CircleCheckFilled />
                      </el-icon>
                      <el-icon v-else-if="s.status === 'warning'">
                        <WarningFilled />
                      </el-icon>
                      <el-icon v-else-if="s.status === 'error'">
                        <CircleCloseFilled />
                      </el-icon>
                      <span
                        v-else
                        class="sxk-generate__tl-dot-num"
                      >{{ i + 1 }}</span>
                    </div>
                    <div class="sxk-generate__tl-info">
                      <!-- 节点头部：步骤号 + Agent 名 + 状态标签 + 耗时 -->
                      <div class="sxk-generate__tl-head">
                        <span class="sxk-generate__tl-step-idx">步骤 {{ i + 1 }}</span>
                        <span class="sxk-generate__tl-name">{{ s.agent }}</span>
                        <el-tag
                          size="small"
                          :type="s.status === 'success' ? 'success' : s.status === 'warning' ? 'warning' : 'danger'"
                          effect="light"
                          class="sxk-generate__tl-status-tag"
                        >
                          <el-icon style="margin-right: 3px">
                            <CircleCheckFilled v-if="s.status === 'success'" />
                            <WarningFilled v-else />
                          </el-icon>
                          {{ STATUS_LABEL[s.status] }}
                        </el-tag>
                      </div>
                      <!-- 节点详情：消息 + issues 合并到同一个主题色块中
                     - 成功节点：仅显示 s.message
                     - 警告/错误节点：显示 s.message + 具体问题列表（视觉合二为一） -->
                      <div
                        v-if="s.message || ((s.status === 'warning' || s.status === 'error') && s.output?.issues?.length)"
                        class="sxk-generate__tl-msg"
                      >
                        <!-- 警告/错误节点：摘要 + 列表（合并为一个块）
                       关键：摘要中的数字使用 dedupIssues 后的真实数量（避免与列表条数不一致）-->
                        <template v-if="s.status === 'warning' || s.status === 'error'">
                          <div
                            v-if="s.message || s.output?.issues?.length"
                            class="sxk-generate__tl-msg-summary"
                          >
                            {{ formatAgentMsg(s) }}
                          </div>
                          <ul
                            v-if="s.output?.issues?.length"
                            class="sxk-generate__tl-issues"
                          >
                            <li
                              v-for="(issue, k) in dedupIssues(s.output.issues)"
                              :key="k"
                              class="sxk-generate__tl-issue"
                            >
                              <span class="sxk-generate__tl-issue-bullet">·</span>
                              <span class="sxk-generate__tl-issue-text">{{ issue }}</span>
                            </li>
                          </ul>
                        </template>
                        <!-- 成功/运行中节点：仅消息 -->
                        <template v-else>
                          {{ s.message }}
                        </template>
                      </div>
                    </div>
                    <span
                      v-if="i < currentDraft.agent_trace.length - 1 || liveCurrentAgent"
                      class="sxk-generate__tl-line"
                    />
                  </div>
                  <!-- Phase E: SSE 流式中"正在执行"占位节点 -->
                  <div
                    v-if="liveCurrentAgent"
                    :key="`running-${liveCurrentAgent}`"
                    class="sxk-generate__tl-node is-running"
                  >
                    <div class="sxk-generate__tl-dot is-running-dot">
                      <el-icon class="is-spin">
                        <Loading />
                      </el-icon>
                    </div>
                    <div class="sxk-generate__tl-info">
                      <div class="sxk-generate__tl-head">
                        <span class="sxk-generate__tl-step-idx">执行中</span>
                        <span class="sxk-generate__tl-name">{{ liveCurrentAgent }}</span>
                        <el-tag
                          size="small"
                          type="primary"
                          effect="light"
                          class="sxk-generate__tl-status-tag"
                        >
                          <el-icon
                            class="is-spin"
                            style="margin-right: 3px"
                          >
                            <Loading />
                          </el-icon>
                          进行中
                        </el-tag>
                      </div>
                      <div class="sxk-generate__tl-msg is-running-msg">
                        Agent 正在执行...
                      </div>
                    </div>
                  </div>
                </div>

                <!-- ============ 折叠时：摘要信息条 ============ -->
                <div
                  v-if="!showAgentTrace"
                  class="sxk-generate__tl-collapsed"
                >
                  <span
                    v-if="currentDraft.validation?.issues?.length"
                    class="sxk-generate__tl-collapsed-warn"
                  >
                    <el-icon><WarningFilled /></el-icon>
                    {{ currentDraft.validation.issues.length }} 个待优化项
                  </span>
                  <!-- "所有 Agent 步骤已完成"提示默认隐藏（避免与时间线节点信息重复） -->
                  <span
                    v-else-if="false"
                    class="sxk-generate__tl-collapsed-ok"
                  >
                    <el-icon><CircleCheckFilled /></el-icon>
                    所有 Agent 步骤已完成
                  </span>
                  <!-- <el-link type="primary" :underline="false">
              点击展开时间线
              <el-icon><ArrowDown /></el-icon>
            </el-link> -->
                </div>
              </el-card>
            </el-col>
            <el-col
              :xs="24"
              :sm="16"
              :md="17"
              :lg="18"
            >
              <!-- 版本对比墙 + 当前预览 -->
              <el-card
                class="sxk-generate__card is-scrollable"
                shadow="never"
                :style="cardScrollStyle"
              >
                <template #footer>
                  <div class="sxk-generate__stage-foot">
                    <span class="sxk-generate__stage-foot-tip">
                      <el-icon><InfoFilled /></el-icon>
                      确认无误后点击「选定此版本」进入编辑与渠道适配
                    </span>
                    <el-button
                      type="primary"
                      size="small"
                      :loading="selectingDraft"
                      @click="onSelectDraftVersion(currentDraft.draft_versions.find(x => String(x.index) === draftVersionIndex))"
                    >
                      选定此版本 →
                    </el-button>
                  </div>
                </template>
                <template #header>
                  <div class="sxk-generate__card-head">
                    <div class="sxk-generate__card-head-left">
                      <b>初稿对比</b>
                      <span class="sxk-generate__card-tip">
                        点击下方任一卡片预览完整内容，满意后点击「选定」进入下一步
                      </span>
                    </div>
                    <el-button
                      size="small"
                      :loading="triggering"
                      @click="onRegenerateDraft"
                    >
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
                    <h1 class="sxk-generate__doc-title">
                      {{ v.title }}
                    </h1>
                    <div
                      class="sxk-generate__doc-content markdown-body"
                      v-html="renderArticle(v.body, v.images, v.title)"
                    />
                    <div
                      v-if="v.tags?.length"
                      class="sxk-generate__doc-tags"
                    >
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
                </div>
              </el-card>
            </el-col>
          </el-row>
        </div>

        <!-- ============ 阶段 1：编辑选定内容 + 多选渠道 ============ -->
        <div
          v-else-if="draftStep === 1"
          class="sxk-generate__stage"
        >
          <!-- 阶段标题 hero（已注释，由右栏 segmented 替代） -->
          <!--
        <div class="sxk-generate__stage-hero">
          <div class="sxk-generate__stage-hero-no">2</div>
          <div class="sxk-generate__stage-hero-info">
            <div class="sxk-generate__stage-hero-title">{{ stepDefs[1].title }}</div>
            <div class="sxk-generate__stage-hero-desc">{{ stepDefs[1].summary }}</div>
          </div>
        </div>
        -->
          <el-row
            :gutter="16"
            class="sxk-generate__stage1-row"
          >
            <!-- 左侧：编辑选定内容 -->
            <el-col :span="16">
              <el-card
                class="sxk-generate__card is-scrollable"
                shadow="never"
                :style="cardScrollStyle"
              >
                <template #header>
                  <div class="sxk-generate__card-head">
                    <b>编辑选定内容</b>
                    <span class="sxk-generate__card-tip">
                      改动标题与正文，确认后进入保存
                    </span>
                  </div>
                </template>
                <div class="sxk-generate__edit-title">
                  <el-input
                    v-model="draftEditingVersion.title"
                    placeholder="文案标题"
                    size="large"
                  >
                    <template #prepend>
                      标题
                    </template>
                  </el-input>
                </div>
                <div class="sxk-generate__edit-body">
                  <div class="sxk-generate__edit-body-head">
                    <span>正文</span>
                    <span class="sxk-generate__edit-body-cnt">{{ bodyCharCount }} 字</span>
                  </div>
                  <el-input
                    v-model="draftEditingVersion.body"
                    class="sxk-generate__edit-body-input"
                    type="textarea"
                    :autosize="{ minRows: 10 }"
                  />
                </div>
                <div
                  v-if="draftEditingVersion.tags?.length"
                  class="sxk-generate__edit-tags"
                >
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
              <el-card
                class="sxk-generate__card sxk-generate__channel-pane is-scrollable"
                shadow="never"
                :style="cardScrollStyle"
              >
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
                  <el-checkbox-group
                    v-model="selectedChannels"
                    class="sxk-generate__channel-list"
                  >
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
                          <div class="sxk-generate__channel-name">
                            {{ ch.display_name }}
                          </div>
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
                    :loading="adaptingDraft"
                    :disabled="!selectedChannels.length"
                    @click="onAdapt"
                  >
                    <el-icon v-if="!adaptingDraft">
                      <Right />
                    </el-icon>
                    {{ adaptingDraft ? '适配中...' : '确认适配（' + selectedChannels.length + ' 个渠道）' }}
                  </el-button>
                </div>
              </el-card>
            </el-col>
          </el-row>
        </div>

        <!-- ============ 阶段 2：保存（卡片对比墙 + 预览/编辑）============ -->
        <div
          v-else
          class="sxk-generate__stage"
        >
          <!-- 阶段标题 hero（已注释，由右栏 segmented 替代） -->
          <!--
        <div class="sxk-generate__stage-hero">
          <div class="sxk-generate__stage-hero-no">3</div>
          <div class="sxk-generate__stage-hero-info">
            <div class="sxk-generate__stage-hero-title">{{ stepDefs[2].title }}</div>
            <div class="sxk-generate__stage-hero-desc">{{ stepDefs[2].summary }}</div>
          </div>
        </div>
        -->
          <el-card
            class="sxk-generate__card is-scrollable sxk-generate__card-horizontal"
            :body-style="cardScrollStyle"
            shadow="never"
          >
            <template #header>
              <div class="sxk-generate__card-head">
                <div class="sxk-generate__card-head-left">
                  <b>保存</b>
                  <span class="sxk-generate__card-tip">
                    共 {{ currentDraft.versions?.length || 0 }} 个渠道版本
                  </span>
                </div>
                <!-- 阶段 2 顶部操作组（按状态动态展示） -->
                <div class="sxk-generate__stage2-actions">
                  <!-- 回到最开始（清空所有数据） -->
                  <el-button
                    size="small"
                    plain
                    :icon="RefreshLeft"
                    @click="onRestartBeginning"
                  >
                    重新开始
                  </el-button>
                  <!-- 导出 -->
                  <el-button
                    size="small"
                    :icon="Download"
                    :loading="exportingDraft"
                    @click="onExport"
                  >
                    {{ exportingDraft ? '导出中' : '导出' }}
                  </el-button>
                  <!-- 主 CTA：保存到历史 -->
                  <el-button
                    v-if="!currentDraft.history_id"
                    size="default"
                    type="primary"
                    :loading="finalizingDraft"
                    @click="onFinalize"
                  >
                    {{ finalizingDraft ? '保存中...' : '保存' }}
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
                </div>
                <div class="sxk-generate__version-card-meta">
                  <span class="sxk-generate__version-card-stat">
                    <el-icon><Document /></el-icon>
                    {{ v.body?.length || 0 }} 字
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
              <!-- 顶部工具栏：仅保留"预览/编辑"切换（左侧重复的渠道信息已在顶部卡墙显示，删除） -->
              <div class="sxk-generate__channel-toolbar">
                <el-radio-group
                  v-model="genEditMode"
                  size="small"
                  class="sxk-generate__mode-switch"
                >
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
              <div
                v-if="!genEditMode"
                class="sxk-generate__doc-page"
              >
                <h1 class="sxk-generate__doc-title">
                  {{ v.title }}
                </h1>
                <div
                  class="sxk-generate__doc-content markdown-body"
                  v-html="renderArticle(v.body, v.images, v.title)"
                />
                <div
                  v-if="v.tags?.length"
                  class="sxk-generate__doc-tags"
                >
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
              <div
                v-else
                class="sxk-generate__edit-area"
              >
                <div class="sxk-generate__edit-title">
                  <el-input
                    v-model="v.title"
                    size="large"
                    placeholder="文案标题"
                  >
                    <template #prepend>
                      标题
                    </template>
                  </el-input>
                </div>
                <div class="sxk-generate__edit-body">
                  <div class="sxk-generate__edit-body-head">
                    <span>正文</span>
                    <span class="sxk-generate__edit-body-cnt">{{ (v.body || '').length }} 字</span>
                  </div>
                  <el-input
                    v-model="v.body"
                    type="textarea"
                    :autosize="{ minRows: 12 }"
                  />
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
                      :title="votedDir(v) === 'like' ? '取消点赞' : '点赞'"
                      @click="onCastVote(v)"
                    >
                      <svg
                        viewBox="0 0 24 24"
                        width="14"
                        height="14"
                        fill="currentColor"
                      >
                        <path d="M2 21h4V9H2v12zm20-11c0-1.1-.9-2-2-2h-6.31l.95-4.57.03-.32c0-.41-.17-.79-.44-1.06L13.17 1 7.59 6.59C7.22 6.95 7 7.45 7 8v10c0 1.1.9 2 2 2h9c.83 0 1.54-.5 1.84-1.22l3.02-7.05c.09-.23.14-.47.14-.73v-2z" />
                      </svg>
                      <span class="sxk-generate__vote-num">{{ v.votes?.like || 0 }}</span>
                    </button>
                    <button
                      class="sxk-generate__vote-btn is-dislike"
                      :class="{ 'is-active': votedDir(v) === 'dislike' }"
                      :title="votedDir(v) === 'dislike' ? '取消点踩' : '点踩'"
                      @click="onCastVote(v, 'dislike')"
                    >
                      <svg
                        viewBox="0 0 24 24"
                        width="14"
                        height="14"
                        fill="currentColor"
                      >
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
                </div>
              </div>
            </div>
          </el-card>
        </div>
      </basic-block>
    </div>
    <!-- /.sxk-generate__body -->

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
      <div
        v-if="currentDraft"
        class="sxk-generate__done-drawer"
      >
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
          <h2 class="sxk-generate__done-title">
            保存已完成
          </h2>

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
        <span />
      </template>
    </el-dialog>

    <!-- SEO 分析弹窗（与系统中其他弹窗保持一致：640px、居中、深色遮罩、圆角 12px、阴影） -->
    <el-dialog
      v-model="seoVisible"
      width="640px"
      align-center
      :show-close="true"
      :close-on-click-modal="true"
      :close-on-press-escape="true"
      :modal="true"
      :modal-append-to-body="true"
      :append-to-body="true"
      :lock-scroll="true"
      custom-class="sxk-generate__seo-dialog"
    >
      <template #header>
        <div class="sxk-generate__seo-header">
          <div class="sxk-generate__seo-header-icon">
            <el-icon><DataAnalysis /></el-icon>
          </div>
          <div class="sxk-generate__seo-header-text">
            <div class="sxk-generate__seo-header-title">
              SEO 智能分析
            </div>
            <div
              v-if="seoTarget"
              class="sxk-generate__seo-header-sub"
            >
              {{ seoTarget.channel }} · {{ seoTarget.title || '未命名版本' }}
            </div>
          </div>
        </div>
      </template>
      <div
        v-if="seoResult"
        v-loading="seoLoading"
        class="sxk-generate__seo"
      >
        <!-- ============ 评分主卡 ============ -->
        <div class="sxk-generate__seo-hero">
          <!-- 左侧：环形评分 -->
          <div class="sxk-generate__seo-ring">
            <svg
              viewBox="0 0 120 120"
              class="sxk-generate__seo-ring-svg"
            >
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
              <div
                class="sxk-generate__seo-ring-num"
                :style="{ color: seoScoreColor }"
              >
                {{ seoResult.score }}
              </div>
              <div class="sxk-generate__seo-ring-tip">
                /100
              </div>
            </div>
          </div>
          <!-- 右侧：评分等级 + 关键词 + 维度统计 -->
          <div class="sxk-generate__seo-side">
            <div
              class="sxk-generate__seo-grade"
              :style="{ background: seoScoreColor + '15', color: seoScoreColor }"
            >
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
            <div
              v-if="seoResult.keywords?.length"
              class="sxk-generate__seo-kw"
            >
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
                <el-icon v-if="s.level === 'good'">
                  <CircleCheckFilled />
                </el-icon>
                <el-icon v-else-if="s.level === 'warning'">
                  <WarningFilled />
                </el-icon>
                <el-icon v-else>
                  <CircleCloseFilled />
                </el-icon>
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
        <div
          v-if="seoResult.stats.meta_description"
          class="sxk-generate__seo-section"
        >
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
          <el-button @click="seoVisible = false">
            关闭
          </el-button>
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
 *   阶段 2：多渠道版本展示 → finalize → 落 history
 *
 * 草稿状态机：stage ∈ draft | editing | adapted | done
 * 持久化：localStorage[`sxk-draft-id-${tabId}`]，每个 Tab 独立，刷新自动恢复
 */
import { ref, reactive, computed, onMounted, onActivated, onBeforeUnmount, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  MagicStick,
  Refresh,
  ArrowRight,
  Download,
  Search,
  PieChart,  // 备用：竞品对比（ICON_MAP）
  Share,      // 备用：渠道适配（ICON_MAP）
  Promotion,  // 备用：活动（ICON_MAP）
  Message,    // 备用：邮件（ICON_MAP）
  Document,   // 默认/产品介绍
  // 智能匹配新增（与 templates 页面 SCENE_STYLE_RULES 一致）
  Monitor,        // banner/官网/首页
  Histogram,      // 产品介绍/产品功能/白皮书
  TrendCharts,    // 竞品/对比/竞争
  Medal,          // 案例/客户/成功
  Film,           // ppt/演示/大纲/路演
  ChatDotRound,   // 社交/媒体/帖子/传播
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
  EditPen,
  Folder,
  DataAnalysis,
  Files,
  Reading,
  Close,
  Check,
  Operation,
  RefreshLeft
} from '@element-plus/icons-vue'
import BasicBlock from '@/components/basic-block/main.vue'
import { sxkApi } from '@/mock/sxkApi'
import { renderMarkdown, renderArticle as renderArticleUtil } from './md'
import { useTagsStore } from '@/store/modules/tags'

// ---------- 路由与基础状态 ----------
const route = useRoute()
const router = useRouter()
const tagsStore = useTagsStore()

// 触发状态
const triggering = ref(false)
const selectingDraft = ref(false)
const adaptingDraft = ref(false)
const finalizingDraft = ref(false)
// 阶段 2 是否已完成（保存到历史后置 true，刷新"保存"步骤状态为"完成"）
const stage2Completed = ref(false)
// 左栏配置卡显示控制：true = 显示（初始/开始新创作），false = 隐藏（生成后）
const configPanelVisible = ref(true)

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

// ========== Phase E: SSE 流式生成状态 ==========
// 是否启用 SSE 流式（真实链路才启用，mock 走原 createDraft 同步流程）
const sseEnabled = sxkApi.isSSEEnabled()
// Agent 实时步骤（SSE 推送中追加，完成后并入 currentDraft.agent_trace）
const liveSteps = ref([])
// 当前正在执行的 Agent 名
const liveCurrentAgent = ref('')
// 已生成的版本（每收到一个 version_done 就按 index 有序插入，实时显示）
const liveVersions = ref([])
// SSE 流实例（用于 abort）
const sseInstance = ref(null)
// Agent 名缩写（去掉 "Agent" 后缀）
const shortAgentName = (name) => String(name || '').replace(/Agent$/i, '').trim() || name

// ========== 生成中 Loading 状态 ==========
// Agent 中文名映射
const AGENT_LABELS = {
  '产品信息检索 Agent': '产品信息检索',
  '竞品分析 Agent': '竞品分析',
  '内容生成 Agent': '内容生成',
  '内容校验 Agent': '内容校验',
  '渠道适配 Agent': '渠道适配'
}
// 草稿生成阶段的标准 Agent 顺序
const DRAFT_AGENT_FLOW = ['产品信息检索 Agent', '竞品分析 Agent', '内容生成 Agent', '内容校验 Agent']
// 渠道适配阶段的 Agent 顺序
const ADAPT_AGENT_FLOW = ['渠道适配 Agent']
// 保存阶段的 Agent 顺序（已去掉文生图，仅保留保存）
const FINALIZE_AGENT_FLOW = []

// Loading 是否显示（阶段 0 生成 + 阶段 1 适配 + 阶段 2 保存）
const genLoadingVisible = computed(() => {
  if (triggering.value && !currentDraft.value) return true
  if (adaptingDraft.value) return true
  if (finalizingDraft.value) return true
  return false
})

// Loading 标题
const genLoadingTitle = computed(() => {
  if (adaptingDraft.value) return 'AI 正在适配渠道…'
  if (finalizingDraft.value) return '正在保存…'
  return 'AI 正在生成文案…'
})

// Loading 副标题
const genLoadingSub = computed(() => {
  if (adaptingDraft.value) {
    return liveCurrentAgent.value ? `${liveCurrentAgent.value} 执行中` : '正在为选定渠道生成适配版本'
  }
  if (finalizingDraft.value) {
    return liveCurrentAgent.value ? `${liveCurrentAgent.value} 执行中` : '正在保存到历史记录'
  }
  return liveCurrentAgent.value ? `${liveCurrentAgent.value} 执行中` : '正在调度多个 Agent 协同工作'
})

// 步骤指示（done / running / wait）
const genLoadingSteps = computed(() => {
  const agentFlow = adaptingDraft.value ? ADAPT_AGENT_FLOW
    : finalizingDraft.value ? FINALIZE_AGENT_FLOW
    : DRAFT_AGENT_FLOW
  const completedAgents = liveSteps.value.map((s) => s.agent)
  return agentFlow.map((agent) => {
    const label = AGENT_LABELS[agent] || shortAgentName(agent)
    if (completedAgents.includes(agent)) return { label, state: 'done' }
    if (liveCurrentAgent.value === agent) return { label, state: 'running' }
    return { label, state: 'wait' }
  })
})

// issues 去重（保留首次出现顺序；后端会重复推送相同问题）
// 关键：规范化空白 + 标点差异（确保完全相同文本才视为重复）
const dedupIssues = (issues) => {
  if (!Array.isArray(issues)) return []
  const normalize = (s) => String(s || '')
    // 去除全角/半角空白差异
    .replace(/[\s\u00A0\u3000]+/g, ' ')
    // 统一全角「」/『』/[]/() 为半角
    .replace(/[\u3010\u3011\uFF5B\uFF5D\u300A\u300B\u300C\u300D]/g, m => ({ '\u3010': '[', '\u3011': ']', '\uFF5B': '{', '\uFF5D': '}', '\u300A': '《', '\u300B': '》', '\u300C': '「', '\u300D': '」' }[m]))
    // 统一冒号
    .replace(/[:\uFF1A\uFF1B]/g, ':')
    .trim()
  const seen = new Set()
  const result = []
  for (const it of issues) {
    const raw = String(it || '').trim()
    if (!raw) continue
    const key = normalize(raw)
    if (seen.has(key)) continue
    seen.add(key)
    result.push(raw)
  }
  return result
}

// 生成节点摘要消息（修正后端 s.message 中"数字与列表条数"不一致的问题）
// - 警告/错误节点：若 s.message 含"发现 N 项..."格式，N 用 dedupIssues 后的真实数量
// - 成功节点：原样返回
// - 其他情况：原样返回
const formatAgentMsg = (s) => {
  if (!s) return ''
  // 成功节点：直接用后端消息
  if (s.status !== 'warning' && s.status !== 'error') {
    return s.message || ''
  }
  const issues = dedupIssues(s.output?.issues)
  // 后端消息格式："发现 N 项需关注的问题"
  // 用真实去重后的 issues.length 替换
  const realCount = issues.length
  // 尝试匹配后端 message 中的数字（"发现 6 项需关注的问题"）
  if (typeof s.message === 'string') {
    const m = s.message.match(/(.*?发现\s*)\d+(\s*项.*)/)
    if (m) {
      return `${m[1]}${realCount}${m[2]}`
    }
  }
  // 兜底：若 message 不含数字模式，根据是否有 issues 生成
  if (realCount > 0) {
    return `发现 ${realCount} 项需关注的问题`
  }
  return s.message || ''
}

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
  if (v.images?.length > 0) return '已就绪'
  if (finalizingDraft.value) return '保存中'
  return '待保存'
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
  // 关闭完成态弹窗
  doneDrawerVisible.value = false
  // 弹一次确认窗（用户确认后直接重置状态，不再二次弹窗）
  ElMessageBox.confirm(
    '开始新创作将清空当前草稿与表单，确定继续？',
    '开始新创作',
    { type: 'warning', confirmButtonText: '开始新创作', cancelButtonText: '取消' }
  )
    .then(() => {
      // 直接重置（不再调用 onDiscardDraft，避免二次弹窗）
      currentDraft.value = null
      draftEditingVersion.value = null
      selectedChannels.value = []
      stage2Completed.value = false
      activeStep.value = -1
      showAgentTrace.value = false
      localStorage.removeItem(DRAFT_STORAGE_KEY)
      // 恢复左栏配置卡（生成前显示，生成后隐藏）
      configPanelVisible.value = true
      // 关键：清空表单所有字段（产品、场景、模板、提示词、动态参数）
      form.product_id = ''
      form.scene_code = 'product_intro'
      form.template_id = ''
      form.params = { prompt: '' }
      // 清空 Element Plus 表单校验状态
      if (formRef.value) formRef.value.clearValidate()
      // 关键：清空草稿相关 UI 状态（版本选择 / 渠道选择等）
      draftVersionIndex.value = ''
      adaptVersionIndex.value = ''
      showAgentTrace.value = false
      // 关键：清空 SEO 评分缓存
      seoResult.value = null
      seoVisible.value = false
      // 关键：清空编辑模式
      genEditMode.value = false
      // 提示用户
      ElMessage.success('已开始新创作')
    })
    .catch(() => {})
}
const onStayHere = () => {
  // 关闭按钮：仅关闭弹窗，不弹提示（用户主动关闭不应被打断）
  doneDrawerVisible.value = false
}

// 回到页面最开始（清空所有数据，如同第一次进入）
function resetToInitialState() {
  currentDraft.value = null
  draftEditingVersion.value = null
  selectedChannels.value = []
  stage2Completed.value = false
  activeStep.value = -1
  showAgentTrace.value = false
  localStorage.removeItem(DRAFT_STORAGE_KEY)
  configPanelVisible.value = true
  form.product_id = ''
  form.scene_code = 'product_intro'
  form.template_id = ''
  form.params = { prompt: '' }
  if (formRef.value) formRef.value.clearValidate()
  draftVersionIndex.value = ''
  adaptVersionIndex.value = ''
  seoResult.value = null
  seoVisible.value = false
  genEditMode.value = false
  doneDrawerVisible.value = false
}

const onRestartBeginning = () => {
  const saved = !!currentDraft.value?.history_id
  if (!saved) {
    // 未保存：警告草稿将丢失
    ElMessageBox.confirm(
      '当前任务尚未保存，回到最先后草稿将无法保存，确定继续？',
      '草稿未保存',
      { type: 'warning', confirmButtonText: '确定回到', cancelButtonText: '取消' }
    )
      .then(() => {
        resetToInitialState()
        ElMessage.success('已回到开始')
      })
      .catch(() => {})
  } else {
    // 已保存：确认是否回到最开始
    ElMessageBox.confirm(
      '回到最先后将清空当前所有数据，确定继续？',
      '回到最开始',
      { type: 'info', confirmButtonText: '确定回到', cancelButtonText: '取消' }
    )
      .then(() => {
        resetToInitialState()
        ElMessage.success('已回到开始')
      })
      .catch(() => {})
  }
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
  params: {},
  word_limit: 0
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
// 阶段命名遵循 B2B 内容生产标准流程：生成 → 编辑 → 发布
const stepDefs = [
  {
    title: '生成初稿',
    desc: '检索 · 生成 · 校验',
    summary: '选择 1 个最符合预期的初稿，进入下一步'
  },
  {
    title: '编辑与渠道适配',
    desc: '改内容 · 选渠道',
    summary: '编辑选定初稿，并选择发布渠道'
  },
  {
    title: '保存',
    desc: '保存历史',
    summary: '将生成内容保存到生成历史'
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

// 将步骤序号映射为后端 stage 字段值
const stageValueMap = ['draft', 'editing', 'adapted']

const onStepJump = (i) => {
  // 点击当前阶段无反应
  if (i === draftStep.value) return

  // 禁用未达成的阶段
  if (i > draftStep.value && !(i === 2 && stage2Completed.value)) {
    ElMessage.info(`请先完成：${stepDefs[draftStep.value].title}`)
    return
  }

  // 阶段 2 已完成时不允许再跳回
  if (i === 2 && stage2Completed.value) {
    ElMessage.info('已完成的工作不能修改')
    return
  }

  // 向前回退：弹窗确认
  if (i < draftStep.value && currentDraft.value) {
    const fromTitle = stepDefs[draftStep.value].title
    const toTitle = stepDefs[i].title
    ElMessageBox.confirm(
      `即将从「${fromTitle}」回到「${toTitle}」，当前阶段未保存的内容将丢失，确定继续？`,
      `回到：${toTitle}`,
      { type: 'warning', confirmButtonText: '确定回到', cancelButtonText: '取消' }
    )
      .then(() => {
        currentDraft.value.stage = stageValueMap[i]
        // 重置阶段 2 完成标记（仅在回退到阶段 0 或 1 时）
        if (i < 2) stage2Completed.value = false
        ElMessage.success(`已回到：${toTitle}`)
      })
      .catch(() => {})
    return
  }
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

// ========== 场景图标/配色：与 templates 页面完全一致 ==========
// 参考：src/views/sxk/templates/index.vue 第 232-253 行

// 内置场景 → 图标映射（按 scene_code 匹配）
const SCENE_ICON_MAP = {
  product_intro: Document,
  competitor: PieChart,
  channel_adapt: Share,
  email: Message,
  event: Promotion,
  other: Document
}

// 内置场景 → 配色（按 scene_code 匹配）
const SCENE_COLOR_MAP = {
  product_intro: { bg: '#eff6ff', color: '#2563eb' },
  competitor:    { bg: '#fff7ed', color: '#ea580c' },
  channel_adapt: { bg: '#f0fdf4', color: '#16a34a' },
  email:         { bg: '#faf5ff', color: '#9333ea' },
  event:         { bg: '#fee2e2', color: '#dc2626' }
}

// 按场景名称关键词匹配图标+配色（顺序优先）
const SCENE_STYLE_RULES = [
  { keywords: ['banner', '官网', '首页'],          icon: Monitor,      bg: '#eff6ff', color: '#2563eb' },  // 蓝
  { keywords: ['产品介绍', '产品功能', '白皮书'],     icon: Histogram,    bg: '#f0fdf4', color: '#16a34a' },  // 绿
  { keywords: ['竞品', '对比', '竞争'],              icon: TrendCharts,  bg: '#fff7ed', color: '#ea580c' },  // 橙
  { keywords: ['案例', '客户', '成功'],              icon: Medal,        bg: '#faf5ff', color: '#9333ea' },  // 紫
  { keywords: ['ppt', '演示', '大纲', '路演'],       icon: Film,         bg: '#fee2e2', color: '#dc2626' },  // 红
  { keywords: ['社交', '媒体', '帖子', '传播'],       icon: ChatDotRound, bg: '#ecfdf5', color: '#059669' },  // 翠绿
  { keywords: ['邮件', 'email', 'edm'],             icon: Message,      bg: '#fffbeb', color: '#d97706' },  // 琥珀
  { keywords: ['活动', 'event', '推广'],            icon: Promotion,    bg: '#fef2f2', color: '#e11d48' }   // 玫红
]

const SCENE_FALLBACK_STYLE = { icon: Document, bg: '#f1f5f9', color: '#475569' }  // slate

// 获取场景样式：先按 scene_code 匹配，再按名称关键词匹配，最后 fallback
function getSceneStyle(sceneCode, sceneName = '') {
  // 1) 先按 code 匹配
  if (SCENE_ICON_MAP[sceneCode]) {
    const c = SCENE_COLOR_MAP[sceneCode] || SCENE_FALLBACK_STYLE
    return { icon: SCENE_ICON_MAP[sceneCode], bg: c.bg, color: c.color }
  }
  // 2) 按名称关键词匹配
  const name = (sceneName || '').toLowerCase()
  for (const rule of SCENE_STYLE_RULES) {
    if (rule.keywords.some((kw) => name.includes(kw.toLowerCase()))) {
      return { icon: rule.icon, bg: rule.bg, color: rule.color }
    }
  }
  // 3) fallback
  return { ...SCENE_FALLBACK_STYLE }
}

// 向后兼容：只获取图标
function getSceneIcon(sceneCode) {
  // 这里没有名称，需调用 getSceneStyle
  return SCENE_ICON_MAP[sceneCode] || Document
}

// ---------- 计算属性 ----------
const currentScene = computed(() =>
  scenes.value.find((s) => s.scene_code === form.scene_code)
)

// 关键：清理 label 末尾/开头的星号（兼容后端多带/少带 * 的情况）
const cleanLabel = (label) =>
  (label || '').replace(/(^\s*\*\s*|\s*\*\s*$)/g, '').trim()

// 关键：动态参数按类型分组（enum / text / textarea）
const enumParams = computed(() => {
  const list = currentScene.value?.params || []
  return list.filter((p) => p.type === 'enum' && p.options?.length)
})
const textParams = computed(() => {
  const list = currentScene.value?.params || []
  return list.filter((p) => p.type === 'text')
})
const textareaParams = computed(() => {
  const list = currentScene.value?.params || []
  return list.filter((p) => p.type === 'textarea')
})

// 关键：填写完成度（必填项中已填写的比例）
const requiredParamList = computed(() => {
  const list = currentScene.value?.params || []
  return list.filter((p) => p.required)
})
const filledRequiredCount = computed(() => {
  return requiredParamList.value.filter((p) => {
    const v = form.params[p.key]
    return v !== undefined && v !== null && String(v).trim() !== ''
  }).length
})
const completionProgress = computed(() => {
  const total = requiredParamList.value.length
  if (total === 0) return 100
  return Math.round((filledRequiredCount.value / total) * 100)
})
const requiredRemaining = computed(() => {
  return Math.max(0, requiredParamList.value.length - filledRequiredCount.value)
})

const draftStep = computed(() => {
  const s = currentDraft.value?.stage
  if (!s || s === 'draft') return 0
  if (s === 'editing') return 1
  return 2 // adapted / done
})

const stepTitle = computed(() => {
  return ['生成初稿', '编辑与渠道适配', '保存'][draftStep.value]
})

// el-card 样式：不锁死高度，让内容自然撑开，页面整体滚动
const cardScrollStyle = computed(() => ({
  display: 'flex',
  flexDirection: 'column'
}))

// 当前阶段的操作提示（与 stepDefs 的 summary 一致）
const stageSubtitleText = computed(() => stepDefs[draftStep.value]?.summary || '')

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
// 多 Tab 隔离：每个 Tab 的草稿 ID 独立存储，key 带 tabId
// setup() 在组件创建时执行一次，此时 route.query.tabId 是本 Tab 的 ID
const DRAFT_STORAGE_KEY = `sxk-draft-id-${route.query.tabId || 'default'}`

onMounted(async () => {
  // 1) 拉取基础数据
  const tasks = [
    loadProductOptions(),
    loadSceneSchemas(),
    loadChannels()
  ]
  await Promise.allSettled(tasks)

  // 2) 处理路由 query
  const { gid, scene, template } = route.query
  if (scene) form.scene_code = String(scene)
  if (template) form.template_id = String(template)

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
      if (template) await onTemplateChange(String(template))
    }
  }
  // 4) 数据加载完毕后更新一次副标题
  updateTabSublabel()
})

// keep-alive 重新激活时，刷新场景 schema（用户可能在其他 Tab 修改了动态参数名称）
onActivated(async () => {
  await loadSceneSchemas()
  updateTabSublabel()
})

onBeforeUnmount(() => {
  // keep-alive 缓存淘汰时（超过 max=15）触发，关闭残留 SSE 连接
  if (sseInstance.value) {
    try {
      sseInstance.value.abort?.()
    } catch {
      // ignore
    }
    sseInstance.value = null
  }
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

// ---------- Tab 副标题：根据产品/场景选择动态更新 ----------
function updateTabSublabel() {
  const tabId = route.query.tabId
  if (!tabId) return
  const parts = []
  if (form.product_id) {
    const p = productOptions.value.find((item) => item.product_id === form.product_id)
    if (p?.name) parts.push(p.name)
  }
  if (form.scene_code && currentScene.value) {
    const label = currentScene.value.label || currentScene.value.name || ''
    if (label) parts.push(label.replace(/\*/g, '').trim())
  }
  tagsStore.setTabSublabel(tabId, parts.join(' · '))
}
watch(() => form.product_id, updateTabSublabel)
watch(() => form.scene_code, updateTabSublabel)

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
  form.template_id = '' // 清空模板选择
  form.params.prompt = '' // 清空提示词
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
  form.template_id = templateId || ''
  if (!templateId) {
    form.params.prompt = ''
    return
  }
  // 优先从已加载的列表项回填（列表项已含 prompt 字段）
  const local = sceneTemplates.value.find((t) => t.template_id === templateId)
  if (local && local.prompt != null) {
    form.params.prompt = local.prompt
    return
  }
  // 兜底：请求模板详情获取 prompt
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
  // Phase E: 真实链路用 SSE 流式，mock 链路用原同步接口
  if (sseEnabled) {
    await _generateDraftSSE({
      product_id: form.product_id,
      scene_code: form.scene_code,
      template_id: form.template_id,
      style: '专业严谨',
      params: form.params,
      word_limit: form.word_limit || 0
    })
    return
  }
  try {
    const resp = await sxkApi.createDraft({
      product_id: form.product_id,
      scene_code: form.scene_code,
      template_id: form.template_id,
      style: '专业严谨',
      params: form.params,
      word_limit: form.word_limit || 0
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
    // 生成成功后，隐藏左栏配置卡（让右栏占满主区）
    configPanelVisible.value = false
    ElMessage.success('已生成 ' + (resp.data.draft_versions?.length || 0) + ' 个初稿')
  } catch (e) {
    ElMessage.error('创建草稿失败：' + (e?.message || '未知错误'))
  } finally {
    triggering.value = false
  }
}

/**
 * Phase E: SSE 流式生成草稿
 *
 * - 显示 Agent 实时工作卡片（liveSteps + liveCurrentAgent）
 * - 收到 step 事件 → 追加到 liveSteps
 * - 收到 done 事件 → 把完整 draft 写入 currentDraft
 * - 收到 error 事件 → 弹错
 * - 失败 → 自动 fallback 到 sxkApi.createDraft（兼容旧后端）
 */
async function _generateDraftSSE(payload) {
  // 重置实时状态
  liveSteps.value = []
  liveCurrentAgent.value = ''
  liveVersions.value = []
  showAgentTrace.value = true
  configPanelVisible.value = false

  try {
    const sse = await sxkApi.createDraftStream(payload, {
      onStep: (step) => {
        // 处理 version_done：每完成一个版本就按 index 有序插入 liveVersions 实时显示
        if (step?.kind === 'version_done' && step.version) {
          const idx = step.index
          // 按 index 升序插入（版本可能乱序到达）
          const list = liveVersions.value.filter((v) => v.index !== idx)
          list.push({ ...step.version, index: idx })
          list.sort((a, b) => a.index - b.index)
          liveVersions.value = list
          return
        }
        // 其他非 Agent 步骤静默忽略（version_start/version_attempt 等内部进度信号）
        if (!step || !step.agent) {
          return
        }
        // step 形如 {agent, status, message?, duration_ms?, output?}
        // 状态为 'running' 时是 Agent 开始；否则是完成
        if (step.status === 'running') {
          liveCurrentAgent.value = step.agent
        } else {
          // 完成事件：移除对应的 running，加入完整 step
          liveSteps.value.push(step)
          liveCurrentAgent.value = ''
        }
      },
      onDone: (draft) => {
        // 流式完成：合并 liveSteps 到 agent_trace
        currentDraft.value = {
          ...draft,
          agent_trace: [...liveSteps.value]
        }
        draftVersionIndex.value = '1'
        activeStep.value = -1
        localStorage.setItem(DRAFT_STORAGE_KEY, draft.id)
        sseInstance.value = null
        triggering.value = false
        liveVersions.value = []
        ElMessage.success(
          '已生成 ' + (draft.draft_versions?.length || 0) + ' 个初稿（流式）'
        )
      },
      onError: (err) => {
        console.error('[SSE] createDraftStream 错误:', err)
        sseInstance.value = null
        triggering.value = false
        // SSE 失败时 fallback 到同步接口
        ElMessage.warning('流式生成失败，降级到同步接口：' + (err.message || ''))
        _generateDraftFallback(payload)
      }
    })
    sseInstance.value = sse
  } catch (e) {
    // sse-client 自身异常（如 import 失败、连接失败）→ fallback
    console.error('[SSE] init 失败:', e)
    triggering.value = false
    _generateDraftFallback(payload)
  }
}

/**
 * Phase E 兼容：SSE 失败时降级到同步接口
 */
async function _generateDraftFallback(payload) {
  triggering.value = true
  try {
    const resp = await sxkApi.createDraft(payload)
    triggering.value = false
    if (resp.code !== 0) {
      ElMessage.error(resp.msg || '创建草稿失败')
      return
    }
    currentDraft.value = resp.data
    draftVersionIndex.value = '1'
    activeStep.value = -1
    showAgentTrace.value = false
    localStorage.setItem(DRAFT_STORAGE_KEY, resp.data.id)
    liveSteps.value = []
    ElMessage.success('已生成 ' + (resp.data.draft_versions?.length || 0) + ' 个初稿')
  } catch (e) {
    ElMessage.error('创建草稿失败：' + (e?.message || '未知错误'))
  }
}

async function onRegenerateDraft() {
  if (!currentDraft.value) return
  // Phase E: 真实链路用 SSE 流式
  if (sseEnabled) {
    await _regenerateDraftSSE(currentDraft.value.id)
    return
  }
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

/**
 * Phase E: SSE 流式重新生成
 */
async function _regenerateDraftSSE(draftId) {
  liveSteps.value = []
  liveCurrentAgent.value = ''
  liveVersions.value = []
  showAgentTrace.value = true
  triggering.value = true
  try {
    const sse = await sxkApi.regenerateDraftStream(draftId, {
      onStep: (step) => {
        // 处理 version_done：每完成一个版本就按 index 有序插入 liveVersions 实时显示
        if (step?.kind === 'version_done' && step.version) {
          const idx = step.index
          const list = liveVersions.value.filter((v) => v.index !== idx)
          list.push({ ...step.version, index: idx })
          list.sort((a, b) => a.index - b.index)
          liveVersions.value = list
          return
        }
        if (!step || !step.agent) {
          return
        }
        if (step.status === 'running') {
          liveCurrentAgent.value = step.agent
        } else {
          liveSteps.value.push(step)
          liveCurrentAgent.value = ''
        }
      },
      onDone: (draft) => {
        currentDraft.value = {
          ...draft,
          agent_trace: [...liveSteps.value]
        }
        draftVersionIndex.value = '1'
        sseInstance.value = null
        triggering.value = false
        liveVersions.value = []
        ElMessage.success('已重新生成初稿（流式）')
      },
      onError: (err) => {
        console.error('[SSE] regenerateDraftStream 错误:', err)
        sseInstance.value = null
        triggering.value = false
        ElMessage.warning('流式重新生成失败，降级到同步接口')
        _regenerateDraftFallback(draftId)
      }
    })
    sseInstance.value = sse
  } catch (e) {
    console.error('[SSE] init 失败:', e)
    triggering.value = false
    _regenerateDraftFallback(draftId)
  }
}

async function _regenerateDraftFallback(draftId) {
  triggering.value = true
  try {
    const resp = await sxkApi.regenerateDraft(draftId)
    triggering.value = false
    if (resp.code !== 0) {
      ElMessage.error(resp.msg || '重新生成失败')
      return
    }
    currentDraft.value = resp.data
    draftVersionIndex.value = '1'
    liveSteps.value = []
    ElMessage.success('已重新生成初稿')
  } catch (e) {
    ElMessage.error('重新生成失败：' + (e?.message || '未知错误'))
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
    ElMessage.success('已选定，进入编辑与渠道适配')
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
    // 再做渠道适配
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
    // 标记阶段 2 已完成（让步骤条"保存"显示为"完成"）
    stage2Completed.value = true
    ElMessage.success('已保存到历史记录')
  } catch (e) {
    ElMessage.error('保存失败：' + (e?.message || '未知错误'))
  } finally {
    finalizingDraft.value = false
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
      // 关键：清空表单字段（保持与 onStartNew 一致）
      form.product_id = ''
      form.scene_code = 'product_intro'
      form.template_id = ''
      form.params = { prompt: '' }
      if (formRef.value) formRef.value.clearValidate()
      draftVersionIndex.value = ''
      adaptVersionIndex.value = ''
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
  // 加载草稿后，隐藏左栏配置卡（已进入阶段 0/1/2）
  configPanelVisible.value = false
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
    // 从历史记录恢复：隐藏左栏配置卡（已进入阶段 2）
    configPanelVisible.value = false
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
// 关键：flex column 容器 + 显式 100% 宽高，让高度能撑满父级，宽度靠 width: 100% 而非 stretch
.sxk-generate {
  display: flex;
  flex-direction: column;
  width: 100% !important;
  min-height: 100% !important; // 不锁死高度，内容自然撑开
  max-width: 100% !important;
  margin: 0 !important;
  margin-left: 0 !important;
  margin-right: 0 !important;
  box-sizing: border-box;
  position: relative;
  // 关键：内部用 flex 嵌套实现横向排列
  & > .sxk-page-welcome,
  & > .sxk-generate__body {
    display: flex;
    width: 100% !important; // 关键：显式撑满父容器宽度（不依赖 stretch）
    box-sizing: border-box;
  }
  & > .sxk-page-welcome {
    flex-direction: row;
    align-items: center;
    margin-bottom: 12px;
    flex-shrink: 0;
  }
  & > .sxk-generate__body {
    flex-direction: row;
    gap: 12px;
    align-items: flex-start; // 不拉伸，让内容决定高度
    flex: 1 1 auto !important;
    height: auto !important;
  }
}

// 关键：本页用 block 布局，欢迎条只需基础宽度撑满
.sxk-page-welcome {
  width: 100%;
  box-sizing: border-box;
  // margin-bottom 由 .sxk-generate > & 子选择器控制
}

// 关键：内容区（左侧 config + 右侧 result 的水平分栏）
.sxk-generate__body {
  width: 100% !important; // 关键：撑满父容器宽度
  box-sizing: border-box; // 关键：避免 padding 撑大
  // display 和 gap 由 .sxk-generate 的子选择器接管

  @media (max-width: 1100px) {
    flex-direction: column;
  }
}

// ---------- 左栏：生成配置 + 阶段指示（全宽撑满，内容自然展开） ----------
.sxk-generate__config {
  // 关键：默认全宽撑满（首次访问无草稿时）
  flex: 1 1 auto;
  width: 100%;
  max-width: 100%;
  display: flex;
  flex-direction: column;
  align-self: flex-start;

  // 关键：当父级是 .sxk-generate__body（有右栏兄弟）时，左栏占 50%
  .sxk-generate__body > & {
    flex: 1 1 0% !important;
    width: 50% !important;
    min-width: 0;
  }

  // 关键：配置区头部（与首页彩色长条风格一致，嵌在 basic-block header 区域）
  .sxk-generate__config-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    width: 100%;
    padding: 0;
    gap: $spacing-md;
  }
  .sxk-generate__config-header-left {
    display: flex;
    align-items: center;
    gap: 12px;
    flex: 1;
    min-width: 0;
  }
  .sxk-generate__config-bar {
    display: inline-block;
    width: 4px;
    height: 28px;
    background: linear-gradient(180deg, #6366f1, #4f46e5);
    border-radius: $radius-sm;
    flex-shrink: 0;
  }
  .sxk-generate__config-title {
    margin: 0 0 2px;
    font-size: 18px;
    font-weight: 700;
    line-height: 1.3;
    background: linear-gradient(135deg, #6366f1, #4f46e5, #3b82f6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  .sxk-generate__config-desc {
    margin: 0;
    font-size: 12px;
    color: $text-secondary;
    line-height: 1.4;
  }

  // 让 basic-block 自然展开
  :deep(.basic-block) {
    display: flex;
    flex-direction: column;
  }
  :deep(.basic-block__body) {
    display: flex;
    flex-direction: column;
    flex: 1 1 0%;
  }
  // basic-block__body 内的 el-form 自然展开
  :deep(.basic-block__body) > .el-form {
    flex: 1 1 0%;
    // 滚动条与文字保持距离
    padding-right: 20px;
  }
  @media (max-width: 1100px) {
    max-width: 100%;
  }
  :deep(.basic-block__header) {
    padding-bottom: $spacing-md;
    flex-shrink: 0;
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

// 右栏子标题（当前阶段操作提示）
.sxk-generate__main-subtitle {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
  font-size: $font-size-sm;
  color: $text-secondary;
  line-height: 1.5;
}
.sxk-generate__main-subtitle-icon {
  color: $primary-color;
  font-size: 14px;
}

// 右栏三阶段分段指示（segmented）
.sxk-generate__main-segments {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  margin-top: 12px;
  padding: 6px;
  background: $bg-hover;
  border-radius: $radius-md;
}
.sxk-generate__main-segment {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: $bg-card;
  border-radius: $radius-sm;
  cursor: pointer;
  transition: all 0.18s ease;
  position: relative;
  overflow: hidden;
  &.is-active {
    background: $primary-color;
    color: #fff;
    box-shadow: 0 2px 8px rgba(26, 86, 219, 0.18);
    .sxk-generate__main-segment-no {
      background: rgba(255, 255, 255, 0.2);
      color: #fff;
      border-color: transparent;
    }
    .sxk-generate__main-segment-title,
    .sxk-generate__main-segment-desc {
      color: #fff;
    }
  }
  &.is-done:not(.is-active) {
    .sxk-generate__main-segment-no {
      background: $primary-color-light;
      color: $primary-color;
      border-color: $primary-color-light;
    }
  }
  &.is-disabled {
    opacity: 0.55;
    cursor: not-allowed;
  }
  &:not(.is-disabled):hover {
    background: $primary-color-light;
  }
  &.is-active:hover {
    background: $primary-color;
  }
}
.sxk-generate__main-segment-no {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: $bg-card;
  border: 1px solid $border-base;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: $font-size-sm;
  font-weight: 600;
  color: $text-secondary;
  transition: all 0.18s ease;
  .el-icon {
    font-size: 14px;
  }
}
.sxk-generate__main-segment-title {
  font-size: $font-size-sm;
  font-weight: 600;
  color: $text-primary;
  line-height: 1.2;
  white-space: nowrap;
}
.sxk-generate__main-segment-desc {
  font-size: $font-size-xs;
  color: $text-secondary;
  line-height: 1.2;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
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
  // 自适应列：最小 180px，最大自动填充
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
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

  // 场景图标：与 templates 页面 tplColor 一致
  // 圆形背景 + 主色（CSS 变量由 template 注入）
  .sxk-generate__scene-icon {
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: $radius-round;
    background: var(--scene-bg);        // 智能匹配的浅色背景
    color: var(--scene-color);          // 智能匹配的主色
    transition: all 0.18s ease;
  }

  &:hover {
    border-color: $primary-color-light;
    background: $bg-hover;
    transform: translateY(-1px);
    .sxk-generate__scene-icon {
      transform: scale(1.08);
    }
  }
  &.is-active {
    border-color: $primary-color;
    background: linear-gradient(135deg, $primary-color 0%, $primary-color-hover 100%);
    color: #fff;
    box-shadow: 0 4px 12px rgba(26, 86, 219, 0.3);

    // 选中态：图标背景白色半透，图标主色保持
    .sxk-generate__scene-icon {
      background: rgba(255, 255, 255, 0.2);
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

// ============================================================
// 4 栏紧凑布局：动态参数一屏全显（关键：消除滚动）
// ============================================================

// 提示词卡片（紧凑、内嵌风格）
.sxk-form-card--prompt {
  padding: $spacing-sm $spacing-md;
  margin-bottom: $spacing-sm;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.02), rgba(79, 70, 229, 0.01));
  &:hover {
    border-color: rgba(99, 102, 241, 0.25);
    box-shadow: 0 2px 8px rgba(99, 102, 241, 0.06);
  }
  .el-textarea__inner {
    background: rgba(255, 255, 255, 0.6);
    border: 1px dashed $border-base;
    transition: all 0.2s;
    &:hover, &:focus {
      background: $bg-card;
      border-style: solid;
      border-color: rgba(99, 102, 241, 0.5);
    }
  }
}

// 紧凑卡片（无 hover、padding 缩小）
.sxk-form-card--params-compact {
  padding: $spacing-sm $spacing-md;
  margin-bottom: $spacing-sm;
  &:hover {
    border-color: $border-light;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.02);
  }
}
.sxk-form-card__head--compact {
  margin-bottom: $spacing-xs;
  padding-bottom: $spacing-xs;
  border-bottom: 1px dashed $border-light;
}
.sxk-form-card__body--compact {
  padding-top: $spacing-xs;
}

// 4 栏紧凑网格（关键：4 字段一行，textarea 也强制 1 行）
.sxk-form-compact {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: $spacing-xs $spacing-sm;
  align-items: start;

  // 响应式
  @media (max-width: 1200px) {
    grid-template-columns: repeat(3, 1fr);
  }
  @media (max-width: 992px) {
    grid-template-columns: repeat(2, 1fr);
  }
  @media (max-width: 576px) {
    grid-template-columns: 1fr;
  }
}

// 单个字段（label + 控件 同行）
.sxk-field {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0; // 防止溢出

  // 枚举类 chip 占满 4 栏
  &--enum {
    grid-column: span 4;
    .sxk-field__chips {
      flex-wrap: wrap;
      gap: 4px;
    }
    @media (max-width: 1200px) {
      grid-column: span 3;
    }
    @media (max-width: 992px) {
      grid-column: span 2;
    }
    @media (max-width: 576px) {
      grid-column: 1;
    }
  }

  // textarea 占 2 栏
  &--textarea {
    grid-column: span 2;
    @media (max-width: 992px) {
      grid-column: span 2;
    }
    @media (max-width: 576px) {
      grid-column: 1;
    }
  }

  &__label {
    font-size: 12px;
    color: $text-secondary;
    line-height: 1.3;
    font-weight: 500;
    display: flex;
    align-items: center;
    gap: 2px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  &__required {
    color: #ef4444;
    font-style: normal;
    font-weight: 700;
    font-size: 13px;
  }
  &__chips {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
  }
}

// 紧凑 chip（更小、更紧凑）
.sxk-param-chip--compact {
  padding: 2px 8px;
  font-size: 12px;
  border-radius: 4px;
  &.is-active {
    box-shadow: 0 1px 4px rgba(99, 102, 241, 0.3);
  }
}

// 表单整体（更紧凑、更专业）
// ============================================================
// 表单卡片化（关键：分 4 卡片让表单更专业）
// ============================================================
.sxk-form-card {
  background: $bg-card;
  border: 1px solid $border-light;
  border-radius: $radius-md;
  padding: $spacing-md $spacing-lg;
  margin-bottom: $spacing-md;
  transition: all 0.2s ease;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.02);

  &:hover {
    border-color: rgba(99, 102, 241, 0.25);
    box-shadow: 0 2px 8px rgba(99, 102, 241, 0.06);
  }

  // 卡片头部
  &__head {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: $spacing-md;
    padding-bottom: $spacing-sm;
    border-bottom: 1px dashed $border-light;
  }
  &__bar {
    display: inline-block;
    width: 3px;
    height: 14px;
    background: linear-gradient(180deg, #6366f1, #4f46e5);
    border-radius: 2px;
    flex-shrink: 0;
  }
  &__title {
    font-size: 14px;
    font-weight: 600;
    color: $text-primary;
    flex-shrink: 0;
  }
  &__desc {
    font-size: 12px;
    color: $text-secondary;
    margin-left: auto;
  }

  // 卡片主体
  &__body {
    display: flex;
    flex-direction: column;
    gap: $spacing-sm;
    // 关键：基础配置卡片需要并排（产品 + 模板）
    &:has(> .sxk-form-card__col) {
      flex-direction: row;
      gap: $spacing-md;
    }
  }
  // 卡片内并排列（基础配置：产品 + 模板）
  &__col {
    flex: 1 1 0%;
    min-width: 0;
  }
  // 提交卡片（无 hover，无边框）
  &--submit {
    text-align: center;
    border: none;
    background: transparent;
    box-shadow: none;
    padding: $spacing-sm 0;
    &:hover {
      border: none;
      box-shadow: none;
    }
  }
}

.sxk-generate__form {
  // 表单行（横向布局）
  &-row {
    display: flex;
    gap: $spacing-md;
    margin-bottom: 0;
    // 2 列布局（产品 + 模板）
    &--2col > * {
      flex: 1 1 0%;
      min-width: 0;
    }
  }
  // 全宽控件 class
  &-full {
    width: 100%;
  }
}
// 动态参数 2 列网格
// ============================================================
// 动态参数全新布局：智能分类 + 视觉分组（chip 按钮 + 紧凑输入）
// ============================================================

// 区域标题（如"选项配置"）
.sxk-param-section {
  margin-bottom: $spacing-md;
  &__title {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 13px;
    font-weight: 600;
    color: $text-primary;
    margin-bottom: $spacing-sm;
    padding-left: 2px;
    .el-icon {
      color: $primary-color;
      font-size: 14px;
    }
  }
}

// 枚举项（label + chip 组）
.sxk-param-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: $spacing-sm;
  &__label {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
    color: $text-secondary;
    flex-wrap: wrap;
  }
  &__label-text {
    color: $text-primary;
    font-weight: 500;
  }
  &__label-hint {
    font-size: 12px;
    color: $text-placeholder;
    background: rgba(99, 102, 241, 0.06);
    padding: 1px 6px;
    border-radius: 3px;
  }
  &__chips {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
  }
}

// chip 按钮
.sxk-param-chip {
  display: inline-flex;
  align-items: center;
  padding: 4px 12px;
  font-size: 13px;
  font-family: inherit;
  color: $text-secondary;
  background: $bg-card;
  border: 1px solid $border-base;
  border-radius: $radius-md;
  cursor: pointer;
  transition: all 0.18s ease;
  user-select: none;
  &:hover {
    color: $primary-color;
    border-color: rgba(99, 102, 241, 0.5);
    background: rgba(99, 102, 241, 0.04);
  }
  &.is-active {
    color: #fff;
    background: linear-gradient(135deg, #6366f1, #4f46e5);
    border-color: #4f46e5;
    box-shadow: 0 2px 6px rgba(99, 102, 241, 0.3);
  }
}

// 文本输入区（2 列网格）
.sxk-param-grid-2col {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: $spacing-sm $spacing-md;
  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
}

// 单个输入项
.sxk-param-input {
  &__label {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 13px;
    color: $text-secondary;
    margin-bottom: 4px;
  }
  &__label-text {
    color: $text-primary;
    font-weight: 500;
  }
  &__label-hint {
    font-size: 12px;
    color: $text-placeholder;
    background: rgba(99, 102, 241, 0.06);
    padding: 1px 6px;
    border-radius: 3px;
  }
  &__hint {
    margin-top: 2px;
    font-size: 12px;
    color: $text-placeholder;
    line-height: 1.4;
  }
  &__tip {
    color: $primary-color;
    cursor: help;
  }
  &--full {
    grid-column: 1 / -1;
  }
}

// 必填红星
.sxk-param-required {
  color: #ef4444;
  font-weight: 700;
  font-size: 14px;
}

// 填写完成度提示
.sxk-param-tip {
  margin-top: $spacing-md;
  padding: 10px 12px;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.04), rgba(79, 70, 229, 0.02));
  border: 1px dashed rgba(99, 102, 241, 0.25);
  border-radius: $radius-md;
  font-size: 13px;
  color: $text-secondary;
  display: flex;
  flex-direction: column;
  gap: 6px;
  .el-icon {
    color: $primary-color;
    font-size: 14px;
    display: inline;
    margin-right: 4px;
  }
  b {
    color: $primary-color;
    font-weight: 600;
  }
  &__bar {
    height: 4px;
    background: rgba(99, 102, 241, 0.1);
    border-radius: 2px;
    overflow: hidden;
  }
  &__bar-fill {
    height: 100%;
    background: linear-gradient(90deg, #6366f1, #4f46e5);
    transition: width 0.3s ease;
  }
}

.sxk-generate__params-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0 $spacing-md;
  // 移动端：1 列
  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
}
.sxk-generate__params-item {
  // form-item 内部边距调整
  margin-bottom: $spacing-md;
  :deep(.el-form-item__label) {
    font-weight: 500;
  }
}
// 提交按钮区（居中）
.sxk-generate__submit-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-top: $spacing-lg;
  padding-top: $spacing-md;
  border-top: 1px dashed $border-light;
  .sxk-generate__submit-tip {
    margin-top: $spacing-sm;
    text-align: center;
  }
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
  flex: 1 1 0% !important;
  width: 50% !important;
  min-width: 0;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  align-self: flex-start;
  // 减少 basic-block 内边距
  :deep(.basic-block) {
    padding: $spacing-md $spacing-lg $spacing-sm;
  }
  // basic-block 内部 __body 自然展开
  :deep(.basic-block__body) {
    display: flex;
    flex-direction: column;
    flex: 1;
  }
  :deep(.basic-block__body) > .el-form {
    flex: 1 1 auto;
  }
  :deep(.basic-block__body) > .sxk-generate__guide {
    flex: 1 1 auto;
  }
}

// 引导卡片（替代原空状态）——分步进度 + 智能提示
.sxk-generate__guide {
  display: flex;
  flex-direction: column;
  gap: $spacing-lg;
  padding: $spacing-lg 0;
  // 顶部欢迎区
  &-hero {
    text-align: center;
    padding: $spacing-md 0 $spacing-lg;
    .el-icon {
      background: rgba(26, 86, 219, 0.1);
      padding: 16px;
      border-radius: $radius-round;
      margin-bottom: $spacing-md;
    }
  }
  &-title {
    font-size: 20px;
    font-weight: 600;
    color: $text-primary;
    margin: 0 0 $spacing-xs;
    letter-spacing: 0.5px;
  }
  &-subtitle {
    font-size: $font-size-sm;
    color: $text-secondary;
    margin: 0;
    line-height: 1.6;
  }
  // 分步进度
  &-steps {
    display: flex;
    flex-direction: column;
    gap: $spacing-md;
    padding: 0 $spacing-md;
  }
  &-step {
    display: flex;
    align-items: center;
    gap: $spacing-md;
    padding: $spacing-md;
    border-radius: $radius-md;
    background: $gray-50;
    transition: all 0.18s ease;
    // 连接线（非最后一个）
    &:not(:last-child)::after {
      content: "";
      position: absolute;
      left: 32px;
      top: 100%;
      width: 2px;
      height: $spacing-md;
      background: $border-light;
    }
    position: relative;
    &.is-active {
      background: rgba(26, 86, 219, 0.08);
      box-shadow: 0 0 0 1px rgba(26, 86, 219, 0.2);
      .sxk-generate__guide-step-no {
        background: #1A56DB;
        color: #fff;
        box-shadow: 0 0 0 4px rgba(26, 86, 219, 0.15);
      }
    }
  }
  &-step-no {
    width: 28px;
    height: 28px;
    border-radius: $radius-round;
    background: $gray-200;
    color: $text-secondary;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 13px;
    font-weight: 600;
    flex-shrink: 0;
    transition: all 0.18s ease;
  }
  &-step-body {
    flex: 1;
    min-width: 0;
  }
  &-step-title {
    font-size: 14px;
    font-weight: 600;
    color: $text-primary;
    margin-bottom: 2px;
  }
  &-step-desc {
    font-size: 12px;
    color: $text-secondary;
  }
  // 底部小贴士
  &-tips {
    margin: 0 $spacing-md;
    padding: $spacing-md;
    background: linear-gradient(135deg, rgba(26, 86, 219, 0.04) 0%, rgba(26, 86, 219, 0.08) 100%);
    border-radius: $radius-md;
    border-left: 3px solid #1A56DB;
  }
  &-tip-title {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 13px;
    font-weight: 600;
    color: #1A56DB;
    margin-bottom: $spacing-sm;
    .el-icon {
      font-size: 14px;
    }
  }
  &-tip-list {
    list-style: none;
    padding: 0;
    margin: 0;
    li {
      position: relative;
      padding-left: 16px;
      font-size: 12px;
      color: $text-secondary;
      line-height: 1.8;
      &::before {
        content: "•";
        position: absolute;
        left: 4px;
        color: #1A56DB;
        font-weight: bold;
      }
    }
  }
}

// ---------- 阶段化容器 ----------
.sxk-generate__stage {
  display: flex;
  flex-direction: column;
  flex: 1;
  gap: $spacing-md;
  padding-top: 4px;
}

// 阶段 0/1 行布局：左 Agent 链路（窄/竖向） + 右 初稿对比（主区）
// 两栏卡片内容自然展开，不锁死高度
.sxk-generate__stage0-row,
.sxk-generate__stage1-row {
  align-items: flex-start; // 不拉伸，让内容决定高度
  > [class*='el-col'] {
    .sxk-generate__card {
      min-height: 0;
    }
  }
}

// Agent 链路卡片（左侧窄栏专用）
.sxk-generate__card-trace {
  :deep(.el-card__header) {
    padding: 12px 14px;
  }
  :deep(.el-card__body) {
    padding: 8px 12px 14px;
  }
}
.sxk-generate__stage-hero {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: linear-gradient(135deg, rgba(26, 86, 219, 0.04), rgba(26, 86, 219, 0.01));
  border-left: 3px solid $primary-color;
  border-radius: 0 $radius-md $radius-md 0;
  &-no {
    flex-shrink: 0;
    width: 32px;
    height: 32px;
    border-radius: $radius-round;
    background: $primary-color;
    color: #fff;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
    font-weight: 600;
  }
  &-info {
    flex: 1;
    min-width: 0;
  }
  &-title {
    font-size: 15px;
    font-weight: 600;
    color: $text-primary;
    line-height: 1.4;
  }
  &-desc {
    font-size: $font-size-xs;
    color: $text-secondary;
    line-height: 1.4;
    margin-top: 2px;
  }
  &-actions {
    flex-shrink: 0;
  }
}

.sxk-generate__card {
  border: 1px solid $border-base;
  border-radius: $radius-lg;
  transition: box-shadow 0.2s ease;
  // 关键：保留底部边框线条 + 轻微阴影（让卡片"浮起"）
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  :deep(.el-card__header) {
    padding: 14px $spacing-md;
    border-bottom-color: $border-light;
    background: $bg-hover;
    border-radius: $radius-lg $radius-lg 0 0;
  }
  :deep(.el-card__body) {
    padding: $spacing-md;
  }
  // 卡片内容自然展开（不固定高度，页面整体滚动）
  &.is-scrollable {
    :deep(.el-card__body) {
      display: flex !important;
      flex-direction: column !important;
    }
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
  // 阶段 2 横向布局：卡墙在左 + 文档在右
  &.sxk-generate__card-horizontal {
    :deep(.el-card__body) {
      // 关键：横向 flex + 不换行
      display: flex !important;
      flex-direction: row !important;
      // 关键：内部可滚动
      min-height: 0;
    }
    // 渠道卡墙：左列，固定宽度
    .sxk-generate__channel-wall {
      flex: 0 0 280px;          // 固定 280px
      flex-direction: column;   // 改为纵向（卡墙在左侧一列）
      min-width: 0;
      margin-right: $spacing-md;
      margin-bottom: 0;
      // 关键：加右边界作为分隔线（用户要求分隔左右两边）
      padding-right: $spacing-md;
      border-right: 1px solid $border-base;
      // 内部卡片纵向排
      .sxk-generate__version-card {
        flex: 0 0 auto;         // 纵向时不展开
      }
    }
    // 文档预览/编辑：右列，撑满剩余
    .sxk-generate__version-preview {
      flex: 1 1 0%;
      min-width: 0;
      min-height: 0;
      // 内部还保持 flex column
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
  flex: 0 1 auto; // 允许收缩（让出空间给 stats）
  min-width: 0;
  cursor: pointer;
  user-select: none;
  // 让内部 b 标题不换行
  > b {
    white-space: nowrap;
  }
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

// ============ Phase E: SSE 实时 Agent 状态卡 ============
// ============ Phase E: SSE 动画 ============
// 关键：保留 sse-pulse 和 spin 动画（用于 tl-node.is-running 占位节点的脉动/旋转效果）
// 旧的 __live-status 卡片 UI 已删除（与下方时间线重复），但动画效果迁移到时间线节点

@keyframes sse-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
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
  display: inline-flex;
  align-items: center;
  flex-direction: row;
  flex-wrap: nowrap;
  gap: 6px;
  margin-left: auto; // 推到右侧（与"校验通过/有待完善"对齐）
  white-space: nowrap;
  flex-shrink: 0;
}
.sxk-generate__trace-stat {
  display: inline-flex;
  align-items: center;
  flex-direction: row;
  flex-wrap: nowrap;
  gap: 3px;
  padding: 2px 8px;
  font-size: 11px;
  color: $text-regular;
  background: $gray-100;
  border-radius: 999px;
  font-weight: 500;
  white-space: nowrap;
  flex-shrink: 0;
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
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 11.5px;
  font-weight: 500;
  line-height: 1.5;
  border: 1px solid transparent;
  white-space: nowrap;
  flex-shrink: 0;

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

// ============ Agent 时间线（侧栏竖向布局：阶段 0 左栏用） ============
// 时间线主容器：竖直排列节点
.sxk-generate__timeline {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  padding: 6px 0 4px;
  gap: 0;
  overflow-x: visible;
}
// 每个节点：水平排列（圆点 + 文字）
.sxk-generate__tl-node {
  position: relative;
  flex: 0 0 auto;
  min-width: 0;
  display: flex;
  flex-direction: row;
  align-items: flex-start; // 圆点与文字顶部对齐
  gap: 12px;
  cursor: default;          // Phase E: 节点不可点击（详情已融合到节点内）
  padding: 12px 10px 32px 6px; // 加大底部 32px 给箭头充足空间（防止被下节点 hover 挡住）
  border-radius: $radius-md;
  transition: all 0.2s ease;
  user-select: none;
  // 节点内部层级：让 line/箭头始终在最上层（不被 hover 背景覆盖）
  > .sxk-generate__tl-line {
    z-index: 2;
  }

  &:hover {
    background: $primary-color-light;
    transform: translateX(2px); // 节点 hover 轻微右移（动效）
  }
  &:hover .sxk-generate__tl-dot {
    transform: scale(1.15);
    box-shadow: 0 0 0 2px $primary-color, 0 4px 12px rgba(26, 86, 219, 0.3);
  }
  &:hover .sxk-generate__tl-info {
    color: $text-primary;
  }

  &.is-active {
    background: $primary-color-light;
    &::before {
      content: '';
      position: absolute;
      left: 0;
      top: 12px;
      bottom: 20px;
      width: 3px;
      background: $primary-color;
      border-radius: 0 2px 2px 0;
    }
    .sxk-generate__tl-info {
      .sxk-generate__tl-name {
        color: $primary-color;
        font-weight: 600;
      }
    }
    .sxk-generate__tl-dot {
      box-shadow: 0 0 0 2px $primary-color, 0 0 0 6px rgba(26, 86, 219, 0.15);
    }
  }
}
// 连接线 + 箭头（竖向布局：粗轨道 + 大箭头 + 完成段流动动画）
@keyframes sxk-flow {
  0%, 100% {
    transform: translateX(-50%) scale(1);
    opacity: 1;
    filter: drop-shadow(0 2px 4px rgba(26, 86, 219, 0.6));
  }
  50% {
    transform: translateX(-50%) scale(1.4);
    opacity: 0.85;
    filter: drop-shadow(0 3px 8px rgba(26, 86, 219, 0.8));
  }
}
.sxk-generate__tl-line {
  position: absolute;
  top: 46px; // 圆点底部（12 padding + 40 圆点 = 52，调整到 46 让轨道更紧凑）
  left: 23px; // 圆点 40px center = 20px + padding 6px - 3px(轨道宽 4 半) ≈ 23px
  width: 4px; // 加粗轨道
  height: 16px; // 轨道长度
  z-index: 2; // 提高层级：不被下节点 hover 背景挡住
  pointer-events: none; // 关键：不让箭头拦截鼠标事件，避免被点击/遮挡
  background: $border-base; // 默认灰色
  border-radius: 2px;

  // 三角箭头 ▼（CSS border 技巧）—— 更大更明显
  &::after {
    content: '';
    position: absolute;
    top: 100%; // 紧贴轨道底部
    left: 50%;
    transform: translateX(-50%);
    width: 0;
    height: 0;
    border-left: 9px solid transparent;    // 加大
    border-right: 9px solid transparent;
    border-top: 12px solid $border-base;  // 更高（12px）
    transition: border-top-color 0.2s ease, transform 0.2s ease;
    filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.15));
  }

  // 节点 hover：箭头放大（高亮）
  .sxk-generate__tl-node:hover > & {
    &::after {
      border-left-width: 11px;
      border-right-width: 11px;
      border-top-width: 14px;
    }
  }

  // 成功状态：粗线 + 大箭头 + 流动动画（深蓝加强）
  // 箭头颜色反映"包含它的节点"的状态（节点成功 → 之后箭头蓝色）
  .is-success > &,
  .is-success.is-active > & {
    background: linear-gradient(180deg, #0c3a91 0%, #1a56db 100%); // 深蓝渐变
    box-shadow: 0 0 8px rgba(12, 58, 145, 0.55);
    &::after {
      border-top-color: #0c3a91; // 深蓝
      animation: sxk-flow 1.6s ease-in-out infinite; // 流动呼吸
    }
  }
  // 警告状态
  .is-warning > & {
    background: $warning-color;
    &::after {
      border-top-color: $warning-color;
    }
  }
  // 错误状态
  .is-error > & {
    background: $danger-color;
    &::after {
      border-top-color: $danger-color;
    }
  }
  // 等待/pending 状态：虚线
  .is-wait > &, .is-pending > & {
    background: repeating-linear-gradient(
      180deg,
      $border-base 0,
      $border-base 4px,
      transparent 4px,
      transparent 8px
    );
    &::after {
      border-top-color: $border-base;
    }
  }

  // 竖向布局：最后一个节点后不需要连接线
  .sxk-generate__tl-node:last-child > & {
    display: none;
  }
}
// 节点圆点（带进度环 + 状态外圈）
.sxk-generate__tl-dot {
  position: relative;
  z-index: 1;
  width: 40px;             // 加大
  height: 40px;            // 加大
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
  // 外环：默认 2px 灰色（未到达的步骤感）
  box-shadow: 0 0 0 2px $border-base;
  flex-shrink: 0;
  // 中心环：进度感
  &::before {
    content: '';
    position: absolute;
    inset: 4px;
    border-radius: 50%;
    background: inherit;
    z-index: 0;
  }
  // 内部图标/数字层级
  > * { position: relative; z-index: 1; }

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

// ============ Phase E: SSE 流式中"执行中"占位节点样式 ============
.sxk-generate__tl-node.is-running {
  cursor: default;
  .sxk-generate__tl-dot.is-running-dot {
    background: $primary-color;
    color: white;
    border-color: $primary-color;
    box-shadow: 0 0 0 2px $primary-color, 0 0 12px rgba(59, 130, 246, 0.4);
    animation: sse-pulse 1.4s ease-in-out infinite;
  }
  .sxk-generate__tl-info {
    color: $primary-color;
    .sxk-generate__tl-time {
      color: $primary-color;
      font-weight: 500;
    }
  }
  .sxk-generate__tl-name {
    font-weight: 600;
  }
}
.sxk-generate__trace-stat.is-running {
  color: $primary-color;
  background: rgba(59, 130, 246, 0.08);
  border-color: rgba(59, 130, 246, 0.3);
}
.sxk-generate__trace-stat.is-running .is-spin {
  animation: spin 1s linear infinite;
}

.sxk-generate__tl-info {
  text-align: left;
  transition: color 0.18s ease;
  max-width: 100%;
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
  overflow: hidden;
}
// ============ 节点内详情（替代独立详情卡） ============
.sxk-generate__tl-head {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.sxk-generate__tl-step-idx {
  font-size: 10.5px;
  color: $text-placeholder;
  background: $bg-card;
  border: 1px solid $border-light;
  padding: 1px 6px;
  border-radius: 999px;
  font-weight: 500;
  flex-shrink: 0;
}
.sxk-generate__tl-name {
  font-size: 13px;
  font-weight: 600;
  color: $text-primary;
  line-height: 1.4;
  flex: 1;
  min-width: 0;
}
.sxk-generate__tl-status-tag {
  flex-shrink: 0;
}
.sxk-generate__tl-time {
  font-size: 11px;
  color: $text-placeholder;
  font-variant-numeric: tabular-nums;
  margin-left: auto;
  flex-shrink: 0;
}
.sxk-generate__tl-msg {
  font-size: 12.5px;
  color: $text-regular;
  line-height: 1.65;
  padding: 6px 10px;
  background: $gray-50;
  border-radius: $radius-sm;
  border-left: 3px solid $border-base;
  word-break: break-word;
}
.sxk-generate__tl-msg.is-running-msg {
  background: rgba(59, 130, 246, 0.06);
  border-left-color: $primary-color;
  color: $primary-color;
  font-style: italic;
}
// 警告/错误节点：消息块用对应主题色（与下方 issues 列表呼应）
.sxk-generate__tl-node.is-warning .sxk-generate__tl-msg {
  background: #fffbe6;
  border-left-color: $warning-color;
  color: #ad6800;
}
.sxk-generate__tl-node.is-error .sxk-generate__tl-msg {
  background: #fff2f0;
  border-left-color: $danger-color;
  color: #cf1322;
}

// ============ 警告/错误节点：具体问题列表（嵌入 __tl-msg 内，与消息块合并为一个黄/红块） ============
.sxk-generate__tl-msg-summary {
  font-weight: 500;
  padding-bottom: 6px;
  margin-bottom: 6px;
  border-bottom: 1px dashed currentColor;
  opacity: 0.9;
}
.sxk-generate__tl-issues {
  list-style: none;
  margin: 0;
  padding: 0;
  font-size: 12.5px;
  line-height: 1.7;
}
.sxk-generate__tl-issue {
  display: flex;
  align-items: flex-start;
  gap: 4px;
  color: inherit;          // 继承父节点主题色（黄/红）
  opacity: 0.85;

  & + & {
    margin-top: 3px;
  }
}
.sxk-generate__tl-issue-bullet {
  flex-shrink: 0;
  font-weight: 700;
  margin-right: 2px;
}
.sxk-generate__tl-issue-text {
  flex: 1;
  word-break: break-word;
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
  // 关键：版本卡墙不滚动（始终显示）
  flex-shrink: 0;

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
  flex: 1 1 0%;
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
  // 关键：去除 max-width + 居中 → 撑满整行（不被裁切）
  // 之前：max-width: 780px; margin: 0 auto; → 内容居中显示（用户希望填满整行）
  // 关键：缩小四周缝隙（用户要求"缩小一点"）
  margin: 6px;        // ← 从 10px 缩到 6px
  padding: 24px 36px; // ← 从 32px 48px 缩到 24px 36px
  // 关键：加深边框（用户要求"加上边框"）
  box-shadow: 0 2px 14px rgba(0, 0, 0, 0.08);
  border: 1px solid $border-base;  // ← 从 light 改为 base（更深）
  border-radius: $radius-sm;
  font-family: Georgia, "Times New Roman", "宋体", SimSun, serif;
  color: #1a1a1a;
  line-height: 1.85;
  position: relative;
  // 关键：flex 撑满 + 内部独立滚动
  // flex: 1 1 auto + min-height: 0 让 margin 生效
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
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
  padding: $spacing-sm $spacing-md;
  background: $bg-card; // 不透明背景，避免内容穿透
  border-top: 1px solid $border-light;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: $spacing-sm;
  flex-shrink: 0; // 关键：不被压缩
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
  flex-shrink: 0; // 标题固定不滚
  :deep(.el-input__wrapper) {
    border-radius: $radius-md;
    background: $gray-50;
    transition: all 0.18s ease;
    box-shadow: 0 0 0 1px transparent inset;
    &.is-focus {
      background: $bg-card;
      box-shadow: 0 0 0 2px $primary-color inset !important;
    }
    &.is-hovering:not(.is-focus) {
      box-shadow: 0 0 0 1px rgba(64, 158, 255, 0.4) inset;
    }
  }
  :deep(.el-input-group__prepend) {
    // 蓝色实色 prepend（与"正文"head 标签的蓝色方条风格保持视觉一致）
    background-color: #1A56DB !important;
    color: #fff !important;
    font-weight: 600;
    font-size: 14px; // 与"正文"字号一致
    border-color: #1A56DB !important;
    padding: 0 18px;
    letter-spacing: 1px; // 与"正文"字距一致
    position: relative;
    // 左侧加白色竖条强调（让 prepend 内部也有"方条装饰"）
    box-shadow: inset 3px 0 0 rgba(255, 255, 255, 0.4);
  }
  :deep(.el-input__inner) {
    font-size: 15px;
    font-weight: 500;
  }
}
.sxk-generate__edit-body {
  display: flex;
  flex-direction: column;
  flex: 1 1 0%;
  // textarea 自动撑开高度，完整展示所有内容
  :deep(.el-textarea) {
    flex: 0 1 auto;
    display: flex;
  }
  :deep(.el-textarea__inner) {
    font-size: $font-size-base;
    line-height: 1.9;
    font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", Georgia, "宋体", serif;
    border-radius: $radius-md;
    padding: $spacing-md;
    background: $gray-50;
    transition: all 0.18s ease;
    border-color: transparent;
    color: $text-primary;
    &:hover {
      border-color: rgba(64, 158, 255, 0.4);
    }
    &:focus {
      background: $bg-card;
      box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.15), 0 0 0 1px $primary-color inset;
    }
  }
}

// tags 区与 textarea 间距（避免视觉粘连）
.sxk-generate__edit-tags {
  margin-top: $spacing-lg; // 与 textarea 拉开距离
  padding-top: $spacing-md;
  border-top: 1px solid $border-light;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  flex-shrink: 0;
  // tags 区域加底色，与 textarea 区分
  background: linear-gradient(180deg, transparent 0%, rgba(64, 158, 255, 0.02) 100%);
  border-radius: 0 0 $radius-md $radius-md;
  :deep(.el-tag) {
    border-radius: $radius-sm;
    transition: all 0.18s ease;
    cursor: default;
    &:hover {
      transform: translateY(-1px);
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
    }
  }
}
.sxk-generate__edit-body-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px; // 与"标题"字号一致
  color: $text-regular;
  font-weight: 500;
  margin-bottom: 8px;
  padding-bottom: 8px;
  border-bottom: 1px solid $border-light;
  // 左侧文字前加蓝色竖条（与"标题"prepend 风格保持一致）
  & > span:first-child {
    display: inline-flex;
    align-items: center;
    font-size: 14px;
    font-weight: 600;
    color: $text-primary;
    letter-spacing: 1px; // 与"标题"字距一致
    &::before {
      content: "";
      display: inline-block;
      width: 3px;
      height: 14px;
      // 蓝色实色（与"标题"prepend 保持一致）
      background: #1A56DB;
      border-radius: 2px;
      margin-right: 8px;
    }
  }
}
.sxk-generate__edit-body-cnt {
  color: $text-regular;
  font-size: $font-size-xs;
  padding: 3px 10px;
  background: rgba(64, 158, 255, 0.08);
  color: $primary-color;
  border-radius: 999px;
  font-weight: 500;
  font-variant-numeric: tabular-nums;
}
// ============ 渠道多选（右栏固定高度 + 独立滚动）============
// 发布渠道卡片（高度由 inline style 锁死，与阶段 0 一致）
.sxk-generate__channel-pane {
  // body 区为 flex column：渠道列表固定 + 底部按钮固定
  :deep(.el-card__body) {
    display: flex !important;
    flex-direction: column !important;
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
  // 渠道列表：占满 body 剩余高度 + 独立滚动
  flex: 1 1 0%;
  min-height: 0;
  overflow-y: auto;
  padding: $spacing-md;
  // 滚动条
  &::-webkit-scrollbar { width: 8px; }
  &::-webkit-scrollbar-thumb {
    background: $text-placeholder;
    border-radius: $radius-sm;
  }
  &::-webkit-scrollbar-track { background: rgba(0, 0, 0, 0.04); }
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
  // 关键：固定不滚动（始终可见）
  flex-shrink: 0;
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
  // 关键：flex 让卡片平分整行（无论几个卡片都填满整行）
  display: flex;
  gap: 10px;
  margin-bottom: $spacing-md;
  // 关键：不缩不增
  flex-shrink: 0;
}
.sxk-generate__version-card {
  // 卡片平分整行（默认）
  flex: 1 1 0%;
  min-width: 0;
  max-width: none;
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

  // 阶段 2 横向布局（卡墙在左）时：纵向排列，每张卡撑满
  .sxk-generate__card-horizontal & {
    flex: 0 0 auto;
    width: 100%;
  }

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
  // 关键：去掉 fadeInUp 动画（用户要求点击卡墙时不要加载动画，只让文档内容变化）
  // 之前：animation: fadeInUp 0.25s ease;
  // 关键：内部也是 flex column
  // - 顶部工具栏 (__channel-toolbar) flex-shrink: 0 → 固定
  // - 预览/编辑区 (.sxk-generate__doc-page / .sxk-generate__edit-area) flex: 1 + overflow-y: auto → 滚
  display: flex;
  flex-direction: column;
  // 关键：让子元素可以滚
  min-height: 0;
}

// 工具栏：仅保留"预览/编辑"切换（不滚动，固定）
.sxk-generate__channel-toolbar {
  display: flex;
  // 关键：右对齐（只剩"预览/编辑"切换时让它靠右）
  justify-content: flex-end;
  align-items: center;
  padding: 6px 12px;
  // 关键：去掉灰色背景（用户要求）+ 透明背景
  background: transparent;
  // 关键：去掉圆角（无背景不需要圆角）
  border-radius: 0;
  // 关键：固定不滚动（始终可见）
  flex-shrink: 0;
  position: relative;
  z-index: 1;
  // 关键：去掉边框（无背景 + 无边框更简洁）
  border: none;
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
  flex: 1 1 0%;
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

// 编辑模式相关（已去掉配图参考列表）
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
// 关键：固定高度 + 内容滚动（不撑开弹窗）
:deep(.sxk-generate__done-dialog) {
  border-radius: 12px;
  overflow: hidden;
  // 弹窗主体高度受限
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  margin: 0 auto; // 居中
  .el-dialog__body {
    padding: 0;
    flex: 1;
    overflow-y: auto; // 内容滚动
    min-height: 0;   // flex 子项允许收缩
    -webkit-overflow-scrolling: touch;
  }
  .el-dialog__header {
    display: none;
  }
  .el-dialog__footer {
    padding: 0;
    flex-shrink: 0;
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
// 关键：与系统中其他弹窗保持视觉一致（圆角 12px、阴影、padding、深色遮罩）
// 1) 弹窗遮罩：Element Plus 2.x 用 el-overlay
//    注：element-plus 全局遮罩默认是 rgba(0,0,0,0.5) 已经很深，
//    但在 scoped 样式 + dialog wrapper 影响下可能颜色变浅。这里强制加深并覆盖。
:deep(.el-overlay-dialog) {
  background-color: rgba(0, 0, 0, 0.5) !important;
}
:deep(.sxk-generate__seo-dialog) {
  // ============ 1. 弹窗主体样式 ============
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 12px 48px rgba(0, 0, 0, 0.18);
  // 关键：固定高度 + 内容滚动
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  margin: 0 auto; // 居中
  // ============ 2. 头部 ============
  .el-dialog__header {
    padding: 18px 24px 14px;
    border-bottom: 1px solid $border-light;
    margin-right: 0;
    flex-shrink: 0;
  }
  // ============ 3. 关闭按钮（圆形、悬浮变红）============
  .el-dialog__headerbtn {
    top: 16px;
    right: 16px;
    width: 28px;
    height: 28px;
    border-radius: 50%;
    background: $gray-50;
    transition: all 0.2s ease;

    .el-dialog__close {
      font-size: 16px;
      color: $text-regular;
    }

    &:hover {
      background: $danger-color;
      .el-dialog__close {
        color: white;
      }
    }
  }
  // ============ 4. 主体（去掉默认内边距 + 滚动）============
  .el-dialog__body {
    padding: 16px 24px;
    flex: 1;
    overflow-y: auto;        // 内容超出时滚动
    min-height: 0;           // flex 子项允许收缩
    -webkit-overflow-scrolling: touch;
  }
  .el-dialog__footer {
    padding: 12px 24px 20px;
    flex-shrink: 0;
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

// ========== 生成中 Loading 覆盖层 ==========
.sxk-gen-loading {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 999;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(6px);

  &__card {
    text-align: center;
    padding: 40px 48px;
    max-width: 400px;
  }

  // 动画图标
  &__icon {
    position: relative;
    width: 72px;
    height: 72px;
    margin: 0 auto 20px;
  }
  &__orb {
    position: absolute;
    inset: 12px;
    border-radius: 50%;
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    box-shadow: 0 0 24px rgba(99, 102, 241, 0.4);
    animation: gen-orb-bounce 1.2s ease-in-out infinite;
  }
  &__pulse {
    position: absolute;
    inset: 0;
    border-radius: 50%;
    border: 2px solid rgba(99, 102, 241, 0.3);
    animation: gen-pulse 1.8s ease-out infinite;
  }
  @keyframes gen-orb-bounce {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(0.85); }
  }
  @keyframes gen-pulse {
    0% { transform: scale(0.8); opacity: 1; }
    100% { transform: scale(1.5); opacity: 0; }
  }

  &__title {
    margin: 0 0 6px;
    font-size: 18px;
    font-weight: 700;
    color: $gray-900;
  }
  &__sub {
    margin: 0 0 24px;
    font-size: 13px;
    color: $text-secondary;
    min-height: 20px;
  }

  // 步骤指示
  &__steps {
    display: flex;
    justify-content: center;
    gap: 20px;
    flex-wrap: wrap;
  }
  &__step {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
    color: $text-placeholder;

    &.done {
      color: #16a34a;
      .sxk-gen-loading__step-dot { background: #22c55e; }
    }
    &.running {
      color: #6366f1;
      font-weight: 600;
      .sxk-gen-loading__step-dot {
        background: #6366f1;
        animation: gen-dot-blink 0.8s ease-in-out infinite;
      }
    }
  }
  &__step-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #d1d5db;
    flex-shrink: 0;
  }
  @keyframes gen-dot-blink {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.3; }
  }
  // 实时版本预览（每完成一个版本就显示一个）
  &__versions {
    margin-top: 20px;
    display: flex;
    flex-direction: column;
    gap: 12px;
    max-height: 320px;
    overflow-y: auto;
    text-align: left;
  }
  &__version {
    padding: 12px 14px;
    border-radius: 8px;
    background: rgba(99, 102, 241, 0.06);
    border: 1px solid rgba(99, 102, 241, 0.15);
    animation: gen-version-in 0.3s ease;
  }
  &__version-head {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 6px;
  }
  &__version-no {
    font-size: 12px;
    font-weight: 600;
    color: #6366f1;
    flex-shrink: 0;
  }
  &__version-title {
    font-size: 13px;
    font-weight: 500;
    color: $text-primary;
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  &__version-stat {
    font-size: 11px;
    color: $text-placeholder;
    flex-shrink: 0;
  }
  &__version-body {
    font-size: 12px;
    line-height: 1.6;
    color: $text-regular;
    max-height: 80px;
    overflow-y: auto;
    white-space: pre-wrap;
    word-break: break-word;
  }
  @keyframes gen-version-in {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
  }
}

// 过渡动画
.gen-loading-fade-enter-active,
.gen-loading-fade-leave-active {
  transition: opacity 0.3s ease;
}
.gen-loading-fade-enter-from,
.gen-loading-fade-leave-to {
  opacity: 0;
}
</style>
