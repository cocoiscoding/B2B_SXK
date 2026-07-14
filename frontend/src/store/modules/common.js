import { defineStore } from 'pinia'
import { setStore, getStore, removeStore } from '@/util/store'
import website from '@/config/website'

export const useCommonStore = defineStore('common', {
  state: () => ({
    language: getStore({ name: 'language' }) || 'zh',
    isCollapse: false,
    isFullScren: false,
    isMenu: true,
    isShade: false,
    screen: -1,
    isLock: getStore({ name: 'isLock' }) || false,
    showTag: true,
    showCollapse: true,
    showSearch: true,
    showLock: true,
    showFullScren: true,
    showTheme: true,
    showMenu: true,
    showColor: true,
    colorName: getStore({ name: 'colorName' }) || '#409EFF',
    themeName: getStore({ name: 'themeName' }) || 'theme-default',
    lockPasswd: getStore({ name: 'lockPasswd' }) || '',
    website: website
  }),
  actions: {
    setLanguage(language) {
      this.language = language
      setStore({ name: 'language', content: this.language })
    },
    setShade(active) {
      this.isShade = active
    },
    setCollapse() {
      this.isCollapse = !this.isCollapse
    },
    setFullScren() {
      this.isFullScren = !this.isFullScren
    },
    setIsMenu(menu) {
      this.isMenu = menu
    },
    setLock() {
      this.isLock = true
      setStore({ name: 'isLock', content: this.isLock, type: 'session' })
    },
    setScreen(screen) {
      this.screen = screen
    },
    setColorName(colorName) {
      this.colorName = colorName
      setStore({ name: 'colorName', content: this.colorName })
    },
    setThemeName(themeName) {
      this.themeName = themeName
      setStore({ name: 'themeName', content: this.themeName })
    },
    setLockPasswd(lockPasswd) {
      this.lockPasswd = lockPasswd
      setStore({ name: 'lockPasswd', content: this.lockPasswd, type: 'session' })
    },
    clearLock() {
      this.isLock = false
      this.lockPasswd = ''
      removeStore({ name: 'lockPasswd', type: 'session' })
      removeStore({ name: 'isLock', type: 'session' })
    }
  }
})
