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
      views: 0
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
        icon: '/assets/icons/calculator.png',
        title: '房贷计算器',
        url: '/pages/tools/calculator/calculator'
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

  /**
   * 页面加载
   */
  onLoad(options) {
    console.log('个人中心页加载')
  },

  /**
   * 页面显示
   */
  onShow() {
    this.checkLoginStatus()
  },

  /**
   * 检查登录状态
   */
  checkLoginStatus() {
    const isLogin = app.globalData.isLogin
    const userInfo = app.globalData.userInfo

    this.setData({
      isLogin,
      userInfo
    })
  },

  /**
   * 去登录
   */
  goToLogin() {
    wx.navigateTo({
      url: '/pages/login/login'
    })
  },

  /**
   * 菜单点击
   */
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

  /**
   * 跳转收藏页
   */
  goToFavorites() {
    wx.navigateTo({
      url: '/pages/user/favorites/favorites'
    })
  },

  /**
   * 跳转预约页
   */
  goToAppointments() {
    wx.navigateTo({
      url: '/pages/user/appointments/appointments'
    })
  },

  /**
   * 跳转浏览历史页
   */
  goToHistory() {
    wx.showToast({
      title: '浏览历史功能开发中',
      icon: 'none'
    })
  },

  /**
   * 退出登录
   */
  handleLogout() {
    wx.showModal({
      title: '提示',
      content: '确定要退出登录吗？',
      success: (res) => {
        if (res.confirm) {
          // 清除登录信息
          app.clearLoginInfo()

          // 更新页面状态
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

  /**
   * 跳转编辑资料
   */
  goToEdit() {
    if (!this.data.isLogin) {
      this.goToLogin()
      return
    }

    wx.navigateTo({
      url: '/pages/user/edit/edit'
    })
  },

  /**
   * 分享
   */
  onShareAppMessage() {
    return {
      title: '县域房产信息平台',
      path: '/pages/index/index'
    }
  }
})
