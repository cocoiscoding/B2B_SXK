/**
 * SSE（Server-Sent Events）客户端工具
 *
 * 为什么不用 axios：
 *   - axios 接收 text/event-stream 后会一次性等流结束才返回
 *   - axios 无法边读边处理
 *   - 必须用原生 fetch + ReadableStream 逐行解析
 *
 * 后端 SSE 协议（来自 B2B-SXK-FastApi/app/routers/drafts.py）：
 *   - 端点：POST /api/drafts/stream、POST /api/drafts/{id}/regenerate/stream
 *   - Content-Type: text/event-stream
 *   - 事件格式：
 *       event: step  data: {agent, status, message?, duration_ms?, output?}
 *       event: done  data: {完整 Draft}
 *       event: error data: {message}
 *
 * 用法：
 *   const sse = new SSEClient({
 *     url: '/api/drafts/stream',
 *     method: 'POST',
 *     data: {...},
 *     onStep: (step) => { ... },     // 每个 Agent 步骤（running + 完整）
 *     onDone: (draft) => { ... },     // 完整草稿
 *     onError: (msg) => { ... }
 *   })
 *   sse.start()
 *   // ...
 *   sse.abort()                       // 主动中断
 */
export class SSEClient {
  /**
   * @param {Object} opts
   * @param {string} opts.url
   * @param {string} [opts.method='POST']
   * @param {Object} [opts.data]
   * @param {Object} [opts.headers]
   * @param {Function} [opts.onStep]    接收 {agent, status, message?, duration_ms?, output?}
   * @param {Function} [opts.onDone]    接收完整 Draft
   * @param {Function} [opts.onError]   接收 {message}
   * @param {Function} [opts.onOpen]    连接建立
   */
  constructor(opts) {
    this.opts = opts
    this.controller = null
    this._aborted = false
  }

  /**
   * 启动 SSE 连接
   * @returns {Promise<void>} resolve 于连接建立（不等 done）
   */
  async start() {
    if (this._aborted) return
    this.controller = new AbortController()

    try {
      // 拼接 baseURL：与 axios.js 一致
      const baseURL = (import.meta.env.VITE_APP_BASE_API || '').replace(/\/$/, '')
      const fullUrl = baseURL + this.opts.url

      const res = await fetch(fullUrl, {
        method: this.opts.method || 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
          // bearer token：与 axios.js 一致
          ...this._authHeader(),
          ...(this.opts.headers || {})
        },
        body: this.opts.data ? JSON.stringify(this.opts.data) : undefined,
        signal: this.controller.signal
      })

      if (!res.ok) {
        // 401/403/500 → 抛错让上层降级到非 SSE 接口
        throw new Error(`SSE 连接失败: HTTP ${res.status}`)
      }

      if (!res.body) {
        throw new Error('SSE 响应没有 body')
      }

      this.opts.onOpen && this.opts.onOpen()
      await this._consumeStream(res.body)
    } catch (e) {
      if (this._aborted) return
      this.opts.onError && this.opts.onError({ message: e.message || String(e) })
      throw e
    }
  }

  /**
   * 主动中断连接
   */
  abort() {
    this._aborted = true
    if (this.controller) {
      try {
        this.controller.abort()
      } catch (e) {
        // 静默
      }
    }
  }

  // ========== 私有方法 ==========

  _authHeader() {
    // 与 axios.js 一致：从 localStorage 读 sx-access-token
    try {
      const token = localStorage.getItem('sx-access-token')
      return token ? { Authorization: `Bearer ${token}` } : {}
    } catch {
      return {}
    }
  }

  /**
   * 逐行消费流式响应，解析 SSE 协议
   */
  async _consumeStream(body) {
    const reader = body.getReader()
    const decoder = new TextDecoder('utf-8')
    let buffer = ''

    // SSE 一条事件 = event: xxx \n data: yyy \n\n
    // 我们用 \n\n 分隔事件，buffer 中积累未完整的部分
    const eventDelimiter = '\n\n'

    try {
      while (!this._aborted) {
        const { value, done } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })

        // 处理完整的事件
        let idx
        while ((idx = buffer.indexOf(eventDelimiter)) >= 0) {
          const raw = buffer.slice(0, idx)
          buffer = buffer.slice(idx + eventDelimiter.length)
          this._parseEvent(raw)
        }
      }

      // 流结束时如果 buffer 仍有内容（最后一条事件没有空行结尾），尝试解析
      if (buffer.trim() && !this._aborted) {
        this._parseEvent(buffer)
      }
    } catch (e) {
      if (this._aborted) return
      throw e
    } finally {
      try { reader.releaseLock() } catch (e) { /* 静默 */ }
    }
  }

  /**
   * 解析单条 SSE 事件
   * 格式：
   *   event: step
   *   data: {...}
   */
  _parseEvent(raw) {
    if (!raw.trim()) return

    let eventName = ''
    let dataStr = ''

    // 按 \n 拆行
    const lines = raw.split(/\r?\n/)
    for (const line of lines) {
      if (line.startsWith('event:')) {
        eventName = line.slice(6).trim()
      } else if (line.startsWith('data:')) {
        // data: 后可能有前导空格，按 SSE 规范应保留一个空格
        dataStr += line.slice(5).trimStart()
      } else if (line.startsWith(':')) {
        // SSE 注释行（心跳），忽略
        continue
      }
    }

    if (!eventName) return  // 没有 event 字段，忽略

    let payload
    try {
      payload = dataStr ? JSON.parse(dataStr) : {}
    } catch (e) {
      console.warn('[SSE] JSON 解析失败:', dataStr)
      return
    }

    switch (eventName) {
      case 'step':
        this.opts.onStep && this.opts.onStep(payload)
        break
      case 'done':
        this.opts.onDone && this.opts.onDone(payload)
        break
      case 'error':
        this.opts.onError && this.opts.onError(payload)
        break
      default:
        console.warn('[SSE] 未知事件:', eventName, payload)
    }
  }
}

export default SSEClient
