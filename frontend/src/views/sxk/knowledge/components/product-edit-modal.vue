<!--
  产品添加/编辑/查看弹窗（查看与编辑合二为一）
  - 对应需求文档 5.2.3 / 4.3.3 / 4.3.4
  - 字段规则（BR-K-03/04）：
      * 产品名称、分类必填
      * 功能列表 ≥ 1
      * 标签（target_customers / competitors / selling_points）支持回车添加
  - 通过 v-model 控制显示，:product-id 区分新增/编辑
  - readonly=true 时以只读模式打开（查看），底部"编辑"按钮可切换到可编辑
-->
<template>
  <el-dialog
    :model-value="modelValue"
    width="640px"
    align-center
    :modal-append-to-body="true"
    :append-to-body="true"
    :lock-scroll="true"
    :show-close="false"
    :close-on-click-modal="false"
    :close-on-press-escape="true"
    class="product-edit-dialog"
    @update:model-value="(v) => $emit('update:modelValue', v)"
    @open="initForm"
  >
    <!-- 头部 -->
    <div class="pe-head">
      <div class="pe-head__left">
        <h3 class="pe-head__title">
          <el-icon class="pe-head__icon">
            <component :is="dialogIcon" />
          </el-icon>
          {{ dialogTitle }}
        </h3>
        <p class="pe-head__sub">
          {{ dialogSubTitle }}
        </p>
      </div>
      <button
        class="pe-head__close"
        @click="$emit('update:modelValue', false)"
      >
        <el-icon :size="20">
          <Close />
        </el-icon>
      </button>
    </div>

    <!-- 可滚动内容区 -->
    <div class="pe-body">
      <el-form
        ref="formRef"
        v-loading="loading"
        :model="form"
        :rules="rules"
        label-width="100px"
        :class="{ 'form-readonly': !editing }"
      >
        <el-form-item
          label="产品名称"
          prop="name"
        >
          <el-input
            v-if="editing"
            v-model="form.name"
            placeholder="如：智能数据平台 X"
            maxlength="64"
            show-word-limit
          />
          <div
            v-else
            class="pe-readonly-text"
          >
            {{ form.name || '无' }}
          </div>
        </el-form-item>

        <el-form-item
          label="产品分类"
          prop="category"
        >
          <el-select
            v-if="editing"
            v-model="form.category"
            multiple
            collapse-tags
            collapse-tags-tooltip
            clearable
            placeholder="可多选"
            style="width: 100%"
          >
            <el-option
              label="数据分析"
              value="数据分析"
            />
            <el-option
              label="CRM"
              value="CRM"
            />
            <el-option
              label="营销自动化"
              value="营销自动化"
            />
            <el-option
              label="企业版"
              value="企业版"
            />
            <el-option
              label="其他"
              value="其他"
            />
          </el-select>
          <div
            v-else
            class="pe-readonly-text"
          >
            {{ (form.category && form.category.length) ? form.category.join('、') : '无' }}
          </div>
        </el-form-item>

        <el-form-item
          label="产品描述"
          prop="description"
        >
          <el-input
            v-if="editing"
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="建议至少 10 字符，简明描述产品定位"
            maxlength="500"
            show-word-limit
          />
          <div
            v-else
            class="pe-readonly-text pe-readonly-text--pre"
          >
            {{ form.description || '无' }}
          </div>
        </el-form-item>

        <!-- 功能特性：动态列表 -->
        <el-form-item
          label="功能特性"
          prop="features"
          required
        >
          <div
            v-if="editing"
            class="dynamic-list"
          >
            <div
              v-for="(f, idx) in form.features"
              :key="idx"
              class="dynamic-list__row"
            >
              <el-input
                v-model="f.name"
                placeholder="功能名称"
                style="width: 160px"
              />
              <el-input
                v-model="f.description"
                placeholder="功能描述（可选）"
                style="flex: 1"
              />
              <el-button
                :disabled="form.features.length <= 1"
                link
                type="danger"
                @click="removeFeature(idx)"
              >
                删除
              </el-button>
            </div>
            <el-button
              link
              type="primary"
              @click="addFeature"
            >
              + 添加功能
            </el-button>
          </div>
          <ul
            v-else
            class="pe-readonly-list"
          >
            <li
              v-for="(f, idx) in form.features.filter((x) => x.name)"
              :key="idx"
            >
              <span class="pe-readonly-list__name">{{ f.name }}</span>
              <span
                v-if="f.description"
                class="pe-readonly-list__desc"
              >{{ f.description }}</span>
            </li>
            <li
              v-if="!form.features.some((x) => x.name)"
              class="pe-readonly-text"
            >
              无
            </li>
          </ul>
        </el-form-item>

        <el-form-item label="目标客户">
          <tag-input
            v-if="editing"
            ref="tagInputTarget"
            v-model="form.target_customers"
            placeholder="回车添加（如：制造业）"
          />
          <div
            v-else
            class="pe-readonly-tags"
          >
            <el-tag
              v-for="t in form.target_customers"
              :key="t"
              type="info"
              effect="plain"
              class="pe-readonly-tag"
            >
              {{ t }}
            </el-tag>
            <span
              v-if="!form.target_customers.length"
              class="pe-readonly-text"
            >无</span>
          </div>
        </el-form-item>

        <el-form-item label="价格信息">
          <el-input
            v-if="editing"
            v-model="form.pricing"
            placeholder="如：基础版 ¥50,000/年"
            maxlength="255"
          />
          <div
            v-else
            class="pe-readonly-text"
          >
            {{ form.pricing || '无' }}
          </div>
        </el-form-item>

        <el-form-item label="竞品名称">
          <tag-input
            v-if="editing"
            ref="tagInputCompetitors"
            v-model="form.competitors"
            placeholder="回车添加（如：产品 Y）"
          />
          <div
            v-else
            class="pe-readonly-tags"
          >
            <el-tag
              v-for="t in form.competitors"
              :key="t"
              type="info"
              effect="plain"
              class="pe-readonly-tag"
            >
              {{ t }}
            </el-tag>
            <span
              v-if="!form.competitors.length"
              class="pe-readonly-text"
            >无</span>
          </div>
        </el-form-item>

        <el-form-item label="产品卖点">
          <tag-input
            v-if="editing"
            ref="tagInputSelling"
            v-model="form.selling_points"
            placeholder="回车添加（如：部署快）"
          />
          <div
            v-else
            class="pe-readonly-tags"
          >
            <el-tag
              v-for="t in form.selling_points"
              :key="t"
              type="info"
              effect="plain"
              class="pe-readonly-tag"
            >
              {{ t }}
            </el-tag>
            <span
              v-if="!form.selling_points.length"
              class="pe-readonly-text"
            >无</span>
          </div>
        </el-form-item>

        <!-- 产品图片（封面/截图等） -->
        <el-form-item label="产品图片">
          <div class="uploader-block">
            <div class="uploader-block__head">
              <span class="uploader-block__hint">支持 PNG / JPG / WebP / GIF，单张 ≤ 5MB，最多 8 张</span>
              <span class="uploader-block__count">{{ imageBuffer.length }}/{{ IMG_MAX }} 张</span>
            </div>
            <div
              v-if="imageBuffer.length"
              class="image-grid"
            >
              <div
                v-for="img in imageBuffer"
                :key="img.id"
                class="image-card"
              >
                <img
                  :src="img.dataUrl || img.url"
                  :alt="img.name"
                >
                <div
                  v-if="editing"
                  class="image-card__mask"
                >
                  <button
                    type="button"
                    class="image-card__del"
                    title="删除"
                    @click="removeImage(img.id)"
                  >
                    <el-icon><Close /></el-icon>
                  </button>
                </div>
                <div
                  class="image-card__name"
                  :title="img.name"
                >
                  {{ img.name }}
                </div>
              </div>
            </div>
            <div
              v-if="editing"
              class="dropzone"
              :class="{ 'dropzone--drag': imageDragOver }"
              @click="$refs.imageInput.click()"
              @dragenter.prevent="imageDragOver = true"
              @dragover.prevent="imageDragOver = true"
              @dragleave.prevent="imageDragOver = false"
              @drop.prevent="onImageDrop"
            >
              <input
                ref="imageInput"
                type="file"
                accept="image/*"
                multiple
                hidden
                @change="onImagePick"
              >
              <el-icon class="dropzone__icon">
                <PictureFilled />
              </el-icon>
              <div class="dropzone__text">
                点击或拖拽上传图片
              </div>
            </div>
            <div
              v-if="!editing && !imageBuffer.length"
              class="empty-text"
            >
              暂无图片
            </div>
          </div>
        </el-form-item>

        <!-- 文档附件（产品手册、竞品资料、报价单等） -->
        <el-form-item label="文档附件">
          <div class="uploader-block">
            <div class="uploader-block__head">
              <span class="uploader-block__hint">支持 PDF / Word / Excel / PPT / TXT / ZIP，单个 ≤ 20MB，最多 10 个</span>
              <span class="uploader-block__count">{{ docBuffer.length }}/{{ DOC_MAX }} 个</span>
            </div>
            <div
              v-if="docBuffer.length"
              class="doc-list"
            >
              <div
                v-for="d in docBuffer"
                :key="d.id"
                class="doc-item"
              >
                <span
                  class="doc-item__ext"
                  :class="extColorClass(d.ext)"
                >{{ d.ext || 'file' }}</span>
                <div class="doc-item__info">
                  <div
                    class="doc-item__name"
                    :title="d.name"
                  >
                    {{ d.name }}
                  </div>
                  <div class="doc-item__meta">
                    {{ formatSize(d.size) }}{{ d.ext ? ' · .' + d.ext : '' }}
                  </div>
                </div>
                <button
                  v-if="editing"
                  type="button"
                  class="doc-item__del"
                  title="删除"
                  @click="removeDoc(d.id)"
                >
                  <el-icon><Delete /></el-icon>
                </button>
              </div>
            </div>
            <div
              v-if="editing"
              class="dropzone"
              :class="{ 'dropzone--drag': docDragOver }"
              @click="$refs.docInput.click()"
              @dragenter.prevent="docDragOver = true"
              @dragover.prevent="docDragOver = true"
              @dragleave.prevent="docDragOver = false"
              @drop.prevent="onDocDrop"
            >
              <input
                ref="docInput"
                type="file"
                multiple
                hidden
                @change="onDocPick"
              >
              <el-icon class="dropzone__icon">
                <UploadFilled />
              </el-icon>
              <div class="dropzone__text">
                点击或拖拽上传文档
              </div>
            </div>
            <div
              v-if="!editing && !docBuffer.length"
              class="empty-text"
            >
              暂无文档
            </div>
          </div>
        </el-form-item>
      </el-form>
    </div>

    <!-- 底部 -->
    <template #footer>
      <div class="pe-foot">
        <!-- 只读查看态：editing=false -->
        <template v-if="!editing">
          <el-button @click="cancel">
            关闭
          </el-button>
          <!-- 关键：canEdit=false（不是创建者）→ 不显示"编辑"按钮 -->
          <el-button
            v-if="canEdit"
            type="primary"
            @click="startEdit"
          >
            编辑
          </el-button>
        </template>
        <!-- 编辑态：editing=true -->
        <template v-else>
          <el-button @click="cancel">
            取消
          </el-button>
          <el-button
            type="primary"
            :loading="saving"
            @click="submit"
          >
            {{ isEdit ? '保存修改' : '创建产品' }}
          </el-button>
        </template>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed, nextTick, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Close, Delete, PictureFilled, UploadFilled, View, EditPen, Plus } from '@element-plus/icons-vue'
