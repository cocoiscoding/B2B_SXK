/**
 * 纯前端 SVG 验证码生成器
 *
 * 用途：Phase 4 后端未启期间，替代 /api/blade-auth/oauth/captcha 接口。
 * 后端 BladeX 就绪后可改回真实接口，本工具整体删除即可。
 *
 * 输出：{ key: string, svg: string }
 *   - key：会话级标识，写入 cookie/localStorage，用于登录时回传校验
 *   - svg：可直接 <img src="data:image/svg+xml,..."> 或 v-html 渲染
 *
 * 设计原则：
 *   - 字符集去除易混淆的 0/O/1/l/I
 *   - 噪点用半透明圆点 + 干扰线，避免依赖 Canvas
 *   - 颜色取自 Element Plus 中性灰，避免过亮/过暗
 */

// 字符集（去 0/O/1/l/I）
const CHARSET = 'ABCDEFGHJKMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789'

/**
 * 生成随机整数 [min, max]
 */
function randInt(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min
}

/**
 * 生成指定长度随机字符串
 */
function randomText(len = 4) {
  let out = ''
  for (let i = 0; i < len; i++) {
    out += CHARSET[randInt(0, CHARSET.length - 1)]
  }
  return out
}

/**
 * 简单 hash → 32 位 hex，用作 key
 */
function quickHash(input) {
  let h = 5381
  for (let i = 0; i < input.length; i++) {
    h = (h * 33) ^ input.charCodeAt(i)
  }
  return (h >>> 0).toString(16).padStart(8, '0')
}

/**
 * 构造 SVG 字符串
 * @param {string} text 验证码字符
 * @param {number} width
 * @param {number} height
 */
function buildSvg(text, width = 110, height = 38) {
  // 干扰线
  const lines = []
  for (let i = 0; i < 4; i++) {
    const x1 = randInt(0, width)
    const y1 = randInt(0, height)
    const x2 = randInt(0, width)
    const y2 = randInt(0, height)
    lines.push(
      `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="#cbd5e1" stroke-width="1" opacity="0.6"/>`
    )
  }
  // 噪点
  const dots = []
  for (let i = 0; i < 30; i++) {
    const cx = randInt(2, width - 2)
    const cy = randInt(2, height - 2)
    const r = randInt(1, 2)
    dots.push(`<circle cx="${cx}" cy="${cy}" r="${r}" fill="#94a3b8" opacity="0.5"/>`)
  }
  // 字符（每个字符随机旋转 / 颜色 / y 偏移）
  const chars = text.split('').map((ch, i) => {
    const x = 14 + i * 22
    const y = randInt(22, 28)
    const rotate = randInt(-25, 25)
    const colors = ['#1f2937', '#1A56DB', '#0f766e', '#9333ea', '#dc2626']
    const fill = colors[randInt(0, colors.length - 1)]
    return `<text x="${x}" y="${y}" font-family="-apple-system, Segoe UI, sans-serif" font-size="20" font-weight="700" fill="${fill}" transform="rotate(${rotate} ${x} ${y})">${ch}</text>`
  })

  return `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">
    <rect width="100%" height="100%" fill="#f8fafc"/>
    ${lines.join('')}
    ${dots.join('')}
    ${chars.join('')}
  </svg>`
}

/**
 * 生成一个验证码
 * @returns {{ key: string, svg: string, text: string }}
 *   - text：原始字符（仅 dev 调试用；生产环境切勿暴露给前端比较逻辑，否则失去意义）
 */
export function createSvgCaptcha() {
  const text = randomText(4)
  const key = quickHash(text + Date.now())
  const svg = buildSvg(text)
  return { key, svg, text }
}

/**
 * 校验前端输入是否匹配
 * （仅 Phase 4 Mock 用 —— 真实后端应在服务端校验，避免前端绕过）
 */
export function checkCaptcha(input, expected) {
  if (!input || !expected) return false
  return String(input).trim().toLowerCase() === String(expected).trim().toLowerCase()
}