// 房源对比页
const compareUtil = require('../../../utils/compare');

Page({
  data: { list: [] },

  onShow() {
    this.setData({ list: compareUtil.getCompareList() });
  },

  removeItem(e) {
    compareUtil.removeFromCompare(e.currentTarget.dataset.id);
    this.setData({ list: compareUtil.getCompareList() });
  },

  clearAll() {
    wx.showModal({
      title: '确认清空',
      content: '确定要清空所有对比房源吗？',
      success: (res) => {
        if (res.confirm) {
          compareUtil.clearCompare();
          this.setData({ list: [] });
        }
      }
    });
  },

  goToDetail(e) {
    wx.navigateTo({ url: '/pages/property/detail/detail?id=' + e.currentTarget.dataset.id });
  },

  goToList() {
    wx.switchTab({ url: '/pages/property/list/list' });
  },

  onShareAppMessage() {
    return { title: '房源对比 - 县域房产平台', path: '/pages/property/compare/compare' };
  }
});
