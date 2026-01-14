// 房源详情页
const api = require('../../../utils/api')
const { formatPrice, formatDate } = require('../../../utils/format')

Page({
  data: {
    propertyId: null,
    property: null,
    loading: true,
    currentImageIndex: 0,
    isFavorite: false,
    showShare: false,
    showContact: false,
    imageUrls: []  // 图片URL列表
  },

  /**
   * 页面加载
   */
  onLoad(options) {
    const { id } = options
    if (id) {
      this.setData({ propertyId: id })
      this.loadPropertyDetail(id)
    } else {
      wx.showToast({
        title: '房源不存在',
        icon: 'none'
      })
      setTimeout(() => {
        wx.navigateBack()
      }, 1500)
    }
  },

  /**
   * 加载房源详情
   */
  async loadPropertyDetail(id) {
    this.setData({ loading: true })

    try {
      const res = await api.get(`/properties/${id}`, {}, false)

      // 提取图片URL列表
      const imageUrls = (res.images || []).map(img => img.url)

      this.setData({
        property: res,
        imageUrls: imageUrls,
        loading: false
      })

      // 记录浏览行为
      this.recordView(id)
    } catch (err) {
      console.error('加载房源详情失败:', err)
      this.setData({ loading: false })

      wx.showToast({
        title: err.message || '加载失败',
        icon: 'none'
      })
    }
  },

  /**
   * 记录浏览行为（仅在登录时记录）
   */
  async recordView(propertyId) {
    // 检查用户是否登录
    const token = wx.getStorageSync('token')
    if (!token) {
      // 未登录，静默跳过
      return
    }

    try {
      // 登录用户记录浏览
      // behavior_type: 1=浏览, target_type: 1=房源
      const result = await api.post('/users/behaviors', {
        behavior_type: 1,
        target_type: 1,
        target_id: parseInt(propertyId)
      }, true)
      console.log('浏览记录成功:', result)
    } catch (err) {
      // 静默处理错误，不影响用户体验
      // 打印完整错误对象用于调试
      console.log('浏览记录失败详情:', {
        message: err.message,
        stack: err.stack,
        toString: err.toString()
      })
    }
  },

  /**
   * 图片轮播变化
   */
  onImageChange(e) {
    this.setData({
      currentImageIndex: e.detail.current
    })
  },

  /**
   * 预览图片
   */
  previewImage(e) {
    const { url, urls } = e.currentTarget.dataset
    wx.previewImage({
      current: url,
      urls: urls
    })
  },

  /**
   * 收藏/取消收藏
   */
  async toggleFavorite() {
    try {
      if (this.data.isFavorite) {
        await api.delete(`/favorites/${this.data.propertyId}`)
        this.setData({ isFavorite: false })
        wx.showToast({
          title: '已取消收藏',
          icon: 'success'
        })
      } else {
        await api.post('/favorites/', {
          property_id: this.data.propertyId
        })
        this.setData({ isFavorite: true })
        wx.showToast({
          title: '收藏成功',
          icon: 'success'
        })
      }
    } catch (err) {
      console.error('收藏操作失败:', err)
      wx.showToast({
        title: err.message || '操作失败',
        icon: 'none'
      })
    }
  },

  /**
   * 分享
   */
  onShareAppMessage() {
    const { property } = this.data
    return {
      title: property ? `${property.title} - ${formatPrice(property.price)}` : '房源详情',
      path: `/pages/property/detail/detail?id=${this.data.propertyId}`,
      imageUrl: property && property.images.length > 0 ? property.images[0].url : ''
    }
  },

  /**
   * 分享到朋友圈
   */
  onShareTimeline() {
    const { property } = this.data
    return {
      title: property ? `${property.title} - ${formatPrice(property.price)}` : '房源详情',
      query: `id=${this.data.propertyId}`,
      imageUrl: property && property.images.length > 0 ? property.images[0].url : ''
    }
  },

  /**
   * 联系经纪人
   */
  contactAgent() {
    const { property } = this.data
    if (!property || !property.agent) {
      wx.showToast({
        title: '暂无经纪人信息',
        icon: 'none'
      })
      return
    }

    wx.showModal({
      title: '联系经纪人',
      content: `经纪人：${property.agent.nickname}\n电话：${property.agent.phone}`,
      confirmText: '拨打电话',
      success: (res) => {
        if (res.confirm) {
          wx.makePhoneCall({
            phoneNumber: property.agent.phone
          })
        }
      }
    })
  },

  /**
   * 预约看房
   */
  makeAppointment() {
    if (!this.data.propertyId) return

    wx.navigateTo({
      url: `/pages/property/appointment/appointment?propertyId=${this.data.propertyId}`
    })
  },

  /**
   * 查看地图位置
   */
  viewMap() {
    const { property } = this.data
    if (!property || !property.latitude || !property.longitude) {
      wx.showToast({
        title: '暂无位置信息',
        icon: 'none'
      })
      return
    }

    wx.openLocation({
      latitude: property.latitude,
      longitude: property.longitude,
      name: property.title || '房源位置',
      address: property.address || ''
    })
  },

  /**
   * 查看VR
   */
  viewVR() {
    const { property } = this.data
    if (!property || !property.vr_url) {
      wx.showToast({
        title: '暂无VR看房',
        icon: 'none'
      })
      return
    }

    wx.navigateTo({
      url: `/pages/property/vr/vr?url=${encodeURIComponent(property.vr_url)}`
    })
  },

  /**
   * 查看视频
   */
  viewVideo() {
    const { property } = this.data
    if (!property || !property.video_url) {
      wx.showToast({
        title: '暂无视频',
        icon: 'none'
      })
      return
    }

    wx.navigateTo({
      url: `/pages/property/video/video?url=${encodeURIComponent(property.video_url)}`
    })
  },

  /**
   * 编辑房源（仅经纪人）
   */
  editProperty() {
    wx.navigateTo({
      url: `/pages/property/edit/edit?id=${this.data.propertyId}`
    })
  }
})
