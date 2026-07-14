/**
 * 神行库（SXK）全局配置
 *
 * 说明：神行库独立部署，clientId / token key 使用 sxk-* 前缀，与其他同源业务系统隔离。
 * 占位的 clientSecret 仅用于本地 /dev 阶段；生产环境应由部署/CI 注入或交由网关鉴权。
 */
export default {
  title: 'sxk',
  logo: 'S',
  key: 'sxk', // 配置主键，目前用于本地存储 key
  indexTitle: '神行库 · 营销 AI',
  clientId: 'sxk', // 客户端id
  clientSecret: 'sxk_secret', // 客户端密钥（仅本地占位；生产请由部署/CI 注入或移至网关鉴权）
  tenantMode: false, // 是否开启租户模式
  tenantId: '000000', // 管理组租户编号
  captchaMode: true, // 是否开启验证码模式
  switchMode: false, // 是否开启部门切换模式
  lockPage: '/lock',
  tokenTime: 3000,
  tokenHeader: 'Blade-Auth',
  // http的status默认放行列表
  statusWhiteList: [],
  // 配置首页不可关闭
  isFirstPage: true,
  fistPage: {
    label: '首页',
    value: '/dashboard',
    params: {},
    query: {},
    meta: {
      i18n: 'dashboard'
    },
    group: [],
    close: false
  },
  // 配置菜单的属性
  menu: {
    iconDefault: 'iconfont icon-caidan',
    props: {
      label: 'name',
      path: 'path',
      icon: 'source',
      children: 'children'
    }
  },
  // 第三方系统授权地址（SXK 独立 OAuth2 服务，由后端 BladeX 提供；占位本地域名）
  authUrl: 'http://localhost:8080/blade-auth/oauth/render',
  // 报表设计器地址（占位；后续接入报表系统时再补）
  reportUrl: '',
  // 单点登录系统认证（占位；SXK 项目暂未启用 SSO）
  ssoUrl: '',
  // 单点登录回调地址
  redirectUri: 'http://localhost:52400',
  // saml 登出地址（占位）
  samlLogoutUrl: ''
}
