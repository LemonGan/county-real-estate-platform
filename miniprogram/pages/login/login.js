// 登录页 - 简洁版
const app = getApp()
const api = require('../../utils/api')

// 开发模式标识
const DEV_MODE = true

Page({
  data: {
    loading: false
  },

  /**
   * 页面加载
   */
  onLoad() {
    // 已登录则直接跳转首页
    if (app.globalData.isLogin) {
      wx.switchTab({
        url: '/pages/index/index'
      })
    }
  },

  /**
   * 微信授权登录 - 主流方式
   */
  async handleWechatLogin() {
    if (this.data.loading) return
    
    this.setData({ loading: true })
    wx.showLoading({ title: '登录中...' })

    try {
      // 1. 获取微信 code（静默获取）
      const code = await this.getWechatCode()
      
      // 2. 开发模式：跳过 getUserProfile，直接使用模拟数据
      let userInfo
      if (DEV_MODE) {
        userInfo = { nickName: '测试用户', avatarUrl: '' }
      } else {
        userInfo = await this.getUserProfile()
      }
      
      // 3. 调用后端登录接口
      const res = await api.post('/auth/wechat/login', {
        code: code,
        nickname: userInfo.nickName,
        avatar: userInfo.avatarUrl
      }, false)

      // 4. 保存登录信息
      app.setLoginInfo(res.access_token, {
        id: res.user_id,
        nickname: userInfo.nickName,
        avatar: userInfo.avatarUrl
      })

      wx.hideLoading()
      wx.showToast({
        title: res.is_new_user ? '欢迎加入' : '登录成功',
        icon: 'success'
      })

      // 延迟跳转首页
      setTimeout(() => {
        wx.switchTab({
          url: '/pages/index/index'
        })
      }, 1500)

    } catch (err) {
      wx.hideLoading()
      console.error('登录失败:', err)
      wx.showToast({
        title: err.message || '登录失败，请重试',
        icon: 'none'
      })
    } finally {
      this.setData({ loading: false })
    }
  },

  /**
   * 获取微信 code（静默登录）
   */
  getWechatCode() {
    return new Promise((resolve, reject) => {
      wx.login({
        success: (res) => {
          if (res.code) {
            resolve(res.code)
          } else {
            reject(new Error('获取登录凭证失败'))
          }
        },
        fail: (err) => {
          console.error('wx.login 失败:', err)
          reject(new Error('微信登录失败'))
        }
      })
    })
  },

  /**
   * 获取用户授权信息
   */
  getUserProfile() {
    return new Promise((resolve, reject) => {
      wx.getUserProfile({
        desc: '用于完善用户资料',
        success: (res) => {
          resolve(res.userInfo)
        },
        fail: (err) => {
          // 用户拒绝授权时，仍然允许静默登录
          console.log('用户拒绝授权:', err)
          resolve({ nickName: '微信用户', avatarUrl: '' })
        }
      })
    })
  },

  /**
   * 游客模式 - 不登录直接看
   */
  goToHome() {
    wx.switchTab({
      url: '/pages/index/index'
    })
  },

  /**
   * 查看用户协议
   */
  showAgreement() {
    wx.showModal({
      title: '用户协议',
      content: '县域房产平台用户协议内容...',
      showCancel: false
    })
  },

  /**
   * 查看隐私政策
   */
  showPrivacy() {
    wx.showModal({
      title: '隐私政策',
      content: '县域房产平台隐私政策内容...',
      showCancel: false
    })
  }
})
