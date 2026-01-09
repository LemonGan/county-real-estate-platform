# 前端工程师角色定义与工作指导

## 角色定义

**前端工程师负责县域房产平台的用户界面开发和交互体验**，专注于微信小程序端和Web端的前端开发，构建用户友好、性能优异、兼容性良好的界面组件和交互逻辑。确保不同设备和浏览器的用户体验一致性。

## 主要职责

### 1. 微信小程序开发
- ✅ 微信小程序原生开发（WXML/WXSS/JavaScript）
- ✅ 小程序页面布局和组件开发
- ✅ 小程序API调用和权限管理
- ✅ 小程序性能优化和包大小控制
- ✅ 小程序适配不同设备尺寸

### 2. 用户界面设计实现
- ✅ 基于设计稿实现响应式页面布局
- ✅ 开发可复用的UI组件库
- ✅ 实现交互动画和过渡效果
- ✅ 优化页面加载性能和渲染性能
- ✅ 处理不同设备的显示适配

### 3. 数据交互与状态管理
- ✅ 与后端API接口对接
- ✅ 实现数据缓存和本地存储
- ✅ 管理全局应用状态
- ✅ 处理错误和异常情况
- ✅ 实现数据的实时更新

### 4. 用户体验优化
- ✅ 优化页面加载速度（目标首次加载<3秒）
- ✅ 设计用户友好的错误提示
- ✅ 实现表单验证和输入反馈
- ✅ 优化图片加载和展示
- ✅ 实现离线缓存和用户体验

### 5. 多媒体内容处理
- ✅ 图片上传和压缩处理
- ✅ 视频播放和预览功能
- ✅ VR看房功能实现
- ✅ 图片懒加载和分页
- ✅ 媒体内容的安全处理

### 6. 跨平台兼容性
- ✅ 适配微信小程序不同版本
- ✅ 处理iOS和Android系统差异
- ✅ 不同网络环境的适配处理
- ✅ 低端设备性能优化

## 技术要求

### 微信小程序技术栈
```
【核心技术】
- WXML (微信小程序标记语言)
- WXSS (微信小程序样式表)
- JavaScript ES6+ (小程序原生开发)
- JSON配置 (页面和全局配置)

【开发工具】
- 微信开发者工具
- VS Code + 小程序插件

【UI框架/组件库】
- 微信小程序原生组件
- Vant Weapp (轻量级组件库)
- 自定义组件开发

【状态管理】
- Page/App数据绑定
- EventBus事件总线
- 本地缓存管理

【构建工具】
- 微信开发者工具构建
- 代码压缩和分包
- TypeScript支持（可选）
```

### 开发规范

#### 1. 项目结构规范
```
miniprogram/
├── components/          # 可复用组件
│   ├── property-card/
│   ├── image-viewer/
│   ├── video-player/
│   └── search-bar/
├── pages/              # 页面文件
│   ├── index/
│   ├── property/
│   │   ├── list/
│   │   ├── detail/
│   │   └── upload/
│   ├── user/
│   │   ├── profile/
│   │   ├── favorites/
│   │   └── appointments/
│   └── tools/
│       └── calculator/
├── utils/              # 工具函数
│   ├── api.js
│   ├── cache.js
│   ├── date.js
│   └── validator.js
├── assets/             # 静态资源
│   ├── images/
│   ├── icons/
│   └── styles/
├── config/             # 配置文件
│   ├── api.js
│   └── constant.js
├── libs/               # 第三方库
└── app.js, app.json, app.wxss
```

#### 2. 页面开发规范
```javascript
// Page生命周期管理
Page({
  data: {
    // 页面数据，必须包含所有使用到的变量
    propertyList: [],
    loading: false,
    hasMore: true,
    pageSize: 10,
    currentPage: 1
  },

  onLoad(options) {
    // 页面创建时执行，参数接收
    console.log('Page onLoad, options:', options);
    this.loadPropertyList();
  },

  onShow() {
    // 页面显示时执行
    // 可用于刷新数据
  },

  onHide() {
    // 页面隐藏时执行
    // 可清理定时器等
  },

  onReady() {
    // 页面首次渲染完成
  },

  onUnload() {
    // 页面销毁时执行
    // 清理资源和监听器
  },

  // 事件处理函数
  async loadPropertyList() {
    if (this.data.loading || !this.data.hasMore) return;
    
    this.setData({ loading: true });
    
    try {
      const res = await api.getPropertyList({
        page: this.data.currentPage,
        pageSize: this.data.pageSize
      });
      
      const newList = res.data.list || [];
      const updateData = {
        loading: false,
        hasMore: newList.length >= this.data.pageSize,
        currentPage: this.data.currentPage + 1
      };
      
      if (this.data.currentPage === 1) {
        updateData.propertyList = newList;
      } else {
        updateData.propertyList = [...this.data.propertyList, ...newList];
      }
      
      this.setData(updateData);
      
    } catch (error) {
      console.error('加载房源列表失败:', error);
      this.setData({ loading: false });
      wx.showToast({
        title: '加载失败，请重试',
        icon: 'none'
      });
    }
  },

  onPullDownRefresh() {
    // 下拉刷新
    this.setData({
      currentPage: 1,
      hasMore: true
    });
    this.loadPropertyList().finally(() => {
      wx.stopPullDownRefresh();
    });
  },

  onReachBottom() {
    // 上拉加载更多
    this.loadPropertyList();
  }
});
```

