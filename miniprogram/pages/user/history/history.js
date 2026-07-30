const api = require('../../../utils/api')
const { formatDateTime } = require('../../../utils/format')

Page({
  data: { history: [], loading: true, page: 1, pageSize: 10, hasMore: true, empty: false },

  onLoad() { this.loadHistory() },
  onReachBottom() { if (this.data.hasMore && !this.data.loading) this.loadHistory(true) },

  imageUrl(value) {
    if (!value || value.startsWith('http')) return value || '/assets/images/default-property.png'
    const origin = (getApp().globalData.baseUrl || '').replace('/api/v1', '')
    return value.startsWith('/static/') ? origin + value : origin + '/static' + value
  },

  async loadHistory(loadMore = false) {
    this.setData({ loading: true })
    const page = loadMore ? this.data.page + 1 : 1
    try {
      const res = await api.get('/users/history/properties', { page, page_size: this.data.pageSize })
      const list = (res.list || []).map((item) => ({
        ...item,
        viewedAtText: formatDateTime(item.viewed_at),
        priceText: item.property.total_price ? `${(item.property.total_price / 10000).toFixed(1)}万` : '待议',
        property: { ...item.property, displayImage: this.imageUrl(item.property.cover_url) }
      }))
      const history = loadMore ? [...this.data.history, ...list] : list
      this.setData({
        history,
        page,
        loading: false,
        empty: history.length === 0,
        hasMore: list.length >= this.data.pageSize
      })
    } catch (err) {
      if (!loadMore) this.setData({ history: [], empty: true })
      this.setData({ loading: false })
      wx.showToast({ title: err.message || '加载失败', icon: 'none' })
    }
  },

  goToDetail(e) {
    const { id } = e.currentTarget.dataset
    wx.navigateTo({ url: `/pages/property/detail/detail?id=${id}` })
  },

  onPullDownRefresh() {
    this.loadHistory().finally(() => wx.stopPullDownRefresh())
  },

  goToList() { wx.switchTab({ url: '/pages/property/list/list' }) }
})