import sxkApi from '@/mock/sxkApi'
import TagInput from '@/components/tag-input/index.vue'

// ========== 上传配置（对齐原型 SXK_v3.html） ==========
const IMG_MAX = 8
const IMG_MAX_SIZE = 5 * 1024 * 1024 // 5MB
const DOC_MAX = 10
const DOC_MAX_SIZE = 20 * 1024 * 1024 // 20MB
const DOC_ALLOWED_EXTS = ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'md', 'zip', 'rar']

// 图片 / 文档缓冲区（与原型 productUploadBuffer 一致，客户端暂存）
const imageBuffer = ref([])
const docBuffer = ref([])
const imageDragOver = ref(false)
const docDragOver = ref(false)
let uploadNextId = 1

const formatSize = (bytes) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
}
const getFileExt = (name) => {
  const dot = name.lastIndexOf('.')
  return dot < 0 ? '' : name.substring(dot + 1).toLowerCase()
}
// 文档扩展名对应的徽章颜色
const extColorClass = (ext) => {
  if (['pdf'].includes(ext)) return 'ext--red'
  if (['doc', 'docx'].includes(ext)) return 'ext--blue'
  if (['xls', 'xlsx'].includes(ext)) return 'ext--green'
  if (['ppt', 'pptx'].includes(ext)) return 'ext--orange'
  if (['zip', 'rar'].includes(ext)) return 'ext--amber'
  return 'ext--gray'
}

