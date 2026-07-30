const api = require('../../../utils/api');

const PROPERTY_TYPES = ['住宅', '商铺', '写字楼', '别墅'];
const TYPE_VALUES = [1, 2, 3, 4];

Page({
  data: {
    propertyId: null,
    loading: true,
    saving: false,
    title: '',
    price: '',
    area: '',
    roomCount: '',
    hallCount: '',
    bathroomCount: '',
    floorInfo: '',
    totalFloors: '',
    address: '',
    description: '',
    transactionType: 1,
    propertyTypes: PROPERTY_TYPES,
    propertyTypeIndex: 0,
  },

  onLoad(options) {
    const propertyId = Number(options.id);
    if (!propertyId) {
      wx.showToast({ title: '房源参数无效', icon: 'none' });
      setTimeout(() => wx.navigateBack(), 1200);
      return;
    }
    this.setData({ propertyId });
    this.loadProperty();
  },

  async loadProperty() {
    try {
      const item = await api.get(`/properties/mine/${this.data.propertyId}`, {}, true);
      const typeIndex = Math.max(0, TYPE_VALUES.indexOf(Number(item.property_type)));
      const price = Number(item.total_price || 0) / 10000;
      this.setData({
        title: item.title || '',
        price: price ? String(price) : '',
        area: item.area != null ? String(item.area) : '',
        roomCount: item.room_count != null ? String(item.room_count) : '',
        hallCount: item.hall_count != null ? String(item.hall_count) : '',
        bathroomCount: item.bathroom_count != null ? String(item.bathroom_count) : '',
        floorInfo: item.floor_info || '',
        totalFloors: item.total_floors != null ? String(item.total_floors) : '',
        address: item.detail_address || '',
        description: item.description || '',
        transactionType: Number(item.transaction_type) || 1,
        propertyTypeIndex: typeIndex,
      });
    } catch (err) {
      wx.showToast({ title: err.message || '房源加载失败', icon: 'none' });
      setTimeout(() => wx.navigateBack(), 1400);
    } finally {
      this.setData({ loading: false });
    }
  },

  onInput(e) {
    this.setData({ [e.currentTarget.dataset.field]: e.detail.value });
  },

  onPropertyTypeChange(e) {
    this.setData({ propertyTypeIndex: Number(e.detail.value) });
  },

  selectTransactionType(e) {
    this.setData({ transactionType: Number(e.currentTarget.dataset.type) });
  },

  validate() {
    const { title, price, area, address, totalFloors } = this.data;
    if (title.trim().length < 2) return this.showValidation('标题至少需要 2 个字');
    if (!(Number(price) > 0)) return this.showValidation('请填写正确的总价');
    if (!(Number(area) > 0)) return this.showValidation('请填写正确的面积');
    if (!address.trim()) return this.showValidation('请填写详细地址');
    if (totalFloors && !(Number(totalFloors) >= 1 && Number(totalFloors) <= 200)) {
      return this.showValidation('总楼层请填写 1 至 200');
    }
    return true;
  },

  showValidation(title) {
    wx.showToast({ title, icon: 'none' });
    return false;
  },

  confirmSave() {
    if (!this.validate() || this.data.saving) return;
    wx.showModal({
      title: '确认保存修改？',
      content: '保存后房源会自动下架并重新进入审核，审核通过后才会再次公开展示。图片和视频本次不会变更。',
      confirmText: '保存并送审',
      confirmColor: '#2f6fed',
      success: (res) => { if (res.confirm) this.save(); },
    });
  },

  async save() {
    this.setData({ saving: true });
    const data = this.data;
    const payload = {
      title: data.title.trim(),
      total_price: Math.round(Number(data.price) * 10000),
      area: Number(data.area),
      room_count: Number(data.roomCount) || 0,
      hall_count: Number(data.hallCount) || 0,
      bathroom_count: Number(data.bathroomCount) || 0,
      floor_info: data.floorInfo.trim() || null,
      total_floors: data.totalFloors ? Number(data.totalFloors) : null,
      property_type: TYPE_VALUES[data.propertyTypeIndex],
      transaction_type: data.transactionType,
      detail_address: data.address.trim(),
      description: data.description.trim() || null,
    };
    try {
      await api.put(`/properties/${data.propertyId}`, payload, true);
      wx.showToast({ title: '已保存，等待审核', icon: 'success' });
      setTimeout(() => wx.navigateBack(), 1300);
    } catch (err) {
      wx.showToast({ title: err.message || '保存失败', icon: 'none' });
    } finally {
      this.setData({ saving: false });
    }
  },
});
