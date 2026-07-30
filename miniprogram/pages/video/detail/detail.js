// pages/video/detail/detail.js
const app = getApp()
const api = require('../../../utils/api.js')
const cache = require('../../../utils/cache.js')

Page({
  data: {
    videoId: null,
    video: null,
    comments: [],
    commentText: '',
    loading: true,
    commentLoading: false,
    showCommentInput: false,
    replyTo: null,
    currentPage: 1,
    hasMoreComments: true
  },

  onLoad(options) {
    this.setData({ videoId: options.id })
    this.loadVideoDetail()
  },

  onShareAppMessage() {
    return {
      title: this.data.video?.title || '县域房产平台 - 房源视频',
      path: `/pages/video/detail/detail?id=${this.data.videoId}`,
      imageUrl: this.data.video?.cover_url
    }
  },

  // 加载视频详情
  async loadVideoDetail() {
    try {
      const [videoRes, commentsRes] = await Promise.all([
        api.get(`/short-videos/${this.data.videoId}/`, {}, false),
        api.get(`/short-videos/${this.data.videoId}/comments/`, {
          page: 1,
          page_size: 20
        }, false)
      ])

      const video = { ...videoRes, is_liked: false, is_favorited: false }
      if (app.globalData.isLogin) {
        try {
          const interaction = await api.get(`/short-videos/${this.data.videoId}/interaction-status`)
          video.is_liked = Boolean(interaction.is_liked)
          video.is_favorited = Boolean(interaction.is_favorited)
        } catch (error) {
          console.warn('加载互动状态失败:', error)
        }
      }
      const currentUserId = app.globalData.userInfo?.id
      const comments = (commentsRes.items || []).map((item) => ({
        ...item,
        is_owner: item.user_id === currentUserId
      }))
      this.setData({
        video,
        comments,
        loading: false,
        hasMoreComments: comments.length >= 20
      })
    } catch (error) {
      console.error('加载视频详情失败:', error)
      this.setData({ loading: false })
      wx.showToast({
        title: '加载失败',
        icon: 'none'
      })
    }
  },

  // 播放状态变化
  onPlayStateChange(e) {
    const { type } = e.detail
    // 可以在这里记录播放行为
  },

  // 点赞
  async onLike() {
    try {
      const result = await api.post(`/short-videos/${this.data.videoId}/like/`)
      const video = { ...this.data.video }
      video.is_liked = Boolean(result.is_liked)
      video.like_count = result.like_count || 0
      this.setData({ video })
    } catch (error) {
      console.error('点赞失败:', error)
    }
  },

  // 收藏
  async onFavorite() {
    try {
      const result = await api.post(`/short-videos/${this.data.videoId}/favorite/`)
      const video = { ...this.data.video }
      video.is_favorited = Boolean(result.is_favorited)
      video.favorite_count = result.favorite_count || 0
      this.setData({ video })
      wx.showToast({
        title: video.is_favorited ? '已收藏' : '已取消收藏',
        icon: 'success'
      })
    } catch (error) {
      console.error('收藏失败:', error)
    }
  },

  // 关注作者
  async onFollow() {
    try {
      const video = { ...this.data.video }
      const result = video.is_followed
        ? await api.del(`/agents/${video.agent_id}/follow/`)
        : await api.post(`/agents/${video.agent_id}/follow/`, {})
      video.is_followed = Boolean(result.following)
      video.follower_count = result.follower_count || 0
      this.setData({ video })
      wx.showToast({ title: video.is_followed ? '已关注' : '已取消关注', icon: 'success' })
    } catch (error) {
      console.error('关注失败:', error)
    }
  },

  // 显示评论输入框
  showCommentInput(e) {
    const commentId = e.currentTarget.dataset.commentId
    const replyToUser = e.currentTarget.dataset.replyTo
    this.setData({
      showCommentInput: true,
      replyTo: commentId ? { id: commentId, user: replyToUser } : null
    })
  },

  // 隐藏评论输入框
  hideCommentInput() {
    this.setData({
      showCommentInput: false,
      commentText: '',
      replyTo: null
    })
  },

  // 评论内容变化
  onCommentInput(e) {
    this.setData({ commentText: e.detail.value })
  },

  // 发送评论
  async sendComment() {
    if (!this.data.commentText.trim()) {
      wx.showToast({
        title: '请输入评论内容',
        icon: 'none'
      })
      return
    }

    this.setData({ commentLoading: true })

    try {
      const res = await api.post(`/short-videos/${this.data.videoId}/comments/`, {
        content: this.data.commentText,
        parent_id: this.data.replyTo?.id || null
      })

      const update = {
        commentText: '',
        showCommentInput: false,
        replyTo: null,
        commentLoading: false
      }
      if (res.status === 1) {
        update.comments = [res, ...this.data.comments]
        const video = { ...this.data.video }
        video.comment_count = (video.comment_count || 0) + 1
        update.video = video
      }
      this.setData(update)
      wx.showToast({
        title: res.status === 0 ? '评论已提交，审核后显示' : '评论成功',
        icon: 'success'
      })
    } catch (error) {
      console.error('评论失败:', error)
      this.setData({ commentLoading: false })
      wx.showToast({
        title: '评论失败',
        icon: 'none'
      })
    }
  },

  // 加载更多评论
  async loadMoreComments() {
    if (this.data.commentLoading || !this.data.hasMoreComments) return

    this.setData({ commentLoading: true, currentPage: this.data.currentPage + 1 })

    try {
      const res = await api.get(`/short-videos/${this.data.videoId}/comments/`, {
        page: this.data.currentPage,
        page_size: 20
      }, false)

      const comments = [...this.data.comments, ...(res.items || [])]
      this.setData({
        comments,
        commentLoading: false,
        hasMoreComments: (res.items || []).length >= 20
      })
    } catch (error) {
      console.error('加载评论失败:', error)
      this.setData({ commentLoading: false })
    }
  },

  // 点赞评论
  async onLikeComment(e) {
    const commentId = e.currentTarget.dataset.id
    const index = e.currentTarget.dataset.index

    try {
      const result = await api.post(`/short-videos/comments/${commentId}/like/`)
      const comments = [...this.data.comments]
      comments[index].is_liked = Boolean(result.is_liked)
      comments[index].like_count = result.like_count || 0
      this.setData({ comments })
    } catch (error) {
      console.error('点赞评论失败:', error)
    }
  },

  // 删除评论
  async onDeleteComment(e) {
    const commentId = e.currentTarget.dataset.id
    const index = e.currentTarget.dataset.index

    wx.showModal({
      title: '确认删除',
      content: '确定要删除这条评论吗？',
      success: async (res) => {
        if (res.confirm) {
          try {
            await api.del(`/short-videos/comments/${commentId}/`)
            const comments = [...this.data.comments]
            comments.splice(index, 1)
            this.setData({ comments })

            // 更新评论数
            const video = { ...this.data.video }
            video.comment_count -= 1
            this.setData({ video })

            wx.showToast({
              title: '删除成功',
              icon: 'success'
            })
          } catch (error) {
            console.error('删除评论失败:', error)
            wx.showToast({
              title: '删除失败',
              icon: 'none'
            })
          }
        }
      }
    })
  },

  // 查看房源详情
  goToProperty() {
    if (this.data.video?.property?.id) {
      wx.navigateTo({
        url: `/pages/property/detail/detail?id=${this.data.video.property.id}`
      })
    }
  },

  // 查看经纪人主页
  goToAgent() {
    wx.navigateTo({
      url: `/pages/agent/detail/detail?id=${this.data.video.agent_id}`
    })
  }
})
