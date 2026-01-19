// pages/property/map/map.js
const app = getApp()
const api = require('../../../utils/api.js')

Page({
  data: {
    longitude: 103.5,
    latitude: 36.0,
    scale: 5,
    markers: [],
    allMarkers: [],
    polyline: [],
    showPropertyCard: false,
    selectedProperty: null,
    centerLocation: null,
    filters: {
      minPrice: '',
      maxPrice: '',
      minArea: '',
      maxArea: '',
      rooms: '',
      propertyType: '',
      distance: ''
    },
    filterVisible: false,
    loading: false,
    // 筛选选项
    roomsOptions: [
      {label: '不限', value: ''},
      {label: '1室', value: '1'},
      {label: '2室', value: '2'},
      {label: '3室', value: '3'},
      {label: '4室+', value: '4'}
    ],
    propertyTypeOptions: [
      {label: '不限', value: ''},
      {label: '住宅', value: '1'},
      {label: '商铺', value: '2'},
      {label: '写字楼', value: '3'},
      {label: '别墅', value: '4'}
    ],
    distanceOptions: [
      {label: '不限', value: ''},
      {label: '1公里', value: '1000'},
      {label: '3公里', value: '3000'},
      {label: '5公里', value: '5000'},
      {label: '10公里', value: '10000'}
    ]
  },

  onLoad(options) {
    if (options.filters) {
      try {
        this.setData({
          filters: JSON.parse(decodeURIComponent(options.filters))
        })
      } catch (e) {
        // ignore
      }
    }

    this.initMap()
  },

  onShow() {
    // 不在这里加载，等待位置获取完成后再加载
  },

  // 初始化地图
  initMap() {
    // 先加载全国房源
    this.loadAllProperties()

    // 获取当前位置并更新地图中心
    wx.getLocation({
      type: 'gcj02',
      success: (res) => {
        this.setData({
          longitude: res.longitude,
          latitude: res.latitude,
          scale: 10
        })
      },
      fail: () => {
        // 定位失败，保持中国地理中心
      }
    })
  },

  // 加载所有房源
  async loadAllProperties() {
    if (this.data.loading || this.data.allMarkers.length > 0) return

    this.setData({ loading: true })

    try {
      const res = await api.get('/properties/', {
        page: 1,
        page_size: 50,
        status_filter: 1
      }, true)

      const markers = []
      if (res.list && res.list.length > 0) {
        for (let i = 0; i < res.list.length; i++) {
          const prop = res.list[i]
          if (prop.latitude && prop.longitude) {
            const priceWan = (prop.total_price || prop.price) / 10000
            markers.push({
              id: prop.id,
              latitude: parseFloat(prop.latitude),
              longitude: parseFloat(prop.longitude),
              iconPath: this.getMarkerIcon(priceWan),
              width: 24,
              height: 24,
              title: prop.title
            })
          }
        }
      }

      this.setData({
        allMarkers: markers,
        markers: markers,
        loading: false
      })
    } catch (err) {
      this.setData({ loading: false })
    }
  },

  // 加载房源标记
  async loadProperties() {
    // 如果设置了中心位置和距离筛选，则进行筛选
    if (this.data.centerLocation && this.data.filters.distance) {
      await this.loadPropertiesByDistance()
    } else {
      // 否则显示所有房源
      this.setData({ markers: this.data.allMarkers })
    }
  },

  // 根据距离加载房源
  async loadPropertiesByDistance() {
    if (!this.data.centerLocation || !this.data.filters.distance) return

    this.setData({ loading: true })

    try {
      const res = await api.get('/properties/nearby/', {
        longitude: this.data.centerLocation.longitude,
        latitude: this.data.centerLocation.latitude,
        radius: parseInt(this.data.filters.distance),
        page_size: 50,
        ...this.buildFilterParamsWithoutDistance(false)
      }, false)

      const markers = []
      if (res.list && res.list.length > 0) {
        for (let i = 0; i < res.list.length; i++) {
          const prop = res.list[i]
          if (prop.latitude && prop.longitude) {
            const priceWan = (prop.total_price || prop.price) / 10000
            markers.push({
              id: prop.id,
              latitude: parseFloat(prop.latitude),
              longitude: parseFloat(prop.longitude),
              iconPath: this.getMarkerIcon(priceWan),
              width: 24,
              height: 24,
              title: prop.title
            })
          }
        }
      }

      this.setData({ markers, loading: false })
    } catch (err) {
      this.setData({ loading: false })
    }
  },

  // 构建筛选参数
  buildFilterParams() {
    const params = {}
    const { filters } = this.data

    if (filters.minPrice) params.min_price = filters.minPrice
    if (filters.maxPrice) params.max_price = filters.maxPrice
    if (filters.minArea) params.min_area = filters.minArea
    if (filters.maxArea) params.max_area = filters.maxArea
    if (filters.rooms) params.rooms = filters.rooms
    if (filters.propertyType) params.property_type = filters.propertyType
    if (filters.distance) params.max_distance = parseInt(filters.distance)

    return params
  },

  // 构建筛选参数（排除距离筛选，用于地图动态加载）
  // useYuanUnit: 是否使用元作为价格单位（true=全国模式用元，false=附近模式用万元）
  buildFilterParamsWithoutDistance(useYuanUnit = false) {
    const params = {}
    const { filters } = this.data

    // 价格单位转换：全国模式需要转换为元，附近模式直接用万元
    if (filters.minPrice) {
      params.min_price = useYuanUnit ? filters.minPrice * 10000 : filters.minPrice
    }
    if (filters.maxPrice) {
      params.max_price = useYuanUnit ? filters.maxPrice * 10000 : filters.maxPrice
    }
    if (filters.minArea) params.min_area = filters.minArea
    if (filters.maxArea) params.max_area = filters.maxArea
    if (filters.rooms) params.rooms = filters.rooms
    if (filters.propertyType) params.property_type = filters.propertyType
    // 不包含 distance 筛选

    return params
  },

  // 获取标记图标（根据价格区间）
  getMarkerIcon(price) {
    // 根据价格区间返回不同颜色的标记
    if (price < 50) {
      return '/assets/icons/marker-green.png'
    } else if (price < 100) {
      return '/assets/icons/marker-blue.png'
    } else if (price < 200) {
      return '/assets/icons/marker-orange.png'
    } else {
      return '/assets/icons/marker-red.png'
    }
  },

  // 地图区域变化 - 不做任何处理，避免频繁更新
  onRegionChange(e) {
    // 空实现，让地图自由缩放移动
  },

  // 点击标记
  onMarkerTap(e) {
    const markerId = e.detail.markerId
    this.loadPropertyDetail(markerId)
  },

  // 加载房源详情
  async loadPropertyDetail(propertyId) {
    try {
      const res = await api.get(`/properties/${propertyId}/`, {}, false)
      this.setData({
        selectedProperty: res,
        showPropertyCard: true
      })
    } catch (error) {
      // ignore
    }
  },

  // 关闭房源卡片
  closePropertyCard() {
    this.setData({
      showPropertyCard: false,
      selectedProperty: null
    })
  },

  // 查看房源详情
  goToPropertyDetail() {
    if (this.data.selectedProperty) {
      wx.navigateTo({
        url: `/pages/property/detail/detail?id=${this.data.selectedProperty.id}`
      })
    }
  },

  // 导航到房源
  navigateToProperty() {
    if (!this.data.selectedProperty) return

    const { longitude, latitude, title } = this.data.selectedProperty

    wx.openLocation({
      longitude,
      latitude,
      name: title,
      scale: 18
    })
  },

  // 显示筛选
  showFilter() {
    this.setData({ filterVisible: true })
  },

  // 隐藏筛选
  hideFilter() {
    this.setData({ filterVisible: false })
  },

  // 筛选条件变化
  onFilterChange(e) {
    const { field } = e.currentTarget.dataset
    // 兼容 bindinput/bindchange 和 bindtap 事件
    const value = e.detail.value !== undefined ? e.detail.value : e.currentTarget.dataset.value
    this.setData({
      [`filters.${field}`]: value
    })
  },

  // 重置筛选
  resetFilters() {
    this.setData({
      filters: {
        minPrice: '',
        maxPrice: '',
        minArea: '',
        maxArea: '',
        rooms: '',
        propertyType: '',
        distance: ''
      }
    })
  },

  // 应用筛选
  applyFilters() {
    this.hideFilter()
    this.loadProperties()
  },

  // 定位到当前位置
  moveToLocation() {
    wx.getLocation({
      type: 'gcj02',
      success: (res) => {
        this.setData({
          longitude: res.longitude,
          latitude: res.latitude,
          scale: 12
        })
      },
      fail: () => {
        wx.showToast({
          title: '获取位置失败，请检查权限',
          icon: 'none'
        })
      }
    })
  },

  // 切换列表/地图视图
  switchToListView() {
    const app = getApp()
    app.globalFilters = this.data.filters

    wx.switchTab({
      url: '/pages/property/list/list'
    })
  },

  // 选择搜索中心位置
  chooseCenterLocation() {
    const that = this
    wx.showActionSheet({
      itemList: ['使用当前位置', '搜索地点'],
      success: (res) => {
        if (res.tapIndex === 0) {
          // 使用当前位置
          that.useCurrentLocationAsCenter()
        } else if (res.tapIndex === 1) {
          // 搜索地点
          that.searchLocation()
        }
      }
    })
  },

  // 使用当前位置作为中心
  useCurrentLocationAsCenter() {
    wx.getLocation({
      type: 'gcj02',
      success: (res) => {
        this.setData({
          centerLocation: {
            latitude: res.latitude,
            longitude: res.longitude,
            name: '当前位置'
          },
          longitude: res.latitude,
          latitude: res.latitude
        })
        wx.showToast({
          title: '已设置为筛选中心',
          icon: 'success'
        })
      },
      fail: () => {
        wx.showToast({
          title: '获取位置失败',
          icon: 'none'
        })
      }
    })
  },

  // 搜索地点
  searchLocation() {
    wx.navigateTo({
      url: '/pages/property/search/search?mode=select'
    })
  },

  // 跳转到位置搜索页面
  goToLocationSearch() {
    wx.navigateTo({
      url: '/pages/property/search/search?mode=select'
    })
  },

  // 清除中心位置设置
  clearCenterLocation() {
    this.setData({
      centerLocation: null,
      markers: this.data.allMarkers  // 恢复显示所有房源
    })
    wx.showToast({
      title: '已显示所有房源',
      icon: 'success'
    })
  }
})
