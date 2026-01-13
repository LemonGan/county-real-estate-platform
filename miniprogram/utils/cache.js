// 缓存管理工具

/**
 * 设置缓存
 * @param {string} key - 缓存键
 * @param {any} data - 缓存数据
 * @param {number} expire - 过期时间（秒）
 */
function setCache(key, data, expire = 7200) {
  const cacheData = {
    data: data,
    expire: expire,
    timestamp: Date.now()
  }

  try {
    wx.setStorageSync(key, JSON.stringify(cacheData))
    return true
  } catch (e) {
    console.error('设置缓存失败:', e)
    return false
  }
}

/**
 * 获取缓存
 * @param {string} key - 缓存键
 */
function getCache(key) {
  try {
    const cacheStr = wx.getStorageSync(key)
    if (!cacheStr) {
      return null
    }

    const cache = JSON.parse(cacheStr)
    const now = Date.now()

    // 检查是否过期
    if (cache.expire && (now - cache.timestamp) / 1000 > cache.expire) {
      wx.removeStorageSync(key)
      return null
    }

    return cache.data
  } catch (e) {
    console.error('获取缓存失败:', e)
    return null
  }
}

/**
 * 删除缓存
 * @param {string} key - 缓存键
 */
function removeCache(key) {
  try {
    wx.removeStorageSync(key)
    return true
  } catch (e) {
    console.error('删除缓存失败:', e)
    return false
  }
}

/**
 * 清空所有缓存
 */
function clearCache() {
  try {
    wx.clearStorageSync()
    return true
  } catch (e) {
    console.error('清空缓存失败:', e)
    return false
  }
}

module.exports = {
  setCache,
  getCache,
  removeCache,
  clearCache
}
