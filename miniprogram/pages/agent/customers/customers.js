// pages/agent/customers.js
const api = require('../../../utils/api');

Page({
  data: {
    customerList: [], page: 1, pageSize: 20,
    loading: false, hasMore: true, searchKeyword: ''
  },

  onLoad() { this.loadCustomers(); },

  onReachBottom() {
    if (this.data.hasMore && !this.data.loading) this.loadCustomers(true);
  },

  async loadCustomers(loadMore = false) {
    if (this.data.loading) return;
    this.setData({ loading: true });
    const page = loadMore ? this.data.page + 1 : 1;

    try {
      const res = await api.get('/agents/customers', { page, page_size: this.data.pageSize, keyword: this.data.searchKeyword });
      if (res && res.list) {
        const newList = loadMore ? [...this.data.customerList, ...res.list] : res.list;
        this.setData({ customerList: newList, page, hasMore: res.list.length >= this.data.pageSize });
      }
    } catch (err) {
      if (!loadMore) this.setData({ customerList: [], hasMore: false });
    }
    this.setData({ loading: false });
  },

  onSearch(e) { this.setData({ searchKeyword: e.detail.value }, () => this.loadCustomers()); },
  viewCustomer() { wx.showToast({ title: '客户详情即将推出', icon: 'none' }); }
});
