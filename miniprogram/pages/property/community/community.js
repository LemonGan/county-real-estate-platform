// 小区详情页
const app = getApp();
const api = require('../../../utils/api');
const format = require('../../../utils/format');

Page({
  data: {
    communityName: '',
    properties: [],
    avgPrice: '--',
    minPrice: '--',
    maxPrice: '--',
    loading: true
  },

  onLoad(options) {
    const { name, city, district } = options;
    if (!name) {
      wx.showToast({ title: '缺少小区名称', icon: 'none' });
      setTimeout(() => wx.navigateBack(), 1500);
      return;
    }
    this.setData({ communityName: decodeURIComponent(name) });
    this.loadProperties(city, district);
  },

  async loadProperties(city, district) {
    try {
      const params = { page: 1, page_size: 50, status_filter: 1, keyword: this.data.communityName };
      const res = await api.get('/properties', params, false);

      const baseUrl = app.globalData.baseUrl || '';
      const staticUrl = baseUrl.replace('/api/v1', '') + '/static';
      const list = (res.list || []).map(item => ({
        ...item,
        cover_url: (item.cover_url && !item.cover_url.startsWith('http')) ? staticUrl + item.cover_url : item.cover_url,
        total_price_text: format.formatPrice(item.total_price),
        area_text: format.formatArea(item.area)
      }));

      // 计算统计数据
      const prices = list.map(p => p.total_price || 0).filter(p => p > 0).map(p => p / 10000);
      const avg = prices.length > 0 ? (prices.reduce((a, b) => a + b, 0) / prices.length).toFixed(0) : '--';
      const min = prices.length > 0 ? Math.min(...prices).toFixed(0) : '--';
      const max = prices.length > 0 ? Math.max(...prices).toFixed(0) : '--';

      this.setData({ properties: list, avgPrice: avg, minPrice: min, maxPrice: max, loading: false });
    } catch (err) {
      this.setData({ loading: false });
    }
  },

  goToDetail(e) {
    wx.navigateTo({ url: '/pages/property/detail/detail?id=' + e.currentTarget.dataset.id });
  },

  onShareAppMessage() {
    return { title: this.data.communityName + ' - 在售房源', path: '/pages/index/index' };
  }
});
