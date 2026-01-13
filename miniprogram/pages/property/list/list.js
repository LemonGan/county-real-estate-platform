// 房源列表页
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

    // 筛选条件
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
    },

    // 筛选面板
    showFilter: false,
    filterOptions: {
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
    console.log('房源列表页加载', options)

    // 如果从搜索页跳转过来，携带关键词
    if (options.keyword) {
      this.setData({
        'filters.keyword': options.keyword
      })
    }

    this.loadPropertyList()
  },

  /**
   * 页面显示
   */
  onShow() {
    // 刷新列表
    this.refreshList()
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
   * 加载房源列表
   */
  async loadPropertyList() {
    if (this.data.loading) return

    this.setData({ loading: true })

    try {
      const params = {
        page: this.data.currentPage,
        page_size: this.data.pageSize,
        status_filter: 1, // 只获取在售房源
        ...this.data.filters
      }

      const res = await api.get('/properties', params, false)

      const properties = (res.list || []).map(item => ({
        ...item,
        total_price_text: format.formatPrice(item.total_price),
        area_text: format.formatArea(item.area),
        room_type: format.formatRoomType(item),
        property_type_text: format.formatPropertyType(item.property_type),
        transaction_type_text: format.formatTransactionType(item.transaction_type)
      }))

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
   * 分享
   */
  onShareAppMessage() {
    return {
      title: '县域房源信息',
      path: '/pages/property/list/list'
    }
  }
})