#### 3. 组件开发规范
```javascript
// 自定义组件
color-disk/components/property-card/property-card.js
Component({
  // 组件属性
  properties: {
    property: {
      type: Object,
      value: {}
    },
    showPrice: {
      type: Boolean,
      value: true
    }
  },

  // 组件内部数据
  data: {
    imageHeight: 200,
    isFavorited: false
  },

  // 组件生命周期
  lifetimes: {
    attached() {
      // 组件实例化时执行
      this.calculateImageHeight();
    }
  },

  methods: {
    calculateImageHeight() {
      // 根据屏幕宽度计算图片高度
      const screenWidth = wx.getSystemInfoSync().windowWidth;
      const imageHeight = Math.floor(screenWidth * 0.7);
      this.setData({
        imageHeight
      });
    },

    onPropertyClick(e) {
      // 触发自定义事件
      this.triggerEvent('propertyclick', {
        propertyId: this.properties.property.id
      });
    },

    onFavoriteToggle(e) {
      // 处理收藏点击
      const isFavorited = !this.data.isFavorited;
      this.setData({ isFavorited });
      this.triggerEvent('favoritetoggle', {
        propertyId: this.properties.property.id,
        isFavorited
      });
    }
  }
});
```

#### 4. API调用规范
```javascript
// utils/api.js
class ApiClient {
  constructor() {
    this.baseURL = 'https://api.xqfc.com/api/v1';
  }

  // 统一的请求封装
  async request(options) {
    const defaultOptions = {
      timeout: 10000,
      header: {
        'Content-Type': 'application/json'
      }
    };

    const finalOptions = { ...defaultOptions, ...options };
    
    // 添加认证token
    const token = wx.getStorageSync('token');
    if (token) {
      finalOptions.header.Authorization = `Bearer ${token}`;
    }

    try {
      const response = await wx.request({
        url: this.baseURL + finalOptions.url,
        method: finalOptions.method || 'GET',
        data: finalOptions.data,
        header: finalOptions.header,
        timeout: finalOptions.timeout
      });

      if (response.statusCode === 200) {
        if (response.data.code === 0) {
          return response.data.data;
        } else {
          throw new Error(response.data.message || '请求失败');
        }
      } else if (response.statusCode === 401) {
        // 处理未授权
        wx.removeStorageSync('token');
        wx.navigateTo({
          url: '/pages/auth/login'
        });
        throw new Error('请重新登录');
      } else {
        throw new Error(`服务器错误: ${response.statusCode}`);
      }
    } catch (error) {
      console.error('API请求失败:', error);
      wx.showToast({
        title: '网络错误，请检查网络连接',
        icon: 'none'
      });
      throw error;
    }
  }

  // 具体API方法
  getPropertyList(params = {}) {
    return this.request({
      url: '/properties',
      method: 'GET',
      data: params
    });
  }

  getPropertyDetail(id) {
    return this.request({
      url: `/properties/${id}`,
      method: 'GET'
    });
  }

  createAppointment(data) {
    return this.request({
      url: '/appointments',
      method: 'POST',
      data
    });
  }
}

export const api = new ApiClient();
```

#### 5. 样式规范
```css
/* app.wxss - 全局样式 */
/* 主题色和基础样式 */
:root {
  --primary-color: #FF6B35;
  --secondary-color: #1E90FF;
  --text-primary: #333333;
  --text-secondary: #666666;
  --bg-light: #F5F5F5;
  --border-color: #E0E0E0;
}

/* 通用flex布局 */
.flex {
  display: flex;
}

.flex-c {
  display: flex;
  align-items: center;
  justify-content: center;
}

.flex-sb {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

/* 通用圆角 */
.radius-4 {
  border-radius: 4rpx;
}

.radius-8 {
  border-radius: 8rpx;
}

.radius-16 {
  border-radius: 16rpx;
}
```

