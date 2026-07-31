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

  normalizeNewsItem(item) {
    return {
      ...item,
      cover_url: item.cover_url || '/assets/images/news-cover-1.jpg',
      summary: item.summary || '暂无摘要',
      publish_time_text: item.publish_time_text || item.publish_time || '',
      tags: item.tags || []
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

      const res = await api.get('/news', params, false)
      const items = (res.items || []).map(this.normalizeNewsItem)
      const total = typeof res.total === 'number' ? res.total : items.length

      this.setData({
        newsList: items,
        loading: false,
        hasMore: this.data.currentPage * this.data.pageSize < total
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

    const nextPage = this.data.currentPage + 1
    this.setData({ loading: true })

    try {
      const params = {
        page: nextPage,
        page_size: this.data.pageSize
      }

      if (this.data.currentCategory !== 'all') {
        params.category = this.data.currentCategory
      }

      const res = await api.get('/news', params, false)
      const items = (res.items || []).map(this.normalizeNewsItem)
      const total = typeof res.total === 'number' ? res.total : this.data.newsList.length + items.length

      this.setData({
        newsList: [...this.data.newsList, ...items],
        loading: false,
        currentPage: nextPage,
        hasMore: nextPage * this.data.pageSize < total
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
