// 收藏价格追踪工具
const TRACK_KEY = 'price_track_map';

function getMap() {
  try { return wx.getStorageSync(TRACK_KEY) || {}; } catch(e) { return {}; }
}

function saveMap(map) { wx.setStorageSync(TRACK_KEY, map); }

module.exports = {
  /** 记录收藏时价格 */
  trackPrice(propertyId, price) {
    const map = getMap();
    if (!map[propertyId]) {
      map[propertyId] = { price: price, time: Date.now() };
    } else {
      map[propertyId] = { ...map[propertyId], price: price };
    }
    saveMap(map);
  },

  /** 获取收藏时价格 */
  getTrackedPrice(propertyId) {
    const map = getMap();
    return map[propertyId] ? map[propertyId].price : null;
  },

  /** 检查降价 */
  checkPriceDrop(propertyId, currentPrice) {
    const tracked = this.getTrackedPrice(propertyId);
    if (tracked && currentPrice < tracked) {
      return { dropped: true, original: tracked, current: currentPrice, diff: tracked - currentPrice };
    }
    return { dropped: false };
  },

  /** 移除追踪 */
  removeTrack(propertyId) {
    const map = getMap();
    delete map[propertyId];
    saveMap(map);
  }
};
