// 我的收藏页
const api = require('../../../utils/api')
const { formatPrice } = require('../../../utils/format')
const priceTrack = require('../../../utils/price_track')

Page({
  data: {
    favorites: [],
    loading: true,
    empty: false
  },

  /**
   * 页面加载
   */
  onLoad(options) {
    this.loadFavorites()
  },

  /**
   * 页面显示
   */
  onShow() {
    // 刷新列表
    this.loadFavorites()
  },

  /**
   * 加载收藏列表
   */
  async loadFavorites() {
    this.setData({ loading: true })

    try {
      const res = await api.get('/favorites/')

      const rawList = res.list || res.items || res || [];
      // 检查降价
      const favorites = rawList.map(item => {
        const prop = item.property || item;
        const currentPrice = prop.total_price || prop.price || 0;
        const drop = priceTrack.checkPriceDrop(prop.id, currentPrice);
        return { ...item, priceDrop: drop.dropped ? (drop.diff / 10000).toFixed(1) : null };
      });
      this.setData({
        favorites,
        loading: false,
        empty: favorites.length === 0
      })
    } catch (err) {
      console.error('加载收藏失败:', err)
      this.setData({ loading: false, empty: true })

      wx.showToast({
        title: err.message || '加载失败',
        icon: 'none'
      })
    }
  },

  /**
   * 跳转房源详情
   */
  goToDetail(e) {
    const { id } = e.currentTarget.dataset
    wx.navigateTo({
      url: `/pages/property/detail/detail?id=${id}`
    })
  },

  /**
   * 取消收藏
   */
  async removeFavorite(e) {
    const { id, index } = e.currentTarget.dataset

    wx.showModal({
      title: '提示',
      content: '确定要取消收藏吗？',
      success: async (res) => {
        if (res.confirm) {
          try {
            await api.delete(`/favorites/${id}`)

            // 从列表中移除
            const favorites = this.data.favorites
            favorites.splice(index, 1)

            this.setData({
              favorites,
              empty: favorites.length === 0
            })

            wx.showToast({
              title: '已取消收藏',
              icon: 'success'
            })
          } catch (err) {
            console.error('取消收藏失败:', err)
            wx.showToast({
              title: err.message || '操作失败',
              icon: 'none'
            })
          }
        }
      }
    })
  },

  /**
   * 下拉刷新
   */
  onPullDownRefresh() {
    this.loadFavorites().then(() => {
      wx.stopPullDownRefresh()
    })
  },

  /**
   * 去逛逛（跳转到房源列表）
   */
  goToList() {
    wx.switchTab({
      url: '/pages/property/list/list'
    })
  },

  /**
   * 分享
   */
  onShareAppMessage() {
    return {
      title: '我的收藏 - 县域房产平台',
      path: '/pages/user/favorites/favorites'
    }
  }
})
