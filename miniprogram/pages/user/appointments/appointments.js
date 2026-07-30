// 看房预约页
const api = require('../../../utils/api')

Page({
  data: {
    appointments: [],
    loading: true,
    empty: false,
    appointmentScope: 'user',
    activeTab: 'all',
    tabs: [
      { key: 'all', label: '全部' },
      { key: 'pending', label: '待确认' },
      { key: 'confirmed', label: '已确认' },
      { key: 'completed', label: '已完成' },
      { key: 'cancelled', label: '已取消' }
    ]
  },

  onLoad(options) {
    const appointmentScope = options.scope === 'agent' ? 'agent' : 'user'
    const statusMap = { '0': 'cancelled', '1': 'pending', '2': 'confirmed', '3': 'completed' }
    this.setData({
      appointmentScope,
      activeTab: statusMap[options.status] || 'all'
    })
    wx.setNavigationBarTitle({ title: appointmentScope === 'agent' ? '接待预约' : '我的预约' })
    this.loadAppointments()
  },

  onShow() {
    this.loadAppointments()
  },

  switchTab(e) {
    this.setData({ activeTab: e.currentTarget.dataset.key })
    this.loadAppointments()
  },

  async loadAppointments() {
    this.setData({ loading: true })
    try {
      const params = { view: this.data.appointmentScope }
      const statusCodes = { pending: 1, confirmed: 2, completed: 3, cancelled: 0 }
      if (this.data.activeTab !== 'all') params.status = statusCodes[this.data.activeTab]
      const res = await api.get('/appointments/', params)
      const statusMeta = {
        0: { text: '已取消', className: 'status-cancelled' },
        1: { text: '待确认', className: 'status-pending' },
        2: { text: '已确认', className: 'status-confirmed' },
        3: { text: '已完成', className: 'status-completed' }
      }
      const isAgentView = this.data.appointmentScope === 'agent'
      const appointments = (res.list || []).map((item) => {
        const agentAction = isAgentView && item.status === 1
          ? { label: '确认预约', nextStatus: 2 }
          : isAgentView && item.status === 2
            ? { label: '完成看房', nextStatus: 3 }
            : null
        return {
          ...item,
          statusMeta: statusMeta[item.status] || statusMeta[1],
          cancellable: !isAgentView && (item.status === 1 || item.status === 2),
          rebookable: !isAgentView && item.status === 0,
          agentAction,
          contactTargetPhone: isAgentView ? item.contact_phone : (item.agent && item.agent.phone),
          contactTargetLabel: isAgentView ? '联系客户' : '联系经纪人'
        }
      })
      this.setData({ appointments, loading: false, empty: appointments.length === 0 })
    } catch (err) {
      console.error('加载预约失败:', err)
      this.setData({ loading: false, empty: true })
      wx.showToast({ title: err.message || '加载失败', icon: 'none' })
    }
  },

  goToDetail(e) {
    const { id } = e.currentTarget.dataset
    if (id) wx.navigateTo({ url: `/pages/property/detail/detail?id=${id}` })
  },

  cancelAppointment(e) {
    const { id } = e.currentTarget.dataset
    wx.showModal({
      title: '取消预约',
      content: '确定要取消本次预约吗？',
      success: async (res) => {
        if (!res.confirm) return
        try {
          await api.del(`/appointments/${id}`)
          await this.loadAppointments()
          wx.showToast({ title: '已取消预约', icon: 'success' })
        } catch (err) {
          wx.showToast({ title: err.message || '操作失败', icon: 'none' })
        }
      }
    })
  },

  updateAppointmentStatus(e) {
    const { id, nextStatus, label } = e.currentTarget.dataset
    wx.showModal({
      title: label,
      content: `确定要${label}吗？`,
      success: async (res) => {
        if (!res.confirm) return
        try {
          await api.put(`/appointments/${id}/status?new_status=${nextStatus}`)
          await this.loadAppointments()
          wx.showToast({ title: '操作成功', icon: 'success' })
        } catch (err) {
          wx.showToast({ title: err.message || '操作失败', icon: 'none' })
        }
      }
    })
  },

  contactTarget(e) {
    const { phone, label } = e.currentTarget.dataset
    if (!phone) {
      wx.showToast({ title: '暂无电话信息', icon: 'none' })
      return
    }
    wx.showModal({
      title: label || '拨打电话',
      content: phone,
      confirmText: '拨打',
      success: (res) => {
        if (res.confirm) wx.makePhoneCall({ phoneNumber: phone })
      }
    })
  },

  rebook(e) {
    const { propertyId } = e.currentTarget.dataset
    wx.navigateTo({ url: `/pages/property/appointment/appointment?propertyId=${propertyId}` })
  },

  onPullDownRefresh() {
    this.loadAppointments().finally(() => wx.stopPullDownRefresh())
  },

  goToList() {
    wx.switchTab({ url: '/pages/property/list/list' })
  },

  onShareAppMessage() {
    return { title: '我的预约 - 县域房产平台', path: '/pages/user/appointments/appointments' }
  }
})
