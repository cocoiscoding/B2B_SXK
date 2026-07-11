/**
 * 内容生成页 Markdown 渲染工具
 * 对齐后端参考版 B2B-SXK-FastApi/frontend 的简易 Markdown 实现
 *
 * 功能：
 *   - renderMarkdown(md)   简易 Markdown → HTML（标题/粗体/斜体/代码/引用/列表/表格/分隔线）
 *   - renderArticle(body, images, title) 文章式渲染（自动剔除重复首标题 + 配图按小节穿插）
 */

const escapeHtml = (s) =>
  (s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
const escapeAttr = (s) =>
  (s || '').replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;')

/**
 * 简易 Markdown 渲染
 * 支持：# h1 / ## h2 / ### h3 / **bold** / `code` / > quote / --- hr / | table | / - list / 1. list
 */
export function renderMarkdown(md) {
  if (!md) return ''
  let html = escapeHtml(md)
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^# (.+)$/gm, '<h1>$1</h1>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/`(.+?)`/g, '<code>$1</code>')
    .replace(/^> (.+)$/gm, '<blockquote>$1</blockquote>')
    .replace(/^---+$/gm, '<hr/>')

  // 表格解析
  const lines = html.split('\n')
  const result = []
  let inTable = false
  for (const line of lines) {
    if (line.startsWith('|') && line.endsWith('|')) {
      if (!inTable) {
        result.push('<table>')
        inTable = true
      }
      const cells = line
        .slice(1, -1)
        .split('|')
        .map((c) => c.trim())
      // 跳过表格分隔行（如 |---|---|）
      if (cells.every((c) => c.startsWith('---') || c === '')) continue
      // 第一行表头用 th，其余 td
      const isHeader = !result.some((r) => r.includes('<tr'))
      const tag = isHeader ? 'th' : 'td'
      result.push('<tr>' + cells.map((c) => `<${tag}>${c}</${tag}>`).join('') + '</tr>')
    } else {
      if (inTable) {
        result.push('</table>')
        inTable = false
      }
      if (line.startsWith('- ')) {
        result.push('<li>' + line.slice(2) + '</li>')
      } else if (/^\d+\.\s/.test(line)) {
        result.push('<li>' + line.replace(/^\d+\.\s/, '') + '</li>')
      } else {
        result.push(line)
      }
    }
  }
  if (inTable) result.push('</table>')
  html = result.join('\n')

  // 合并相邻 li 为 ul
  html = html.replace(/(<li>.*?<\/li>\n?)+/g, (m) => '<ul>' + m + '</ul>')
  return html
}

/**
 * 单图 HTML 片段
 */
function figureHtml(img) {
  const cap = (img && (img.caption || img.theme)) || '配图'
  const url = (img && img.url) || ''
  if (!url) return ''
  return `<figure class="article-fig"><img src="${escapeAttr(url)}" alt="${escapeAttr(cap)}"/><figcaption>${escapeHtml(cap)}</figcaption></figure>`
}

/**
 * 文章式渲染：先把 Markdown 转 HTML，
 * 再去掉与文章标题重复的正文首标题，
 * 最后在文章小节边界（首块 / 标题块 / 末块）穿插配图。
 * 无配图则纯正文。
 */
export function renderArticle(body, images, title) {
  if (!body) return ''
  const imgs = Array.isArray(images) ? images.filter((i) => i && i.url) : []
  let html = renderMarkdown(body)

  // 去掉与文章标题重复的正文首标题
  if (title) {
    const m = html.match(/^\s*<h[12]>([^<]*)<\/h[12]>\s*/)
    if (m) {
      const h = m[1].trim()
      if (h && (title.includes(h) || h.includes(title))) {
        html = html.slice(m[0].length)
      }
    }
  }

  if (!imgs.length) return html

  // 按空行切块
  const blocks = html.split(/\n{2,}/).map((s) => s.trim()).filter(Boolean)
  if (blocks.length <= 1) {
    return html + '\n\n' + imgs.map(figureHtml).join('\n\n')
  }

  // 候选插入点（块索引，在其后插入配图）
  const points = []
  const push = (i) => {
    if (i >= 0 && i < blocks.length && !points.includes(i)) points.push(i)
  }
  push(0)
  blocks.forEach((b, i) => {
    if (/^<h[1-6]>/.test(b)) push(i)
  })
  push(blocks.length - 1)

  // 每张图分配一个插入点（不足则循环复用同一位置）
  const after = {}
  imgs.forEach((img, k) => {
    const p = points[k % points.length]
    ;(after[p] = after[p] || []).push(img)
  })

  const out = []
  blocks.forEach((blk, i) => {
    out.push(blk)
    ;(after[i] || []).forEach((img) => out.push(figureHtml(img)))
  })
  return out.join('\n\n')
}
