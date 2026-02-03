import * as echarts from 'echarts'

// 默认颜色配置
export const defaultColors = [
    '#409EFF', '#67C23A', '#E6A23C', '#F56C6C', '#909399',
    '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7'
]

// 创建基础配置
export const createBaseOptions = (options = {}) => {
    return {
        tooltip: {
            trigger: 'axis',
            axisPointer: {
                type: 'shadow'
            }
        },
        grid: {
            left: '3%',
            right: '4%',
            bottom: '3%',
            containLabel: true
        },
        ...options
    }
}

// 创建折线图配置
export const createLineChartOptions = (xAxisData, seriesData, options = {}) => {
    return {
        xAxis: {
            type: 'category',
            data: xAxisData,
            axisLine: { lineStyle: { color: '#DCDFE6' } },
            axisLabel: { color: '#606266' }
        },
        yAxis: {
            type: 'value',
            axisLine: { lineStyle: { color: '#DCDFE6' } },
            axisLabel: { color: '#606266' },
            splitLine: { lineStyle: { color: '#F2F6FC', type: 'dashed' } }
        },
        series: seriesData.map((series, index) => ({
            name: series.name,
            type: 'line',
            data: series.data,
            smooth: true,
            itemStyle: { color: defaultColors[index] },
            lineStyle: { width: 3, color: defaultColors[index] }
        })),
        color: defaultColors,
        ...options
    }
}

// 创建柱状图配置
export const createBarChartOptions = (xAxisData, seriesData, options = {}) => {
    return {
        xAxis: {
            type: 'category',
            data: xAxisData,
            axisLine: { lineStyle: { color: '#DCDFE6' } },
            axisLabel: { color: '#606266' }
        },
        yAxis: {
            type: 'value',
            axisLine: { lineStyle: { color: '#DCDFE6' } },
            axisLabel: { color: '#606266' },
            splitLine: { lineStyle: { color: '#F2F6FC', type: 'dashed' } }
        },
        series: seriesData.map((series, index) => ({
            name: series.name,
            type: 'bar',
            data: series.data,
            itemStyle: { color: defaultColors[index] }
        })),
        color: defaultColors,
        ...options
    }
}

// 创建饼图配置
export const createPieChartOptions = (seriesData, options = {}) => {
    return {
        tooltip: {
            trigger: 'item',
            formatter: '{a} <br/>{b}: {c} ({d}%)'
        },
        legend: {
            orient: 'vertical',
            right: 10,
            top: 'center',
            textStyle: { color: '#606266' }
        },
        series: [{
            name: seriesData.name || '数据',
            type: 'pie',
            radius: ['50%', '70%'],
            avoidLabelOverlap: false,
            itemStyle: {
                borderColor: '#fff',
                borderWidth: 2
            },
            label: {
                show: false,
                position: 'center'
            },
            emphasis: {
                label: {
                    show: true,
                    fontSize: '16',
                    fontWeight: 'bold'
                }
            },
            labelLine: {
                show: false
            },
            data: seriesData.data,
            color: defaultColors
        }],
        ...options
    }
}

// 响应式调整
export const responsiveChart = (chartInstance) => {
    const handleResize = () => {
        if (chartInstance) {
            chartInstance.resize()
        }
    }

    window.addEventListener('resize', handleResize)

    return () => {
        window.removeEventListener('resize', handleResize)
    }
}

// 格式化数字
export const formatNumber = (num) => {
    if (num >= 10000) {
        return (num / 10000).toFixed(1) + '万'
    }
    if (num >= 1000) {
        return (num / 1000).toFixed(1) + '千'
    }
    return num.toString()
}

// 下载图表为图片
export const downloadChartAsImage = (chartInstance, filename = 'chart') => {
    if (!chartInstance) return

    const dataURL = chartInstance.getDataURL({
        type: 'png',
        pixelRatio: 2,
        backgroundColor: '#fff'
    })

    const link = document.createElement('a')
    link.href = dataURL
    link.download = `${filename}_${new Date().getTime()}.png`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
}