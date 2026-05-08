// pages/agent/properties.js
const app = getApp();
const api = require('../../../utils/api');

Page({
  data: {
    propertyList: [], page: 1, pageSize: 10,
    loading: false, hasMore: true, status: 1
  },

  onLoad(options) {
    if (options.status) this.setData({ status: parseInt(options.status) });
    this.loadProperties();
  },

  onReachBottom() {
    if (this.data.hasMore && !this.data.loading) this.loadProperties(true);
  },

  switchStatus(e) {
    const status = parseInt(e.currentTarget.dataset.status);
    this.setData({ status, propertyList: [], page: 1, hasMore: true });
    this.loadProperties();
  },

  async loadProperties(loadMore = false) {
    if (this.data.loading) return;
    this.setData({ loading: true });
    const page = loadMore ? this.data.page + 1 : 1;

    try {
      const res = await api.get('/properties', {
        page, page_size: this.data.pageSize,
        agent_id: app.globalData.userInfo.id,
        status: this.data.status
      });

      if (res && res.list) {
        const newList = loadMore ? [...this.data.propertyList, ...res.list] : res.list;
        this.setData({ propertyList: newList, page, hasMore: res.list.length >= this.data.pageSize });
      }
    } catch (err) {
      if (!loadMore) {
        this.setData({ propertyList: [
          { id: 1, title: '市中心精装三房', cover_url: '', province: '广东', city: '深圳', district: '南山', detail_address: '科技园', rooms: 3, halls: 2, area: 120, total_price: 150, view_count: 156, favorite_count: 12, status: 1 },
          { id: 2, title: '学区房出售', cover_url: '', province: '广东', city: '深圳', district: '福田', detail_address: '百花路', rooms: 2, halls: 1, area: 80, total_price: 280, view_count: 234, favorite_count: 18, status: 1 }
        ]});
      }
    }
    this.setData({ loading: false });
  },

  viewProperty(e) { wx.navigateTo({ url: `/pages/property/detail/detail?id=${e.currentTarget.dataset.id}` }); },
  addProperty() { wx.navigateTo({ url: '/pages/agent/add-property/add-property' }); }
});
