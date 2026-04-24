/**
 * 代理请求完成通知客户端 (WebSocket)
 */
const NOTIFY_INTERVAL = 60000  // 通知保留窗口 (1分钟)
const RECONNECT_DELAY_MIN = 2000
const RECONNECT_DELAY_MAX = 15000

let _ws = null
let _reconnectTimer = null
let _reconnectDelay = RECONNECT_DELAY_MIN
let _heartTimer = null
let _onMessage = null
let _recentEvents = []
let _isConnected = false

export const NOTIFY_TYPES = {
    QA_STARTED: 'qa_started',
    QA_COMPLETED: 'qa_completed',
}

/**
 * 生成唯一事件 ID
 */
function genEventId() {
    return 'js_' + Date.now().toString(36) + Math.random().toString(36).slice(2, 8)
}

/**
 * 建立通知连接
 */
export function connectNotify(onMessageCB) {
    if (_onMessage) disconnectNotify()
    _onMessage = onMessageCB
    _reconnectDelay = RECONNECT_DELAY_MIN
    _connect()
}

function _connect() {
    if (_isConnected) return
    _isConnected = true
    const baseUrl = uni.getStorageSync('luckapi_baseUrl') || 'http://10.222.9.24:8000/admin/api'
    const token = uni.getStorageSync('luckapi_token')
    const serverUrl = baseUrl
        .replace('http://', 'ws://')
        .replace('https://', 'wss://')
        .replace('/admin/api', '') + '/v1/events?token=' + token

    _ws = uni.connectSocket({
        url: serverUrl,
        header: { 'Authorization': 'Bearer ' + token },
    })

    function onMsgHandler(res) {
        const msg = res.data || ''
        if (msg === 'heartbeat' || msg === 'pong') return

        try {
            const evt = JSON.parse(msg)
            if (evt.event && evt.event !== 'qa_started' && evt.event !== 'qa_completed') return
            _addRecentEvent(evt)
            if (_onMessage) {
                _onMessage(evt.event, evt)
            }
        } catch {
            // 静默忽略非 JSON 数据
        }
    }

    if (typeof _ws.onMessage === 'function') {
        _ws.onMessage = onMsgHandler
    } else if (typeof _ws.on === 'function') {
        _ws.on('message', onMsgHandler)
    }

    if (typeof _ws.onOpen === 'function') {
        _ws.onOpen(() => {
            console.log('[Notify] WebSocket connected')
            _reconnectDelay = RECONNECT_DELAY_MIN
            _fetchMissedEvents()
        })
    } else if (typeof _ws.on === 'function') {
        _ws.on('open', () => {
            console.log('[Notify] WebSocket connected')
            _reconnectDelay = RECONNECT_DELAY_MIN
            _fetchMissedEvents()
        })
    }

    if (typeof _ws.onClose === 'function') {
        _ws.onClose(() => {
            console.log('[Notify] WebSocket closed')
            _isConnected = false
            _scheduleReconnect()
        })
    } else if (typeof _ws.on === 'function') {
        _ws.on('close', () => {
            console.log('[Notify] WebSocket closed')
            _isConnected = false
            _scheduleReconnect()
        })
    }

    if (typeof _ws.onError === 'function') {
        _ws.onError(() => {
            _isConnected = false
        })
    } else if (typeof _ws.on === 'function') {
        _ws.on('error', () => {
            _isConnected = false
        })
    }
}

function _scheduleReconnect() {
    clearTimeout(_reconnectTimer)
    _reconnectTimer = setTimeout(() => {
        _reconnectDelay = Math.min(_reconnectDelay * 2, RECONNECT_DELAY_MAX)
        console.log('[Notify] Reconnecting in', _reconnectDelay / 1000, 's')
        _connect()
    }, _reconnectDelay)
}

/**
 * 查询离线期间遗漏的事件
 */
function _fetchMissedEvents() {
    const baseUrl = uni.getStorageSync('luckapi_baseUrl') || 'http://10.222.9.24:8000/admin/api'
    const token = uni.getStorageSync('luckapi_token')
    const now = Date.now()
    const since = now - NOTIFY_INTERVAL

    uni.request({
        url: baseUrl + '/v1/events/recent?since=' + since + '&token=' + token,
        method: 'GET',
        success: (res) => {
            if (res.data && Array.isArray(res.data)) {
                for (const evt of res.data) {
                    const eventType = evt.event || evt._event
                    if (eventType === 'qa_started' || eventType === 'qa_completed') {
                        _addRecentEvent(evt)
                        if (_onMessage) {
                            _onMessage(eventType, evt)
                        }
                    }
                }
            }
        },
        fail: () => {},
    })
}

/**
 * 添加事件到最近列表（去重）
 */
function _addRecentEvent(payload) {
    // Generate event_id for dedup if not present (real-time events)
    if (!payload.event_id) {
        payload.event_id = genEventId()
    }

    // Also use record_id for dedup if available (from REST API)
    const key = payload.event_id || ''

    const dup = _recentEvents.find(e => e.event_id === key || e.record_id === payload.record_id)
    if (!dup) {
        _recentEvents.push({ ...payload, event_id: payload.event_id })
        if (_recentEvents.length > 50) _recentEvents.shift()
    }
}

/**
 * 断开通知连接
 */
export function disconnectNotify() {
    if (_ws && _ws.close) _ws.close()
    _ws = null
    _isConnected = false
    clearTimeout(_reconnectTimer)
    _recentEvents = []
    _onMessage = null
}

/**
 * 查询缓存的最近通知
 */
export function getRecentNotifications() {
    return _recentEvents
}
