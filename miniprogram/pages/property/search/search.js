// 搜索页
const api = require('../../../utils/api')

const SERVICE_CITY = '钦州市'
const SERVICE_REGION = '灵山县'
const SERVICE_LONGITUDE = 109.29
const SERVICE_LATITUDE = 22.42

Page({
  data: {
    mode: 'property',  // 'property' 搜索房源, 'location' 选择位置
    viewMode: 'list',  // 'list' 列表视图, 'map' 地图视图
    keyword: '',
    history: [],
    hotSearches: [],
    searchResults: [],
    locationResults: [],  // 位置搜索结果
    searching: false,
    hasResults: false,
    showHistory: true,
    searchTimer: null,  // 搜索防抖定时器
    
    // 地图相关
    mapLongitude: SERVICE_LONGITUDE,
    mapLatitude: SERVICE_LATITUDE,
    mapMarkers: [],
    selectedProperty: null,
    showPropertyCard: false
  },

  /**
   * 页面加载
   */
  onLoad(options) {
    console.log('搜索页加载, options:', options)

    // 检查模式
    if (options.mode === 'select') {
      this.setData({ mode: 'location' })
      wx.setNavigationBarTitle({
        title: '搜索灵山县位置'
      })
      this.loadSearchHistory()
      this.loadHotSearches()
    } else {
      this.setData({ mode: 'property' })
      this.loadSearchHistory()
      this.loadHotSearches()
    }
  },

  /**
   * 加载搜索历史
   */
  loadSearchHistory() {
    try {
      const historyKey = this.data.mode === 'location' ? 'locationSearchHistory' : 'searchHistory'
      const history = wx.getStorageSync(historyKey) || []
      this.setData({ history })
    } catch (err) {
      console.error('加载搜索历史失败:', err)
    }
  },

  clearHistory() {
    const historyKey = this.data.mode === 'location' ? 'locationSearchHistory' : 'searchHistory';
    wx.showModal({
      title: '清空搜索历史？',
      content: '清空后无法恢复。',
      success: (res) => {
        if (!res.confirm) return;
        wx.removeStorageSync(historyKey);
        this.setData({ history: [] });
      },
    });
  },

  /**
   * 保存搜索历史
   */
  saveSearchHistory(keyword) {
    let history = this.data.history

    // 移除已存在的相同关键词
    history = history.filter(item => item !== keyword)

    // 添加到开头
    history.unshift(keyword)

    // 最多保留10条
    history = history.slice(0, 10)

    this.setData({ history })

    try {
      const historyKey = this.data.mode === 'location' ? 'locationSearchHistory' : 'searchHistory'
      wx.setStorageSync(historyKey, history)
    } catch (err) {
      console.error('保存搜索历史失败:', err)
    }
  },

  /**
   * 加载热门搜索
   */
  async loadHotSearches() {
    // 位置搜索模式的热门位置
    if (this.data.mode === 'location') {
      this.setData({
        hotSearches: ['灵山县', '灵城街道', '三海街道', '武利镇', '新圩镇', '檀圩镇']
      })
      return
    }

    // 房源搜索模式的热门搜索
    try {
      const res = await api.get('/statistics/hot-search', {}, false)
      // 后端返回的是对象数组 [{keyword, count}, ...]，需要提取 keyword 字段
      const keywords = res.keywords || []
      this.setData({
        hotSearches: keywords.map(item => item.keyword || item)
      })
    } catch (err) {
      console.error('加载热门搜索失败:', err)
      this.setData({
        hotSearches: ['学区房', '地铁房', '精装修', '南北通透', '低首付']
      })
    }
  },

  /**
   * 输入变化（带防抖）
   */
  onInputChange(e) {
    const keyword = e.detail.value
    this.setData({ keyword })

    // 清除之前的定时器
    if (this.data.searchTimer) {
      clearTimeout(this.data.searchTimer)
    }

    // 如果是位置搜索模式，实时搜索
    if (this.data.mode === 'location' && keyword.trim()) {
      this.setData({
        searchTimer: setTimeout(() => {
          this.searchLocation(keyword)
        }, 500)
      })
    }
  },

  /**
   * 清空输入
   */
  clearInput() {
    this.setData({
      keyword: '',
      showHistory: true,
      locationResults: []
    })
  },

  /**
   * 搜索位置
   */
  async searchLocation(keyword) {
    if (!keyword.trim()) {
      this.setData({ locationResults: [] })
      return
    }

    this.setData({
      searching: true,
      showHistory: false
    })

    try {
      // 调用后端地图搜索API
      const res = await api.get('/map/search', {
        keyword: keyword,
        city: SERVICE_CITY,
        region: SERVICE_REGION
      }, false)

      console.log('位置搜索结果:', res)

      this.setData({
        locationResults: res.data || [],
        searching: false
      })
    } catch (err) {
      console.error('位置搜索失败:', err)
      this.setData({
        searching: false,
        locationResults: []
      })

      if (err.message && !err.message.includes('abort')) {
        console.warn('搜索位置失败:', err.message)
        wx.showToast({
          title: err.message.includes('暂未配置') ? '地图搜索服务暂未配置' : '位置搜索暂不可用',
          icon: 'none'
        })
      }
    }
  },

  /**
   * 执行房源搜索
   */
  async doSearch(keyword) {
    const searchKeyword = keyword || this.data.keyword

    if (!searchKeyword.trim()) {
      wx.showToast({
        title: '请输入搜索关键词',
        icon: 'none'
      })
      return
    }

    this.setData({
      searching: true,
      showHistory: false
    })

    try {
      const res = await api.get('/properties', {
        keyword: searchKeyword,
        page: 1,
        page_size: 20
      }, false)

      this.setData({
        searchResults: res.list || res.items || res,
        hasResults: (res.list && res.list.length > 0) || (res.items && res.items.length > 0) || (res && res.length > 0),
        searching: false
      })

      // 保存搜索历史
      this.saveSearchHistory(searchKeyword)
    } catch (err) {
      console.error('搜索失败:', err)
      this.setData({
        searching: false,
        hasResults: false
      })

      wx.showToast({
        title: err.message || '搜索失败',
        icon: 'none'
      })
    }
  },

  /**
   * 确认搜索
   */
  onConfirm() {
    if (this.data.mode === 'location') {
      // 位置搜索模式，触发搜索
      this.searchLocation(this.data.keyword)
    } else {
      // 房源搜索模式
      this.doSearch()
    }
  },

  /**
   * 点击历史记录
   */
  onHistoryTap(e) {
    const { keyword } = e.currentTarget.dataset
    this.setData({ keyword })

    if (this.data.mode === 'location') {
      this.searchLocation(keyword)
    } else {
      this.doSearch(keyword)
    }
  },

  /**
   * 点击热门搜索
   */
  onHotTap(e) {
    const { keyword } = e.currentTarget.dataset
    this.setData({ keyword })

    if (this.data.mode === 'location') {
      this.searchLocation(keyword)
    } else {
      this.doSearch(keyword)
    }
  },

  /**
   * 选择位置
   */
  selectLocation(e) {
    const { location } = e.currentTarget.dataset

    // 返回地图页，携带位置信息
    const pages = getCurrentPages()
    const prevPage = pages[pages.length - 2]

    if (prevPage && prevPage.route && prevPage.route.includes('pages/property/map/map')) {
      // 设置地图页的中心位置
      prevPage.setData({
        centerLocation: {
          latitude: location.latitude,
          longitude: location.longitude,
          name: location.title
        },
        longitude: location.longitude,
        latitude: location.latitude,
        scale: 13
      })

      wx.navigateBack()
    }
  },

  /**
   * 跳转房源详情
   */
  goToDetail(e) {
    const { id } = e.currentTarget.dataset
    wx.navigateTo({
      url: `/pages/property/detail/detail?id=${id}`
    })
  },

  /**
   * 跳转筛选页
   */
  goToFilter() {
    wx.navigateTo({
      url: '/pages/property/list/list?from=search'
    })
  },

  // ========== 地图视图相关 ==========

  /**
   * 切换到列表视图
   */
  switchToListView() {
    this.setData({ viewMode: 'list' })
  },

  /**
   * 切换到地图视图
   */
  switchToMapView() {
    this.setData({ viewMode: 'map' })
    this.initMapView()
  },

  /**
   * 初始化地图视图
   */
  initMapView() {
    // 获取用户位置
    wx.getLocation({
      type: 'gcj02',
      success: (res) => {
        this.setData({
          mapLongitude: res.longitude,
          mapLatitude: res.latitude
        })
      }
    })

    // 构建地图标记（使用搜索结果或全部房源）
    const properties = this.data.searchResults.length > 0 ? this.data.searchResults : []
    this.buildMapMarkers(properties)
  },

  /**
   * 构建地图标记
   */
  buildMapMarkers(properties) {
    const markers = []
    properties.forEach(prop => {
      if (prop.latitude && prop.longitude) {
        const priceWan = (prop.total_price || prop.price) / 10000
        markers.push({
          id: prop.id,
          latitude: parseFloat(prop.latitude),
          longitude: parseFloat(prop.longitude),
          iconPath: this.getMarkerIcon(priceWan),
          width: 36,
          height: 36,
          title: prop.title
        })
      }
    })
    this.setData({ mapMarkers: markers })
  },

  /**
   * 获取标记图标
   */
  getMarkerIcon(price) {
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

  /**
   * 点击地图标记
   */
  onMarkerTap(e) {
    const markerId = e.detail.markerId
    // 从搜索结果中查找
    let property = this.data.searchResults.find(p => p.id === markerId)
    if (property) {
      // 处理图片
      const baseUrl = getApp().globalData.baseUrl || 'https://api.imlemon.top/api/v1'
      const staticUrl = baseUrl.replace('/api/v1', '') + '/static'
      let coverUrl = property.cover_url || (property.images && property.images[0] ? property.images[0].image_url : '')
      if (coverUrl && !coverUrl.startsWith('http')) {
        coverUrl = staticUrl + coverUrl
      }
      property = {
        ...property,
        cover_image_url: coverUrl,
        total_price_text: (property.total_price || property.price) >= 10000 
          ? ((property.total_price || property.price) / 10000).toString() 
          : (property.total_price || property.price).toString(),
        area_text: property.area ? `${property.area}㎡` : '',
        room_type: `${property.rooms || property.room_count || 0}室${property.halls || property.hall_count || 0}厅`
      }
      
      this.setData({
        selectedProperty: property,
        showPropertyCard: true
      })
    }
  },

  /**
   * 关闭房源卡片
   */
  closePropertyCard() {
    this.setData({
      showPropertyCard: false,
      selectedProperty: null
    })
  },

  /**
   * 从地图卡片查看详情
   */
  goToDetailFromMap() {
    if (this.data.selectedProperty) {
      wx.navigateTo({
        url: `/pages/property/detail/detail?id=${this.data.selectedProperty.id}`
      })
    }
  }
})
