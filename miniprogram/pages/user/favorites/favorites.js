// 我的收藏页
const api = require('../../../utils/api')
const priceTrack = require('../../../utils/price_track')

Page({
  data: { favorites: [], loading: true, empty: false },

  onLoad() { this.loadFavorites() },
  onShow() { this.loadFavorites() },

  normalizeImage(property) {
    const baseUrl = getApp().globalData.baseUrl || 'https://api.imlemon.top/api/v1'
    const origin = baseUrl.replace('/api/v1', '')
    const staticUrl = origin + '/static'
    const source = property.cover_url || (property.images && property.images[0]) || ''
    if (!source || source.startsWith('http')) return source || '/assets/images/default-property.png'
    if (source.startsWith('/static/')) return origin + source
    return staticUrl + source
  },

  async loadFavorites() {
    this.setData({ loading: true })
    try {
      const res = await api.get('/favorites/')
      const favorites = (res.list || []).map((item) => {
        const property = item.property || {}
        const currentPrice = property.total_price || property.price || 0
        const drop = priceTrack.checkPriceDrop(property.id, currentPrice)
        return {
          ...item,
          property: { ...property, displayImage: this.normalizeImage(property) },
          priceText: currentPrice ? `${(currentPrice / 10000).toFixed(1)}万` : '待议',
          priceDrop: drop.dropped ? (drop.diff / 10000).toFixed(1) : null
        }
      })
      this.setData({ favorites, loading: false, empty: favorites.length === 0 })
    } catch (err) {
      console.error('加载收藏失败:', err)
      this.setData({ loading: false, empty: true })
      wx.showToast({ title: err.message || '加载失败', icon: 'none' })
    }
  },

  goToDetail(e) {
    const { id } = e.currentTarget.dataset
    if (id) wx.navigateTo({ url: `/pages/property/detail/detail?id=${id}` })
  },

  removeFavorite(e) {
    const { id, index } = e.currentTarget.dataset
    wx.showModal({
      title: '取消收藏',
      content: '确定要取消收藏吗？',
      success: async (res) => {
        if (!res.confirm) return
        try {
          await api.del(`/favorites/${id}`)
          const favorites = [...this.data.favorites]
          favorites.splice(index, 1)
          this.setData({ favorites, empty: favorites.length === 0 })
          wx.showToast({ title: '已取消收藏', icon: 'success' })
        } catch (err) {
          wx.showToast({ title: err.message || '操作失败', icon: 'none' })
        }
      }
    })
  },

  onPullDownRefresh() {
    this.loadFavorites().finally(() => wx.stopPullDownRefresh())
  },

  goToList() { wx.switchTab({ url: '/pages/property/list/list' }) },
  onShareAppMessage() { return { title: '我的收藏 - 县域房产平台', path: '/pages/user/favorites/favorites' } }
})
