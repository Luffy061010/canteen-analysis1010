import axios from 'axios';
import { ElMessageBox, ElMessage } from 'element-plus';
import { clearAuthToken, clearStoredUserInfo, getAuthToken } from '@/utils/auth';

// 创建axios实例 - 修复环境变量引用
const apiService = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:3000/api',
    timeout: 10000,
});

// 请求拦截器
apiService.interceptors.request.use(
    (config) => {
        const token = getAuthToken();
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// 响应拦截器
apiService.interceptors.response.use(
    (response) => {
        return response.data;
    },
    (error) => {
        if (error.response) {
            const status = error.response.status
            switch (status) {
                case 401:
                    // 不要自动清除 token 并跳转，弹窗提示用户会话过期，用户确认后再清理并跳转
                    ElMessageBox.confirm(
                        '登录已过期，请重新登录',
                        '提示',
                        { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
                    ).then(() => {
                        clearAuthToken();
                        clearStoredUserInfo();
                        window.location.href = '/login';
                    }).catch(() => {
                        // 用户取消，不自动登出
                    })
                    break;
                case 403:
                    ElMessage.error('没有权限访问该资源');
                    break;
                case 404:
                    ElMessage.error('请求的资源不存在');
                    break;
                case 500:
                    ElMessage.error('服务器内部错误');
                    break;
                default:
                    ElMessage.error(`请求失败 (${status})`);
            }
        } else {
            ElMessage.error('网络错误，请检查网络连接');
        }
        return Promise.reject(error);
    }
);

// API模块
const api = {
    student: {
        getList: (params) => apiService.get('/students', { params }),
        getDetail: (id) => apiService.get(`/students/${id}`),
        update: (id, data) => apiService.put(`/students/${id}`, data),
        create: (data) => apiService.post('/students', data),
        delete: (id) => apiService.delete(`/students/${id}`),
    },
    consumption: {
        getList: (params) => apiService.get('/consumptions', { params }),
        getDetail: (id) => apiService.get(`/consumptions/${id}`),
        getStatistics: (params) => apiService.get('/consumptions/statistics', { params }),
        driftDetection: (data) => apiService.post('/consumptions/drift-detection', data),
        povertyIdentification: (data) => apiService.post('/consumptions/poverty-identification', data),
        scoreCorrelation: (data) => apiService.post('/consumptions/score-correlation', data),
    },
    system: {
        getOverview: () => apiService.get('/system/overview'),
        getAlerts: (params) => apiService.get('/system/alerts', { params }),
    },
    auth: {
        login: (data) => apiService.post('/auth/login', data),
        logout: () => apiService.post('/auth/logout'),
        getUserInfo: () => apiService.get('/auth/userinfo'),
    },
};

export { apiService, api };
export default apiService;
