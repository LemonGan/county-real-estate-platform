// 关于我们页
Page({
  data: {
    version: '1.0.0',
    appName: '县域房产信息平台',
    intro: '专注县域房产信息服务，为三四线城市和县城用户提供真实、可靠的房源信息和专业的房产咨询服务。',
    features: [
      {
        icon: '/assets/icons/feature-1.png',
        title: '真实房源',
        desc: '严格审核房源信息，确保真实可靠'
      },
      {
        icon: '/assets/icons/feature-2.png',
        title: 'VR看房',
        desc: '足不出户，在线沉浸式看房体验'
      },
      {
        icon: '/assets/icons/feature-3.png',
        title: '智能推荐',
        desc: 'AI算法精准匹配您的购房需求'
      },
      {
        icon: '/assets/icons/feature-4.png',
        title: '专业服务',
        desc: '金牌经纪人一对一专属服务'
      }
    ],
    contacts: [
      { icon: '/assets/icons/phone.png', label: '客服电话', value: '400-123-4567' },
      { icon: '/assets/icons/email.png', label: '邮箱', value: 'service@example.com' },
      { icon: '/assets/icons/wechat.png', label: '微信公众号', value: '县域房产' },
      { icon: '/assets/icons/website.png', label: '官网', value: 'www.example.com' }
    ]
  },

  /**
   * 页面加载
   */
  onLoad() {

  },

  /**
   * 联系客服
   */
  contactService() {
    wx.showModal({
      title: '联系客服',
      content: '客服电话：400-123-4567\n工作时间：9:00-18:00',
      confirmText: '拨打电话',
      success: (res) => {
        if (res.confirm) {
          wx.makePhoneCall({
            phoneNumber: '4001234567'
          })
        }
      }
    })
  },

  /**
   * 复制文本
   */
  copyText(e) {
    const { text } = e.currentTarget.dataset
    wx.setClipboardData({
      data: text,
      success: () => {
        wx.showToast({
          title: '复制成功',
          icon: 'success'
        })
      }
    })
  },

  /**
   * 分享
   */
  onShareAppMessage() {
    return {
      title: this.data.appName,
      path: '/pages/index/index'
    }
  }
})
