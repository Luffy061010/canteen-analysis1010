import { createRouter, createWebHistory } from 'vue-router'
import { getAuthToken, getStoredUserInfo } from '@/utils/auth'

// 定义路由配置
const routes = [
    {
        path: '/login',
        name: 'Login',
        component: () => import('../views/Login.vue'),
        meta: { title: '登录' }
    },
    {
        path: '/',
        name: 'Dashboard',
        component: () => import('../views/Dashboard.vue'),
        meta: { title: '首页' }
    },
    {
        path: '/users',
        name: 'Users',
        component: () => import('../views/Users.vue'),
        meta: { title: '用户管理' }
    },
    {
        path: '/logs',
        name: 'Logs',
        component: () => import('../views/Logs.vue'),
        meta: { title: '系统日志' }
    },
    {
        path: '/student-info',
        name: 'StudentInfo',
        component: () => import('../views/student_info/StudentInfo.vue'),
        meta: { title: '学生信息管理' }
    },
    {
        path: '/consumption-query',
        name: 'ConsumptionQuery',
        component: () => import('../views/ConsumptionQuery.vue'),
        meta: { title: '消费信息查询' }
    },
    {
        path: '/consumption-statistics',
        name: 'ConsumptionStatistics',
        component: () => import('../views/analysis/ConsumptionDataQuery.vue'),
        meta: { title: '消费数据统计' }
    },
    {
        path: '/user',
        name: 'UserHome',
        component: () => import('../modules/user-module/UserModule.vue'),
        meta: { title: '个人中心' }
    },
    {
        path: '/user-consumption',
        name: 'UserConsumptionQuery',
        component: () => import('../modules/user-module/UserConsumptionQuery.vue'),
        meta: { title: '个人消费查询' }
    },
    {
        path: '/user-portrait',
        name: 'UserPortrait',
        component: () => import('../modules/user-module/UserPortrait.vue'),
        meta: { title: '个人用户画像' }
    },
    {
        path: '/user-recent-changes',
        name: 'UserRecentChanges',
        component: () => import('../modules/user-module/UserConsumptionQuery.vue'),
        meta: { title: '个人消费查询' }
    },
    {
        path: '/system',
        name: 'SystemManagement',
        component: () => import('../views/SystemManagement.vue'),
        meta: { title: '系统管理', requiresAdmin: true }
    },
    {
        path: '/consumption-analysis',
        name: 'ConsumptionAnalysis',
        component: () => import('../views/ConsumptionAnalysis.vue'),
        redirect: '/consumption-analysis/drift-detection',
        meta: { title: '消费数据分析' },
        children: [
            {
                path: 'drift-detection',
                name: 'ConsumptionDrift',
                component: () => import('../views/analysis/ConsumptionDrift.vue'),
                meta: { title: '消费概念漂移检测' }
            },
            {
                path: 'user-portrait-analysis',
                name: 'UserPortraitAnalysis',
                component: () => import('../views/analysis/PovertyIdentification.vue'),
                meta: { title: '用户画像模块' }
            },
            {
                path: 'score-correlation',
                name: 'ScoreCorrelation',
                component: () => import('../views/analysis/ScoreCorrelation.vue'),
                meta: { title: '成绩关联分析' }
            }
        ]
    }
]

// 创建路由实例
const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes
})

// 路由守卫 - 权限验证和页面标题设置
router.beforeEach((to, from, next) => {
    if (to.meta && to.meta.title) {
        document.title = `${to.meta.title} - 用户消费分析系统 V1.0`
    }

    const token = getAuthToken()
    const isLoginRoute = to.path === '/login'

    if (!isLoginRoute && !token) {
        next({ path: '/login', query: { redirect: to.fullPath } })
        return
    }

    // 管理员路由校验
    if (to.meta && to.meta.requiresAdmin) {
        const info = getStoredUserInfo()
        if (!info || !info.is_admin) {
            console.warn('需要管理员权限：访问被阻止', to.path)
            next({ path: '/' })
            return
        }
    }

    next()
})

router.onError((error) => {
    console.error('路由错误:', error)
})

export default router