// 图片上传：校验 + 入缓冲区
const handleImageFiles = (fileList) => {
  const files = Array.from(fileList || [])
  if (files.length === 0) return
  const remain = IMG_MAX - imageBuffer.value.length
  if (remain <= 0) {
    ElMessage.warning(`最多上传 ${IMG_MAX} 张图片`)
    return
  }
  let accepted = 0
  let rejected = 0
  files.slice(0, remain).forEach((file) => {
    if (!file.type.startsWith('image/')) {
      rejected++
      return
    }
    if (file.size > IMG_MAX_SIZE) {
      ElMessage.warning(`「${file.name}」超过 5MB，已跳过`)
      rejected++
      return
    }
    const reader = new FileReader()
    reader.onload = (e) => {
      imageBuffer.value.push({
        id: uploadNextId++,
        name: file.name,
        size: file.size,
        type: file.type,
        dataUrl: e.target.result,
        // 真实后端链路需要原始 File 对象做 multipart 上传（仅内存中，不入 mock）
        file: file
      })
    }
    reader.readAsDataURL(file)
    accepted++
  })
  if (accepted === 0 && rejected > 0) ElMessage.warning('所有文件均未通过校验')
  else if (rejected > 0) ElMessage.info(`已跳过 ${rejected} 个不合格文件`)
}
const onImagePick = (e) => {
  handleImageFiles(e.target.files)
  e.target.value = ''
}
const onImageDrop = (e) => {
  imageDragOver.value = false
  handleImageFiles(e.dataTransfer?.files)
}
const removeImage = (id) => {
  imageBuffer.value = imageBuffer.value.filter((x) => x.id !== id)
}

