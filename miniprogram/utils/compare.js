// 房源对比功能 - 全局管理
const COMPARE_KEY = 'property_compare_list';
const MAX_COMPARE = 4;

function getList() {
  try {
    const list = wx.getStorageSync(COMPARE_KEY);
    return Array.isArray(list) ? list : [];
  } catch (e) {
    return [];
  }
}

function saveList(list) {
  wx.setStorageSync(COMPARE_KEY, list.slice(0, MAX_COMPARE));
}

module.exports = {
  MAX_COMPARE,

  /** 获取对比列表 */
  getCompareList() { return getList(); },

  /** 是否已在对比中 */
  isInCompare(propertyId) {
    return getList().some(p => p.id === propertyId);
  },

  /** 添加到对比 */
  addToCompare(property) {
    const list = getList();
    if (list.length >= MAX_COMPARE) {
      wx.showToast({ title: '最多对比' + MAX_COMPARE + '套房源', icon: 'none' });
      return false;
    }
    if (list.some(p => p.id === property.id)) {
      wx.showToast({ title: '已在对比列表中', icon: 'none' });
      return false;
    }
    list.push({
      id: property.id,
      title: property.title,
      price: property.total_price || property.price,
      area: property.area,
      rooms: property.room_count || property.rooms,
      halls: property.hall_count || property.halls,
      orientation: property.orientation,
      floor: property.floor_info || property.floor,
      buildYear: property.build_year,
      decoration: property.decoration,
      community: property.community_name || property.community,
      address: property.address || property.detail_address,
      district: property.district,
      coverUrl: property.cover_url || property.cover_image_url
    });
    saveList(list);
    wx.showToast({ title: '已加入对比', icon: 'success' });
    return true;
  },

  /** 从对比中移除 */
  removeFromCompare(propertyId) {
    const list = getList().filter(p => p.id !== propertyId);
    saveList(list);
    wx.showToast({ title: '已移除', icon: 'success' });
  },

  /** 清空对比 */
  clearCompare() {
    wx.removeStorageSync(COMPARE_KEY);
  }
};
