// 房源详情�?
const api = require('../../../utils/api')
const app = getApp()
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
        title: '房源不存�?,
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

      // 处理图片URL
      const baseUrl = app.globalData.baseUrl || 'http://127.0.0.1:8000/api/v1'
      const staticUrl = baseUrl.replace('/api/v1', '') + '/static'

      // 提取图片URL列表（后端返回的是字符串数组�?
      let imageUrls = []
      if (res.images && res.images.length > 0) {
        imageUrls = res.images.map(img => {
          let url = typeof img === 'string' ? img : (img.url || img.image_url || '')
          if (url && !url.startsWith('http')) {
            return staticUrl + url
          }
          return url
        })
      } else if (res.cover_url) {
        // 如果没有images，用cover_url
        let coverUrl = res.cover_url
        if (!coverUrl.startsWith('http')) {
          coverUrl = staticUrl + coverUrl
        }
        imageUrls = [coverUrl]
      }
      
      // 字段映射：API返回字段与页面所需字段对应
      let coverUrl = res.cover_url || (res.images && res.images[0] ? (typeof res.images[0] === 'string' ? res.images[0] : res.images[0].url || res.images[0].image_url) : '')
      if (coverUrl && !coverUrl.startsWith('http')) {
        res.cover_image_url = staticUrl + coverUrl
      }
      // 确保是http开头的网络请求
      if (res.cover_image_url && !res.cover_image_url.startsWith('http')) {
        res.cover_image_url = 'http://' + res.cover_image_url
      }
      res.price = res.total_price || 0;
      res.price_display = formatPrice(res.total_price);
      res.floor = (res.floor_info && typeof res.floor_info === 'string') ? res.floor_info.split('/')[0] : (res.floor || '--');
      res.total_floors = (res.floor_info && typeof res.floor_info === 'string') ? res.floor_info.split('/')[1] : (res.total_floors || '--');
      res.community_name = res.community || res.village || res.detail_address || ''
      res.address = res.detail_address || res.address || ''
      res.rooms = res.room_count || res.rooms || 0
      res.halls = res.hall_count || res.halls || 0
      res.bathrooms = res.bathroom_count || 0

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
   * 记录浏览行为（仅在登录时记录�?
   */
  async recordView(propertyId) {
    const token = wx.getStorageSync('token')
    if (!token) {
      return
    }

    try {
      const result = await api.post('/users/behaviors', {
        behavior_type: 1,
        target_type: 1,
        target_id: parseInt(propertyId)
      }, true)

    } catch (err) {

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
        await api.delete(`/favorites/properties/${this.data.propertyId}`)
        this.setData({ isFavorite: false })
        wx.showToast({
          title: '已取消收�?,
          icon: 'success'
        })
      } else {
        await api.post(`/favorites/properties/${this.data.propertyId}`, {
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
    const { property, imageUrls } = this.data
    const shareImage = imageUrls && imageUrls.length > 0 ? imageUrls[0] : ''
    return {
      title: property ? `${property.title} - ${formatPrice(property.price)}` : '房源详情',
      path: `/pages/property/detail/detail?id=${this.data.propertyId}`,
      imageUrl: shareImage
    }
  },

  /**
   * 分享到朋友圈
   */
  onShareTimeline() {
    const { property, imageUrls } = this.data
    const shareImage = imageUrls && imageUrls.length > 0 ? imageUrls[0] : ''
    return {
      title: property ? `${property.title} - ${formatPrice(property.price)}` : '房源详情',
      query: `id=${this.data.propertyId}`,
      imageUrl: shareImage
    }
  },

  /**
   * 联系经纪�?
   */
  contactAgent() {
    const { property } = this.data
    if (!property || !property.agent) {
      wx.showToast({
        title: '暂无经纪人信�?,
        icon: 'none'
      })
      return
    }

    wx.showModal({
      title: '联系经纪�?,
      content: `经纪人：${property.agent.nickname}\n电话�?{property.agent.phone}`,
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
    const videoUrl = property && (property.video_url || (property.video_urls && property.video_urls[0]))
    if (!videoUrl) {
      wx.showToast({
        title: '暂无视频',
        icon: 'none'
      })
      return
    }

    wx.navigateTo({
      url: `/pages/property/video/video?url=${encodeURIComponent(videoUrl)}`
    })
  },

  /**
   * 编辑房源（仅经纪人）
   */
  editProperty() {
    wx.navigateTo({
      url: `/pages/property/edit/edit?id=${this.data.propertyId}`
    })
  },

  /**
   * 查看评价
   */
  goToReview() {
    wx.navigateTo({
      url: '/pages/property/review/review?id=' + this.data.propertyId
    })
  },

  /**
   * 生成海报
   */
  goToPoster() {
    const property = encodeURIComponent(JSON.stringify(this.data.property))
    wx.navigateTo({
      url: '/pages/property/poster/poster?property=' + property
    })
  },

  onShareTap() {
    // 显示分享菜单
    wx.showShareMenu({
      withShareTicket: true,
      menus: ['shareAppMessage', 'shareTimeline']
    })
  },

  /**
   * 返回首页
   */
  goHome() {
    wx.switchTab({
      url: '/pages/index/index'
    })
  }
})
