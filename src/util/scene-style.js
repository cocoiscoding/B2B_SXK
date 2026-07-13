/**
 * 场景图标 / 配色 智能匹配（共享给 dashboard 和 templates 页面）
 * 关键：与 templates/index.vue 的 tplColor 完全一致，避免两个页面展示同一场景时图标/颜色不同
 *
 * 优先级：
 *   1) 按 sceneCode 精确匹配 ICON_MAP（兼容旧版 mock code）
 *   2) 按场景名称关键词匹配 SCENE_STYLE_RULES（覆盖后端真实场景）
 *   3) 兜底 FALLBACK_STYLE
 */

import {
  Document, PieChart, Share, Message, Promotion, Monitor, Histogram,
  TrendCharts, Medal, Film, ChatDotRound, DataAnalysis, Money, Calendar, Files
} from '@element-plus/icons-vue'

// 旧版 code → 图标映射
export const SCENE_ICON_MAP = {
  product_intro: Document,
  product_introduction: Histogram,
  competitor: PieChart,
  competitor_analysis: TrendCharts,
  channel_adapt: Share,
  multi_channel: Share,
  email: Message,
  email_marketing: Message,
  event: Promotion,
  event_promotion: Promotion,
  social: ChatDotRound,
  speech: Film,
  other: Document,
  // 后端 S001-S006（对应 B2B-SXK-FastApi 种子场景）
  S001: Monitor,        // 线下展会物料 → Monitor (banner/官网/首页类)
  S002: Histogram,      // 产品介绍文案
  S003: TrendCharts,    // 竞品对比分析报告
  S004: Medal,          // 客户案例包装
  S005: Film,           // 演讲 PPT 大纲
  S006: ChatDotRound    // 社交媒体帖子
}

// 按场景名称关键词匹配图标+配色（顺序优先）
export const SCENE_STYLE_RULES = [
  { keywords: ['banner', '官网', '首页', '展会'], icon: Monitor,      bg: '#eff6ff', color: '#2563eb' },  // 蓝
  { keywords: ['产品介绍', '产品功能', '白皮书'], icon: Histogram,    bg: '#f0fdf4', color: '#16a34a' },  // 绿
  { keywords: ['竞品', '对比', '竞争'], icon: TrendCharts,           bg: '#fff7ed', color: '#ea580c' },  // 橙
  { keywords: ['案例', '客户', '成功'], icon: Medal,                 bg: '#faf5ff', color: '#9333ea' },  // 紫
  { keywords: ['ppt', '演示', '大纲', '路演', '演讲'], icon: Film,     bg: '#fee2e2', color: '#dc2626' },  // 红
  { keywords: ['社交', '媒体', '帖子', '传播'], icon: ChatDotRound,  bg: '#ecfdf5', color: '#059669' },  // 翠绿
  { keywords: ['邮件', 'email', 'edm'], icon: Message,               bg: '#fffbeb', color: '#d97706' },  // 琥珀
  { keywords: ['活动', 'event', '推广'], icon: Promotion,            bg: '#fef2f2', color: '#e11d48' }   // 玫红
]

export const SCENE_FALLBACK_STYLE = { icon: Document, bg: '#f1f5f9', color: '#475569' }  // slate

/**
 * 获取场景的图标 + 配色
 * @param {string} sceneCode 场景 code
 * @param {string} sceneName 场景名称（用于关键词匹配）
 * @returns {{ icon: Component, bg: string, color: string }}
 */
export function getSceneStyle(sceneCode, sceneName = '') {
  // 1) 按 code 精确匹配
  if (SCENE_ICON_MAP[sceneCode]) {
    // 颜色优先用名称关键词匹配
    const byName = matchByName(sceneName)
    if (byName) {
      return { icon: SCENE_ICON_MAP[sceneCode], bg: byName.bg, color: byName.color }
    }
    return { icon: SCENE_ICON_MAP[sceneCode], bg: SCENE_FALLBACK_STYLE.bg, color: SCENE_FALLBACK_STYLE.color }
  }
  // 2) 按名称关键词匹配
  const byName = matchByName(sceneName)
  if (byName) {
    return byName
  }
  // 3) 兜底
  return { ...SCENE_FALLBACK_STYLE }
}

function matchByName(sceneName) {
  const name = (sceneName || '').toLowerCase()
  if (!name) return null
  for (const rule of SCENE_STYLE_RULES) {
    if (rule.keywords.some((kw) => name.includes(kw.toLowerCase()))) {
      return { icon: rule.icon, bg: rule.bg, color: rule.color }
    }
  }
  return null
}
