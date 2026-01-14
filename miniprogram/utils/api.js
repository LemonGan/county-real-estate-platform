// API请求封装工具
const app = getApp()

/**
 * 发起HTTP请求
 * @param {string} url - 请求地址
 * @param {string} method - 请求方法
 * @param {object} data - 请求数据
 * @param {boolean} needAuth - 是否需要认证
 */
function request(url, method = 'GET', data = {}, needAuth = true) {
  return new Promise((resolve, reject) => {
    // 显示加载提示
    wx.showLoading({
      title: '加载中...',
      mask: true
    })

    // 构建请求头
    const header = {
      'content-type': 'application/json'
    }

    // 添加认证token
    if (needAuth) {
      const token = wx.getStorageSync('token')
      if (token) {
        header['Authorization'] = `Bearer ${token}`
      } else {
        wx.hideLoading()
        wx.showToast({
          title: '请先登录',
          icon: 'none'
        })
        // 跳转到登录页
        setTimeout(() => {
          wx.navigateTo({
            url: '/pages/login/login'
          })
        }, 1500)
        reject(new Error('未登录'))
        return
      }
    }

    // 发起请求
    wx.request({
      url: `${app.globalData.baseUrl}${url}`,
      method: method,
      data: data,
      header: header,
      success: (res) => {
        wx.hideLoading()

        // 2xx状态码都表示成功
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data)
        } else if (res.statusCode === 401) {
          // token过期，清除登录信息
          app.clearLoginInfo()
          wx.showToast({
            title: '登录已过期，请重新登录',
            icon: 'none'
          })
          setTimeout(() => {
            wx.navigateTo({
              url: '/pages/login/login'
            })
          }, 1500)
          reject(new Error('未授权'))
        } else {
          // 打印完整响应用于调试
          console.log('API错误响应:', {
            statusCode: res.statusCode,
            data: res.data,
            header: res.header
          })
          wx.showToast({
            title: res.data.message || '请求失败',
            icon: 'none'
          })
          reject(new Error(res.data.message || '请求失败'))
        }
      },
      fail: (err) => {
        wx.hideLoading()
        wx.showToast({
          title: '网络请求失败',
          icon: 'none'
        })
        reject(err)
      }
    })
  })
}

/**
 * GET请求
 */
function get(url, data = {}, needAuth = true) {
  return request(url, 'GET', data, needAuth)
}

/**
 * POST请求
 */
function post(url, data = {}, needAuth = true) {
  return request(url, 'POST', data, needAuth)
}

/**
 * PUT请求
 */
function put(url, data = {}, needAuth = true) {
  return request(url, 'PUT', data, needAuth)
}

/**
 * DELETE请求
 */
function del(url, data = {}, needAuth = true) {
  return request(url, 'DELETE', data, needAuth)
}

/**
 * 图片上传
 */
function uploadImage(filePath) {
  return new Promise((resolve, reject) => {
    wx.showLoading({
      title: '上传中...',
      mask: true
    })

    const token = wx.getStorageSync('token')

    wx.uploadFile({
      url: `${app.globalData.baseUrl}/properties/images`,
      filePath: filePath,
      name: 'file',
      header: {
        'Authorization': `Bearer ${token}`
      },
      success: (res) => {
        wx.hideLoading()
        const data = JSON.parse(res.data)
        if (data.code === 0) {
          resolve(data.data)
        } else {
          wx.showToast({
            title: data.message || '上传失败',
            icon: 'none'
          })
          reject(new Error(data.message))
        }
      },
      fail: (err) => {
        wx.hideLoading()
        wx.showToast({
          title: '上传失败',
          icon: 'none'
        })
        reject(err)
      }
    })
  })
}

module.exports = {
  request,
  get,
  post,
  put,
  del,
  uploadImage
}
