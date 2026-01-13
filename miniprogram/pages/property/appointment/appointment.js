// 预约看房页
const api = require('../../../utils/api')

Page({
  data: {
    propertyId: null,
    property: null,
    loading: true,

    // 表单数据
    appointmentDate: '',
    appointmentTime: '',
    contactName: '',
    contactPhone: '',
    remark: '',

    // 时间选项
    timeOptions: [
      '09:00', '10:00', '11:00', '12:00',
      '13:00', '14:00', '15:00', '16:00',
      '17:00', '18:00', '19:00', '20:00'
    ],

    // 最小日期（今天）
    minDate: '',
    submitting: false
  },

  /**
   * 页面加载
   */
  onLoad(options) {
    const { propertyId } = options
    if (propertyId) {
      this.setData({ propertyId })
      this.loadPropertyInfo(propertyId)
    }

    // 设置最小日期
    const today = new Date()
    const minDate = this.formatDateForInput(today)
    this.setData({ minDate })
  },

  /**
   * 加载房源信息
   */
  async loadPropertyInfo(id) {
    this.setData({ loading: true })

    try {
      const res = await api.get(`/properties/${id}`)
      this.setData({
        property: res,
        loading: false
      })
    } catch (err) {
      console.error('加载房源信息失败:', err)
      this.setData({ loading: false })
      wx.showToast({
        title: err.message || '加载失败',
        icon: 'none'
      })
    }
  },

  /**
   * 格式化日期供picker使用
   */
  formatDateForInput(date) {
    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    return `${year}-${month}-${day}`
  },

  /**
   * 日期选择
   */
  onDateChange(e) {
    this.setData({
      appointmentDate: e.detail.value
    })
  },

  /**
   * 时间选择
   */
  onTimeChange(e) {
    this.setData({
      appointmentTime: e.detail.value
    })
  },

  /**
   * 输入变化
   */
  onInputChange(e) {
    const { field } = e.currentTarget.dataset
    this.setData({
      [field]: e.detail.value
    })
  },

  /**
   * 验证表单
   */
  validateForm() {
    const { appointmentDate, appointmentTime, contactName, contactPhone } = this.data

    if (!appointmentDate) {
      wx.showToast({
        title: '请选择预约日期',
        icon: 'none'
      })
      return false
    }

    if (!appointmentTime) {
      wx.showToast({
        title: '请选择预约时间',
        icon: 'none'
      })
      return false
    }

    if (!contactName.trim()) {
      wx.showToast({
        title: '请输入联系人姓名',
        icon: 'none'
      })
      return false
    }

    if (!contactPhone.trim()) {
      wx.showToast({
        title: '请输入联系电话',
        icon: 'none'
      })
      return false
    }

    // 验证手机号格式
    const phonePattern = /^1[3-9]\d{9}$/
    if (!phonePattern.test(contactPhone)) {
      wx.showToast({
        title: '请输入正确的手机号',
        icon: 'none'
      })
      return false
    }

    return true
  },

  /**
   * 提交预约
   */
  async submitAppointment() {
    if (!this.validateForm()) {
      return
    }

    this.setData({ submitting: true })

    try {
      const { propertyId, appointmentDate, appointmentTime, contactName, contactPhone, remark } = this.data

      // 组合日期和时间
      const appointmentTimeFull = `${appointmentDate} ${appointmentTime}:00`

      await api.post('/appointments/', {
        property_id: propertyId,
        appointment_time: appointmentTimeFull,
        contact_name: contactName,
        contact_phone: contactPhone,
        remark: remark || null
      })

      wx.showToast({
        title: '预约成功',
        icon: 'success'
      })

      setTimeout(() => {
        wx.navigateBack()
      }, 1500)
    } catch (err) {
      console.error('预约失败:', err)
      wx.showToast({
        title: err.message || '预约失败',
        icon: 'none'
      })
    } finally {
      this.setData({ submitting: false })
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
  }
})
