// pages/agent/workbench.js
const app = getApp();
const api = require('../../../utils/api');

Page({
  data: {
    userInfo: {},
    workbench: { today_appointments: 0, pending_appointments: 0, property_count: 0, customer_count: 0, new_customers_yesterday: 0, monthly_sales: 0, monthly_views: 0 },
    propertyStats: { total: 0, on_sale: 0, sold: 0, total_views: 0, total_favorites: 0 },
    appointmentStats: { total: 0, completed: 0, cancelled: 0, pending: 0, success_rate: 0 },
    todoList: []
  },

  onLoad() { this.loadUserInfo(); },
  onShow() {
    if (app.globalData.userInfo && app.globalData.userInfo.is_agent) {
      this.loadWorkbenchData();
    }
  },

  loadUserInfo() {
    this.setData({ userInfo: app.globalData.userInfo || {} });
  },

  async loadWorkbenchData() {
    try {
      const workbenchRes = await api.get('/agents/workbench');
      if (workbenchRes) this.setData({ workbench: workbenchRes });

      const statsRes = await api.get('/agents/property-stats');
      if (statsRes) this.setData({ propertyStats: statsRes });

      const apptRes = await api.get('/agents/appointment-stats');
      if (apptRes) this.setData({ appointmentStats: apptRes });
    } catch (err) {
      wx.showToast({ title: '工作台数据加载失败', icon: 'none' });
    }
  },

  goToAppointments() { wx.navigateTo({ url: '/pages/user/appointments/appointments?scope=agent' }); },
  goToPending() { wx.navigateTo({ url: '/pages/user/appointments/appointments?scope=agent&status=1' }); },
  goToProperties() { wx.navigateTo({ url: '/pages/agent/properties/properties' }); },
  goToCustomers() { wx.navigateTo({ url: '/pages/agent/customers/customers' }); },
  goToPropertyStats() { this.goToProperties(); },
  goToAppointmentStats() { this.goToAppointments(); },
  addProperty() { wx.navigateTo({ url: '/pages/property/add/add' }); },
  scanQR() { wx.scanCode({ success() { wx.showToast({ title: '扫码成功', icon: 'success' }); } }); },
  makePoster() { wx.navigateTo({ url: '/pages/property/poster/poster' }); },
  calculator() { wx.navigateTo({ url: '/pages/tools/calculator/calculator' }); }
});
