const app = getApp()
const api = require('../../../utils/api')

Page({
  data: {
    nickname: '',
    avatar: '',
    avatarPreview: '',
    loading: true,
    saving: false
  },

  displayImage(url) {
    if (!url || url.startsWith('http') || url.startsWith('wxfile://')) return url
    const origin = (app.globalData.baseUrl || '').replace('/api/v1', '')
    return url.startsWith('/static/') ? origin + url : url
  },

  async onLoad() {
    try {
      const user = await api.get('/users/me')
      this.setData({
        nickname: user.nickname || '',
        avatar: user.avatar || '',
        avatarPreview: this.displayImage(user.avatar || ''),
        loading: false
      })
    } catch (err) {
      const cached = app.globalData.userInfo || {}
      this.setData({
        nickname: cached.nickname || '',
        avatar: cached.avatar || '',
        avatarPreview: this.displayImage(cached.avatar || ''),
        loading: false
      })
      wx.showToast({ title: err.message || '资料加载失败', icon: 'none' })
    }
  },

  onNicknameInput(e) {
    this.setData({ nickname: e.detail.value })
  },

  chooseAvatar() {
    wx.chooseMedia({
      count: 1,
      mediaType: ['image'],
      sourceType: ['album', 'camera'],
      success: (res) => {
        const filePath = res.tempFiles[0].tempFilePath
        this.setData({ avatarPreview: filePath, avatar: filePath })
      }
    })
  },

  async saveProfile() {
    const nickname = this.data.nickname.trim()
    if (!nickname) {
      wx.showToast({ title: '请输入昵称', icon: 'none' })
      return
    }
    if (this.data.saving) return
    this.setData({ saving: true })
    try {
      let avatar = this.data.avatar
      if (avatar && !avatar.startsWith('http') && !avatar.startsWith('/')) {
        const uploaded = await api.uploadImage(avatar)
        avatar = uploaded.url
      }
      const user = await api.put('/users/me', { nickname, avatar: avatar || null })
      const mergedUser = { ...(app.globalData.userInfo || {}), ...user }
      app.globalData.userInfo = mergedUser
      wx.setStorageSync('userInfo', mergedUser)
      this.setData({ avatar, avatarPreview: this.displayImage(avatar) })
      wx.showToast({ title: '资料已保存', icon: 'success' })
      setTimeout(() => wx.navigateBack(), 500)
    } catch (err) {
      wx.showToast({ title: err.message || '保存失败', icon: 'none' })
    } finally {
      this.setData({ saving: false })
    }
  }
})
