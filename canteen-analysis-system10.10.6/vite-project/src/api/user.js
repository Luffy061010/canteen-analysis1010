// API 调用封装：Java 后端 + FastAPI 分析服务
import axios from 'axios'
import request from "@/utils/request";
import router from '@/router/index'
import { clearAuthToken, clearStoredUserInfo, getAuthToken } from "@/utils/auth";

// 使用环境变量配置API基础地址
// API_BASE_URL 为空时，由 request 实例的 /api 基础前缀负责；避免 /api/api 的重复
const RAW_API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';
const API_BASE_URL = RAW_API_BASE_URL === '/api' ? '' : RAW_API_BASE_URL;
const FASTAPI_BASE_URL = import.meta.env.VITE_FASTAPI_BASE_URL || '/fastapi';

// 独立的 FastAPI 客户端，防止被 Java 前缀再次代理
const fastapiRequest = axios.create({
    baseURL: FASTAPI_BASE_URL,
    timeout: 300000,
});

let fastapiUnauthorizedRedirecting = false

const formatDateOnly = (input) => {
    if (input === null || input === undefined || input === '') return ''

    if (Object.prototype.toString.call(input) === '[object Date]') {
        if (Number.isNaN(input.getTime())) return ''
        const year = input.getFullYear()
        const month = String(input.getMonth() + 1).padStart(2, '0')
        const day = String(input.getDate()).padStart(2, '0')
        return `${year}-${month}-${day}`
    }

    const raw = String(input).trim()
    if (!raw) return ''
    if (/^\d{4}-\d{2}-\d{2}$/.test(raw)) return raw

    const parsed = new Date(raw)
    if (Number.isNaN(parsed.getTime())) return ''
    const year = parsed.getFullYear()
    const month = String(parsed.getMonth() + 1).padStart(2, '0')
    const day = String(parsed.getDate()).padStart(2, '0')
    return `${year}-${month}-${day}`
}

