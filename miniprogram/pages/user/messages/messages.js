const api = require('../../../utils/api')

const PAGE_SIZE = 20

Page({
  data: {
    messages: [],
    loading: true,
    loadingMore: false,
    empty: false,
    page: 1,
    hasMore: true,
    unreadCount: 0
  },

  onLoad() {
    this.loadMessages(true)
  },

  onPullDownRefresh() {
    this.loadMessages(true).finally(() => wx.stopPullDownRefresh())
  },

  onReachBottom() {
    if (!this.data.loading && !this.data.loadingMore && this.data.hasMore) {
      this.loadMessages(false)
    }
  },

  async loadMessages(reset) {
    const page = reset ? 1 : this.data.page + 1
    this.setData(reset ? { loading: true } : { loadingMore: true })
    try {
      const res = await api.get('/messages', { page, page_size: PAGE_SIZE })
      const list = (res.list || []).map((item) => this.formatMessage(item))
      const messages = reset ? list : this.data.messages.concat(list)
      this.setData({
        messages,
        page,
        unreadCount: res.unread_count || 0,
        hasMore: messages.length < (res.total || 0),
        empty: messages.length === 0,
        loading: false,
        loadingMore: false
      })
    } catch (err) {
      console.error('加载通知失败:', err)
      this.setData({ loading: false, loadingMore: false, empty: this.data.messages.length === 0 })
    }
  },

  formatMessage(item) {
    const typeMeta = {
      1: { text: '系统通知', className: 'type-system', icon: '公告' },
      2: { text: '预约提醒', className: 'type-appointment', icon: '预约' },
      3: { text: '房源动态', className: 'type-property', icon: '房源' }
    }
    return {
      ...item,
      typeMeta: typeMeta[item.type] || typeMeta[1],
      displayTime: this.formatTime(item.created_at)
    }
  },

  formatTime(value) {
    if (!value) return ''
    const date = new Date(String(value).replace(' ', 'T'))
    if (Number.isNaN(date.getTime())) return String(value).slice(0, 16)
    const now = new Date()
    const pad = (number) => String(number).padStart(2, '0')
    const time = `${pad(date.getHours())}:${pad(date.getMinutes())}`
    if (date.toDateString() === now.toDateString()) return `今天 ${time}`
    const yesterday = new Date(now)
    yesterday.setDate(now.getDate() - 1)
    if (date.toDateString() === yesterday.toDateString()) return `昨天 ${time}`
    return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
  },

  async markRead(e) {
    const { id, index, isRead } = e.currentTarget.dataset
    if (isRead) return
    try {
      await api.post(`/messages/${id}/read`, {})
      const messages = this.data.messages.slice()
      messages[index] = { ...messages[index], is_read: true }
      this.setData({ messages, unreadCount: Math.max(0, this.data.unreadCount - 1) })
    } catch (err) {
      console.error('标记消息已读失败:', err)
    }
  },

  markAllRead() {
    if (!this.data.unreadCount) return
    wx.showModal({
      title: '全部标为已读',
      content: '确定将全部消息标记为已读吗？',
      success: async (res) => {
        if (!res.confirm) return
        try {
          await api.post('/messages/read-all', {})
          this.setData({
            messages: this.data.messages.map((item) => ({ ...item, is_read: true })),
            unreadCount: 0
          })
          wx.showToast({ title: '已全部标为已读', icon: 'success' })
        } catch (err) {
          console.error('全部标记已读失败:', err)
        }
      }
    })
  }
})
