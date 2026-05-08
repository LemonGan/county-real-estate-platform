// 会员中心页面
const app = getApp()
const api = require('../../../utils/api')

Page({
  data: {
    userInfo: null,
    isMember: false,
    memberLevel: 0,
    memberTag: '',
    daysRemaining: 0,
    exchangeCode: ''
  },

  onLoad() {
    this.setData({
      userInfo: app.globalData.userInfo
    })
  },

  onShow() {
    if (app.globalData.isLogin) {
      this.checkMemberStatus()
    }
  },

  async checkMemberStatus() {
    try {
      const res = await api.get('/member/status', {}, true)
      this.setData({
        isMember: res.is_member,
        memberLevel: res.member_level,
        daysRemaining: res.days_remaining,
        memberTag: this.getMemberTag(res.member_level)
      })
    } catch (err) {
      console.log('检查会员状态失败:', err)
    }
  },

  getMemberTag(level) {
    const tags = {1: '月卡会员', 2: '季卡会员', 3: '年卡会员'}
    return tags[level] || ''
  },

  onInputCode(e) {
    this.setData({
      exchangeCode: e.detail.value
    })
  },

  async buyMember(e) {
    const level = e.currentTarget.dataset.level
    const prices = {1: '9.9元', 2: '19.9元', 3: '59.9元'}
    
    wx.showModal({
      title: '确认开通',
      content: `确定花费${prices[level]}开通会员？`,
      success: async (res) => {
        if (res.confirm) {
          await this.doBuyMember(level)
        }
      }
    })
  },

  async doBuyMember(level) {
    wx.showLoading({title: '开通中...'})
    
    try {
      const res = await api.post('/member/buy', {level: level}, true)
      wx.hideLoading()
      
      wx.showToast({title: '开通成功', icon: 'success'})
      
      this.checkMemberStatus()
      
    } catch (err) {
      wx.hideLoading()
      wx.showToast({
        title: err.message || '开通失败',
        icon: 'none'
      })
    }
  },

  async exchangeMember() {
    const code = this.data.exchangeCode.trim()
    
    if (!code) {
      wx.showToast({title: '请输入兑换码', icon: 'none'})
      return
    }
    
    wx.showLoading({title: '兑换中...'})
    
    try {
      const res = await api.post('/member/exchange', {code: code}, true)
      wx.hideLoading()
      
      wx.showToast({title: '兑换成功', icon: 'success'})
      
      this.setData({exchangeCode: ''})
      this.checkMemberStatus()
      
    } catch (err) {
      wx.hideLoading()
      wx.showToast({
        title: err.message || '兑换失败',
        icon: 'none'
      })
    }
  }
})
