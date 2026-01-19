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

  // 加载资讯详情
  async loadNewsDetail() {
    this.setData({ loading: true })

    try {
      const res = await api.get(`/news/${this.data.newsId}`, {}, false)

      // 增加浏览量
      this.incrementViewCount()

      this.setData({
        news: res,
        loading: false
      })
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
      // TODO: 调用后端API增加浏览量
      // await api.post(`/news/${this.data.newsId}/view/`, {}, false)
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

    // TODO: 实现收藏功能
    wx.showToast({
      title: this.data.isCollected ? '已取消收藏' : '收藏成功',
      icon: 'success'
    })
    this.setData({ isCollected: !this.data.isCollected })
  },

  // 点赞资讯
  async likeNews() {
    try {
      // TODO: 实现点赞功能
      this.setData({ isLiked: !this.data.isLiked })
      wx.showToast({
        title: this.data.isLiked ? '点赞成功' : '取消点赞',
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
