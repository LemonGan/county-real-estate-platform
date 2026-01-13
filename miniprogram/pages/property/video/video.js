// pages/property/video/video.js
Page({
  data: {
    videoUrl: '',
    loading: true,
    error: false,
    errorMessage: '',
    isPlaying: false,
    currentTime: 0,
    duration: 0
  },

  onLoad(options) {
    const { url } = options
    if (url) {
      this.setData({
        videoUrl: decodeURIComponent(url)
      })
    } else {
      this.setData({
        error: true,
        errorMessage: '视频地址无效',
        loading: false
      })
    }
  },

  // 视频加载完成
  onVideoLoaded(e) {
    console.log('视频加载完成', e.detail)
    this.setData({
      loading: false,
      duration: e.detail.duration
    })
  },

  // 视频加载失败
  onVideoError(e) {
    console.error('视频加载失败', e.detail)
    this.setData({
      error: true,
      errorMessage: '视频加载失败',
      loading: false
    })
  },

  // 播放状态变化
  onPlayStateChange(e) {
    const { type } = e.detail
    if (type === 'play') {
      this.setData({ isPlaying: true })
    } else if (type === 'pause' || type === 'ended') {
      this.setData({ isPlaying: false })
    }
  },

  // 时间更新
  onTimeUpdate(e) {
    const { currentTime, duration } = e.detail
    this.setData({
      currentTime,
      duration
    })
  },

  // 格式化时间
  formatTime(seconds) {
    if (!seconds) return '00:00'
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  },

  // 返回
  goBack() {
    wx.navigateBack()
  },

  // 分享
  onShareAppMessage() {
    return {
      title: '房源视频 - 沉浸式看房体验',
      path: '/pages/index/index'
    }
  }
})
