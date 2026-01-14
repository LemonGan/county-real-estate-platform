// pages/property/map/map.js
const app = getApp()
const api = require('../../../utils/api.js')

Page({
  data: {
    longitude: 120.153576,  // 默认杭州坐标
    latitude: 30.287459,
    scale: 14,
    markers: [],
    polyline: [],
    showPropertyCard: false,
    selectedProperty: null,
    centerLocation: null,  // 搜索中心位置 {latitude, longitude, name}
    selectMode: false,  // 是否在选择位置模式
    selectModeTip: '',  // 选择模式提示文字
    filters: {
      minPrice: '',
      maxPrice: '',
      minArea: '',
      maxArea: '',
      rooms: '',
      propertyType: '',
      distance: ''  // 距离筛选：空=不限，1000=1km，3000=3km，5000=5km，10000=10km
    },
    filterVisible: false,
    loading: false,
    mapContext: null,
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
    // 从房源列表进入时，传入筛选条件
    if (options.filters) {
      try {
        this.setData({
          filters: JSON.parse(decodeURIComponent(options.filters))
        })
      } catch (e) {
        console.error('解析筛选条件失败:', e)
      }
    }

    this.initMap()
  },

  onReady() {
    this.setData({
      mapContext: wx.createMapContext('propertyMap', this)
    })
  },

  onShow() {
    // 不在这里加载，等待位置获取完成后再加载
  },

  // 初始化地图
  initMap() {
    // 先设置默认位置（杭州）
    this.setData({
      longitude: 120.153576,
      latitude: 30.287459
    })

    // 获取当前位置
    wx.getLocation({
      type: 'gcj02',
      success: (res) => {
        this.setData({
          longitude: res.longitude,
          latitude: res.latitude
        })
        // 获取到位置后，加载房源
        this.loadProperties()
      },
      fail: () => {
        // 使用默认位置，加载房源
        this.loadProperties()
      }
    })
  },

  // 加载房源标记
  async loadProperties() {
    if (this.data.loading) return

    console.log('loadProperties 被调用, 当前 data:', {
      longitude: this.data.longitude,
      latitude: this.data.latitude,
      longitudeType: typeof this.data.longitude,
      latitudeType: typeof this.data.latitude
    })

    this.setData({ loading: true })

    try {
      // 使用中心位置（优先使用用户选择的位置，否则使用当前位置）
      let centerLat, centerLon
      if (this.data.centerLocation) {
        centerLat = this.data.centerLocation.latitude
        centerLon = this.data.centerLocation.longitude
      } else {
        centerLat = this.data.latitude
        centerLon = this.data.longitude
      }

      // 确保使用有效的坐标（如果当前坐标无效，使用默认杭州坐标）
      centerLon = centerLon || 120.153576
      centerLat = centerLat || 30.287459

      console.log('加载房源，使用中心坐标:', { latitude: centerLat, longitude: centerLon })
      if (this.data.centerLocation) {
        console.log('中心位置名称:', this.data.centerLocation.name)
      }

      // 构建筛选参数
      const params = {
        longitude: centerLon,
        latitude: centerLat,
        radius: 5000, // 5公里范围
        ...this.buildFilterParams()
      }

      console.log('API 请求参数:', params)

      const res = await api.get('/properties/nearby/', params, false)

      console.log('API 返回结果:', res)
      console.log('房源数量:', res.list ? res.list.length : 0)

      // 转换为地图标记（只处理有经纬度的房源）
      const markers = (res.list || [])
        .filter(item => {
          const hasCoords = item.longitude && item.latitude
          if (!hasCoords) {
            console.log('房源缺少坐标，跳过:', item.id, item.title)
          }
          return hasCoords
        })
        .map((item, index) => ({
          id: item.id,
          longitude: parseFloat(item.longitude),
          latitude: parseFloat(item.latitude),
          title: item.title,
          iconPath: this.getMarkerIcon(item.total_price ? item.total_price / 10000 : 0),
          width: 45,
          height: 45,
          alpha: 1,
          callout: {
            content: item.total_price ? `${(item.total_price / 10000).toFixed(0)}万` : '价格面议',
            color: '#fff',
            fontSize: 16,
            borderRadius: 8,
            bgColor: '#ff4d4f',
            padding: 8,
            display: 'ALWAYS',
            textAlign: 'center'
          },
        customCallout: {
          anchorY: 0,
          anchorX: 0,
          display: 'ALWAYS'
        }
      }))

      console.log('创建的标记数量:', markers.length)
      console.log('标记详情:', markers.map(m => ({ id: m.id, lng: m.longitude, lat: m.latitude })))

      this.setData({
        markers,
        loading: false
      })

      console.log('标记已更新到页面，当前地图中心:', {
        longitude: this.data.longitude,
        latitude: this.data.latitude
      })
    } catch (error) {
      console.error('加载房源失败:', error)
      this.setData({ loading: false })
      wx.showToast({
        title: '加载失败',
        icon: 'none'
      })
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

  // 地图区域变化
  onRegionChange(e) {
    if (e.type === 'end') {
      const { longitude, latitude, scale } = e.detail
      console.log('地图区域变化:', { longitude, latitude, scale })

      // 只有在坐标有效时才更新
      if (longitude && latitude) {
        this.setData({
          longitude,
          latitude,
          scale: scale || this.data.scale
        })
        // 延迟加载，避免频繁请求
        clearTimeout(this.loadTimer)
        this.loadTimer = setTimeout(() => {
          this.loadProperties()
        }, 500)
      } else {
        console.warn('地图区域变化事件中的坐标无效，跳过更新')
      }
    }
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
      console.error('加载房源详情失败:', error)
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
    console.log('应用筛选，筛选条件:', this.data.filters)
    this.hideFilter()
    this.loadProperties()
  },

  // 定位到当前位置
  moveToLocation() {
    console.log('定位到当前位置')
    wx.getLocation({
      type: 'gcj02',
      success: (res) => {
        console.log('获取位置成功:', res)
        this.setData({
          longitude: res.longitude,
          latitude: res.latitude,
          scale: 15
        })
        if (this.data.mapContext) {
          this.data.mapContext.moveToLocation({
            longitude: res.longitude,
            latitude: res.latitude
          })
        }
        this.loadProperties()
      },
      fail: (err) => {
        console.error('获取位置失败:', err)
        wx.showToast({
          title: '获取位置失败，请检查权限',
          icon: 'none'
        })
      }
    })
  },

  // 切换列表/地图视图
  switchToListView() {
    console.log('切换到列表视图')

    // 将筛选条件保存到全局变量
    const app = getApp()
    app.globalFilters = this.data.filters

    // 使用 switchTab 跳转到 tabBar 页面
    wx.switchTab({
      url: '/pages/property/list/list',
      success: () => {
        console.log('跳转到列表页成功')
      },
      fail: (err) => {
        console.error('跳转到列表页失败:', err)
      }
    })
  },

  // 选择搜索中心位置
  chooseCenterLocation() {
    const that = this
    wx.showActionSheet({
      itemList: ['使用当前位置', '在地图上选择', '搜索地点'],
      success: (res) => {
        if (res.tapIndex === 0) {
          // 使用当前位置
          that.useCurrentLocationAsCenter()
        } else if (res.tapIndex === 1) {
          // 在地图上选择
          that.selectLocationOnMap()
        } else if (res.tapIndex === 2) {
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
          latitude: res.longitude
        })
        wx.showToast({
          title: '已设置为当前位置',
          icon: 'success'
        })
        // 重新加载房源
        this.loadProperties()
      },
      fail: () => {
        wx.showToast({
          title: '获取位置失败',
          icon: 'none'
        })
      }
    })
  },

  // 在地图上选择位置
  selectLocationOnMap() {
    // 进入选点模式
    this.setData({
      selectMode: true,
      selectModeTip: '点击地图选择搜索中心位置'
    })
    wx.showToast({
      title: '请点击地图选择位置',
      icon: 'none'
    })
  },

  // 处理地图点击（选择中心位置）
  onMapTap(e) {
    if (this.data.selectMode) {
      const { latitude, longitude } = e.detail
      this.setData({
        centerLocation: {
          latitude,
          longitude,
          name: '自定义位置'
        },
        longitude: latitude,
        latitude: longitude,
        selectMode: false,
        selectModeTip: ''
      })
      wx.showToast({
        title: '已设置中心位置',
        icon: 'success'
      })
      // 重新加载房源
      this.loadProperties()
    }
  },

  // 取消选择模式
  cancelSelectMode() {
    this.setData({
      selectMode: false,
      selectModeTip: ''
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
      centerLocation: null
    })
    wx.showToast({
      title: '已恢复使用当前位置',
      icon: 'success'
    })
    // 重新加载房源
    this.loadProperties()
  }
})
