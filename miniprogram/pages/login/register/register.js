// 注册页
const app = getApp()
const api = require('../../../utils/api')

Page({
  data: {
    phone: '',
    password: '',
    confirmPassword: '',
    code: '',
    countdown: 0,
    agree: false
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
   * 发送验证码
   */
  async sendCode() {
    const { phone } = this.data

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

    try {
      // TODO: 调用发送验证码API
      wx.showToast({
        title: '验证码已发送',
        icon: 'success'
      })

      // 倒计时
      this.setData({ countdown: 60 })
      const timer = setInterval(() => {
        if (this.data.countdown > 0) {
          this.setData({ countdown: this.data.countdown - 1 })
        } else {
          clearInterval(timer)
        }
      }, 1000)
    } catch (err) {
      console.error('发送验证码失败:', err)
    }
  },

  /**
   * 同意协议
   */
  onAgreeChange(e) {
    this.setData({
      agree: e.detail.value.length > 0
    })
  },

  /**
   * 注册
   */
  async handleRegister() {
    const { phone, password, confirmPassword, agree } = this.data

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

    // 验证确认密码
    if (password !== confirmPassword) {
      wx.showToast({
        title: '两次密码不一致',
        icon: 'none'
      })
      return
    }

    // 验证协议
    if (!agree) {
      wx.showToast({
        title: '请同意用户协议',
        icon: 'none'
      })
      return
    }

    try {
      wx.showLoading({
        title: '注册中...',
        mask: true
      })

      const res = await api.post('/auth/register', {
        username: phone,
        phone: phone,
        password: password
      }, false)

      wx.hideLoading()

      wx.showToast({
        title: '注册成功',
        icon: 'success'
      })

      // 跳转到登录页
      setTimeout(() => {
        wx.navigateBack()
      }, 1500)
    } catch (err) {
      wx.hideLoading()
      console.error('注册失败:', err)
    }
  },

  /**
   * 返回登录
   */
  goBack() {
    wx.navigateBack()
  }
})