// 文档上传：校验 + 入缓冲区
const handleDocFiles = (fileList) => {
  const files = Array.from(fileList || [])
  if (files.length === 0) return
  const remain = DOC_MAX - docBuffer.value.length
  if (remain <= 0) {
    ElMessage.warning(`最多上传 ${DOC_MAX} 个文档`)
    return
  }
  let accepted = 0
  let rejected = 0
  files.slice(0, remain).forEach((file) => {
    const ext = getFileExt(file.name)
    if (!DOC_ALLOWED_EXTS.includes(ext)) {
      ElMessage.warning(`「${file.name}」类型不支持，已跳过`)
      rejected++
      return
    }
    if (file.size > DOC_MAX_SIZE) {
      ElMessage.warning(`「${file.name}」超过 20MB，已跳过`)
      rejected++
      return
    }
    docBuffer.value.push({
      id: uploadNextId++,
      name: file.name,
      size: file.size,
      type: file.type || '',
      ext
    })
    accepted++
  })
  if (accepted === 0 && rejected > 0) ElMessage.warning('所有文件均未通过校验')
  else if (rejected > 0) ElMessage.info(`已跳过 ${rejected} 个不合格文件`)
}
const onDocPick = (e) => {
  handleDocFiles(e.target.files)
  e.target.value = ''
}
const onDocDrop = (e) => {
  docDragOver.value = false
  handleDocFiles(e.dataTransfer?.files)
}
const removeDoc = (id) => {
  docBuffer.value = docBuffer.value.filter((x) => x.id !== id)
}
const resetUploadBuffer = () => {
  imageBuffer.value = []
  docBuffer.value = []
}

