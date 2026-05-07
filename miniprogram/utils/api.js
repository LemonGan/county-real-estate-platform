// API请求封装工具
const app = getApp()

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

    if (needAuth) {
      const token = wx.getStorageSync('token');
      if (token) {
        header['Authorization'] = `Bearer ${token}`;
      } else {
        if (showLoading) wx.hideLoading();
        wx.showToast({ title: '请先登录', icon: 'none' });
        setTimeout(() => { wx.navigateTo({ url: '/pages/login/login' }); }, 1500);
        reject(new Error('未登录'));
        return;
      }
    }

    wx.request({
      url: `${app.globalData.baseUrl}${url}`,
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
          wx.showToast({ title: res.data.message || '请求失败', icon: 'none' });
          reject(new Error(res.data.message || '请求失败'));
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
    wx.uploadFile({
      url: `${app.globalData.baseUrl}/properties/images`,
      filePath: filePath,
      name: 'file',
      header: { 'Authorization': `Bearer ${token}` },
      success: (res) => {
        wx.hideLoading();
        const data = JSON.parse(res.data);
        if (data.code === 0) {
          resolve(data.data);
        } else {
          wx.showToast({ title: data.message || '上传失败', icon: 'none' });
          reject(new Error(data.message));
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
