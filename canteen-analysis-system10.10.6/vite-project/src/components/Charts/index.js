import BaseChart from './BaseChart.vue'

// 全局注册（可选）
const install = (app) => {
    app.component('BaseChart', BaseChart)
}

// 导出组件
export {
    BaseChart,
    install
}

// 默认导出
export default {
    install
}