// ========== v-model ==========
const props = defineProps({
  modelValue: { type: Boolean, default: false },
  productId: { type: String, default: null },
  readonly: { type: Boolean, default: false },
  // 关键：当前用户是否有编辑权限（产品创建者或管理员）
  // false → 即使是查看模式也只读，底部不显示"编辑"按钮
  canEdit: { type: Boolean, default: true },
  // Word/PDF 建库预填数据（真实后端 import-docx 返回的 product 草稿）
  prefillData: { type: Object, default: null }
})
const emit = defineEmits(['update:modelValue', 'saved'])

// ========== 表单状态 ==========
const formRef = ref(null)
const tagInputTarget = ref(null)
const tagInputCompetitors = ref(null)
const tagInputSelling = ref(null)
const loading = ref(false)
const saving = ref(false)
// 是否处于编辑态：readonly 模式下初始为 false，点击"编辑"后切换为 true
const editing = ref(true)

/**
 * 归一化 category 为字符串数组：后端契约 {category: string[]}
 * 兼容：null / undefined / 字符串 / 数组 / 拼接字符串 "a, b"
 */
const normalizeCategory = (v) => {
  if (Array.isArray(v)) return v.map((x) => String(x).trim()).filter(Boolean)
  if (v == null) return []
  const s = String(v).trim()
  if (!s) return []
  return s.split(/[,，、;;\n]/).map((x) => x.trim()).filter(Boolean)
}

const blankForm = () => ({
  name: '',
  category: [],
  description: '',
  pricing: '',
  features: [{ name: '', description: '' }],
  target_customers: [],
  competitors: [],
  selling_points: []
})
const form = reactive(blankForm())

const isEdit = computed(() => !!props.productId)

// 弹窗标题：只读查看 → "产品详情"，编辑已有 → "编辑产品"，新增 → "添加产品"
const dialogTitle = computed(() => {
  if (!editing.value && isEdit.value) return '产品详情'
  return isEdit.value ? '编辑产品' : '添加产品'
})

// 点击底部"编辑"按钮，从只读切换到可编辑
const startEdit = () => {
  editing.value = true
}

const rules = {
  name: [{ required: true, message: '请输入产品名称', trigger: 'blur' }],
  // category 改为自定义校验：避免空数组 [] 触发静默 required 失败
  category: [
    {
      validator: (rule, value, cb) => {
        if (Array.isArray(value) && value.length > 0) cb()
        else cb(new Error('请至少选择一个产品分类'))
      },
      trigger: 'change'
    }
  ]
}

// ========== 动态功能列表 ==========
const addFeature = () =>
  form.features.push({ name: '', description: '' })

const removeFeature = (idx) => {
  if (form.features.length <= 1) return
  form.features.splice(idx, 1)
}

// ========== 数据加载：编辑时回填 ==========
const initForm = async () => {
  // 每次打开都先重置
  Object.assign(form, blankForm())
  resetUploadBuffer()
  // readonly 模式 → 初始不可编辑；否则 → 可编辑
  editing.value = !props.readonly
  // Word/PDF 建库预填：真实后端 import-docx 返回 product 草稿，直接预填
  if (props.prefillData) {
    Object.assign(form, {
      ...props.prefillData,
      category: normalizeCategory(props.prefillData.category),
      features: props.prefillData.features?.length
        ? props.prefillData.features
        : [{ name: '', description: '' }]
    })
    return
  }
  if (!props.productId) return
  loading.value = true
  const res = await sxkApi.getProduct(props.productId)
  loading.value = false
  if (res.data) {
    Object.assign(form, {
      ...res.data,
      category: normalizeCategory(res.data.category),
      features: res.data.features?.length
        ? res.data.features
        : [{ name: '', description: '' }]
    })
    // 回填附件（对齐原型 editProduct 的 attachments 预填逻辑）
    const att = res.data.attachments
    if (att) {
      if (Array.isArray(att.images)) {
        imageBuffer.value = att.images.map((im) => ({
          id: uploadNextId++,
          name: im.name,
          size: im.size || 0,
          type: im.type || 'image/png',
          dataUrl: im.dataUrl || '',
          url: im.url || ''  // 真实后端返回的 URL（无 dataUrl）
        }))
      }
      if (Array.isArray(att.docs)) {
        docBuffer.value = att.docs.map((d) => ({
          id: uploadNextId++,
          name: d.name,
          size: d.size || 0,
          type: d.type || '',
          ext: d.ext || getFileExt(d.name)
        }))
      }
    }
  } else {
    ElMessage.error(res.msg || '加载产品失败')
  }
}

