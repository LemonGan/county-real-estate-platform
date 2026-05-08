// 房源列表页
const app = getApp()
const api = require('../../../utils/api')
const format = require('../../../utils/format')
const cache = require('../../../utils/cache')

Page({
  data: {
    propertyList: [],
    loading: false,
    hasMore: true,
    currentPage: 1,
    pageSize: 10,
    total: 0,
    userLocation: null,  // 用户位置信息
    centerLocation: null,  // 搜索中心位置 {latitude, longitude, name}

    // 筛选条件
    filters: {
      city: '',
      district: '',
      minPrice: '',
      maxPrice: '',
      minArea: '',
      maxArea: '',
      rooms: '',  // 户型筛选
      distance: '',  // 距离筛选
      propertyType: null,
      transactionType: null,
      propertyTypeTag: '',
      keyword: ''
    },

    // 筛选面板
    showFilter: false,
    filterOptions: {
      distances: [
        { label: '不限', value: '' },
        { label: '1公里', value: '1000' },
        { label: '3公里', value: '3000' },
        { label: '5公里', value: '5000' },
        { label: '10公里', value: '10000' }
      ],
      propertyTypes: [
        { label: '全部', value: null },
        { label: '住宅', value: 1 },
        { label: '商铺', value: 2 },
        { label: '写字楼', value: 3 },
        { label: '别墅', value: 4 }
      ],
      transactionTypes: [
        { label: '全部', value: null },
        { label: '出售', value: 1 },
        { label: '出租', value: 2 }
      ]
    }
  },

  /**
   * 页面加载
   */
  onLoad(options) {
    console.log('房源列表页加载', options);

    // 读取首页传入的交易类型
    const transactionType = wx.getStorageSync('listTransactionType');
    if (transactionType) {
      this.setData({ 'filters.transactionType': parseInt(transactionType) });
      wx.removeStorageSync('listTransactionType');
    }

    // 读取首页传入的房源属性标签（新房/二手），供后端上线后生效
    const propertyTypeTag = wx.getStorageSync('listPropertyTypeTag');
    if (propertyTypeTag) {
      this.setData({ 'filters.propertyTypeTag': propertyTypeTag });
      wx.removeStorageSync('listPropertyTypeTag');
    }

    // 如果从搜索页跳转过来，携带关键词
    if (options.keyword) {
      this.setData({
        'filters.keyword': options.keyword
      })
    }

    // 获取用户位置（用于距离筛选）
    this.getUserLocation()

    this.loadPropertyList()
  },

  /**
   * 获取用户位置
   */
  getUserLocation() {
    wx.getLocation({
      type: 'gcj02',
      success: (res) => {
        this.setData({
          userLocation: {
            latitude: res.latitude,
            longitude: res.longitude
          }
        })
        console.log('获取用户位置成功:', this.data.userLocation)
      },
      fail: (err) => {
        console.log('获取用户位置失败:', err)
        // 获取位置失败不影响其他功能
      }
    })
  },

  /**
   * 页面显示
   */
  onShow() {
    // 检查是否有从地图页传来的筛选条件
    const app = getApp()
    if (app && app.globalFilters) {
      console.log('检测到地图页传来的筛选条件:', app.globalFilters)

      // 转换筛选条件格式（地图页的格式可能不同）
      const mapFilters = app.globalFilters
      const newFilters = {
        ...this.data.filters
      }

      // 映射筛选字段
      if (mapFilters.minPrice) newFilters.minPrice = mapFilters.minPrice
      if (mapFilters.maxPrice) newFilters.maxPrice = mapFilters.maxPrice
      if (mapFilters.minArea) newFilters.minArea = mapFilters.minArea
      if (mapFilters.maxArea) newFilters.maxArea = mapFilters.maxArea
      if (mapFilters.rooms) newFilters.rooms = mapFilters.rooms
      if (mapFilters.propertyType) newFilters.propertyType = mapFilters.propertyType

      this.setData({ filters: newFilters })

      // 清除全局筛选条件
      app.globalFilters = null

      // 重置分页并加载
      this.setData({
        currentPage: 1,
        hasMore: true
      })
      this.loadPropertyList()
    } else {
      // 正常刷新列表
      this.refreshList()
    }
  },

  /**
   * 下拉刷新
   */
  onPullDownRefresh() {
    this.refreshList()
    setTimeout(() => {
      wx.stopPullDownRefresh()
    }, 1000)
  },

  /**
   * 上拉加载更多
   */
  onReachBottom() {
    if (this.data.hasMore && !this.data.loading) {
      this.loadMore()
    }
  },

  /**
   * 构建API请求参数
   */
  buildAPIParams() {
    const params = {
      page: this.data.currentPage,
      page_size: this.data.pageSize,
      status_filter: 1  // 只获取在售房源
    }

    const { filters, userLocation, centerLocation } = this.data

    // 转换字段名（驼峰转下划线）
    if (filters.city) params.city = filters.city
    if (filters.district) params.district = filters.district
    if (filters.minPrice) params.min_price = filters.minPrice
    if (filters.maxPrice) params.max_price = filters.maxPrice
    if (filters.minArea) params.min_area = filters.minArea
    if (filters.maxArea) params.max_area = filters.maxArea
    if (filters.rooms) params.rooms = filters.rooms
    if (filters.distance) {
      params.max_distance = parseInt(filters.distance)
      // 如果有距离筛选，需要传递用户位置或中心位置
      let location = centerLocation || userLocation
      if (location && location.latitude && location.longitude) {
        params.latitude = location.latitude
        params.longitude = location.longitude
      }
    }
    if (filters.propertyType) params.property_type = filters.propertyType
    if (filters.transactionType) params.transaction_type = filters.transactionType
    if (filters.keyword) params.keyword = filters.keyword

    return params
  },

  /**
   * 加载房源列表
   */
  async loadPropertyList() {
    if (this.data.loading) return

    this.setData({ loading: true })

    try {
      const params = this.buildAPIParams()

      console.log('列表页 API 请求参数:', params)

      const res = await api.get('/properties', params, false)

      const baseUrl = app.globalData.baseUrl || 'http://127.0.0.1:8000/api/v1'
      const staticUrl = baseUrl.replace('/api/v1', '') + '/static'
      const properties = (res.list || []).map(item => {
        // 处理封面图
        let coverUrl = item.cover_url || (item.images && item.images[0] ? item.images[0].image_url : '')
        if (coverUrl && !coverUrl.startsWith('http')) {
          coverUrl = staticUrl + coverUrl
        }
        // 确保是http开头的网络请求
        if (coverUrl && !coverUrl.startsWith('http')) {
          coverUrl = 'http://' + coverUrl
        }
        return {
          ...item,
          cover_image_url: coverUrl,
          total_price_text: format.formatPrice(item.total_price),
          area_text: format.formatArea(item.area),
          room_type: format.formatRoomType(item),
          property_type_text: format.formatPropertyType(item.property_type),
          transaction_type_text: format.formatTransactionType(item.transaction_type)
        }
      })

      this.setData({
        propertyList: this.data.currentPage === 1 ? properties : [...this.data.propertyList, ...properties],
        total: res.total || 0,
        hasMore: properties.length >= this.data.pageSize,
        loading: false
      })

      // 缓存列表数据
      cache.setCache('property_list', properties)
    } catch (err) {
      console.error('加载房源列表失败:', err)
      this.setData({ loading: false })

      // 尝试从缓存加载
      const cachedList = cache.getCache('property_list')
      if (cachedList) {
        this.setData({
          propertyList: cachedList,
          total: cachedList.length
        })
      }
    }
  },

  /**
   * 刷新列表
   */
  refreshList() {
    this.setData({
      currentPage: 1,
      hasMore: true
    })
    this.loadPropertyList()
  },

  /**
   * 加载更多
   */
  loadMore() {
    this.setData({
      currentPage: this.data.currentPage + 1
    })
    this.loadPropertyList()
  },

  /**
   * 显示筛选面板
   */
  showFilterPanel() {
    this.setData({
      showFilter: true
    })
  },

  /**
   * 隐藏筛选面板
   */
  hideFilterPanel() {
    this.setData({
      showFilter: false
    })
  },

  /**
   * 筛选条件变化
   */
  onFilterChange(e) {
    const { field } = e.currentTarget.dataset
    const { value } = e.detail

    this.setData({
      [`filters.${field}`]: value
    })
  },

  /**
   * 重置筛选
   */
  resetFilters() {
    this.setData({
      filters: {
        city: '',
        district: '',
        minPrice: '',
        maxPrice: '',
        minArea: '',
        maxArea: '',
        propertyType: null,
        transactionType: null,
        keyword: ''
      }
    })

    this.applyFilters()
  },

  /**
   * 应用筛选
   */
  applyFilters() {
    this.hideFilterPanel()
    this.refreshList()
  },

  /**
   * 查看详情
   */
  goToDetail(e) {
    const { id } = e.currentTarget.dataset
    wx.navigateTo({
      url: `/pages/property/detail/detail?id=${id}`
    })
  },

  /**
   * 跳转搜索页
   */
  goToSearch() {
    wx.navigateTo({
      url: '/pages/property/search/search'
    })
  },

  /**
   * 选择搜索中心位置
   */
  chooseCenterLocation() {
    const that = this
    wx.showActionSheet({
      itemList: ['使用当前位置', '在地图上选择'],
      success: (res) => {
        if (res.tapIndex === 0) {
          // 使用当前位置
          that.useCurrentLocationAsCenter()
        } else if (res.tapIndex === 1) {
          // 在地图上选择
          wx.navigateTo({
            url: '/pages/property/map/map?mode=select'
          })
        }
      }
    })
  },

  /**
   * 使用当前位置作为中心
   */
  useCurrentLocationAsCenter() {
    wx.getLocation({
      type: 'gcj02',
      success: (res) => {
        this.setData({
          centerLocation: {
            latitude: res.latitude,
            longitude: res.longitude,
            name: '当前位置'
          }
        })
        wx.showToast({
          title: '已设置为中心位置',
          icon: 'success'
        })
        // 如果有距离筛选，重新加载列表
        if (this.data.filters.distance) {
          this.refreshList()
        }
      },
      fail: () => {
        wx.showToast({
          title: '获取位置失败',
          icon: 'none'
        })
      }
    })
  },

  /**
   * 清除中心位置设置
   */
  clearCenterLocation() {
    this.setData({
      centerLocation: null
    })
    wx.showToast({
      title: '已恢复当前位置',
      icon: 'success'
    })
    // 如果有距离筛选，重新加载列表
    if (this.data.filters.distance) {
      this.refreshList()
    }
  },

  /**
   * 分享
   */
  onShareAppMessage() {
    return {
      title: '县域房源信息',
      path: '/pages/property/list/list'
    }
  }
})
