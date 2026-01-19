// 搜索页
const api = require('../../../utils/api')

Page({
  data: {
    mode: 'property',  // 'property' 搜索房源, 'location' 选择位置
    keyword: '',
    history: [],
    hotSearches: [],
    searchResults: [],
    locationResults: [],  // 位置搜索结果
    searching: false,
    hasResults: false,
    showHistory: true,
    searchTimer: null  // 搜索防抖定时器
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
        title: '搜索位置'
      })
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
        hotSearches: ['西湖', '钱江新城', '滨江', '西湖区', '上城区', '拱墅区', '西湖景区', '城西银泰']
      })
      return
    }

    // 房源搜索模式的热门搜索
    try {
      const res = await api.get('/statistics/hot-search', {}, false)
      this.setData({
        hotSearches: res.keywords || []
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
        city: '杭州'  // 可以根据用户当前位置动态设置
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

      // 静默失败，不显示错误提示
      if (err.message && !err.message.includes('abort')) {
        console.warn('搜索位置失败:', err.message)
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
        searchResults: res.items || res,
        hasResults: (res.items && res.items.length > 0) || (res && res.length > 0),
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

    // 保存搜索历史
    this.saveSearchHistory(location.title)

    wx.navigateBack()
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
  }
})
