// pages/news/list/list.js
const app = getApp()
const api = require('../../../utils/api.js')

Page({
  data: {
    newsList: [],
    loading: false,
    hasMore: true,
    currentPage: 1,
    pageSize: 10,
    currentCategory: 'all',
    categories: [
      { value: 'all', label: '全部' },
      { value: 'market', label: '市场分析' },
      { value: 'guide', label: '购房指南' },
      { value: 'policy', label: '政策解读' },
      { value: 'knowledge', label: '房产知识' }
    ]
  },

  onLoad(options) {
    // 从其他页面进入时可能带分类参数
    if (options.category) {
      this.setData({ currentCategory: options.category })
    }
    this.loadNewsList()
  },

  onPullDownRefresh() {
    this.setData({ currentPage: 1, newsList: [], hasMore: true })
    this.loadNewsList().then(() => {
      wx.stopPullDownRefresh()
    })
  },

  onReachBottom() {
    if (this.data.hasMore && !this.data.loading) {
      this.loadMoreNews()
    }
  },

  onShareAppMessage() {
    return {
      title: '县域房产平台 - 房产资讯',
      path: '/pages/news/list/list'
    }
  },

  // 切换分类
  switchCategory(e) {
    const category = e.currentTarget.dataset.value
    this.setData({ currentCategory: category, currentPage: 1, newsList: [], hasMore: true })
    this.loadNewsList()
  },

  // 加载资讯列表
  async loadNewsList() {
    if (this.data.loading) return

    this.setData({ loading: true })

    try {
      const params = {
        page: this.data.currentPage,
        page_size: this.data.pageSize
      }

      if (this.data.currentCategory !== 'all') {
        params.category = this.data.currentCategory
      }

      const res = await api.get('/news/', params, false)

      this.setData({
        newsList: res.items || [],
        loading: false,
        hasMore: (res.items || []).length >= this.data.pageSize
      })
    } catch (error) {
      console.error('加载资讯列表失败:', error)
      this.setData({ loading: false })
      wx.showToast({
        title: '加载失败',
        icon: 'none'
      })
    }
  },

  // 加载更多资讯
  async loadMoreNews() {
    if (this.data.loading || !this.data.hasMore) return

    this.setData({ loading: true, currentPage: this.data.currentPage + 1 })

    try {
      const params = {
        page: this.data.currentPage,
        page_size: this.data.pageSize
      }

      if (this.data.currentCategory !== 'all') {
        params.category = this.data.currentCategory
      }

      const res = await api.get('/news/', params, false)

      this.setData({
        newsList: [...this.data.newsList, ...(res.items || [])],
        loading: false,
        hasMore: (res.items || []).length >= this.data.pageSize
      })
    } catch (error) {
      console.error('加载更多资讯失败:', error)
      this.setData({ loading: false })
    }
  },

  // 查看资讯详情
  goToNewsDetail(e) {
    const newsId = e.currentTarget.dataset.id
    wx.navigateTo({
      url: `/pages/news/detail/detail?id=${newsId}`
    })
  }
})
