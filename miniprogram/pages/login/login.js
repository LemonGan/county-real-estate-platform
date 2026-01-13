// 登录页
const app = getApp()
const api = require('../../utils/api')

Page({
  data: {
    phone: '',
    password: '',
    code: '',
    isWechatLogin: false
  },

  /**
   * 页面加载
   */
  onLoad(options) {
    // 检查是否已登录
    if (app.globalData.isLogin) {
      wx.navigateBack()
    }
  },

  /**
   * 输入框变化
   */
  onInputChange(e) {
    const { field } = e.currentTarget.dataset
    this.setData({
      [field]: e.detail.value
    })
  },

  /**
   * 切换登录方式
   */
  switchLoginType() {
    this.setData({
      isWechatLogin: !this.data.isWechatLogin
    })
  },

  /**
   * 手机号密码登录
   */
  async handleLogin() {
    const { phone, password } = this.data

    // 验证手机号
    if (!phone) {
      wx.showToast({
        title: '请输入手机号',
        icon: 'none'
      })
      return
    }

    if (!/^1[3-9]\d{9}$/.test(phone)) {
      wx.showToast({
        title: '手机号格式不正确',
        icon: 'none'
      })
      return
    }

    // 验证密码
    if (!password) {
      wx.showToast({
        title: '请输入密码',
        icon: 'none'
      })
      return
    }

    if (password.length < 6) {
      wx.showToast({
        title: '密码至少6位',
        icon: 'none'
      })
      return
    }

    try {
      const res = await api.post('/auth/login', {
        phone: phone,
        password: password
      }, false)

      // 保存登录信息
      app.setLoginInfo(res.access_token, {
        id: res.user_id,
        phone: phone
      })

      wx.showToast({
        title: '登录成功',
        icon: 'success'
      })

      setTimeout(() => {
        wx.switchTab({
          url: '/pages/index/index'
        })
      }, 1500)
    } catch (err) {
      console.error('登录失败:', err)
    }
  },

  /**
   * 微信授权登录
   */
  async handleWechatLogin() {
    const { code } = this.data

    if (!code) {
      wx.showToast({
        title: '获取授权信息失败',
        icon: 'none'
      })
      return
    }

    try {
      // 获取用户信息
      const userInfo = await this.getUserProfile()

      const res = await api.post('/auth/wechat/login', {
        code: code,
        nickname: userInfo.nickName,
        avatar: userInfo.avatarUrl
      }, false)

      // 保存登录信息
      app.setLoginInfo(res.access_token, {
        id: res.user_id,
        nickname: userInfo.nickName,
        avatar: userInfo.avatarUrl
      })

      wx.showToast({
        title: res.is_new_user ? '注册成功' : '登录成功',
        icon: 'success'
      })

      setTimeout(() => {
        wx.switchTab({
          url: '/pages/index/index'
        })
      }, 1500)
    } catch (err) {
      console.error('微信登录失败:', err)
    }
  },

  /**
   * 获取微信用户信息
   */
  getUserProfile() {
    return new Promise((resolve, reject) => {
      wx.getUserProfile({
        desc: '用于完善用户资料',
        success: (res) => {
          resolve(res.userInfo)
        },
        fail: (err) => {
          wx.showToast({
            title: '需要授权才能登录',
            icon: 'none'
          })
          reject(err)
        }
      })
    })
  },

  /**
   * 获取微信code
   */
  getWechatCode() {
    return new Promise((resolve, reject) => {
      wx.login({
        success: (res) => {
          if (res.code) {
            this.setData({ code: res.code })
            resolve(res.code)
          } else {
            reject(new Error('获取微信code失败'))
          }
        },
        fail: (err) => {
          console.error('wx.login失败:', err)
          reject(err)
        }
      })
    })
  },

  /**
   * 跳转注册
   */
  goToRegister() {
    wx.navigateTo({
      url: '/pages/login/register/register'
    })
  },

  /**
   * 忘记密码
   */
  forgotPassword() {
    wx.showToast({
      title: '密码重置功能开发中',
      icon: 'none'
    })
  }
})
