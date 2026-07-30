// 设置页
const app = getApp()

Page({
  data: {
    version: '1.0.0',
    cacheSize: '0MB'
  },

  /**
   * 页面加载
   */
  onLoad() {
    this.getCacheSize()
  },

  /**
   * 获取缓存大小
   */
  getCacheSize() {
    try {
      const res = wx.getStorageInfoSync()
      const size = (res.currentSize / 1024).toFixed(2)
      this.setData({
        cacheSize: `${size}MB`
      })
    } catch (err) {
      console.error('获取缓存大小失败:', err)
    }
  },

  /**
   * 清除缓存
   */
  clearCache() {
    wx.showModal({
      title: '提示',
      content: '确定要清除缓存吗？',
      success: (res) => {
        if (res.confirm) {
          try {
            wx.clearStorageSync()
            this.setData({ cacheSize: '0MB' })
            wx.showToast({
              title: '清除成功',
              icon: 'success'
            })
          } catch (err) {
            console.error('清除缓存失败:', err)
            wx.showToast({
              title: '清除失败',
              icon: 'none'
            })
          }
        }
      }
    })
  },

  /**
   * 检查更新
   */
  checkUpdate() {
    if (wx.canIUse('getUpdateManager')) {
      const updateManager = wx.getUpdateManager()

      updateManager.onCheckForUpdate((res) => {
        if (res.hasUpdate) {
          updateManager.onUpdateReady(() => {
            wx.showModal({
              title: '更新提示',
              content: '新版本已准备好，是否重启应用？',
              success: (res) => {
                if (res.confirm) {
                  updateManager.applyUpdate()
                }
              }
            })
          })

          updateManager.onUpdateFailed(() => {
            wx.showModal({
              title: '更新失败',
              content: '新版本下载失败，请检查网络后重试',
              showCancel: false
            })
          })
        } else {
          wx.showToast({
            title: '当前已是最新版本',
            icon: 'none'
          })
        }
      })
    } else {
      wx.showToast({
        title: '当前微信版本不支持检查更新',
        icon: 'none'
      })
    }
  },

  /**
   * 关于我们
   */
  goToAbout() {
    wx.navigateTo({
      url: '/pages/user/about/about'
    })
  },

  /**
   * 用户协议
   */
  goToAgreement() {
    wx.navigateTo({
      url: '/pages/user/agreement/agreement'
    })
  },

  /**
   * 隐私政策
   */
  goToPrivacy() {
    wx.navigateTo({
      url: '/pages/user/privacy/privacy'
    })
  },

  /**
   * 意见反馈
   */
  goToFeedback() {
    wx.navigateTo({
      url: '/pages/user/feedback/feedback'
    })
  },

  /**
   * 联系客服
   */
  contactService() {
    wx.showModal({
      title: '联系平台',
      content: '平台客服渠道正在完善。你可以通过“意见反馈”提交问题，我们会尽快处理。',
      confirmText: '去反馈',
      cancelText: '暂不处理',
      success: (res) => {
        if (res.confirm) this.goToFeedback()
      }
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
