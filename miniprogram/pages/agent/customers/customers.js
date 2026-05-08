// pages/agent/customers.js
const app = getApp();
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
      const res = await api.get('/agents/customers', { page, page_size: this.data.pageSize });
      if (res && res.list) {
        const newList = loadMore ? [...this.data.customerList, ...res.list] : res.list;
        this.setData({ customerList: newList, page, hasMore: res.list.length >= this.data.pageSize });
      }
    } catch (err) {
      if (!loadMore) {
        this.setData({ customerList: [
          { id: 1, nickname: '张三', phone: '138****1234', avatar: '', current_city: '深圳', hometown_city: '湖南', favorite_count: 5 },
          { id: 2, nickname: '李四', phone: '139****5678', avatar: '', current_city: '广州', hometown_city: '江西', favorite_count: 3 },
          { id: 3, nickname: '王五', phone: '137****9012', avatar: '', current_city: '东莞', hometown_city: '湖北', favorite_count: 8 }
        ]});
      }
    }
    this.setData({ loading: false });
  },

  onSearch(e) { this.setData({ searchKeyword: e.detail.value }); },
  viewCustomer(e) { wx.navigateTo({ url: `/pages/agent/customer-detail/customer-detail?id=${e.currentTarget.dataset.id}` }); }
});
