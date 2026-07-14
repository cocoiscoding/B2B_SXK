import { defineStore } from 'pinia'
import { setStore, getStore } from '@/util/store'
import website from '@/config/website'
import { validatenull } from '@/util/validate'

// 首页固定 tabId（不可关闭、单实例）
const WELCOME_TAB_ID = 'tab_welcome'

function deepClone(obj) {
  if (obj === null || typeof obj !== 'object') return obj
  return JSON.parse(JSON.stringify(obj))
}

// 生成唯一 tabId
export function generateTabId() {
  return `tab_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
}

// 构建首页 tag（带固定 tabId）
function buildWelcomeTag() {
  const tag = deepClone(website.fistPage)
  tag.tabId = WELCOME_TAB_ID
  tag.value = '/dashboard'
  tag.close = false
  return tag
}

export const useTagsStore = defineStore('tags', {
  state: () => {
    const welcome = buildWelcomeTag()
    const storedList = getStore({ name: 'tagList' })
    const storedTag = getStore({ name: 'tag' })
    // 迁移：旧 tagList 中的 tag 没有 tabId 字段，直接重置
    const tagList = storedList && storedList.length && storedList.every((t) => t.tabId)
      ? storedList
      : [welcome]
    const tag = storedTag && storedTag.tabId ? storedTag : welcome
    return { tag, tagList, tagWel: welcome }
  },
  actions: {
    addTag(tag) {
      this.tag = tag
      setStore({ name: 'tag', content: this.tag })
      // 按 tabId 去重（首页 tabId 固定，其他页面每次导航生成新 tabId）
      if (tag.tabId) {
        const index = this.tagList.findIndex((ele) => ele.tabId === tag.tabId)
        if (index !== -1) {
          // 标签已存在：更新 value（query 可能已变化，如清除 openDetail），
          // 确保 tags.vue 中 goTag(tag) 跳转到最新 URL
          this.tagList[index] = tag
          setStore({ name: 'tagList', content: this.tagList })
          return
        }
      } else {
        // 兜底：无 tabId 时按 value 去重
        if (this.tagList.some((ele) => ele.value === tag.value)) return
      }
      this.tagList.push(tag)
      setStore({ name: 'tagList', content: this.tagList })
    },
    delTag(tag) {
      const index = this.tagList.findIndex((item) =>
        tag.tabId ? item.tabId === tag.tabId : item.value === tag.value
      )
      if (index !== -1) {
        this.tagList.splice(index, 1)
        setStore({ name: 'tagList', content: this.tagList })
      }
      // 如果关闭的是当前标签，跳转到相邻标签
      const isCurrent = tag.tabId
        ? this.tag.tabId === tag.tabId
        : this.tag.value === tag.value
      if (isCurrent) {
        const nowTag = this.tagList[index] || this.tagList[index - 1] || this.tagWel
        this.tag = nowTag
        setStore({ name: 'tag', content: this.tag })
        return nowTag
      }
    },
    delAllTag() {
      this.tagList = [this.tagWel]
      this.tag = this.tagWel
      setStore({ name: 'tagList', content: this.tagList })
      setStore({ name: 'tag', content: this.tag })
    },
    // 关闭其他：仅保留首页和当前 tag
    delOtherTag(tag) {
      this.tagList = this.tagList.filter(
        (item) => item.tabId === WELCOME_TAB_ID || item.tabId === tag.tabId
      )
      this.tag = tag
      setStore({ name: 'tagList', content: this.tagList })
      setStore({ name: 'tag', content: this.tag })
    },
    closeTag(tag) {
      return this.delTag(tag)
    },
    // 通过 tabId 设置当前激活 tag
    setActiveByTabId(tabId) {
      const found = this.tagList.find((t) => t.tabId === tabId)
      if (found) {
        this.tag = found
        setStore({ name: 'tag', content: this.tag })
      }
    },
    // 通过 tabId 更新副标题（业务上下文摘要，如"产品名 · 场景名"）
    setTabSublabel(tabId, sublabel) {
      const index = this.tagList.findIndex((t) => t.tabId === tabId)
      if (index !== -1) {
        this.tagList[index].sublabel = sublabel || ''
        setStore({ name: 'tagList', content: this.tagList })
      }
    }
  }
})
