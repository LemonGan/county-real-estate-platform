// 首页
const app = getApp()
const api = require('../../utils/api')
const format = require('../../utils/format')
const compareUtil = require('../../utils/compare')

Page({
  data: {
    banners: [], // 轮播图
    hotProperties: [], // 热门房源
    recommendProperties: [], // 推荐房源
    newsList: [], // 房产资讯
    loading: false,
    hasMore: true,
    currentPage: 1,
    pageSize: 5,
    compareCount: 0
  },

  /**
   * 页面加载
   */
  onLoad(options) {
    this.loadBanners();
    this.loadHotProperties();
    this.loadNews();
  },

  /**
   * 页面显示
   */
  onShow() {
    this.setData({ compareCount: compareUtil.getCompareList().length });
    // 刷新最新上架房源
    if (app.globalData.isLogin) {
      this.loadRecommendProperties()
    }
  },

  /**
   * 下拉刷新
   */
  onPullDownRefresh() {
    this.loadBanners()
    this.loadHotProperties()
    this.loadNews()

    if (app.globalData.isLogin) {
      this.loadRecommendProperties()
    }
    setTimeout(() => {
      wx.stopPullDownRefresh()
    }, 1000)
  },

  /**
   * 处理房源图片URL
   */
  processProperties(list) {
    const origin = (app.globalData.baseUrl || 'https://api.imlemon.top/api/v1').replace('/api/v1', '')
    return (list || []).map(item => {
      const firstImage = item.images && item.images[0]
      const imageValue = item.cover_url || (typeof firstImage === 'string' ? firstImage : (firstImage && firstImage.image_url)) || ''
      const coverUrl = imageValue && !imageValue.startsWith('http')
        ? origin + (imageValue.startsWith('/static/') ? imageValue : `/static/${imageValue.replace(/^\//, '')}`)
        : imageValue
      return {
        ...item,
        cover_image_url: coverUrl,
        total_price_text: format.formatPrice(item.total_price),
        area_text: format.formatArea(item.area),
        room_type: format.formatRoomType(item),
        property_type_text: format.formatPropertyType(item.property_type),
        transaction_type_text: format.formatTransactionType(item.transaction_type)
      }
    })
  },

  /**
   * 加载轮播图
   */
  loadBanners() {
    // 运营后台尚未接入轮播素材，不展示占位图片。
    this.setData({ banners: [] })
  },

  /**
   * 加载热门房源
   */
  async loadHotProperties() {
    if (this.data.loading) return

    this.setData({ loading: true })

    try {
      const res = await api.get('/properties', {
        page: 1,
        page_size: this.data.pageSize,
        status_filter: 1 // 只获取在售房源
      }, false)

      this.setData({
        hotProperties: this.processProperties(res.list),
        loading: false
      })
    } catch (err) {
      console.error('加载热门房源失败:', err)
      this.setData({ loading: false })
    }
  },

  /**
   * 加载最新上架房源
   */
  async loadRecommendProperties() {
    try {
      const res = await api.get('/properties', {
        page: 1,
        page_size: 5,
        status_filter: 1
      }, false)

      this.setData({
        recommendProperties: this.processProperties(res.list)
      })
    } catch (err) {
      console.error('加载推荐房源失败:', err)
    }
  },

  /**
   * 加载房产资讯
   */
  async loadNews() {
    try {
      const res = await api.get('/news/', {
        page: 1,
        page_size: 5
      }, false)

      this.setData({
        newsList: (res.items || []).map(item => ({
          ...item,
          publish_time_text: this.formatPublishTime(item.created_at)
        }))
      })
    } catch (err) {
      console.error('加载房产资讯失败:', err)
    }
  },

  /**
   * 格式化发布时间
   */
  formatPublishTime(dateStr) {
    const now = new Date()
    // 将日期字符串转换为 iOS 兼容格式 (yyyy-MM-ddTHH:mm:ss)
    const iosDateStr = dateStr.replace(/\s+/g, 'T')
    const date = new Date(iosDateStr)
    const diff = now - date
    const days = Math.floor(diff / (1000 * 60 * 60 * 24))

    if (days === 0) {
      const hours = Math.floor(diff / (1000 * 60 * 60))
      if (hours === 0) {
        const minutes = Math.floor(diff / (1000 * 60))
        return minutes <= 0 ? '刚刚' : minutes + '分钟前'
      }
      return hours + '小时前'
    } else if (days === 1) {
      return '昨天'
    } else if (days < 7) {
      return days + '天前'
    } else {
      return format.formatDate(dateStr, 'MM-DD')
    }
  },

  /**
   * 查看房源详情
   */
  goToDetail(e) {
    const { id } = e.currentTarget.dataset
    wx.navigateTo({
      url: `/pages/property/detail/detail?id=${id}`
    })
  },

  /**
   * 跳转到房源列表
   */
  goToList(e) {
    const transactionType = e?.currentTarget?.dataset?.transaction || 1;
    const propertyTypeTag = e?.currentTarget?.dataset?.propertyType || '';
    wx.setStorageSync('listTransactionType', transactionType);
    wx.setStorageSync('listPropertyTypeTag', propertyTypeTag);
    wx.switchTab({
      url: '/pages/property/list/list'
    });
  },

  /**
   * 跳转到搜索页
   */
  goToSearch() {
    wx.navigateTo({
      url: '/pages/property/search/search'
    })
  },

  /**
   * 跳转到资讯列表
   */
  goToNews() {
    wx.navigateTo({
      url: '/pages/news/list/list'
    })
  },

  /**
   * 跳转到资讯详情
   */
  goToNewsDetail(e) {
    const { id } = e.currentTarget.dataset
    wx.navigateTo({
      url: `/pages/news/detail/detail?id=${id}`
    })
  },

  goToCompare() {
    wx.navigateTo({ url: '/pages/property/compare/compare' });
  },

  goToMap() {
    wx.navigateTo({ url: '/pages/property/map/map' });
  },

  /**
   * 分享
   */
  onShareAppMessage() {
    return {
      title: '县域房产信息平台',
      path: '/pages/index/index',
      imageUrl: '/assets/images/share.jpg'
    }
  }
})