// ========== 提交 ==========
const cancel = () => emit('update:modelValue', false)

const submit = async () => {
  // 关键：保存前主动触发所有 tag-input 的 commit() 收集未回车的输入
  tagInputTarget.value?.commit?.()
  tagInputCompetitors.value?.commit?.()
  tagInputSelling.value?.commit?.()
  // 暴力兜底：直接读取所有 tag-input 内部 input 的 value，强制同步到 form
  // 适用场景：tag-input 内部 ref 或 v-model 出问题时的最终保底
  const tagInputs = document.querySelectorAll('.tag-input__native')
  const tagForms = [form.target_customers, form.competitors, form.selling_points]
  let i = 0
  for (const inp of tagInputs) {
    const v = String(inp.value || '').trim()
    if (v && tagForms[i] && !tagForms[i].includes(v)) {
      tagForms[i].push(v)
    }
    if (tagForms[i]) {
      // 统一清理：去掉空字符串和非字符串
      tagForms[i] = tagForms[i].filter((x) => typeof x === 'string' && x.trim())
    }
    i++
  }
  // 等待 Vue 完成 v-model reactive 更新
  await nextTick()
  try {
    console.log('[product-edit-modal] submit start', { category: form.category, name: form.name, competitors: form.competitors })
    await formRef.value?.validate()
  } catch (err) {
    // 关键：不再静默 return，提示用户校验失败的具体字段
    console.warn('[product-edit-modal] form validate failed', err)
    ElMessage.error('请检查表单填写是否完整')
    return
  }
  // BR-K-03 自定义校验：功能列表至少 1 项且 name 非空
  const validFeatures = form.features.filter((f) => f.name.trim())
  if (validFeatures.length === 0) {
    ElMessage.error('请至少添加一个功能特性')
    return
  }
  const payload = {
    ...form,
    features: validFeatures.map((f, i) => ({
      name: f.name.trim(),
      description: f.description?.trim() || '',
      sort_order: i + 1
    })),
    target_customers: form.target_customers.filter((s) => s.trim()),
    competitors: form.competitors.filter((s) => s.trim()),
    selling_points: form.selling_points.filter((s) => s.trim()),
    // 附件随产品一起保存（与原型 saveProduct 行为一致）
    attachments: {
      images: imageBuffer.value.map((im) => ({
        name: im.name,
        size: im.size,
        type: im.type,
        dataUrl: im.dataUrl
      })),
      docs: docBuffer.value.map((d) => ({
        name: d.name,
        size: d.size,
        type: d.type,
        ext: d.ext
      }))
    }
  }
  saving.value = true
  // 真实后端链路需要 File 对象做 multipart 上传；mock 链路不需要（dataUrl 已存 buffer）
  const withFiles = {
    images: imageBuffer.value,
    docs: docBuffer.value
  }
  let res
  if (isEdit.value) {
    res = await sxkApi.updateProduct(props.productId, payload, withFiles)
  } else {
    res = await sxkApi.createProduct(payload, withFiles)
  }
  saving.value = false
  if (res.code === 0) {
    ElMessage.success(isEdit.value ? '已保存' : '已创建')
    emit('saved')
    emit('update:modelValue', false)
  } else {
    // 透传业务错误码对应提示（mock 阶段与接口文档一致）
    ElMessage.error(res.msg || '保存失败')
  }
}
</script>

