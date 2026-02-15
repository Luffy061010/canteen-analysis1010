// src/components/Layout/index.js
// 布局组件导出文件

// 导入布局组件
import BrandBar from './Layout/BrandBar.vue'
import Header from './Layout/Header.vue'
import Sidebar from './Layout/Sidebar.vue'

// 导出组件
export { BrandBar, Header, Sidebar }

// 默认导出
export default {
  install(app) {
    app.component('BrandBar', BrandBar)
    app.component('Header', Header)
    app.component('Sidebar', Sidebar)
  }
}