// pages/property/poster/poster.js
const app = getApp()

Page({
  data: {
    property: null,
    posterUrl: ''
  },

  onLoad(options) {
    try {
      const propertyStr = options.property || '{}'
      const property = JSON.parse(decodeURIComponent(propertyStr))
      this.setData({ property })
      this.generatePoster()
    } catch (e) {
      console.error('参数解析失败:', e)
      wx.showToast({ title: '参数错误', icon: 'none' })
    }
  },

  generatePoster() {
    const query = wx.createSelectorQuery()
    query.select('#posterCanvas')
      .fields({ node: true, size: true })
      .exec((res) => {
        if (!res[0] || !res[0].node) {
          console.error('Canvas not found')
          return
        }
        
        const canvas = res[0].node
        const ctx = canvas.getContext('2d')
        
        const dpr = wx.getSystemInfoSync().pixelRatio
        canvas.width = res[0].width * dpr
        canvas.height = res[0].height * dpr
        ctx.scale(dpr, dpr)
        
        const p = this.data.property || {}
        
        // 背景
        ctx.fillStyle = '#ffffff'
        ctx.fillRect(0, 0, 300, 480)
        
        // 顶部图片占位
        ctx.fillStyle = '#e0e0e0'
        ctx.fillRect(0, 0, 300, 160)
        
        // 标题
        ctx.fillStyle = '#1a1a1a'
        ctx.font = 'bold 16px sans-serif'
        const title = p.title || '房源标题'
        ctx.fillText(title.length > 15 ? title.substring(0, 15) + '...' : title, 20, 190)
        
        // 价格
        ctx.fillStyle = '#ff6b6b'
        ctx.font = 'bold 24px sans-serif'
        ctx.fillText(`¥${p.total_price || 0}万`, 20, 225)
        
        // 地址
        ctx.fillStyle = '#888888'
        ctx.font = '12px sans-serif'
        const address = `${p.province || ''} ${p.city || ''} ${p.district || ''}`
        ctx.fillText(address, 20, 255)
        
        // 标签
        ctx.fillStyle = '#e8f4ff'
        const roomText = `${p.rooms || 0}室${p.halls || 0}厅`
        ctx.fillRect(20, 275, 70, 22)
        ctx.fillStyle = '#4facfe'
        ctx.font = '11px sans-serif'
        ctx.fillText(roomText, 28, 290)
        
        ctx.fillStyle = '#e8f4ff'
        ctx.fillText(`${p.area || 0}㎡`, 100, 290)
        
        // 底部
        ctx.fillStyle = '#f8f9fa'
        ctx.fillRect(0, 400, 300, 80)
        
        ctx.fillStyle = '#666666'
        ctx.font = '11px sans-serif'
        ctx.fillText('长按识别二维码查看', 85, 430)
        ctx.fillText('县域房产平台', 110, 450)
        
        // 二维码占位
        ctx.fillStyle = '#dddddd'
        ctx.fillRect(20, 410, 50, 50)
      })
  },

  savePoster() {
    const query = wx.createSelectorQuery()
    query.select('#posterCanvas')
      .fields({ node: true, size: true })
      .exec((res) => {
        if (!res[0] || !res[0].node) {
          wx.showToast({ title: '生成失败', icon: 'none' })
          return
        }
        
        wx.canvasToTempFilePath({
          canvas: res[0].node,
          success: (result) => {
            wx.saveImageToPhotosAlbum({
              filePath: result.tempFilePath,
              success: () => {
                wx.showToast({ title: '保存成功', icon: 'success' })
              },
              fail: (err) => {
                if (err.errMsg.includes('auth deny')) {
                  wx.showModal({
                    title: '提示',
                    content: '需要授权保存图片到相册',
                    success: (res) => {
                      if (res.confirm) {
                        wx.openSetting()
                      }
                    }
                  })
                } else {
                  wx.showToast({ title: '保存失败', icon: 'none' })
                }
              }
            })
          },
          fail: () => {
            wx.showToast({ title: '生成失败', icon: 'none' })
          }
        })
      })
  },

  onShareAppMessage() {
    return {
      title: `${this.data.property.title} - ¥${this.data.property.total_price}万`,
      path: `/pages/property/detail/detail?id=${this.data.property.id}`
    }
  }
})