<style lang="scss">
// 全局样式：覆盖 el-dialog 默认 padding（弹窗 teleport 到 body，scoped 无法穿透）
// 关键：与系统中其他弹窗保持视觉一致（圆角 12px、阴影、深色遮罩、滚动）
.product-edit-dialog {
  // 弹窗总高上限 80vh（依赖全局 .el-dialog 的 max-height + flex 列布局）
  max-height: 80vh !important;
  display: flex;
  flex-direction: column;
  .el-dialog__header {
    display: none;
  }
  .el-dialog__body {
    // 关键：body 不滚动，body 内的 .pe-body 自己滚动
    padding: 0;
    flex: 1;
    min-height: 0;
    display: flex;
    flex-direction: column;
    overflow: hidden; // 防止 body 自身出现滚动条
  }
  .el-dialog__footer {
    // 恢复 padding，让按钮距弹窗底 16px
    padding: 12px 24px 16px;
    border-top: 1px solid $border-light;
    flex-shrink: 0;
  }
}
</style>

<style lang="scss" scoped>
// ========== 头部（关键：固定不动，不随 body 滚动） ==========
.pe-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: $spacing-lg $spacing-lg $spacing-md;
  border-bottom: 1px solid $border-light;
  flex-shrink: 0;  // 关键：不收缩，固定在顶部

  &__title {
    display: flex;
    align-items: center;
    gap: $spacing-sm;
    font-size: 16px;
    font-weight: 600;
    color: $text-primary;
    margin: 0;
  }

  &__icon {
    color: $primary-color;
    font-size: 20px;
  }

  &__sub {
    font-size: 12px;
    color: $text-placeholder;
    margin: $spacing-xs 0 0;
  }

  &__close {
    flex-shrink: 0;
    background: none;
    border: none;
    cursor: pointer;
    color: $text-placeholder;
    padding: 4px;
    border-radius: $radius-sm;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    justify-content: center;

    &:hover {
      color: $text-primary;
      background: $gray-100;
    }
  }
}

// ========== 可滚动内容区（关键：自身滚动，标题和底部固定） ==========
// 关键：标题 .pe-head 在外层不滚动，.pe-body 自身滚动
.pe-body {
  flex: 1;
  min-height: 0;          // 关键：允许 flex 子项收缩
  overflow-y: auto;       // 关键：内容超出时滚动
  -webkit-overflow-scrolling: touch;
  padding: $spacing-lg;

  // 自定义滚动条样式（与其他弹窗一致）
  &::-webkit-scrollbar {
    width: 6px;
  }
  &::-webkit-scrollbar-thumb {
    background: $border-base;
    border-radius: 3px;
  }
  &::-webkit-scrollbar-track {
    background: transparent;
  }
}

// ========== 底部 ==========
.pe-foot {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: $spacing-sm;
  // 关键：padding 由 .el-dialog__footer 提供（12px 24px 16px），此处不重复
  // border-top 也由 footer 提供
  padding: 0;
  border: none;
}

.dynamic-list {
  display: flex;
  flex-direction: column;
  gap: $spacing-sm;
  width: 100%;

  &__row {
    display: flex;
    align-items: center;
    gap: $spacing-sm;
  }
}

/* ===== 上传区块容器 ===== */
.uploader-block {
  width: 100%;

  &__head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 8px;
  }

  &__hint {
    font-size: 12px;
    color: $text-secondary;
  }

  &__count {
    font-size: 12px;
    color: $text-placeholder;
    flex-shrink: 0;
  }
}

/* ===== 图片预览网格（4 列） ===== */
.image-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  margin-bottom: 8px;
}

.image-card {
  position: relative;
  aspect-ratio: 1 / 1;
  border: 1px solid $border-light;
  border-radius: $radius-sm;
  overflow: hidden;
  background: $gray-100;

  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
  }

  &__mask {
    position: absolute;
    inset: 0;
    background: rgba(0, 0, 0, 0);
    display: flex;
    align-items: center;
    justify-content: center;
    opacity: 0;
    transition: all 0.2s ease;
  }

  &:hover &__mask {
    background: rgba(0, 0, 0, 0.4);
    opacity: 1;
  }

  &__del {
    width: 28px;
    height: 28px;
    border: none;
    border-radius: 50%;
    background: $danger-color;
    color: #fff;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
    transition: background 0.2s ease;

    &:hover {
      background: #dc2626;
    }
  }

  &__name {
    position: absolute;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    color: #fff;
    font-size: 11px;
    padding: 2px 6px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}

