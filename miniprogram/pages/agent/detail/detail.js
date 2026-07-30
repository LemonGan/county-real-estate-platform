const api = require('../../../utils/api.js')
const app = getApp()

Page({
  data: {
    agentId: null,
    agent: null,
    properties: [],
    loading: true,
    loadingMore: false,
    loadError: false,
    currentPage: 1,
    hasMore: true
  },

  onLoad(options) {
    if (!options.id) {
      this.setData({ loading: false, loadError: true })
      return
    }
    this.setData({ agentId: options.id })
    this.loadAgentDetail()
  },

  imageUrl(value) {
    if (!value || value.startsWith('http')) return value || '/assets/images/default-property.png'
    const origin = (app.globalData.baseUrl || '').replace('/api/v1', '')
    return value.startsWith('/static/') ? origin + value : origin + '/static' + value
  },

  async loadAgentDetail() {
    this.setData({ loading: true, loadError: false })
    try {
      const agent = await api.get(`/agents/${this.data.agentId}`, {}, false)
      this.setData({ agent, loading: false })
      this.loadAgentProperties()
    } catch (error) {
      console.error('加载经纪人详情失败:', error)
      this.setData({ loading: false, loadError: true })
    }
  },

  async loadAgentProperties(loadMore = false) {
    if (this.data.loadingMore) return
    this.setData({ loadingMore: true })
    const page = loadMore ? this.data.currentPage + 1 : 1
    try {
      const res = await api.get(`/agents/${this.data.agentId}/properties`, { page, page_size: 10, status_filter: 1 }, false)
      const list = (res.list || []).map((item) => ({
        ...item,
        displayImage: this.imageUrl(item.cover_url || (item.images && item.images[0])),
        priceText: item.total_price ? `${(item.total_price / 10000).toFixed(1)}万` : '待议'
      }))
      this.setData({
        properties: loadMore ? [...this.data.properties, ...list] : list,
        currentPage: page,
        hasMore: page * 10 < (res.total || 0),
        loadingMore: false
      })
    } catch (error) {
      console.error('加载经纪人房源失败:', error)
      this.setData({ loadingMore: false })
    }
  },

  goToPropertyDetail(e) {
    wx.navigateTo({ url: `/pages/property/detail/detail?id=${e.currentTarget.dataset.id}` })
  },

  loadMore() {
    if (this.data.hasMore) this.loadAgentProperties(true)
  },

  goBack() { wx.navigateBack() },

  onShareAppMessage() {
    const { agent } = this.data
    return {
      title: agent ? `${agent.nickname}的房源` : '经纪人主页',
      path: `/pages/agent/detail/detail?id=${this.data.agentId}`,
      imageUrl: agent && agent.avatar_url || ''
    }
  }
})
