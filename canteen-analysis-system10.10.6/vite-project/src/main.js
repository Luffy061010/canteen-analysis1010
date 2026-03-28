import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import App from './App.vue'
import router from './router'
import components from './components'
import { resetBootLoginPassed } from './utils/auth'
import './styles/global.scss'

// 创建应用实例
const app = createApp(App)

// 每次页面完整启动时重置启动登录门禁，确保先显示登录页。
resetBootLoginPassed()

// 注册所有图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// UI 组件库与中文本地化
app.use(ElementPlus, {
  locale: zhCn
})

// 路由与全局组件注册
app.use(router)
app.use(components)
app.mount('#app')

