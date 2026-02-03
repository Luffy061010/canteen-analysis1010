
export const COLLEGES_MAJORS = {
    '计算机学院': {
        'majors': ['计算机科学与技术', '软件工程', '人工智能', '数据科学与大数据技术'],
        'code': '01'
    },
    '电子信息学院': {
        'majors': ['电子信息工程', '通信工程', '微电子科学与工程', '光电信息科学与工程'],
        'code': '02'
    },
    '机械工程学院': {
        'majors': ['机械工程', '智能制造工程', '车辆工程', '工业设计'],
        'code': '03'
    },
    '管理学院': {
        'majors': ['工商管理', '会计学', '市场营销', '人力资源管理'],
        'code': '04'
    },
    '经济学院': {
        'majors': ['经济学', '金融学', '国际经济与贸易', '保险学'],
        'code': '05'
    }
}

// 专业代码映射，用于生成班级名称
export const MAJOR_CODE = {
    '计算机科学与技术': '计科',
    '软件工程': '软件',
    '人工智能': '智能',
    '数据科学与大数据技术': '数据',
    '电子信息工程': '电信',
    '通信工程': '通信',
    '微电子科学与工程': '微电子',
    '光电信息科学与工程': '光电',
    '机械工程': '机械',
    '智能制造工程': '智造',
    '车辆工程': '车辆',
    '工业设计': '工设',
    '工商管理': '工商',
    '会计学': '会计',
    '市场营销': '营销',
    '人力资源管理': '人力',
    '经济学': '经济',
    '金融学': '金融',
    '国际经济与贸易': '国贸',
    '保险学': '保险'
}

// 根据专业和年级生成班级列表（格式：计科2401）
export const generateClassNames = (major, grade) => {
    const majorCode = MAJOR_CODE[major]
    if (!majorCode || !grade) return []
    
    // 提取年级年份（如"2024级" -> "2024" -> "24"）
    const gradeYear = grade.replace('级', '')
    // 只取年份的后两位数字（如"2024" -> "24"）
    const yearSuffix = gradeYear.length >= 4 ? gradeYear.slice(-2) : gradeYear
    
    // 生成班级列表，每个专业通常有1-5个班
    const classes = []
    for (let i = 1; i <= 5; i++) {
        const className = `${majorCode}${yearSuffix}${String(i).padStart(2, '0')}`
        classes.push(className)
    }
    return classes
}

// 兼容旧代码，保留MAJOR_CLAZZ
export const MAJOR_CLAZZ = MAJOR_CODE

