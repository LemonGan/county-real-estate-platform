// 房贷计算器 - 纯本地计算
Page({
  data: {
    totalPrice: 50,           // 房屋总价（万元）
    downPaymentRatio: 30,     // 首付比例
    annualRate: 3.95,         // LPR 利率
    years: 30,                // 贷款年限
    paymentType: 'equal_interest', // 等额本息 / 等额本金

    downPayment: 0,           // 首付金额（万元）
    principal: 0,             // 贷款本金（万元）
    monthlyPayment: 0,        // 月供（元）
    totalInterest: 0,         // 总利息（万元）
    totalPayment: 0,          // 总还款（万元）
    firstMonth: 0,            // 首月月供（等额本金专用）

    yearOptions: ['5','10','15','20','25','30'],
    yearIndex: 5,
    showResult: false
  },

  onLoad() { this.doCalculate(); },

  setQuickPrice(e) {
    this.setData({ totalPrice: e.currentTarget.dataset.val });
    this.doCalculate();
  },

  setRatio(e) {
    this.setData({ downPaymentRatio: e.currentTarget.dataset.val });
    this.doCalculate();
  },

  switchType(e) {
    this.setData({ paymentType: e.currentTarget.dataset.type });
    this.doCalculate();
  },

  onYearChange(e) {
    const idx = parseInt(e.detail.value);
    this.setData({ yearIndex: idx, years: parseInt(this.data.yearOptions[idx]) });
    this.doCalculate();
  },

  onInputChange(e) {
    const { field } = e.currentTarget.dataset;
    this.setData({ [field]: parseFloat(e.detail.value) || 0 });
  },

  doCalculate() {
    const { totalPrice, downPaymentRatio, annualRate, years, paymentType } = this.data;
    if (!totalPrice || !years || !annualRate) return;

    const totalYuan = totalPrice * 10000;
    const down = totalYuan * downPaymentRatio / 100;
    const loan = totalYuan - down;
    const months = years * 12;
    const monthRate = annualRate / 100 / 12;

    let monthly, totalInt, totalPay, first;

    if (paymentType === 'equal_interest') {
      // 等额本息: M = P * r * (1+r)^n / ((1+r)^n - 1)
      const pow = Math.pow(1 + monthRate, months);
      monthly = Math.round(loan * monthRate * pow / (pow - 1));
      totalPay = monthly * months;
      totalInt = totalPay - loan;
      first = monthly;
    } else {
      // 等额本金: 每月本金=P/n, 每月利息=剩余本金*r
      const monthlyPrincipal = Math.round(loan / months);
      first = monthlyPrincipal + Math.round(loan * monthRate);
      totalInt = 0;
      let remaining = loan;
      for (let i = 0; i < months; i++) {
        totalInt += Math.round(remaining * monthRate);
        remaining -= monthlyPrincipal;
      }
      totalPay = loan + totalInt;
      monthly = Math.round(first - (first - (monthlyPrincipal + Math.round(remaining * monthRate))) / months * (months - 1));
    }

    this.setData({
      downPayment: (down / 10000).toFixed(1),
      principal: (loan / 10000).toFixed(1),
      monthlyPayment: Math.round(monthly).toLocaleString(),
      totalInterest: (totalInt / 10000).toFixed(2),
      totalPayment: (totalPay / 10000).toFixed(2),
      firstMonth: Math.round(first).toLocaleString(),
      showResult: true
    });
  },

  onShareAppMessage() {
    return { title: '房贷计算器 - 县域房产平台', path: '/pages/tools/calculator/calculator' };
  }
});
