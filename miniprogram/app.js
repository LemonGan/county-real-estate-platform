// 县域房产平台小程序主入口
App({
  globalData: {
    userInfo: null,
    token: null,
    baseUrl: 'https://api.imlemon.top/api/v1', // 生产环境API
    isLogin: false, 
    location: null
  },

  /**
   * 小程序初始化
   */
  onLaunch() {
    console.log('小程序启动');

    // 检查登录状态
    this.checkLoginStatus();

    // 获取系统信息
    const systemInfo = wx.getSystemInfoSync();
    this.globalData.systemInfo = systemInfo;

    // 检查更新
    this.checkUpdate();
  },

  /**
   * 小程序显示时
   */
  onShow() {
    console.log('小程序显示');
  },

  /**
   * 检查登录状态
   */
  checkLoginStatus() {
    const token = wx.getStorageSync('token');
    const userInfo = wx.getStorageSync('userInfo');

    if (token && userInfo) {
      this.globalData.token = token;
      this.globalData.userInfo = userInfo;
      this.globalData.isLogin = true;
      console.log('用户已登录');
    } else {
      this.globalData.isLogin = false;
      console.log('用户未登录');
    }
  },

  /**
   * 检查小程序更新
   */
  checkUpdate() {
    if (wx.canIUse('getUpdateManager')) {
      const updateManager = wx.getUpdateManager();

      updateManager.onCheckForUpdate((res) => {
        if (res.hasUpdate) {
          console.log('发现新版本');
        }
      });

      updateManager.onUpdateReady(() => {
        wx.showModal({
          title: '更新提示',
          content: '新版本已经准备好，是否重启应用？',
          success(res) {
            if (res.confirm) {
              updateManager.applyUpdate();
            }
          }
        });
      });

      updateManager.onUpdateFailed(() => {
        console.error('新版本下载失败');
      });
    }
  },

  /**
   * 设置登录信息
   */
  setLoginInfo(token, userInfo) {
    this.globalData.token = token;
    this.globalData.userInfo = userInfo;
    this.globalData.isLogin = true;

    // 持久化存储
    wx.setStorageSync('token', token);
    wx.setStorageSync('userInfo', userInfo);
  },

  /**
   * 清除登录信息
   */
  clearLoginInfo() {
    this.globalData.token = null;
    this.globalData.userInfo = null;
    this.globalData.isLogin = false;

    wx.removeStorageSync('token');
    wx.removeStorageSync('userInfo');
  }
});
