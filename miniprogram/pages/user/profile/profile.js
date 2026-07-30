// 用户个人中心页
const app = getApp()
const api = require('../../../utils/api')

Page({
  data: {
    userInfo: null,
    isLogin: false,
    stats: {
      favorites: 0,
      appointments: 0,
      views: 0,
      messages: 0
    },
    menuList: [
      {
        icon: '/assets/icons/favorites.png',
        title: '我的收藏',
        url: '/pages/user/favorites/favorites'
      },
      {
        icon: '/assets/icons/appointment.png',
        title: '看房预约',
        url: '/pages/user/appointments/appointments'
      },
      {
        icon: '/assets/icons/chat.png',
        title: '消息通知',
        url: '/pages/user/messages/messages',
        badge: 0
      },
      {
        icon: '/assets/icons/calculator.png',
        title: '房贷计算器',
        url: '/pages/tools/calculator/calculator'
      },
      {
        icon: '/assets/icons/work.png',
        title: '申请成为经纪人',
        url: '/pages/user/agent-apply/agent-apply'
      },
      {
        icon: '/assets/icons/setting.png',
        title: '设置',
        url: '/pages/user/setting/setting'
      },
      {
        icon: '/assets/icons/about.png',
        title: '关于我们',
        url: '/pages/user/about/about'
      }
    ]
  },

  onLoad(options) {
    console.log('个人中心页加载')
  },

  onShow() {
    this.checkLoginStatus()
    if (app.globalData.isLogin) {
      this.refreshUserInfo()
      this.loadStats()
    }
  },

  async loadStats() {
    const [favorites, appointments, behaviors, messages] = await Promise.allSettled([
      api.get('/favorites/', { page: 1, page_size: 1 }),
      api.get('/appointments/', { page: 1, page_size: 1 }),
      api.get('/users/behaviors/stats', { days: 30 }),
      api.get('/messages/unread-count')
    ])
    const value = (result, fallback) => result.status === 'fulfilled' ? result.value : fallback
    const favoriteData = value(favorites, { total: 0 })
    const appointmentData = value(appointments, { total: 0 })
    const behaviorData = value(behaviors, { behavior_type: { view: 0 } })
    const messageData = value(messages, { unread_count: 0 })
    const unreadMessages = messageData.unread_count || 0
    this.setData({
      stats: {
        favorites: favoriteData.total || 0,
        appointments: appointmentData.total || 0,
        views: (behaviorData.behavior_type && behaviorData.behavior_type.view) || 0,
        messages: unreadMessages
      },
      menuList: this.data.menuList.map((item) => item.url === '/pages/user/messages/messages'
        ? { ...item, badge: unreadMessages > 99 ? '99+' : unreadMessages }
        : item)
    })
  },

  async refreshUserInfo() {
    try {
      const user = await api.get('/users/me')
      app.globalData.userInfo = user
      wx.setStorageSync('userInfo', user)
      this.setData({ userInfo: this.formatUserInfo(user), isLogin: true })
    } catch (err) {
      console.log('用户资料刷新失败:', err.message)
    }
  },

  formatUserInfo(userInfo) {
    if (!userInfo) return null
    const avatar = userInfo.avatar || ''
    const origin = (app.globalData.baseUrl || '').replace('/api/v1', '')
    const avatarDisplay = avatar && !avatar.startsWith('http') && avatar.startsWith('/static/') ? origin + avatar : avatar
    return { ...userInfo, avatarDisplay }
  },

  checkLoginStatus() {
    const isLogin = app.globalData.isLogin
    const userInfo = this.formatUserInfo(app.globalData.userInfo)
    this.setData({ isLogin, userInfo })
  },

  goToLogin() {
    wx.navigateTo({
      url: '/pages/login/login'
    })
  },

  onMenuClick(e) {
    const { url } = e.currentTarget.dataset

    if (!this.data.isLogin) {
      wx.showToast({
        title: '请先登录',
        icon: 'none'
      })
      setTimeout(() => {
        this.goToLogin()
      }, 1500)
      return
    }

    wx.navigateTo({
      url: url
    })
  },

  goToFavorites() {
    wx.navigateTo({
      url: '/pages/user/favorites/favorites'
    })
  },

  goToAppointments() {
    wx.navigateTo({
      url: '/pages/user/appointments/appointments'
    })
  },

  goToHistory() {
    wx.navigateTo({ url: '/pages/user/history/history' })
  },

  handleLogout() {
    wx.showModal({
      title: '提示',
      content: '确定要退出登录吗？',
      success: (res) => {
        if (res.confirm) {
          app.clearLoginInfo()
          this.setData({
            isLogin: false,
            userInfo: null
          })
          wx.showToast({
            title: '已退出登录',
            icon: 'success'
          })
        }
      }
    })
  },

  goToEdit() {
    if (!this.data.isLogin) {
      this.goToLogin()
      return
    }
    wx.navigateTo({
      url: '/pages/user/edit/edit'
    })
  },

  onShareAppMessage() {
    return {
      title: '县域房产信息平台',
      path: '/pages/index/index'
    }
  }
})
