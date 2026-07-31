// pages/news/detail/detail.js
const api = require('../../../utils/api.js')
const app = getApp()

Page({
  data: {
    newsId: null,
    news: null,
    loading: true,
    isCollected: false,
    isLiked: false
  },

  onLoad(options) {
    const { id } = options
    if (id) {
      this.setData({ newsId: id })
      this.loadNewsDetail()
    } else {
      wx.showToast({
        title: '资讯不存在',
        icon: 'none'
      })
      setTimeout(() => {
        wx.navigateBack()
      }, 1500)
    }
  },

  onShareAppMessage() {
    const { news } = this.data
    return {
      title: news ? news.title : '房产资讯',
      path: `/pages/news/detail/detail?id=${this.data.newsId}`,
      imageUrl: news ? news.cover_url : ''
    }
  },

  normalizeNews(item) {
    return {
      ...item,
      cover_url: item.cover_url || '/assets/images/news-cover-1.jpg',
      summary: item.summary || '',
      publish_time_text: item.publish_time_text || item.publish_time || '',
      tags: item.tags || []
    }
  },

  // 加载资讯详情
  async loadNewsDetail() {
    this.setData({ loading: true })

    try {
      const res = this.normalizeNews(await api.get(`/news/${this.data.newsId}`, {}, false))

      this.setData({
        news: res,
        isLiked: !!res.is_liked,
        isCollected: !!res.is_collected,
        loading: false
      })

      // 增加浏览量，并同步本地展示数字
      this.incrementViewCount()
    } catch (error) {
      console.error('加载资讯详情失败:', error)
      this.setData({ loading: false })
      wx.showToast({
        title: '加载失败',
        icon: 'none'
      })
    }
  },

  // 增加浏览量
  async incrementViewCount() {
    try {
      const res = await api.post(`/news/${this.data.newsId}/view`, {}, false)
      if (res && typeof res.view_count === 'number' && this.data.news) {
        this.setData({
          news: { ...this.data.news, view_count: res.view_count }
        })
      }
    } catch (error) {
      console.error('增加浏览量失败:', error)
    }
  },

  // 收藏资讯
  async collectNews() {
    if (!app.globalData.isLogin) {
      wx.navigateTo({
        url: '/pages/login/login'
      })
      return
    }

    try {
      const res = await api.post(`/news/${this.data.newsId}/collect`, {}, true)
      this.setData({
        isCollected: !!res.is_collected,
        news: { ...this.data.news, collect_count: res.collect_count }
      })
      wx.showToast({
        title: res.is_collected ? '收藏成功' : '已取消收藏',
        icon: 'success'
      })
    } catch (error) {
      console.error('收藏失败:', error)
    }
  },

  // 点赞资讯
  async likeNews() {
    if (!app.globalData.isLogin) {
      wx.navigateTo({
        url: '/pages/login/login'
      })
      return
    }

    try {
      const res = await api.post(`/news/${this.data.newsId}/like`, {}, true)
      this.setData({
        isLiked: !!res.is_liked,
        news: { ...this.data.news, like_count: res.like_count }
      })
      wx.showToast({
        title: res.is_liked ? '点赞成功' : '已取消点赞',
        icon: 'success'
      })
    } catch (error) {
      console.error('点赞失败:', error)
    }
  },

  // 返回首页
  goHome() {
    wx.switchTab({
      url: '/pages/index/index'
    })
  }
})