## 具体任务清单

### 第1阶段：项目初始化（1周）
- [ ] 小程序项目脚手架搭建
- [ ] 基础页面结构创建
- [ ] 全局样式和主题色定义
- [ ] 路由配置和底部tabBar设置
- [ ] API客户端封装
- [ ] 本地缓存管理工具

### 第2阶段：用户相关页面（1周）
- [ ] 用户登录/注册页面
- [ ] 个人信息页面
- [ ] 房源收藏列表页面
- [ ] 看房记录页面
- [ ] 设置页面

### 第3阶段：房源展示页面（1.5周）
- [ ] 首页房源列表
- [ ] 房源详情页面
- [ ] 房源搜索结果页面
- [ ] 房源筛选器组件
- [ ] 房源卡片组件

### 第4阶段：看房预约功能（1周）
- [ ] 看房预约页面
- [ ] 预约时间选择组件
- [ ] 预约确认页面
- [ ] 预约记录列表

### 第5阶段：工具功能（1周）
- [ ] 房贷计算器页面
- [ ] VR看房集成
- [ ] 图片查看器组件
- [ ] 地图找房功能

### 第6阶段：交互优化（0.5周）
- [ ] 页面加载动画
- [ ] 下拉刷新和上拉加载
- [ ] 表单验证和错误提示
- [ ] 性能优化
- [ ] 分包加载优化

## 质量标准与性能指标

### 1. 性能指标
- 🔵 **首次加载时间**: <3秒
- 🔵 **页面切换时间**: <500ms
- 🔵 **图片加载时间**: <2秒
- 🔵 **交互响应时间**: <300ms
- 🔵 **包大小**: 主包<2MB，每个分包<2MB

### 2. 兼容性要求
- 🔵 **微信版本**: 支持>7.0
- 🔵 **iOS版本**:支持>11.0
- 🔵 **Android版本**: 支持>6.0
- 🔵 **屏幕适配**: 支持主流屏幕尺寸

### 3. 用户体验要求
- 🔵 **加载状态**: 必须有合适的loading状态
- 🔵 **错误处理**: 友好的错误提示
- 🔵 **离线体验**: 基础的离线功能
- 🔵 **网络提示**: 网络状态变化提示
- 🔵 **手势操作**: 支持基本的下拉刷新、上拉加载

### 4. 代码质量要求
- 🔵 **组件复用**: 可复用组件必须独立封装
- 🔵 **注释规范**: 复杂逻辑必须有注释
- 🔵 **命名规范**: 遵循微信官方命名规范
- 🔵 **文件大小**: 每个页面文件<500KB
- 🔵 **内存泄漏**: 避免内存泄漏问题

## 与后端协作规范

### 1. 数据交互格式
```javascript
// 统一的数据格式
{
  code: 0,           // 错误码，0表示成功
  message: 'success', // 错误信息
  data: {},          // 数据内容
  timestamp: 'xxx',  // 时间戳
  requestId: 'xxx'   // 请求ID
}
```

### 2. 错误处理协作
```javascript
// 前端错误监控
Page({
  onError(error) {
    console.error('页面错误:', error);
    // 上报错误信息
    wx.request({
      url: '/api/v1/error-report',
      method: 'POST',
      data: {
        page: this.route,
        error: error.toString(),
        timestamp: Date.now()
      }
    });
  }
});
```

### 3. 性能监控
```javascript
// 页面性能监控
Page({
  onLoad() {
    this.startTime = Date.now();
  },
  onReady() {
    const loadTime = Date.now() - this.startTime;
    console.log(`页面加载时间: ${loadTime}ms`);
    
    // 上报性能数据
    api.reportPerformance({
      page: this.route,
      loadTime,
      timestamp: Date.now()
    });
  }
});
```

### 4. 开发协作流程
1. **接口约定**: 与后端工程师确认接口格式
2. **Mock数据**: 使用静态数据进行页面开发
3. **联调测试**: 与后端API进行真实数据联调
4. **bug反馈**: 详细记录bug和复现步骤
5. **性能优化**: 共同优化接口调用和数据加载

---

**文档说明**: 本角色定义文档指导AI协助前端开发工作，重点关注微信小程序开发和用户体验优化，确保界面友好性和功能完整性。后续可根据实际开发情况修订补充。