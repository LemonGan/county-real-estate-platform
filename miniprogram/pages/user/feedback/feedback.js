const api = require('../../../utils/api')

const CATEGORY_OPTIONS = [
  { key: 'general', label: '其他建议' },
  { key: 'property', label: '房源问题' },
  { key: 'agent', label: '经纪人服务' },
  { key: 'feature', label: '功能建议' },
  { key: 'bug', label: '异常报错' }
]

const STATUS_LABELS = {
  pending: '待处理',
  processing: '处理中',
  resolved: '已解决',
  closed: '已关闭'
}

const CATEGORY_LABELS = CATEGORY_OPTIONS.reduce((result, item) => {
  result[item.key] = item.label
  return result
}, {})

Page({
  data: {
    categories: CATEGORY_OPTIONS,
    category: 'general',
    content: '',
    contact: '',
    feedbacks: [],
    loading: false,
    submitting: false,
    loginRequired: false
  },

  onShow() {
    this.loadFeedbacks()
  },

  chooseCategory(e) {
    this.setData({ category: e.currentTarget.dataset.key })
  },

  onInput(e) {
    this.setData({ [e.currentTarget.dataset.field]: e.detail.value })
  },

  goToLogin() {
    wx.navigateTo({ url: '/pages/login/login' })
  },

  async loadFeedbacks() {
    if (this.data.loading) return
    const token = wx.getStorageSync('token')
    if (!token) {
      this.setData({ feedbacks: [], loading: false, loginRequired: true })
      return
    }
    this.setData({ loading: true, loginRequired: false })
    try {
      const res = await api.get('/feedback/mine', { page: 1, page_size: 20 }, true)
      const feedbacks = (res.items || []).map(item => ({
        ...item,
        category_label: CATEGORY_LABELS[item.category] || item.category,
        status_label: STATUS_LABELS[item.status] || item.status,
        created_display: item.created_at ? String(item.created_at).replace('T', ' ').slice(0, 16) : ''
      }))
      this.setData({ feedbacks })
    } catch (err) {
      this.setData({ feedbacks: [], loginRequired: /未登录|登录|401/.test(err.message || '') })
    } finally {
      this.setData({ loading: false })
    }
  },

  async submit() {
    const content = this.data.content.trim()
    if (content.length < 5) {
      wx.showToast({ title: '请至少填写 5 个字', icon: 'none' })
      return
    }
    if (this.data.submitting) return

    this.setData({ submitting: true })
    try {
      await api.post('/feedback', {
        category: this.data.category,
        content,
        contact: this.data.contact.trim() || null
      }, true)
      this.setData({ content: '', contact: '' })
      wx.showToast({ title: '已提交，感谢反馈', icon: 'success' })
      this.loadFeedbacks()
    } catch (err) {
      wx.showToast({ title: err.message || '提交失败，请稍后重试', icon: 'none' })
    } finally {
      this.setData({ submitting: false })
    }
  }
})
