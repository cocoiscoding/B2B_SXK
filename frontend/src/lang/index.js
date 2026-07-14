import { createI18n } from 'vue-i18n'
import enLocale from './en'
import zhLocale from './zh'
import { getStore } from '@/util/store'

const messages = {
  en: {
    ...enLocale
  },
  zh: {
    ...zhLocale
  }
}

const i18n = createI18n({
  legacy: false,
  locale: getStore({ name: 'language' }) || 'zh',
  fallbackLocale: 'zh',
  messages
})

export default i18n
