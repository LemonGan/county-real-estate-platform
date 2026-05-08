// pages/property/vr/vr.js
Page({
  data: {
    vrUrl: '', loading: true, error: false, errorMessage: '',
    gyroEnabled: false, currentScene: 0, scenes: [], hotspots: []
  },

  onLoad(options) {
    const { url } = options;
    if (url) {
      this.setData({ vrUrl: decodeURIComponent(url) });
      this.loadVRScene();
    } else {
      this.setData({ error: true, errorMessage: 'VR资源地址无效', loading: false });
    }
  },

  onReady() { this.checkGyroscopeSupport(); },

  checkGyroscopeSupport() {
    wx.startGyroscope({
      success: () => { wx.stopGyroscope(); this.setData({ gyroEnabled: true }); },
      fail: () => {}
    });
  },

  loadVRScene() {
    this.setData({
      loading: false,
      scenes: [
        { id: 'scene1', name: '客厅', panorama: this.data.vrUrl },
        { id: 'scene2', name: '卧室', panorama: '' }
      ],
      hotspots: [
        { sceneId: 'scene1', x: 1000, y: 500, targetScene: 'scene2', label: '进入卧室' }
      ]
    });
  },

  onVRReady() { this.setData({ loading: false }); },
  onVRError() {
    this.setData({ error: true, errorMessage: 'VR资源加载失败', loading: false });
  },

  switchScene(e) {
    const { sceneId } = e.currentTarget.dataset;
    const scene = this.data.scenes.find(s => s.id === sceneId);
    if (scene) this.setData({ currentScene: sceneId });
  },

  onHotspotTap(e) {
    const { targetScene, label } = e.detail;
    if (targetScene) {
      wx.showToast({ title: '正在进入' + label + '...', icon: 'loading' });
      this.switchScene({ currentTarget: { dataset: { sceneId: targetScene } } });
    }
  },

  enableGyroscope() {
    wx.startGyroscope({
      interval: 'normal',
      success: () => { wx.showToast({ title: '已开启体感', icon: 'success' }); },
      fail: () => { wx.showToast({ title: '开启失败', icon: 'none' }); }
    });
  },

  disableGyroscope() {
    wx.stopGyroscope();
    wx.showToast({ title: '已关闭体感', icon: 'success' });
  },

  toggleFullscreen() {
    const vrContext = wx.createVRContext('vr-viewer');
    if (vrContext) vrContext.toggleFullscreen();
  },

  resetView() {
    const vrContext = wx.createVRContext('vr-viewer');
    if (vrContext) {
      vrContext.resetView();
      wx.showToast({ title: '视角已重置', icon: 'success' });
    }
  },

  showHelp() {
    wx.showModal({
      title: 'VR看房操作指南',
      content: '单指拖动：旋转视角\n双指缩放：放大缩小\n点击热点：切换场景\n开启体感：手机转动控制视角',
      showCancel: false
    });
  },

  onShareAppMessage() {
    return { title: 'VR看房 - 沉浸式体验', path: '/pages/index/index', imageUrl: '' };
  }
});
