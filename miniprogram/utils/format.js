// 格式化工具函数

/**
 * 格式化价格显示
 * @param {number} price - 价格（元）
 */
function formatPrice(price) {
  if (!price && price !== 0) return '价格面议'

  if (price >= 10000) {
    return (price / 10000).toFixed(2) + '万'
  }

  return price.toLocaleString()
}

/**
 * 格式化面积显示
 * @param {number} area - 面积（平方米）
 */
function formatArea(area) {
  if (!area) return '-'
  return area + '㎡'
}

/**
 * 格式化日期时间
 * @param {string} datetime - 日期时间字符串
 */
function formatDateTime(datetime) {
  if (!datetime) return '-'

  // 处理iOS日期格式兼容性
  let dateString = datetime
  if (typeof datetime === 'string') {
    dateString = datetime.replace(/\s+/g, 'T')
  }

  const date = new Date(dateString)
  const now = new Date()
  const diff = now - date

  // 小于1分钟
  if (diff < 60000) {
    return '刚刚'
  }

  // 小于1小时
  if (diff < 3600000) {
    return Math.floor(diff / 60000) + '分钟前'
  }

  // 小于1天
  if (diff < 86400000) {
    return Math.floor(diff / 3600000) + '小时前'
  }

  // 小于7天
  if (diff < 604800000) {
    return Math.floor(diff / 86400000) + '天前'
  }

  // 格式化日期
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')

  return `${year}-${month}-${day}`
}

/**
 * 格式化日期
 * @param {string|Date} date - 日期
 * @param {string} format - 格式模板，如 'YYYY-MM-DD', 'MM-DD'
 */
function formatDate(date, format = 'YYYY-MM-DD') {
  if (!date) return '-'

  // 处理iOS日期格式兼容性
  // iOS不支持 "2024-01-15 10:30:00"，需要转换为 "2024/01/15 10:30:00" 或 "2024-01-15T10:30:00"
  let dateString = date
  if (typeof date === 'string') {
    // 替换空格和冒号为iOS兼容格式
    dateString = date.replace(/\s+/g, 'T')
  }

  const d = date instanceof Date ? date : new Date(dateString)

  // 检查日期是否有效
  if (isNaN(d.getTime())) {
    return '-'
  }

  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const hours = String(d.getHours()).padStart(2, '0')
  const minutes = String(d.getMinutes()).padStart(2, '0')
  const seconds = String(d.getSeconds()).padStart(2, '0')

  return format
    .replace('YYYY', year)
    .replace('MM', month)
    .replace('DD', day)
    .replace('HH', hours)
    .replace('mm', minutes)
    .replace('ss', seconds)
}

/**
 * 格式化房源类型
 * @param {number} type - 房源类型
 */
function formatPropertyType(type) {
  const typeMap = {
    1: '住宅',
    2: '商铺',
    3: '写字楼',
    4: '别墅'
  }
  return typeMap[type] || '其他'
}

/**
 * 格式化交易类型
 * @param {number} type - 交易类型
 */
function formatTransactionType(type) {
  const typeMap = {
    1: '出售',
    2: '出租'
  }
  return typeMap[type] || '其他'
}

/**
 * 格式化房源状态
 * @param {number} status - 房源状态
 */
function formatPropertyStatus(status) {
  const statusMap = {
    1: '在售',
    2: '已售',
    3: '下架'
  }
  return statusMap[status] || '未知'
}

/**
 * 获取房源状态颜色
 * @param {number} status - 房源状态
 */
function getPropertyStatusColor(status) {
  const colorMap = {
    1: '#52c41a',     // 在售 - 绿色
    2: '#8c8c8c',     // 已售 - 灰色
    3: '#ff4d4f'      // 下架 - 红色
  }
  return colorMap[status] || '#8c8c8c'
}

/**
 * 格式化户型
 * @param {object} property - 房源对象
 */
function formatRoomType(property) {
  const { room_count, hall_count, bathroom_count } = property

  let roomType = ''

  if (room_count) {
    roomType += room_count + '室'
  }

  if (hall_count) {
    roomType += hall_count + '厅'
  }

  if (bathroom_count) {
    roomType += bathroom_count + '卫'
  }

  return roomType || '-'
}

/**
 * 截断文本
 * @param {string} text - 原文本
 * @param {number} length - 最大长度
 */
function truncateText(text, length = 20) {
  if (!text) return ''

  if (text.length <= length) {
    return text
  }

  return text.substring(0, length) + '...'
}

/**
 * 防抖函数
 * @param {function} fn - 要执行的函数
 * @param {number} delay - 延迟时间（毫秒）
 */
function debounce(fn, delay = 300) {
  let timer = null

  return function(...args) {
    if (timer) {
      clearTimeout(timer)
    }

    timer = setTimeout(() => {
      fn.apply(this, args)
    }, delay)
  }
}

/**
 * 节流函数
 * @param {function} fn - 要执行的函数
 * @param {number} interval - 时间间隔（毫秒）
 */
function throttle(fn, interval = 300) {
  let lastTime = 0

  return function(...args) {
    const now = Date.now()

    if (now - lastTime >= interval) {
      lastTime = now
      fn.apply(this, args)
    }
  }
}

module.exports = {
  formatPrice,
  formatArea,
  formatDateTime,
  formatDate,
  formatPropertyType,
  formatTransactionType,
  formatPropertyStatus,
  getPropertyStatusColor,
  formatRoomType,
  truncateText,
  debounce,
  throttle
}
