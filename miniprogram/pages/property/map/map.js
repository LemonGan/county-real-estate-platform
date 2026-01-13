// pages/property/map/map.js
const app = getApp()
const api = require('../../../utils/api.js')

Page({
  data: {
    longitude: 0,
    latitude: 0,
    scale: 14,
    markers: [],
    polyline: [],
    showPropertyCard: false,
    selectedProperty: null,
    filters: {
      minPrice: '',
      maxPrice: '',
      minArea: '',
      maxArea: '',
      rooms: '',
      propertyType: ''
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
      {label: '住宅', value: 'residential'},
      {label: '别墅', value: 'villa'},
      {label: '商铺', value: 'commercial'},
      {label: '写字楼', value: 'office'}
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
    this.loadProperties()
  },

  // 初始化地图
  initMap() {
    // 获取当前位置
    wx.getLocation({
      type: 'gcj02',
      success: (res) => {
        this.setData({
          longitude: res.longitude,
          latitude: res.latitude
        })
      },
      fail: () => {
        // 默认位置（可以在配置中设置）
        this.setData({
          longitude: 120.153576, // 杭州
          latitude: 30.287459
        })
      }
    })
  },

  // 加载房源标记
  async loadProperties() {
    if (this.data.loading) return

    this.setData({ loading: true })

    try {
      // 构建筛选参数
      const params = {
        longitude: this.data.longitude,
        latitude: this.data.latitude,
        radius: 5000, // 5公里范围
        ...this.buildFilterParams()
      }

      const res = await api.get('/properties/nearby/', params)

      // 转换为地图标记
      const markers = (res.items || []).map((item, index) => ({
        id: item.id,
        longitude: item.longitude,
        latitude: item.latitude,
        title: item.title,
        iconPath: this.getMarkerIcon(item.price),
        width: 30,
        height: 30,
        alpha: 0.9,
        callout: {
          content: `${item.price}万`,
          color: '#fff',
          fontSize: 12,
          borderRadius: 4,
          bgColor: '#667eea',
          padding: 4,
          display: 'ALWAYS'
        },
        customCallout: {
          anchorY: 0,
          anchorX: 0,
          display: 'ALWAYS'
        }
      }))

      this.setData({
        markers,
        loading: false
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
      this.setData({
        longitude,
        latitude,
        scale
      })
      // 延迟加载，避免频繁请求
      clearTimeout(this.loadTimer)
      this.loadTimer = setTimeout(() => {
        this.loadProperties()
      }, 500)
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
      const res = await api.get(`/properties/${propertyId}/`)
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
    const value = e.detail.value
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
        propertyType: ''
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
          scale: 15
        })
        if (this.data.mapContext) {
          this.data.mapContext.moveToLocation({
            longitude: res.longitude,
            latitude: res.latitude
          })
        }
        this.loadProperties()
      }
    })
  },

  // 切换列表/地图视图
  switchToListView() {
    const filters = encodeURIComponent(JSON.stringify(this.data.filters))
    wx.navigateTo({
      url: `/pages/property/list/list?filters=${filters}`
    })
  }
})
