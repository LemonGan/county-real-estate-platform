// 成为经纪人申请页面
const app = getApp()
const api = require('../../../utils/api')

Page({
  data: {
    realName: '',
    idCard: '',
    agentLicense: '',
    company: '',
    phone: '',
    loading: false
  },

  onLoad() {
    const userInfo = app.globalData.userInfo
    if (userInfo && userInfo.is_agent) {
      wx.showModal({
        title: '提示',
        content: '您已经是经纪人了，是否前往工作台？',
        success: (res) => {
          if (res.confirm) {
            wx.switchTab({
              url: '/pages/agent/workbench/workbench'
            })
          }
        }
      })
    }
  },

  onInput(e) {
    const field = e.currentTarget.dataset.field
    this.setData({
      [field]: e.detail.value
    })
  },

  async submit() {
    const { realName, idCard, agentLicense, company, phone } = this.data

    if (!realName) {
      wx.showToast({ title: '请输入真实姓名', icon: 'none' })
      return
    }
    if (!idCard || idCard.length !== 18) {
      wx.showToast({ title: '请输入正确的身份证号', icon: 'none' })
      return
    }
    if (!agentLicense) {
      wx.showToast({ title: '请输入执业证号', icon: 'none' })
      return
    }
    if (!company) {
      wx.showToast({ title: '请输入所属公司', icon: 'none' })
      return
    }
    if (!phone || phone.length !== 11) {
      wx.showToast({ title: '请输入正确的手机号', icon: 'none' })
      return
    }

    this.setData({ loading: true })

    try {
      const res = await api.post('/agent-auth/apply', {
        real_name: realName,
        id_card: idCard,
        agent_license: agentLicense,
        company: company,
        phone: phone
      }, true)

      wx.showModal({
        title: '申请已提交',
        content: (res && res.message) || '资料已提交，等待后台审核通过后即可使用经纪人工作台。',
        showCancel: false,
        success: () => wx.navigateBack()
      })

    } catch (err) {
      wx.showToast({
        title: err.message || '申请失败',
        icon: 'none'
      })
    } finally {
      this.setData({ loading: false })
    }
  }
})
