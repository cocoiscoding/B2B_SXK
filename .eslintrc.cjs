/* 神行库 ESLint 配置（Vue 3 + Vite + Element Plus）
 * 最小规则集：eslint:recommended + plugin:vue/vue3-recommended
 * 关闭多词组件名限制：sxk 模块下存在单字 / 双字业务组件（如 basic-block）
 */
module.exports = {
  root: true,
  env: {
    browser: true,
    node: true,
    es2022: true
  },
  extends: [
    'eslint:recommended',
    'plugin:vue/vue3-recommended'
  ],
  parserOptions: {
    ecmaVersion: 2022,
    sourceType: 'module'
  },
  rules: {
    'no-console': process.env.NODE_ENV === 'production' ? 'error' : 'off',
    'no-debugger': process.env.NODE_ENV === 'production' ? 'error' : 'off',
    // 下划线前缀的参数/变量视为有意保留（签名兼容等）
    'no-unused-vars': ['error', { argsIgnorePattern: '^_', varsIgnorePattern: '^_' }],
    'vue/multi-word-component-names': 'off'
  }
}