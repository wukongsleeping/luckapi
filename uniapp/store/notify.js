const STORAGE_KEY_UNREAD = 'luckapi_notify_unread'

let listeners = []

function getUnreadCount() {
    try {
        return parseInt(uni.getStorageSync(STORAGE_KEY_UNREAD) || '0')
    } catch {
        return 0
    }
}

function saveUnreadCount(n) {
    try {
        uni.setStorageSync(STORAGE_KEY_UNREAD, String(n))
    } catch (e) {}
}

function countUnread(events) {
    return events.filter(e => e._viewed !== true).length
}

function refreshAll() {
    try {
        const { getRecentNotifications } = require('@/api/notify.js')
        const events = getRecentNotifications()
        const unread = countUnread(events)
        saveUnreadCount(unread)

        // Emit for any page listening
        uni.$emit('notify_update', { items: events, unread })
        listeners.forEach(cb => cb({ items: events, unread }))
    } catch (e) {
        console.error('Failed to refresh notifications:', e)
    }
}

export const notifyStore = {
    unreadCount: 0,

    listen(cb) {
        listeners.push(cb)
        refreshAll()
    },
    unlisten(cb) {
        const i = listeners.indexOf(cb)
        if (i >= 0) listeners.splice(i, 1)
    },

    onRealtime(type, data) {
        if (type !== 'qa_started' && type !== 'qa_completed') return
        refreshAll()
    },

    markAllViewed() {
        const { getRecentNotifications } = require('@/api/notify.js')
        const events = getRecentNotifications()
        events.forEach(e => { e._viewed = true })
        saveUnreadCount(0)
        uni.$emit('notify_update', { items: events, unread: 0 })
        listeners.forEach(cb => cb({ items: events, unread: 0 }))
    },
}
