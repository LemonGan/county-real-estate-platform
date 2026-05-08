// pages/property/add/add.js
const app = getApp()
const api = require('../../../utils/api')

Page({
  data: {
    title: '', price: '', area: '',
    roomCount: '', hallCount: '', bathroomCount: '',
    floor: '', totalFloor: '',
    direction: '', decoration: '', propertyType: '', ownership: '',
    address: '', description: '', images: [], video: '', vrUrl: '',
    transactionType: 1,
    propertyTypes: ['住宅', '商铺', '写字楼', '别墅', '公寓', '其他'],
    propertyTypeIndex: 0,
    directions: ['东', '南', '西', '北', '东南', '东北', '西南', '西北', '南北'],
    directionIndex: 0,
    decorations: ['毛坯', '简装', '精装', '豪华装修'],
    decorationIndex: 0,
    ownerships: ['商品房', '经济适用房', '房改房', '集资房', '其他'],
    ownershipIndex: 0,
    submitting: false,
    floorOptions: [],
    floorIndex: 0,
    longitude: '', latitude: ''
  },

  onLoad() { this.initFloorOptions(); },

  chooseLocation() {
    const that = this;
    wx.chooseLocation({
      success(res) {
        that.setData({
          address: res.address || that.data.address,
          longitude: res.longitude,
          latitude: res.latitude
        });
        wx.showToast({ title: '位置已选择', icon: 'success' });
      },
      fail(err) {
        if (err.errMsg.indexOf('auth deny') > -1 || err.errMsg.indexOf('authorize') > -1) {
          wx.showModal({
            title: '提示',
            content: '需要授权位置权限才能使用地图选点',
            confirmText: '去设置',
            success(res) { if (res.confirm) wx.openSetting(); }
          });
        } else {
          wx.showToast({ title: '请选择位置', icon: 'none' });
        }
      }
    });
  },

  initFloorOptions() {
    const floors = [];
    for (let i = 1; i <= 50; i++) floors.push(i + '层');
    this.setData({ floorOptions: floors });
  },

  onPropertyTypeChange(e) { this.setData({ propertyTypeIndex: e.detail.value }); },
  onDirectionChange(e) { this.setData({ directionIndex: e.detail.value }); },
  onDecorationChange(e) { this.setData({ decorationIndex: e.detail.value }); },
  onOwnershipChange(e) { this.setData({ ownershipIndex: e.detail.value }); },
  onFloorChange(e) { this.setData({ floorIndex: e.detail.value }); },
  onTotalFloorChange(e) { this.setData({ totalFloor: e.detail.value }); },

  selectTransactionType(e) {
    this.setData({ transactionType: parseInt(e.currentTarget.dataset.type) });
  },

  onInputChange(e) {
    this.setData({ [e.currentTarget.dataset.field]: e.detail.value });
  },

  chooseImage() {
    if (this.data.images.length >= 9) {
      wx.showToast({ title: '最多9张图片', icon: 'none' });
      return;
    }
    wx.chooseMedia({
      count: 9 - this.data.images.length,
      mediaType: ['image'],
      sourceType: ['album', 'camera'],
      success: (res) => {
        const newImages = res.tempFiles.map(f => f.tempFilePath);
        this.setData({ images: [...this.data.images, ...newImages].slice(0, 9) });
      }
    });
  },

  deleteImage(e) {
    const images = this.data.images;
    images.splice(e.currentTarget.dataset.index, 1);
    this.setData({ images });
  },

  chooseVideo() {
    wx.chooseMedia({
      count: 1, mediaType: ['video'], sourceType: ['album', 'camera'],
      success: (res) => { this.setData({ video: res.tempFiles[0].tempFilePath }); }
    });
  },

  deleteVideo() { this.setData({ video: '' }); },
  inputVrUrl(e) { this.setData({ vrUrl: e.detail.value }); },

  previewImage(e) {
    wx.previewImage({
      current: this.data.images[e.currentTarget.dataset.index],
      urls: this.data.images
    });
  },

  validate() {
    if (!this.data.title.trim()) { wx.showToast({ title: '请输入房源标题', icon: 'none' }); return false; }
    if (!this.data.price) { wx.showToast({ title: '请输入价格', icon: 'none' }); return false; }
    if (!this.data.area) { wx.showToast({ title: '请输入面积', icon: 'none' }); return false; }
    if (!this.data.address.trim()) { wx.showToast({ title: '请输入地址', icon: 'none' }); return false; }
    if (!this.data.longitude || !this.data.latitude) { wx.showToast({ title: '请点击地图选择位置', icon: 'none' }); return false; }
    if (this.data.images.length === 0) { wx.showToast({ title: '请至少上传一张图片', icon: 'none' }); return false; }
    return true;
  },

  async submit() {
    if (!this.validate()) return;
    if (this.data.submitting) return;
    this.setData({ submitting: true });
    wx.showLoading({ title: '提交中...' });

    try {
      const imageUrls = await this.uploadImages();
      const propertyTypeMap = { '住宅': 1, '商铺': 2, '写字楼': 3, '别墅': 4, '公寓': 5, '其他': 6 };
      const propertyData = {
        title: this.data.title,
        total_price: parseFloat(this.data.price) * 10000,
        area: parseFloat(this.data.area),
        room_count: parseInt(this.data.roomCount) || 0,
        hall_count: parseInt(this.data.hallCount) || 0,
        bathroom_count: parseInt(this.data.bathroomCount) || 0,
        floor_info: (this.data.floorIndex + 1) + '层',
        total_floors: parseInt(this.data.totalFloor) || 0,
        orientation: this.data.directions[this.data.directionIndex],
        decoration: this.data.decorations[this.data.decorationIndex],
        property_type: propertyTypeMap[this.data.propertyTypes[this.data.propertyTypeIndex]] || 1,
        transaction_type: this.data.transactionType,
        ownership: this.data.ownerships[this.data.ownershipIndex],
        address: this.data.address,
        description: this.data.description,
        images: imageUrls,
        vr_url: this.data.vrUrl || null,
        video_urls: this.data.video ? [this.data.video] : null,
        status: 1,
        province: '浙江省',
        city: '杭州市',
        district: this.data.address ? '未知' : '',
        longitude: this.data.longitude,
        latitude: this.data.latitude
      };

      const res = await api.post('/properties', propertyData);
      wx.hideLoading();
      wx.showToast({ title: '提交成功，等待审核', icon: 'success' });
      setTimeout(() => { wx.navigateBack(); }, 1500);
    } catch (err) {
      wx.hideLoading();
      wx.showToast({ title: err.message || '提交失败', icon: 'none' });
    } finally {
      this.setData({ submitting: false });
    }
  },

  async uploadImages() {
    const urls = [];
    for (let i = 0; i < this.data.images.length; i++) {
      const imagePath = this.data.images[i];
      if (imagePath.startsWith('http')) { urls.push(imagePath); continue; }
      try {
        const res = await new Promise((resolve, reject) => {
          wx.uploadFile({
            url: app.globalData.baseUrl + '/api/v1/upload',
            filePath: imagePath, name: 'file',
            success: resolve, fail: reject
          });
        });
        const data = JSON.parse(res.data);
        if (data.url) urls.push(data.url);
      } catch (err) {
        // upload failed, skip
      }
    }
    return urls;
  }
});
