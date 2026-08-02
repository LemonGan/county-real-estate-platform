// API请求封装工具
const app = getApp()
const DEFAULT_BASE_URL = 'https://api.imlemon.top/api/v1'
const HTTP_TEST_BASE_URL = 'http://8.138.129.142:8881/api/v1'

function getEnvVersion() {
  try {
    const accountInfo = wx.getAccountInfoSync()
    return accountInfo && accountInfo.miniProgram && accountInfo.miniProgram.envVersion
  } catch (error) {
    return ''
  }
}

function getBaseUrl() {
  // 明文 HTTP 只允许在开发环境临时联调，不会进入体验版或正式版。
  if (app && app.globalData && app.globalData.apiMode === 'http-test' && getEnvVersion() === 'develop') {
    return HTTP_TEST_BASE_URL
  }

  const configured = app && app.globalData && app.globalData.baseUrl
  const baseUrl = configured || DEFAULT_BASE_URL

  // 真机预览/体验版不能请求旧的 HTTP/IP 调试地址；发现旧地址时强制回落到正式 HTTPS 域名。
  if (/^http:\/\//.test(baseUrl) || baseUrl.indexOf('8.138.129.142') >= 0 || baseUrl.indexOf(':8881') >= 0) {
    if (app && app.globalData) app.globalData.baseUrl = DEFAULT_BASE_URL
    return DEFAULT_BASE_URL
  }

  return baseUrl.replace(/\/$/, '')
}

function buildUrl(path) {
  const safePath = String(path || '')
  return getBaseUrl() + (safePath.startsWith('/') ? safePath : '/' + safePath)
}

/**
 * 发起HTTP请求
 */
function request(url, method = 'GET', data = {}, needAuth = true) {
  return new Promise((resolve, reject) => {
    // 仅非 GET 请求显示 loading 遮罩，GET 由页面自行管理骨架屏
    const showLoading = method !== 'GET';
    if (showLoading) {
      wx.showLoading({ title: '处理中...', mask: true });
    }

    const header = { 'content-type': 'application/json' };
    const token = wx.getStorageSync('token');

    if (token) {
      header['Authorization'] = `Bearer ${token}`;
    } else if (needAuth) {
      if (showLoading) wx.hideLoading();
      wx.showToast({ title: '请先登录', icon: 'none' });
      setTimeout(() => { wx.navigateTo({ url: '/pages/login/login' }); }, 1500);
      reject(new Error('未登录'));
      return;
    }

    wx.request({
      url: buildUrl(url),
      method: method,
      data: data,
      header: header,
      success: (res) => {
        if (showLoading) wx.hideLoading();
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data);
        } else if (res.statusCode === 401) {
          app.clearLoginInfo();
          wx.showToast({ title: '登录已过期，请重新登录', icon: 'none' });
          setTimeout(() => { wx.navigateTo({ url: '/pages/login/login' }); }, 1500);
          reject(new Error('未授权'));
        } else {
          console.log('API错误响应:', { statusCode: res.statusCode, data: res.data });
          const message = res.data && (res.data.detail || res.data.message) || '请求失败';
          wx.showToast({ title: message, icon: 'none' });
          reject(new Error(message));
        }
      },
      fail: (err) => {
        if (showLoading) wx.hideLoading();
        wx.showToast({ title: '网络请求失败', icon: 'none' });
        reject(err);
      }
    });
  });
}

function get(url, data = {}, needAuth = true) {
  return request(url, 'GET', data, needAuth);
}

function post(url, data = {}, needAuth = true) {
  return request(url, 'POST', data, needAuth);
}

function put(url, data = {}, needAuth = true) {
  return request(url, 'PUT', data, needAuth);
}

function del(url, data = {}, needAuth = true) {
  return request(url, 'DELETE', data, needAuth);
}

function uploadImage(filePath) {
  return new Promise((resolve, reject) => {
    wx.showLoading({ title: '上传中...', mask: true });
    const token = wx.getStorageSync('token');
    if (!token) {
      wx.hideLoading();
      reject(new Error('请先登录'));
      return;
    }
    wx.uploadFile({
      url: buildUrl('/upload'),
      filePath: filePath,
      name: 'file',
      header: { 'Authorization': `Bearer ${token}` },
      success: (res) => {
        wx.hideLoading();
        let data;
        try {
          data = JSON.parse(res.data);
        } catch (error) {
          reject(new Error('上传响应格式错误'));
          return;
        }
        if (res.statusCode >= 200 && res.statusCode < 300 && data.url) {
          resolve(data);
        } else {
          const message = data.detail || data.message || '上传失败';
          wx.showToast({ title: message, icon: 'none' });
          reject(new Error(message));
        }
      },
      fail: (err) => {
        wx.hideLoading();
        wx.showToast({ title: '上传失败', icon: 'none' });
        reject(err);
      }
    });
  });
}

module.exports = { request, get, post, put, del, uploadImage };
