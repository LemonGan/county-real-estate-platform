// 看房预约页
const api = require('../../../utils/api')
const { formatDate } = require('../../../utils/format')

Page({
  data: {
    appointments: [],
    loading: true,
    empty: false,
    activeTab: 'all', // all, pending, completed, cancelled
    tabs: [
      { key: 'all', label: '全部' },
      { key: 'pending', label: '待确认' },
      { key: 'confirmed', label: '已确认' },
      { key: 'completed', label: '已完成' },
      { key: 'cancelled', label: '已取消' }
    ]
  },

  /**
   * 页面加载
   */
  onLoad(options) {
    // 处理 status 参数（1=待处理/待确认，2=已确认）
    if (options.status) {
      const statusMap = { '1': 'pending', '2': 'confirmed', '3': 'completed', '4': 'cancelled' }
      const status = statusMap[options.status]
      if (status) {
        this.setData({ activeTab: status })
      }
    }
    this.loadAppointments()
  },

  /**
   * 页面显示
   */
  onShow() {
    this.loadAppointments()
  },

  /**
   * 切换标签
   */
  switchTab(e) {
    const { key } = e.currentTarget.dataset
    this.setData({ activeTab: key })
    this.loadAppointments()
  },

  /**
   * 加载预约列表
   */
  async loadAppointments() {
    this.setData({ loading: true })

    try {
      const params = {}
      if (this.data.activeTab !== 'all') {
        params.status = this.data.activeTab
      }

      const res = await api.get('/appointments/', params)

      this.setData({
        appointments: res.items || res,
        loading: false,
        empty: (!res.items || res.items.length === 0) && (!res || res.length === 0)
      })
    } catch (err) {
      console.error('加载预约失败:', err)
      this.setData({
        loading: false,
        empty: true
      })

      wx.showToast({
        title: err.message || '加载失败',
        icon: 'none'
      })
    }
  },

  /**
   * 跳转房源详情
   */
  goToDetail(e) {
    const { id } = e.currentTarget.dataset
    wx.navigateTo({
      url: `/pages/property/detail/detail?id=${id}`
    })
  },

  /**
   * 跳转预约详情
   */
  goToAppointmentDetail(e) {
    const { id } = e.currentTarget.dataset
    wx.navigateTo({
      url: `/pages/property/appointment-detail/appointment-detail?id=${id}`
    })
  },

  /**
   * 取消预约
   */
  cancelAppointment(e) {
    const { id, index } = e.currentTarget.dataset

    wx.showModal({
      title: '提示',
      content: '确定要取消预约吗？',
      success: async (res) => {
        if (res.confirm) {
          try {
            await api.put(`/appointments/${id}/cancel`)

            // 更新列表状态
            const appointments = this.data.appointments
            appointments[index].status = 'cancelled'

            this.setData({ appointments })

            wx.showToast({
              title: '已取消预约',
              icon: 'success'
            })
          } catch (err) {
            console.error('取消预约失败:', err)
            wx.showToast({
              title: err.message || '操作失败',
              icon: 'none'
            })
          }
        }
      }
    })
  },

  /**
   * 联系经纪人
   */
  contactAgent(e) {
    const { phone } = e.currentTarget.dataset
    if (!phone) {
      wx.showToast({
        title: '暂无电话信息',
        icon: 'none'
      })
      return
    }

    wx.showModal({
      title: '拨打电话',
      content: phone,
      confirmText: '拨打',
      success: (res) => {
        if (res.confirm) {
          wx.makePhoneCall({
            phoneNumber: phone
          })
        }
      }
    })
  },

  /**
   * 重新预约
   */
  rebook(e) {
    const { propertyId } = e.currentTarget.dataset
    wx.navigateTo({
      url: `/pages/property/appointment/appointment?propertyId=${propertyId}`
    })
  },

  /**
   * 获取状态文本
   */
  getStatusText(status) {
    const statusMap = {
      'pending': '待确认',
      'confirmed': '已确认',
      'completed': '已完成',
      'cancelled': '已取消'
    }
    return statusMap[status] || status
  },

  /**
   * 获取状态样式
   */
  getStatusClass(status) {
    const classMap = {
      'pending': 'status-pending',
      'confirmed': 'status-confirmed',
      'completed': 'status-completed',
      'cancelled': 'status-cancelled'
    }
    return classMap[status] || ''
  },

  /**
   * 下拉刷新
   */
  onPullDownRefresh() {
    this.loadAppointments().then(() => {
      wx.stopPullDownRefresh()
    })
  },

  /**
   * 去逛逛（跳转到房源列表）
   */
  goToList() {
    wx.switchTab({
      url: '/pages/property/list/list'
    })
  },

  /**
   * 分享
   */
  onShareAppMessage() {
    return {
      title: '我的预约 - 县域房产平台',
      path: '/pages/user/appointments/appointments'
    }
  }
})