fastapiRequest.interceptors.request.use((config) => {
    const token = getAuthToken();
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

fastapiRequest.interceptors.response.use(
    (response) => response.data,
    (error) => {
        if (error?.response?.status === 401) {
            clearAuthToken()
            clearStoredUserInfo()
            if (!fastapiUnauthorizedRedirecting) {
                fastapiUnauthorizedRedirecting = true
                const redirect = router.currentRoute?.value?.fullPath || '/'
                router.replace({ path: '/login', query: { redirect } }).finally(() => {
                    fastapiUnauthorizedRedirecting = false
                })
            }
        }
        return Promise.reject(error)
    }
);

// 统一参数处理函数
const buildParams = (form) => {
    const params = {}
    if (!form) return params

    const paramMap = {
        'grade': 'grade',
        'college': 'college',
        'major': 'major',
        'username': 'username',
        'action': 'action',
        'user_id': 'user_id',
        'class': 'className',
        'className': 'className',
        'studentId': 'studentId',
        'page': 'page',
        'pageSize': 'pageSize',
        'page_size': 'page_size',
        'timeBegin': 'timeBegin',
        'timeEnd': 'timeEnd',
        'time_begin': 'time_begin',
        'time_end': 'time_end',
        // FastAPI 参数常用下划线风格
        'timeBegin$fastapi': 'time_begin',
        'timeEnd$fastapi': 'time_end',
        'startDate': 'start_date',
        'endDate': 'end_date',
        'start_date': 'start_date',
        'end_date': 'end_date',
        'term': 'term',
        'correlationMethod': 'correlationMethod',
        'variable1': 'variable1',
        'driftMethod': 'driftMethod',
        'timeWindow': 'timeWindow',
        'clusterMethod': 'clusterMethod',
        'clusterNums': 'n_clusters',
        'n_clusters': 'n_clusters'
    }

    Object.keys(paramMap).forEach(key => {
        const paramKey = paramMap[key]
        const value = form[key]
        if (value !== null && value !== undefined && value !== '') {
            // 数值类型（分页）保持数字，其他转字符串
            if (paramKey === 'page' || paramKey === 'pageSize' || paramKey === 'page_size') {
                const num = Number(value)
                if (!Number.isNaN(num)) {
                    params[paramKey] = num
                }
            } else {
                const isDateParam = ['timeBegin', 'timeEnd', 'time_begin', 'time_end', 'start_date', 'end_date'].includes(paramKey)
                if (isDateParam) {
                    const normalized = formatDateOnly(value)
                    if (normalized) {
                        params[paramKey] = normalized
                    }
                } else {
                    params[paramKey] = String(value)
                }
            }
        }
    })

    return params
}

// ==================== 学生信息相关API ====================
export const getStudentInfo = (form) => {
    const params = buildParams(form)
    console.log('查询学生信息参数:', params)
    return request.get(`${API_BASE_URL}/basic_data/student/info`, {params})
}

export const getStudentScores = (params) => {
    if (!params || !params.studentId) {
        throw new Error('studentId is required')
    }
    const queryParams = buildParams(params)
    return request.get(`${API_BASE_URL}/basic_data/student/score`, {params: queryParams})
}

// ==================== 消费数据相关API ====================
const ensureTimeRange = (params = {}) => {
    const next = { ...params }
    if (!next.timeBegin || !next.timeEnd) {
        // 防止后端 SQL 拼接出现无 WHERE 时的语法错误，给一个超宽时间范围兜底
        next.timeBegin = next.timeBegin || '1970-01-01'
        next.timeEnd = next.timeEnd || '2099-12-31'
    }
    return next
}

export const getConsumption = (form) => {
    const params = ensureTimeRange(buildParams(form))
    return request.get(`${API_BASE_URL}/consumption_data/StudentConsumptionStat`, {
        params,
        timeout: 300000
    })
}

export const getConsumptionData = (form) => {
    const params = ensureTimeRange(buildParams(form))
    return request.get(`${API_BASE_URL}/consumption_data/StudentConsumption`, {
        params,
        timeout: 300000
    })
}

export const getConsumptionTop = (form) => {
    const params = ensureTimeRange(buildParams(form))
    return request.get(`${API_BASE_URL}/consumption_data/window/top/barAndPie`, {
        params,
        timeout: 300000
    })
}

export const getConsumptionGroup = (form) => {
    // 后端未提供 group 接口，复用 TOP 数据保证页面可用
    return getConsumptionTop(form)
}

// ==================== 分析相关API ====================
export const getScoreCorrelation = (form) => {
    const params = buildParams(form)
    return fastapiRequest.get(`/analysis/correlation`, { params })
}

export const getConsumptionDrift = (form) => {
    const params = buildParams(form)
    // 兜底时间范围，避免后端 400
    if (!params.timeBegin || !params.timeEnd) {
        params.timeBegin = params.timeBegin || '1970-01-01'
        params.timeEnd = params.timeEnd || '2099-12-31'
    }
    // 注意不要以 / 开头，否则会绕过 baseURL
    return fastapiRequest.get(`analysis/drift`, { params })
}

export const getPovertyIdentification = (form) => {
    const params = buildParams(form)
    return fastapiRequest.get(`/analysis/cluster`, { params })
}

// ==================== 汇总数据API ====================
export const getSummaryData = (form) => {
    const params = buildParams(form)
    return fastapiRequest.get(`/analysis/summary/data`, { params })
}

// ==================== 兼容性API ====================
export const getConsumptionDateQuery = (form) => {
    return getConsumptionData(form)
}

// ==================== 新增API（基于您的后端代码） ====================

// 获取学生列表
export const getStudentList = (form) => {
    const params = buildParams(form)
    return request.get(`${API_BASE_URL}/basic_data/student/list`, {params})
}

// 获取学生详情
export const getStudentDetail = (studentId) => {
    return request.get(`${API_BASE_URL}/basic_data/student/detail/${studentId}`)
}

// 添加学生
export const addStudent = (data) => {
    return request.post(`${API_BASE_URL}/basic_data/student/add`, data)
}

// 更新学生信息
export const updateStudent = (studentId, data) => {
    return request.put(`${API_BASE_URL}/basic_data/student/update/${studentId}`, data)
}

// 删除学生
export const deleteStudent = (studentId) => {
    return request.delete(`${API_BASE_URL}/basic_data/student/delete/${studentId}`)
}

// 导入学生数据
export const importStudents = (file) => {
    const formData = new FormData()
    formData.append('file', file)
    return request.post(`${API_BASE_URL}/basic_data/student/import`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
    })
}

// 导出学生数据
export const exportStudents = (params) => {
    return request.get(`${API_BASE_URL}/basic_data/student/export`, {
        params,
        responseType: 'blob'
    })
}

// 消费趋势分析
export const getConsumptionTrend = (form) => {
    // 未实现趋势接口，使用已有统计接口兜底
    return getConsumption(form)
}

// 窗口消费排名
export const getWindowRanking = (form) => {
    return getConsumptionTop(form)
}

// 贫困生鉴别分析
export const getPoorIdentification = (form) => {
    const params = buildParams(form)
    return fastapiRequest.get(`/analysis/cluster`, { params })
}

// 消费对比分析
export const getConsumptionCompare = (form) => {
    const params = buildParams(form)
    // 未发现真实接口，复用汇总接口保证不报错
    return fastapiRequest.get(`/analysis/summary/data`, { params })
}

// 获取仪表板数据
export const getDashboardData = () => {
    return request.get(`${API_BASE_URL}/dashboard/data`)
}

// 获取系统状态
export const getSystemStatus = () => {
    return request.get(`${API_BASE_URL}/system/status`)
}

// ========== 管理员申请相关 ==========
export const applyAdmin = (data) => {
    // data: { reason?: string }
    return fastapiRequest.post(`/admin/apply`, data)
}

export const getAdminApplications = (params) => {
    const queryParams = buildParams(params)
    return fastapiRequest.get(`/admin/applications`, { params: queryParams })
}

export const approveAdminApplication = (appId) => {
    return fastapiRequest.put(`/admin/applications/${appId}/approve`)
}

// ==================== 系统日志相关API ====================
// 获取系统日志列表
export const getSystemLogs = (params) => {
    const queryParams = buildParams(params)
    // 使用 fastapiRequest 指向 FastAPI 服务
    return fastapiRequest.get(`/logs`, { params: queryParams })
}

// 更细粒度的搜索接口（用户名/操作/日期范围）
export const searchLogs = (params) => {
    const queryParams = buildParams(params)
    return fastapiRequest.get(`/logs/search`, { params: queryParams })
}

export const getSystemLogStats = (params) => {
    const queryParams = buildParams(params)
    // 后端未实现统计接口，暂用 /logs 返回总量（前端可从响应 total 字段读取）
    return fastapiRequest.get(`/logs`, { params: queryParams })
}

// 导出系统日志
export const exportSystemLogs = (params) => {
    // 导出日志 CSV（管理员）
    return fastapiRequest.get(`/logs/export`, {
        params,
        responseType: 'blob'
    })
}

// 删除系统日志 - 后端未实现，保留占位（不可用）
export const deleteSystemLogs = (logIds) => {
    return fastapiRequest.delete(`/logs`, { data: { logIds } })
}

// ========== 用户管理（FastAPI） ==========
export const getUsers = (params) => {
    const queryParams = {}
    if (params?.page !== undefined) queryParams.page = Number(params.page)
    const pageSizeVal = params?.page_size ?? params?.pageSize
    if (pageSizeVal !== undefined) queryParams.page_size = Number(pageSizeVal)
    if (params?.username !== undefined && params?.username !== '') queryParams.username = String(params.username)
    if (params?.is_admin !== undefined && params?.is_admin !== '') queryParams.is_admin = Boolean(Number(params.is_admin))
    return fastapiRequest.get(`/users`, { params: queryParams })
}

export const addUserApi = (data) => {
    return fastapiRequest.post(`/users`, data)
}

export const deleteUserApi = (userId) => {
    return fastapiRequest.delete(`/users/${userId}`)
}

export const setUserRoleApi = (userId, isAdmin) => {
    return fastapiRequest.put(`/users/${userId}/role`, null, { params: { is_admin: isAdmin } })
}

export const updateUserStatusApi = (userId, isActive) => {
    return fastapiRequest.put(`/users/${userId}/status`, null, { params: { is_active: isActive } })
}

// ==================== 登录相关API ====================
export const login = (data) => {
    // 使用 FastAPI 登录
    return fastapiRequest.post(`/login`, data)
}

export const registerApi = (data) => {
    return fastapiRequest.post(`/register`, data)
}

export const forgotPasswordApi = (data) => {
    return fastapiRequest.post(`/forgot-password`, data)
}

export const logout = () => {
    return fastapiRequest.post(`/logout`)
}

export const getUserInfo = () => {
    return fastapiRequest.get(`/me`)
}
export const getstudentId = (studentId) => {
    return request.get(`${API_BASE_URL}/basic_data/student/detail/${studentId}`)
}

// 默认导出
export default {
    // 学生信息
    getStudentInfo,
    getStudentScores,
    getStudentList,
    getStudentDetail,
    addStudent,
    updateStudent,
    deleteStudent,
    importStudents,
    exportStudents,

    // 消费数据
    getConsumption,
    getConsumptionData,
    getConsumptionTop,
    getConsumptionGroup,
    getConsumptionTrend,
    getWindowRanking,
    getConsumptionDateQuery,

    // 分析功能
    getScoreCorrelation,
    getConsumptionDrift,
    getPovertyIdentification,
    getPoorIdentification,
    getConsumptionCompare,

    // 汇总数据
    getSummaryData,

    // 系统功能
    getDashboardData,
    getSystemStatus,

    // 系统日志
    getSystemLogs,
    getSystemLogStats,
    exportSystemLogs,
    deleteSystemLogs,

    // 用户管理
    getUsers,
    addUserApi,
    deleteUserApi,
    setUserRoleApi,
    updateUserStatusApi,
    // 管理员申请
    applyAdmin,
    getAdminApplications,
    approveAdminApplication,
    registerApi,
    forgotPasswordApi,

    // 登录
    login,
    logout,
    getUserInfo
}