/* ===== 文档列表 ===== */
.doc-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 8px;
}

.doc-item {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #fff;
  border: 1px solid $border-light;
  border-radius: $radius-sm;
  padding: 8px 12px;

  &__ext {
    flex-shrink: 0;
    min-width: 38px;
    height: 24px;
    padding: 0 6px;
    border-radius: $radius-sm;
    color: #fff;
    font-size: 11px;
    font-weight: 600;
    line-height: 24px;
    text-align: center;
    text-transform: uppercase;
    letter-spacing: 0.3px;
  }

  &__info {
    flex: 1;
    min-width: 0;
  }

  &__name {
    font-size: 13px;
    color: $text-primary;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  &__meta {
    font-size: 12px;
    color: $text-placeholder;
    margin-top: 2px;
  }

  &__del {
    flex-shrink: 0;
    border: none;
    background: transparent;
    color: $danger-color;
    cursor: pointer;
    padding: 4px 6px;
    border-radius: $radius-sm;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
    transition: background 0.2s ease;

    &:hover {
      background: #fef2f2;
    }
  }
}

/* 扩展名徽章配色 */
.ext--red { background: #e53935; }
.ext--blue { background: #1e88e5; }
.ext--green { background: #43a047; }
.ext--orange { background: #fb8c00; }
.ext--amber { background: #f0ad4e; }
.ext--gray { background: #909399; }

/* ===== 拖拽上传区 ===== */
.dropzone {
  border: 2px dashed $border-base;
  border-radius: $radius-md;
  padding: 16px;
  text-align: center;
  cursor: pointer;
  transition: border-color 0.2s ease, background 0.2s ease;

  &__icon {
    font-size: 24px;
    color: $text-placeholder;
  }

  &__text {
    font-size: 12px;
    color: $text-secondary;
    margin-top: 4px;
  }

  &:hover,
  &--drag {
    border-color: $primary-color;
    background: $primary-color-light;
  }

  &--drag &__icon,
  &:hover &__icon {
    color: $primary-color;
  }
}

/* ===== 只读模式：表单整体弱化 ===== */
.form-readonly {
  :deep(.el-input.is-disabled .el-input__inner),
  :deep(.el-input.is-disabled .el-input__textarea),
  :deep(.el-textarea.is-disabled .el-textarea__inner) {
    color: $text-primary;
    background: $gray-50;
    cursor: default;
    -webkit-text-fill-color: $text-primary;
  }
  :deep(.el-select.is-disabled .el-input__inner) {
    color: $text-primary;
    background: $gray-50;
    cursor: default;
    -webkit-text-fill-color: $text-primary;
  }
}

/* ===== 只读模式：纯文本展示（关键：无文本框，仅文字）===== */
.pe-readonly-text {
  font-size: 14px;
  line-height: 1.6;
  color: $text-primary;
  padding: 4px 0;
  word-break: break-word;
  min-height: 32px;
  display: flex;
  align-items: center;
  // 当显示"无"占位时使用浅灰
  &:empty::before {
    content: '无';
    color: $text-placeholder;
  }
}
.pe-readonly-text--pre {
  white-space: pre-wrap;
  display: block;
}

.pe-readonly-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: $spacing-sm;
  width: 100%;

  li {
    display: flex;
    align-items: baseline;
    gap: $spacing-sm;
    font-size: 14px;
    line-height: 1.6;
    color: $text-primary;
    padding: 6px 10px;
    background: $gray-50;
    border-radius: $radius-sm;
  }
  .pe-readonly-list__name {
    font-weight: 600;
    color: $text-primary;
    flex-shrink: 0;
  }
  .pe-readonly-list__desc {
    color: $text-secondary;
    font-size: 13px;
  }
}

.pe-readonly-tags {
  display: flex;
  flex-wrap: wrap;
  gap: $spacing-xs;
  align-items: center;
  min-height: 32px;
  padding: 4px 0;
}
.pe-readonly-tag {
  font-size: 12px;
}

.empty-text {
  font-size: 13px;
  color: $text-placeholder;
  padding: 12px 0;
}
</style>
