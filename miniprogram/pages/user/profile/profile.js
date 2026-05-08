// 用户个人中心�?const app = getApp()
const api = require('../../../utils/api')

Page({
  data: {
    userInfo: null,
    isLogin: false,
    stats: {
      favorites: 0,
      appointments: 0,
      views: 0
    },
    menuList: [
      {
        icon: '/assets/icons/vip.png',
        title: '会员中心',
        url: '/pages/user/member/member'
      },
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
        icon: '/assets/icons/calculator.png',
        title: '房贷计算�?,
        url: '/pages/tools/calculator/calculator'
      },
      {
        icon: '/assets/icons/work.png',
        title: '申请成为经纪�?,
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

  },

  onShow() {
    this.checkLoginStatus()
  },

  checkLoginStatus() {
    const isLogin = app.globalData.isLogin
    const userInfo = app.globalData.userInfo

    this.setData({
      isLogin,
      userInfo
    })
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
    wx.showToast({
      title: '浏览历史功能开发中',
      icon: 'none'
    })
  },

  handleLogout() {
    wx.showModal({
      title: '提示',
      content: '确定要退出登录吗�?,
      success: (res) => {
        if (res.confirm) {
          app.clearLoginInfo()
          this.setData({
            isLogin: false,
            userInfo: null
          })
          wx.showToast({
            title: '已退出登�?,
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
