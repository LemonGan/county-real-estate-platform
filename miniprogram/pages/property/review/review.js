// pages/property/review/review.js
const api = require('../../../utils/api')

Page({
  data: {
    propertyId: null,
    reviewList: [],
    page: 1,
    pageSize: 10,
    loading: false,
    hasMore: true,
    stats: {
      avg_rating: 0,
      avgRating: 0,
      total_count: 0
    },
    hasReviewed: false,
    isAddMode: false,
    showModal: false,
    myRating: 5,
    content: '',
    contentLength: 0
  },

  onLoad(options) {
    // 如果id为0或空，表示发布新房源
    if (!options.id || options.id === '0') {
      this.setData({ isAddMode: true })
      wx.setNavigationBarTitle({ title: '发布房源' })
      return
    }
    const propertyId = options.id || options.property_id
    this.setData({ propertyId: parseInt(propertyId) })
    this.loadReviews()
    this.checkMyReview()
  },

  onReachBottom() {
    if (this.data.hasMore && !this.data.loading) {
      this.loadReviews(true)
    }
  },

  async loadReviews(loadMore = false) {
    if (this.data.loading) return
    this.setData({ loading: true })
    
    const page = loadMore ? this.data.page + 1 : 1
    
    try {
      const res = await api.get(`/properties/${this.data.propertyId}/reviews`, {
        page,
        page_size: this.data.pageSize
      }, false)
      
      if (res && res.list) {
        const newList = loadMore ? [...this.data.reviewList, ...res.list] : res.list
        this.setData({
          reviewList: newList,
          page,
          hasMore: res.list.length >= this.data.pageSize,
          stats: {
            avg_rating: res.avg_rating || 0,
            avgRating: res.avg_rating || 0,
            total_count: res.total_count || 0
          }
        })
      }
    } catch (err) {
      console.error('加载评价失败:', err)
    }
    
    this.setData({ loading: false })
  },

  async checkMyReview() {
    const token = wx.getStorageSync('token')
    if (!token) return
    
    try {
      const res = await api.get('/properties/reviews/my')
      
      if (res && res.list) {
        const myReview = res.list.find(r => r.property_id == this.data.propertyId)
        if (myReview) {
          this.setData({ hasReviewed: true })
        }
      }
    } catch (err) {
      console.error('检查评价失败:', err)
    }
  },

  openReviewModal() {
    const token = wx.getStorageSync('token')
    if (!token) {
      wx.showToast({ title: '请先登录', icon: 'none' })
      return
    }
    this.setData({ showModal: true })
  },

  closeModal() {
    this.setData({ showModal: false, myRating: 5, content: '', contentLength: 0 })
  },

  setRating(e) {
    this.setData({ myRating: e.currentTarget.dataset.rating })
  },

  onContentInput(e) {
    this.setData({ 
      content: e.detail.value,
      contentLength: e.detail.value.length
    })
  },

  async submitReview() {
    if (!this.data.content.trim()) {
      wx.showToast({ title: '请输入评价内容', icon: 'none' })
      return
    }
    
    const token = wx.getStorageSync('token')
    
    wx.showLoading({ title: '提交中...' })
    
    try {
      const res = await api.post(`/properties/${this.data.propertyId}/reviews`, {
        rating: this.data.myRating,
        content: this.data.content
      })
      
      wx.hideLoading()
      
      if (res && res.id) {
        wx.showToast({ title: '提交成功', icon: 'success' })
        this.closeModal()
        this.setData({ hasReviewed: true })
        this.loadReviews()
      } else {
        wx.showToast({ title: res.data.message || '提交失败', icon: 'none' })
      }
    } catch (err) {
      wx.hideLoading()
      wx.showToast({ title: '提交失败', icon: 'none' })
    }
  },

  goBack() {
    wx.navigateTo({ url: '/pages/index/index' })
  },

  previewImage(e) {
    const src = e.currentTarget.dataset.src
    wx.previewImage({
      urls: [src]
    })
  }
})
