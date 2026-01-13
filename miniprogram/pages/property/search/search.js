// 房源搜索页
const api = require('../../../utils/api')
const { formatPrice } = require('../../../utils/format')

Page({
  data: {
    keyword: '',
    history: [],
    hotSearches: [],
    searchResults: [],
    searching: false,
    hasResults: false,
    showHistory: true
  },

  /**
   * 页面加载
   */
  onLoad(options) {
    this.loadSearchHistory()
    this.loadHotSearches()
  },

  /**
   * 加载搜索历史
   */
  loadSearchHistory() {
    try {
      const history = wx.getStorageSync('searchHistory') || []
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
      wx.setStorageSync('searchHistory', history)
    } catch (err) {
      console.error('保存搜索历史失败:', err)
    }
  },

  /**
   * 加载热门搜索
   */
  async loadHotSearches() {
    try {
      const res = await api.get('/statistics/hot-search', {}, false)
      this.setData({
        hotSearches: res.keywords || []
      })
    } catch (err) {
      console.error('加载热门搜索失败:', err)
      // 设置默认热门搜索
      this.setData({
        hotSearches: ['学区房', '地铁房', '精装修', '南北通透', '低首付']
      })
    }
  },

  /**
   * 输入变化
   */
  onInputChange(e) {
    this.setData({
      keyword: e.detail.value
    })
  },

  /**
   * 清空输入
   */
  clearInput() {
    this.setData({
      keyword: '',
      showHistory: true
    })
  },

  /**
   * 执行搜索
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
      })

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
    this.doSearch()
  },

  /**
   * 点击历史记录
   */
  onHistoryTap(e) {
    const { keyword } = e.currentTarget.dataset
    this.setData({ keyword })
    this.doSearch(keyword)
  },

  /**
   * 点击热门搜索
   */
  onHotTap(e) {
    const { keyword } = e.currentTarget.dataset
    this.setData({ keyword })
    this.doSearch(keyword)
  },

  /**
   * 清空历史记录
   */
  clearHistory() {
    wx.showModal({
      title: '提示',
      content: '确定要清空搜索历史吗？',
      success: (res) => {
        if (res.confirm) {
          this.setData({ history: [] })
          try {
            wx.removeStorageSync('searchHistory')
          } catch (err) {
            console.error('清空搜索历史失败:', err)
          }
        }
      }
    })
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
