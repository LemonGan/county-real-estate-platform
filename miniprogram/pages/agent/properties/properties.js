// pages/agent/properties.js
const app = getApp();
const api = require('../../../utils/api');

Page({
  data: {
    propertyList: [], page: 1, pageSize: 10,
    loading: false, hasMore: true, status: 'pending', hasLoaded: false
  },

  onLoad(options) {
    if (options.status) this.setData({ status: String(options.status) });
    this.loadProperties();
  },

  onShow() {
    if (this.data.hasLoaded && !this.data.loading) this.loadProperties();
  },

  onReachBottom() {
    if (this.data.hasMore && !this.data.loading) this.loadProperties(true);
  },

  switchStatus(e) {
    const status = String(e.currentTarget.dataset.status);
    this.setData({ status, propertyList: [], page: 1, hasMore: true });
    this.loadProperties();
  },

  async loadProperties(loadMore = false) {
    if (this.data.loading) return;
    this.setData({ loading: true });
    const page = loadMore ? this.data.page + 1 : 1;
    const query = { page, page_size: this.data.pageSize };

    if (this.data.status === 'pending') query.audit_status = 0;
    else if (this.data.status === 'rejected') query.audit_status = 2;
    else query.status = parseInt(this.data.status);

    try {
      const res = await api.get('/properties/mine', query, true);
      if (res && res.list) {
        const list = res.list.map(item => ({
          ...item,
          price_in_wan: ((Number(item.total_price) || 0) / 10000).toFixed(1)
        }));
        const newList = loadMore ? [...this.data.propertyList, ...list] : list;
        this.setData({ propertyList: newList, page, hasMore: list.length >= this.data.pageSize });
      }
    } catch (err) {
      if (!loadMore) this.setData({ propertyList: [] });
      wx.showToast({ title: err.message || '加载失败', icon: 'none' });
    }
    this.setData({ loading: false, hasLoaded: true });
  },

  viewProperty(e) {
    const property = this.data.propertyList.find(item => item.id === e.currentTarget.dataset.id);
    if (property && property.audit_status !== 1) {
      wx.showToast({ title: property.audit_status === 2 ? '该房源未通过审核' : '房源正在审核中', icon: 'none' });
      return;
    }
    wx.navigateTo({ url: `/pages/property/detail/detail?id=${e.currentTarget.dataset.id}` });
  },
  editProperty(e) {
    const propertyId = e.currentTarget.dataset.id;
    if (!propertyId) return;
    wx.navigateTo({ url: `/pages/property/edit/edit?id=${propertyId}` });
  },

  changePropertyStatus(e) {
    const propertyId = e.currentTarget.dataset.id;
    const newStatus = Number(e.currentTarget.dataset.status);
    const actions = {
      1: { title: '重新上架房源？', content: '房源将恢复为在售状态并重新出现在公开列表中。', confirmText: '确认上架' },
      2: { title: '标记为已售？', content: '标记后房源将不再公开展示。请确认交易已完成。', confirmText: '标记已售' },
      3: { title: '下架该房源？', content: '下架后房源将不再公开展示，之后可以重新上架。', confirmText: '确认下架' },
    };
    const action = actions[newStatus];
    if (!propertyId || !action) return;
    wx.showModal({
      ...action,
      confirmColor: newStatus === 2 ? '#d84a4a' : '#2f6fed',
      success: async (res) => {
        if (!res.confirm) return;
        try {
          await api.request(`/properties/${propertyId}/status?new_status=${newStatus}`, 'PATCH', {}, true);
          wx.showToast({ title: newStatus === 1 ? '已重新上架' : (newStatus === 2 ? '已标记为已售' : '已下架'), icon: 'success' });
          this.setData({ propertyList: [], page: 1, hasMore: true });
          this.loadProperties();
        } catch (err) {
          wx.showToast({ title: err.message || '操作失败', icon: 'none' });
        }
      },
    });
  },

  addProperty() { wx.navigateTo({ url: '/pages/property/add/add' }); }
});
