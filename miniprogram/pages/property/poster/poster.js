// 房源海报生成
const app = getApp();

Page({
  data: {
    property: null,
    saving: false,
    canvasWidth: 375,
    canvasHeight: 600
  },

  onLoad(options) {
    const { id, title, price, area, rooms, halls, community, cover } = options;
    if (!id) {
      wx.showToast({ title: '缺少房源信息', icon: 'none' });
      setTimeout(() => wx.navigateBack(), 1500);
      return;
    }
    this.setData({
      property: {
        id, title: decodeURIComponent(title || ''),
        price: parseFloat(price) || 0,
        area: parseFloat(area) || 0,
        rooms: parseInt(rooms) || 0,
        halls: parseInt(halls) || 0,
        community: decodeURIComponent(community || ''),
        cover: decodeURIComponent(cover || '')
      }
    });
    this.drawPoster();
  },

  async drawPoster() {
    const { property, canvasWidth, canvasHeight } = this.data;
    const query = wx.createSelectorQuery();
    query.select('#posterCanvas').fields({ node: true, size: true }).exec((res) => {
      if (!res || !res[0]) return;
      const canvas = res[0].node;
      const ctx = canvas.getContext('2d');
      const dpr = wx.getSystemInfoSync().pixelRatio;
      canvas.width = canvasWidth * dpr;
      canvas.height = canvasHeight * dpr;
      ctx.scale(dpr, dpr);

      // 白色背景
      ctx.fillStyle = '#ffffff';
      ctx.fillRect(0, 0, canvasWidth, canvasHeight);

      // 顶部渐变色条
      const gradient = ctx.createLinearGradient(0, 0, canvasWidth, 0);
      gradient.addColorStop(0, '#667eea');
      gradient.addColorStop(1, '#764ba2');
      ctx.fillStyle = gradient;
      ctx.fillRect(0, 0, canvasWidth, 8);

      // 标题
      ctx.fillStyle = '#1a1a2e';
      ctx.font = 'bold 20px sans-serif';
      const title = property.title.length > 18 ? property.title.slice(0, 18) + '...' : property.title;
      ctx.fillText(title, 24, 50);

      // 房源图片
      if (property.cover) {
        const img = canvas.createImage();
        img.src = property.cover;
        img.onload = () => {
          ctx.drawImage(img, 24, 72, canvasWidth - 48, 220);
          this.drawInfo(ctx, canvasWidth);
        };
        img.onerror = () => this.drawInfo(ctx, canvasWidth);
      } else {
        // 占位图
        ctx.fillStyle = '#f0f0f0';
        ctx.fillRect(24, 72, canvasWidth - 48, 220);
        ctx.fillStyle = '#ccc';
        ctx.font = '40px sans-serif';
        ctx.fillText('🏠', canvasWidth / 2 - 24, 200);
        this.drawInfo(ctx, canvasWidth);
      }
    });
  },

  drawInfo(ctx, w) {
    const { property } = this.data;
    const priceWan = (property.price / 10000).toFixed(0);

    // 价格
    ctx.fillStyle = '#ff4d4f';
    ctx.font = 'bold 36px sans-serif';
    ctx.fillText(priceWan + '万', 24, 340);
    ctx.fillStyle = '#999';
    ctx.font = '14px sans-serif';
    ctx.fillText(property.transaction_type ? '元/月' : '元/套', 24 + ctx.measureText(priceWan + '万').width + 8, 340);

    // 标签
    const tags = [];
    if (property.rooms) tags.push(property.rooms + '室' + property.halls + '厅');
    if (property.area) tags.push(property.area + '㎡');
    if (property.community) tags.push(property.community);
    ctx.fillStyle = '#667eea';
    ctx.font = '14px sans-serif';
    let tagX = 24;
    tags.forEach(t => {
      const tw = ctx.measureText(t).width + 20;
      ctx.fillStyle = '#e6e9ff';
      ctx.beginPath();
      this.roundRect(ctx, tagX, 358, tw, 26, 13);
      ctx.fill();
      ctx.fillStyle = '#667eea';
      ctx.fillText(t, tagX + 10, 376);
      tagX += tw + 10;
    });

    // 分割线
    ctx.strokeStyle = '#eee';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(24, 410);
    ctx.lineTo(w - 24, 410);
    ctx.stroke();

    // 底部信息
    ctx.fillStyle = '#666';
    ctx.font = '13px sans-serif';
    ctx.fillText('扫码查看房源详情', 24, 450);
    ctx.fillText('县域房产平台 · 找好房安好家', 24, 472);

    // 小程序码占位
    ctx.fillStyle = '#f5f5f5';
    ctx.fillRect(w - 120, 430, 96, 96);
    ctx.fillStyle = '#ccc';
    ctx.font = '11px sans-serif';
    ctx.fillText('小程序码', w - 100, 485);
  },

  roundRect(ctx, x, y, w, h, r) {
    ctx.moveTo(x + r, y);
    ctx.lineTo(x + w - r, y);
    ctx.arc(x + w - r, y + r, r, Math.PI * 1.5, 0);
    ctx.lineTo(x + w, y + h - r);
    ctx.arc(x + w - r, y + h - r, r, 0, Math.PI * 0.5);
    ctx.lineTo(x + r, y + h);
    ctx.arc(x + r, y + h - r, r, Math.PI * 0.5, Math.PI);
    ctx.lineTo(x, y + r);
    ctx.arc(x + r, y + r, r, Math.PI, Math.PI * 1.5);
    ctx.closePath();
  },

  redraw() {
    this.drawPoster();
  },

  async savePoster() {
    this.setData({ saving: true });
    const query = wx.createSelectorQuery();
    query.select('#posterCanvas').fields({ node: true }).exec((res) => {
      if (!res || !res[0]) return;
      wx.canvasToTempFilePath({
        canvas: res[0].node,
        success: (result) => {
          wx.saveImageToPhotosAlbum({
            filePath: result.tempFilePath,
            success: () => {
              wx.showToast({ title: '已保存到相册', icon: 'success' });
              this.setData({ saving: false });
            },
            fail: (err) => {
              if (err.errMsg.includes('auth deny')) {
                wx.showModal({
                  title: '需要相册权限',
                  content: '请在设置中允许小程序保存图片到相册',
                  confirmText: '去设置',
                  success: (r) => {
                    if (r.confirm) wx.openSetting();
                  }
                });
              }
              this.setData({ saving: false });
            }
          });
        },
        fail: () => {
          wx.showToast({ title: '生成失败', icon: 'none' });
          this.setData({ saving: false });
        }
      });
    });
  },

  onShareAppMessage() {
    return { title: '好房推荐 - ' + (this.data.property?.title || ''), path: '/pages/index/index' };
  }
});
