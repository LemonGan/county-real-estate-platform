// pages/property/video/video.js
Page({
  data: {
    videoUrl: '', loading: true, error: false, errorMessage: '',
    isPlaying: false, currentTime: 0, duration: 0
  },

  onLoad(options) {
    const { url } = options;
    if (url) {
      this.setData({ videoUrl: decodeURIComponent(url) });
    } else {
      this.setData({ error: true, errorMessage: '视频地址无效', loading: false });
    }
  },

  onVideoLoaded(e) {
    this.setData({ loading: false, duration: e.detail.duration });
  },

  onVideoError() {
    this.setData({ error: true, errorMessage: '视频加载失败', loading: false });
  },

  onPlayStateChange(e) {
    const { type } = e.detail;
    if (type === 'play') this.setData({ isPlaying: true });
    else if (type === 'pause' || type === 'ended') this.setData({ isPlaying: false });
  },

  onTimeUpdate(e) {
    this.setData({ currentTime: e.detail.currentTime, duration: e.detail.duration });
  },

  formatTime(seconds) {
    if (!seconds) return '00:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return mins.toString().padStart(2, '0') + ':' + secs.toString().padStart(2, '0');
  },

  goBack() { wx.navigateBack(); },

  onShareAppMessage() {
    return { title: '房源视频 - 沉浸式看房体验', path: '/pages/index/index' };
  }
});
