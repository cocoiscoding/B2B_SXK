import { defineStore } from 'pinia'
import { setStore, getStore } from '@/util/store'
import website from '@/config/website'
import { validatenull } from '@/util/validate'

export const useTagsStore = defineStore('tags', {
  state: () => ({
    tag: getStore({ name: 'tag' }) || deepClone(website.fistPage),
    tagList: getStore({ name: 'tagList' }) || [deepClone(website.fistPage)],
    tagWel: deepClone(website.fistPage)
  }),
  actions: {
    addTag(tag) {
      this.tag = tag
      setStore({ name: 'tag', content: this.tag })
      if (this.tagList.some((ele) => ele.value === tag.value)) return
      this.tagList.push(tag)
      setStore({ name: 'tagList', content: this.tagList })
    },
    delTag(tag) {
      let index = this.tagList.findIndex((item) => item.value === tag.value)
      if (index !== -1) {
        this.tagList.splice(index, 1)
        setStore({ name: 'tagList', content: this.tagList })
      }
      // 如果关闭的是当前标签，跳转到上一个
      if (tag.value === this.tag.value) {
        let nowTag = this.tagList[index] || this.tagList[index - 1] || this.tagWel
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
    closeTag(tag) {
      return this.delTag(tag)
    }
  }
})

function deepClone(obj) {
  if (obj === null || typeof obj !== 'object') return obj
  return JSON.parse(JSON.stringify(obj))
}
