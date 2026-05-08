// pages/property/vr/vr.js
Page({
  data: {
    vrUrl: '',
    loading: true,
    error: false,
    errorMessage: '',
    gyroEnabled: false,
    currentScene: 0,
    scenes: [],
    hotspots: []
  },

  onLoad(options) {
    const { url } = options
    if (url) {
      this.setData({
        vrUrl: decodeURIComponent(url)
      })
      this.loadVRScene()
    } else {
      this.setData({
        error: true,
        errorMessage: 'VR资源地址无效',
        loading: false
      })
    }
  },

  onReady() {
    // 检查设备方向传感器支持
    this.checkGyroscopeSupport()
  },

  // 检查陀螺仪支持
  checkGyroscopeSupport() {
    wx.startGyroscope({
      success: () => {
        wx.stopGyroscope()
        this.setData({ gyroEnabled: true })
      },
      fail: () => {
        console.log('设备不支持陀螺仪')
      }
    })
  },

  // 加载VR场景
  loadVRScene() {
    // 这里应该加载VR场景配置
    // 实际项目中需要从后端获取VR场景数据和热点信�?
    this.setData({
      loading: false,
      scenes: [
        {
          id: 'scene1',
          name: '客厅',
          panorama: this.data.vrUrl
        },
        {
          id: 'scene2',
          name: '卧室',
          panorama: '' // 实际应该是另一个全景图URL
        }
      ],
      hotspots: [
        {
          sceneId: 'scene1',
          x: 1000,
          y: 500,
          targetScene: 'scene2',
          label: '进入卧室'
        }
      ]
    })
  },

  // VR视图加载完成
  onVRReady(e) {
    console.log('VR视图加载完成', e.detail)
    this.setData({ loading: false })
  },

  // VR视图加载失败
  onVRError(e) {
    console.error('VR视图加载失败', e.detail)
    this.setData({
      error: true,
      errorMessage: 'VR资源加载失败',
      loading: false
    })
  },

  // 切换场景
  switchScene(e) {
    const { sceneId } = e.currentTarget.dataset
    const scene = this.data.scenes.find(s => s.id === sceneId)
    if (scene) {
      this.setData({ currentScene: sceneId })
      // 通知VR组件切换场景
    }
  },

  // 点击热点
  onHotspotTap(e) {
    const { targetScene, label } = e.detail
    if (targetScene) {
      wx.showToast({
        title: `正在进入${label}...`,
        icon: 'loading'
      })
      this.switchScene({ currentTarget: { dataset: { sceneId: targetScene } } })
    }
  },

  // 开启陀螺仪
  enableGyroscope() {
    wx.startGyroscope({
      interval: 'normal',
      success: () => {
        wx.showToast({
          title: '已开启体�?,
          icon: 'success'
        })
      },
      fail: () => {
        wx.showToast({
          title: '开启失�?,
          icon: 'none'
        })
      }
    })
  },

  // 关闭陀螺仪
  disableGyroscope() {
    wx.stopGyroscope()
    wx.showToast({
      title: '已关闭体�?,
      icon: 'success'
    })
  },

  // 切换全屏
  toggleFullscreen() {
    const vrContext = wx.createVRContext('vr-viewer')
    if (vrContext) {
      vrContext.toggleFullscreen()
    }
  },

  // 重置视角
  resetView() {
    const vrContext = wx.createVRContext('vr-viewer')
    if (vrContext) {
      vrContext.resetView()
      wx.showToast({
        title: '视角已重�?,
        icon: 'success'
      })
    }
  },

  // 显示帮助
  showHelp() {
    wx.showModal({
      title: 'VR看房操作指南',
      content: '�?单指拖动：旋转视角\n�?双指缩放：放�?缩小\n�?点击热点：切换场景\n�?开启体感：手机转动控制视角',
      showCancel: false
    })
  },

  // 分享
  onShareAppMessage() {
    return {
      title: 'VR看房 - 沉浸式体�?,
      path: '/pages/index/index',
      imageUrl: ''
    }
  }
})
