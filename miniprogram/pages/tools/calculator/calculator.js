// 房贷计算器
const api = require('../../../utils/api')

Page({
  data: {
    // 贷款信息
    principal: 500000,      // 贷款本金（元）
    annualRate: 4.9,        // 年利率（%）
    years: 30,              // 贷款年限（年）
    paymentType: 'equal_principal_interest', // 还款方式

    // 计算结果
    monthlyPayment: 0,      // 月供
    totalInterest: 0,       // 总利息
    totalPayment: 0,        // 总还款额
    paymentSchedule: [],    // 还款计划

    // 界面状态
    calculating: false,
    showResult: false
  },

  /**
   * 页面加载
   */
  onLoad(options) {
    this.calculate()
  },

  /**
   * 输入变化
   */
  onInputChange(e) {
    const { field } = e.currentTarget.dataset
    let value = e.detail.value

    // 转换数字
    if (field !== 'paymentType') {
      value = parseFloat(value) || 0
    }

    this.setData({
      [field]: value,
      showResult: false
    })

    // 自动计算
    this.calculate()
  },

  /**
   * 切换还款方式
   */
  switchPaymentType(e) {
    const type = e.currentTarget.dataset.type
    this.setData({
      paymentType: type,
      showResult: false
    })
    this.calculate()
  },

  /**
   * 计算房贷
   */
  async calculate() {
    const { principal, annualRate, years, paymentType } = this.data

    if (!principal || !annualRate || !years) {
      return
    }

    this.setData({ calculating: true })

    try {
      const res = await api.post('/tools/mortgage-calculator', {
        principal: principal,
        annual_rate: annualRate,
        years: years,
        payment_type: paymentType
      }, false)

      this.setData({
        monthlyPayment: res.monthly_payment || 0,
        totalInterest: res.total_interest || 0,
        totalPayment: res.total_payment || 0,
        paymentSchedule: res.payment_schedule || [],
        showResult: true,
        calculating: false
      })
    } catch (err) {
      console.error('计算失败:', err)
      this.setData({ calculating: false })
    }
  },

  /**
   * 重置
   */
  reset() {
    this.setData({
      principal: 500000,
      annualRate: 4.9,
      years: 30,
      paymentType: 'equal_principal_interest',
      showResult: false
    })
  },

  /**
   * 分享
   */
  onShareAppMessage() {
    return {
      title: '房贷计算器 - 县域房产平台',
      path: '/pages/tools/calculator/calculator'
    }
  }
})
