// pages/agent/detail/detail.js
const api = require('../../../utils/api.js')
const app = getApp()

Page({
  data: {
    agentId: null,
    agent: null,
    properties: [],
    loading: true,
    isFollowed: false,
    currentPage: 1,
    hasMore: true
  },

  onLoad(options) {
    const { id } = options
    if (id) {
      this.setData({ agentId: id })
      this.loadAgentDetail()
    } else {
      wx.showToast({
        title: '经纪人不存在',
        icon: 'none'
      })
      setTimeout(() => {
        wx.navigateBack()
      }, 1500)
    }
  },

  onShareAppMessage() {
    const { agent } = this.data
    return {
      title: agent ? `${agent.nickname} - 金牌经纪人` : '经纪人主页',
      path: `/pages/agent/detail/detail?id=${this.data.agentId}`,
      imageUrl: agent ? agent.avatar_url : ''
    }
  },

  // 加载经纪人详情
  async loadAgentDetail() {
    this.setData({ loading: true })

    try {
      // 调用经纪人详情API
      const res = await api.get(`/agents/${this.data.agentId}/`, {}, false)

      this.setData({
        agent: res,
        loading: false
      })

      // 加载经纪人房源
      this.loadAgentProperties()
    } catch (error) {
      console.error('加载经纪人详情失败:', error)
      this.setData({ loading: false })
      wx.showToast({
        title: '加载失败',
        icon: 'none'
      })
    }
  },

  // 加载经纪人房源
  async loadAgentProperties() {
    try {
      const res = await api.get('/properties/', {
        page: this.data.currentPage,
        page_size: 10,
        agent_id: this.data.agentId,
        status_filter: 1
      }, false)

      this.setData({
        properties: res.list || [],
        hasMore: (res.list || []).length >= 10
      })
    } catch (error) {
      console.error('加载经纪人房源失败:', error)
    }
  },

  // 关注经纪人
  async followAgent() {
    if (!app.globalData.isLogin) {
      wx.navigateTo({
        url: '/pages/login/login'
      })
      return
    }

    try {
      // TODO: 实现关注API
      // await api.post(`/agents/${this.data.agentId}/follow/`)

      this.setData({
        isFollowed: !this.data.isFollowed
      })

      wx.showToast({
        title: this.data.isFollowed ? '已关注' : '已取消关注',
        icon: 'success'
      })
    } catch (error) {
      console.error('关注失败:', error)
    }
  },

  // 联系经纪人
  contactAgent() {
    const { agent } = this.data
    if (!agent) return

    wx.showModal({
      title: '联系经纪人',
      content: `经纪人：${agent.nickname}\n电话：${agent.phone}`,
      confirmText: '拨打电话',
      success: (res) => {
        if (res.confirm) {
          wx.makePhoneCall({
            phoneNumber: agent.phone
          })
        }
      }
    })
  },

  // 查看房源详情
  goToPropertyDetail(e) {
    const propertyId = e.currentTarget.dataset.id
    wx.navigateTo({
      url: `/pages/property/detail/detail?id=${propertyId}`
    })
  },

  // 在线咨询
  startChat() {
    if (!app.globalData.isLogin) {
      wx.navigateTo({
        url: '/pages/login/login'
      })
      return
    }

    wx.showToast({
      title: '咨询功能即将上线',
      icon: 'none'
    })
  },

  // 查看更多房源
  loadMore() {
    if (this.data.hasMore && !this.data.loading) {
      this.setData({ currentPage: this.data.currentPage + 1 })
      this.loadAgentProperties()
    }
  }
})
