// 首页
const app = getApp()
const api = require('../../utils/api')
const cache = require('../../utils/cache')
const format = require('../../utils/format')

Page({
  data: {
    banners: [], // 轮播图
    hotProperties: [], // 热门房源
    recommendProperties: [], // 推荐房源
    hotVideos: [], // 热门视频
    newsList: [], // 房产资讯
    loading: false,
    hasMore: true,
    currentPage: 1,
    pageSize: 5
  },

  /**
   * 页面加载
   */
  onLoad(options) {
    console.log('首页加载')
    this.loadBanners()
    this.loadHotProperties()
    this.loadHotVideos()
    this.loadNews()
  },

  /**
   * 页面显示
   */
  onShow() {
    // 刷新推荐房源
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
    this.loadHotVideos()
    this.loadNews()

    if (app.globalData.isLogin) {
      this.loadRecommendProperties()
    }

    setTimeout(() => {
      wx.stopPullDownRefresh()
    }, 1000)
  },

  /**
   * 加载轮播图
   */
  async loadBanners() {
    try {
      // TODO: 调用轮播图API
      const banners = [
        { id: 1, image: '/assets/images/banner1.jpg', title: '精选房源推荐' },
        { id: 2, image: '/assets/images/banner2.jpg', title: '新房上市' },
        { id: 3, image: '/assets/images/banner3.jpg', title: '热门房源' }
      ]

      this.setData({ banners })
    } catch (err) {
      console.error('加载轮播图失败:', err)
    }
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
        hotProperties: res.list || [],
        loading: false
      })
    } catch (err) {
      console.error('加载热门房源失败:', err)
      this.setData({ loading: false })
    }
  },

  /**
   * 加载推荐房源
   */
  async loadRecommendProperties() {
    try {
      // TODO: 调用推荐算法API
      const res = await api.get('/properties', {
        page: 1,
        page_size: 5,
        status_filter: 1
      }, false)

      this.setData({
        recommendProperties: res.list || []
      })
    } catch (err) {
      console.error('加载推荐房源失败:', err)
    }
  },

  /**
   * 加载热门视频
   */
  async loadHotVideos() {
    try {
      const res = await api.get('/short-videos/', {
        page: 1,
        page_size: 5,
        type: 'hot'
      }, false)

      this.setData({
        hotVideos: (res.items || []).map(item => ({
          ...item,
          play_count_text: this.formatPlayCount(item.play_count)
        }))
      })
    } catch (err) {
      console.error('加载热门视频失败:', err)
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
   * 格式化播放次数
   */
  formatPlayCount(count) {
    if (count >= 10000) {
      return (count / 10000).toFixed(1) + '万'
    } else if (count >= 1000) {
      return (count / 1000).toFixed(1) + 'k'
    }
    return count.toString()
  },

  /**
   * 格式化发布时间
   */
  formatPublishTime(dateStr) {
    const now = new Date()
    const date = new Date(dateStr)
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
  goToList() {
    wx.switchTab({
      url: '/pages/property/list/list'
    })
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
   * 跳转到地图找房
   */
  goToMap() {
    wx.navigateTo({
      url: '/pages/property/map/map'
    })
  },

  /**
   * 跳转到视频列表
   */
  goToVideos() {
    wx.navigateTo({
      url: '/pages/video/list/list'
    })
  },

  /**
   * 跳转到视频详情
   */
  goToVideoDetail(e) {
    const { id } = e.currentTarget.dataset
    wx.navigateTo({
      url: `/pages/video/detail/detail?id=${id}`
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
