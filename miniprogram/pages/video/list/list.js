// pages/video/list/list.js
const app = getApp()
const api = require('../../../utils/api.js')
const cache = require('../../../utils/cache.js')

Page({
  data: {
    videoList: [],
    loading: false,
    currentTab: 0,
    tabs: ['推荐', '关注', '最新'],
    page: 1,
    hasMore: true,
    currentVideoId: null,
    currentVideoIndex: 0,
    isPlaying: false,
    viewedVideoIds: {}
  },

  onLoad(options) {
    this.loadVideoList()
  },

  onShow() {
    // 从缓存恢复播放状态
    const playingId = cache.getCache('currentPlayingVideo')
    if (playingId) {
      this.setData({ currentVideoId: playingId })
    }
  },

  onPullDownRefresh() {
    this.setData({ page: 1, videoList: [], hasMore: true })
    this.loadVideoList().then(() => {
      wx.stopPullDownRefresh()
    })
  },

  onReachBottom() {
    if (this.data.hasMore && !this.data.loading) {
      this.loadMoreVideos()
    }
  },

  onShareAppMessage() {
    return {
      title: '县域房产平台 - 精选房源视频',
      path: '/pages/video/list/list'
    }
  },

  // 切换标签
  switchTab(e) {
    const index = e.currentTarget.dataset.index
    this.setData({ currentTab: index, page: 1, videoList: [], hasMore: true })
    this.loadVideoList()
  },

  async hydrateInteractionStatus(videos) {
    const normalized = (videos || []).map((video) => ({ ...video, is_liked: false, is_favorited: false }))
    if (!app.globalData.isLogin || normalized.length === 0) return normalized
    const hydrated = await Promise.all(normalized.map(async (video) => {
      try {
        const status = await api.get(`/short-videos/${video.id}/interaction-status`)
        return { ...video, is_liked: Boolean(status.is_liked), is_favorited: Boolean(status.is_favorited) }
      } catch (error) {
        console.warn('加载视频互动状态失败:', error)
        return video
      }
    }))
    return hydrated
  },

  // 加载视频列表
  async loadVideoList() {
    if (this.data.loading) return

    this.setData({ loading: true })

    try {
      const tabType = ['recommend', 'follow', 'latest'][this.data.currentTab]
      const res = await api.get('/short-videos/', {
        page: this.data.page,
        page_size: 10,
        type: tabType
      }, false)

      const videos = await this.hydrateInteractionStatus(res.list || res.items || [])

      this.setData({
        videoList: videos,
        loading: false,
        hasMore: videos.length >= 10
      })
    } catch (error) {
      console.error('加载视频列表失败:', error)
      this.setData({ loading: false })
      wx.showToast({
        title: '加载失败',
        icon: 'none'
      })
    }
  },

  // 加载更多视频
  async loadMoreVideos() {
    if (this.data.loading || !this.data.hasMore) return

    this.setData({ loading: true, page: this.data.page + 1 })

    try {
      const tabType = ['recommend', 'follow', 'latest'][this.data.currentTab]
      const res = await api.get('/short-videos/', {
        page: this.data.page,
        page_size: 10,
        type: tabType
      }, false)

      const videos = await this.hydrateInteractionStatus(res.list || res.items || [])

      this.setData({
        videoList: [...this.data.videoList, ...videos],
        loading: false,
        hasMore: videos.length >= 10
      })
    } catch (error) {
      console.error('加载更多视频失败:', error)
      this.setData({ loading: false })
    }
  },

  // 播放视频
  onPlayVideo(e) {
    const videoId = e.currentTarget.dataset.id
    const viewedVideoIds = { ...this.data.viewedVideoIds }
    this.setData({ currentVideoId: videoId, isPlaying: true })
    cache.setCache('currentPlayingVideo', videoId, 600)
    if (videoId && !viewedVideoIds[videoId]) {
      viewedVideoIds[videoId] = true
      this.setData({ viewedVideoIds })
      api.post(`/short-videos/${videoId}/stats/view`, {}, false).catch((error) => {
        console.warn('记录播放失败:', error)
      })
    }
  },

  // 暂停视频
  onPauseVideo() {
    this.setData({ isPlaying: false })
  },

  // 视频播放结束
  onVideoEnd() {
    this.setData({ isPlaying: false })
    // 自动播放下一个视频
    const currentIndex = this.data.videoList.findIndex(v => v.id === this.data.currentVideoId)
    if (currentIndex < this.data.videoList.length - 1) {
      const nextVideo = this.data.videoList[currentIndex + 1]
      this.setData({ currentVideoId: nextVideo.id })
    }
  },

  onSwiperChange(e) {
    const currentVideoIndex = Number(e.detail.current) || 0;
    const currentVideo = this.data.videoList[currentVideoIndex];
    this.setData({
      currentVideoIndex,
      currentVideoId: currentVideo ? currentVideo.id : null,
      isPlaying: Boolean(currentVideo),
    });
  },

  goToAgent(e) {
    const agentId = e.currentTarget.dataset.agentId;
    if (!agentId) {
      wx.showToast({ title: '暂无经纪人信息', icon: 'none' });
      return;
    }
    wx.navigateTo({ url: `/pages/agent/detail/detail?id=${agentId}` });
  },

  // 点赞
  async onLike(e) {
    const videoId = e.currentTarget.dataset.id
    const index = e.currentTarget.dataset.index

    try {
      const result = await api.post(`/short-videos/${videoId}/like/`)
      const videoList = [...this.data.videoList]
      videoList[index].is_liked = Boolean(result.is_liked)
      videoList[index].like_count = result.like_count || 0
      this.setData({ videoList })
    } catch (error) {
      console.error('点赞失败:', error)
    }
  },

  // 收藏
  async onFavorite(e) {
    const videoId = e.currentTarget.dataset.id
    const index = e.currentTarget.dataset.index

    try {
      const result = await api.post(`/short-videos/${videoId}/favorite/`)
      const videoList = [...this.data.videoList]
      videoList[index].is_favorited = Boolean(result.is_favorited)
      videoList[index].favorite_count = result.favorite_count || 0
      this.setData({ videoList })
      wx.showToast({
        title: videoList[index].is_favorited ? '已收藏' : '已取消收藏',
        icon: 'success'
      })
    } catch (error) {
      console.error('收藏失败:', error)
    }
  },

  // 查看房源详情
  goToProperty(e) {
    const propertyId = e.currentTarget.dataset.id
    wx.navigateTo({
      url: `/pages/property/detail/detail?id=${propertyId}`
    })
  },

  // 查看视频详情
  goToVideoDetail(e) {
    const videoId = e.currentTarget.dataset.id
    wx.navigateTo({
      url: `/pages/video/detail/detail?id=${videoId}`
    })
  },

  // 分享
  onShare(e) {
    const { id, title, cover } = e.currentTarget.dataset
    wx.showShareMenu({
      withShareTicket: true,
      menus: ['shareAppMessage', 'shareTimeline']
    })
  }
})
