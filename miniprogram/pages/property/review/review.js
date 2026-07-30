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
    canResubmit: false,
    myReview: null,
    myReviewStatus: null,
    reviewImages: [],
    uploadingImages: false,
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
  },

  onShow() {
    if (!this.data.isAddMode && this.data.propertyId) this.checkMyReview()
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
        const newList = (loadMore ? [...this.data.reviewList, ...res.list] : res.list).map((item) => ({
          ...item,
          displayImages: (item.images || []).map((url) => this.toDisplayUrl(url))
        }))
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
    if (!token) {
      this.setData({ hasReviewed: false, canResubmit: false, myReview: null, myReviewStatus: null })
      return
    }
    
    try {
      const res = await api.get('/properties/reviews/my')
      
      if (res && res.list) {
        const myReview = res.list.find(r => r.property_id == this.data.propertyId)
        if (myReview) {
          const statusMap = {
            0: { label: '审核中', className: 'pending', hint: '评价审核通过后会在房源页公开显示。' },
            1: { label: '已通过', className: 'approved', hint: '你的评价已公开展示，感谢真实分享。' },
            2: { label: '未通过', className: 'rejected', hint: '请修改内容后重新提交审核。' }
          }
          const status = statusMap[myReview.is_verified] || statusMap[0]
          this.setData({
            hasReviewed: true,
            canResubmit: myReview.is_verified === 2,
            myReview,
            myReviewStatus: { ...status, note: myReview.review_note || '' }
          })
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
    const myReview = this.data.myReview
    this.setData({
      showModal: true,
      myRating: this.data.canResubmit && myReview ? myReview.rating : 5,
      content: this.data.canResubmit && myReview ? myReview.content : '',
      contentLength: this.data.canResubmit && myReview && myReview.content ? myReview.content.length : 0,
      reviewImages: this.data.canResubmit && myReview ? (myReview.images || []).map((url) => ({ url, displayUrl: this.toDisplayUrl(url) })) : []
    })
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

  toDisplayUrl(url) {
    if (!url || url.startsWith('http')) return url
    const origin = (getApp().globalData.baseUrl || '').replace('/api/v1', '')
    return origin + url
  },

  chooseReviewImages() {
    if (this.data.uploadingImages) return
    const remaining = 3 - this.data.reviewImages.length
    if (remaining <= 0) {
      wx.showToast({ title: '最多上传 3 张图片', icon: 'none' })
      return
    }
    wx.chooseMedia({
      count: remaining,
      mediaType: ['image'],
      sourceType: ['album', 'camera'],
      success: async (res) => {
        this.setData({ uploadingImages: true })
        try {
          const uploaded = []
          for (const file of res.tempFiles) {
            const result = await api.uploadImage(file.tempFilePath)
            uploaded.push({ url: result.url, displayUrl: this.toDisplayUrl(result.url) })
          }
          this.setData({ reviewImages: this.data.reviewImages.concat(uploaded).slice(0, 3) })
        } catch (err) {
          wx.showToast({ title: err.message || '图片上传失败', icon: 'none' })
        } finally {
          this.setData({ uploadingImages: false })
        }
      }
    })
  },

  removeReviewImage(e) {
    const reviewImages = this.data.reviewImages.slice()
    reviewImages.splice(e.currentTarget.dataset.index, 1)
    this.setData({ reviewImages })
  },

  previewReviewImage(e) {
    const index = e.currentTarget.dataset.index
    wx.previewImage({
      current: this.data.reviewImages[index].displayUrl,
      urls: this.data.reviewImages.map((item) => item.displayUrl)
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
        content: this.data.content,
        images: this.data.reviewImages.map((item) => item.url)
      })
      
      wx.hideLoading()
      
      if (res && res.id) {
        wx.showToast({ title: this.data.canResubmit ? '已重新提交审核' : '提交成功，等待审核', icon: 'success' })
        this.closeModal()
        this.setData({
          hasReviewed: true,
          canResubmit: false,
          myReviewStatus: { label: '审核中', className: 'pending', hint: '评价审核通过后会在房源页公开显示。', note: '' }
        })
        this.checkMyReview()
        this.loadReviews()
      } else {
        wx.showToast({ title: res.data.message || '提交失败', icon: 'none' })
      }
    } catch (err) {
      wx.hideLoading()
      wx.showToast({ title: err.message || '提交失败', icon: 'none' })
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
