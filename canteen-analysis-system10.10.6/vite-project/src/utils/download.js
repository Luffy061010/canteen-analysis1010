const escapeCsv = (value, key = '') => {
  if (value === null || value === undefined) return ''
  const raw = String(value)
  const normalized = raw.replace(/\r?\n/g, ' ')
  const lowerKey = String(key || '').toLowerCase()

  // 兼容 Excel：防止长数字（学号/用户ID等）被科学计数法显示
  const looksLikeLongNumber = /^\d{11,}$/.test(normalized)
  const looksLikeDateTime = /^\d{4}-\d{2}-\d{2}(?:[ T]\d{2}:\d{2}:\d{2})?$/.test(normalized)
  const shouldForceText = looksLikeLongNumber
    || looksLikeDateTime
    || ['uid', 'userid', 'user_id', 'studentid', 'student_id', 'username', 'consume_time', 'consumptiontime', 'created_at'].includes(lowerKey)
  const str = shouldForceText ? `="${normalized.replace(/"/g, '""')}"` : normalized

  if (str.includes('"') || str.includes(',') || str.includes('\n')) {
    return `"${str.replace(/"/g, '""')}"`
  }
  return str
}

export const exportCsv = (rows, columns, filename = 'export.csv') => {
  const headers = columns.map(col => escapeCsv(col.label, col.key)).join(',')
  const lines = rows.map(row => columns.map(col => escapeCsv(row[col.key], col.key)).join(','))
  const csvContent = `\uFEFF${headers}\n${lines.join('\n')}`
  downloadBlob(new Blob([csvContent], { type: 'text/csv;charset=utf-8;' }), filename)
}

const normalizeExcelValue = (value, key = '') => {
  if (value === null || value === undefined) return ''
  const lowerKey = String(key || '').toLowerCase()
  const text = String(value).replace(/\r?\n/g, ' ')

  const forceTextKeys = [
    'uid', 'userid', 'user_id', 'studentid', 'student_id', 'username',
    'consume_time', 'consumptiontime', 'created_at',
    'phone', 'phonenumber', 'class', 'classname', 'grade', 'name', 'college', 'major'
  ]
  const looksLikeLongNumber = /^\d{11,}$/.test(text)
  const looksLikeDateTime = /^\d{4}-\d{2}-\d{2}(?:[ T]\d{2}:\d{2}:\d{2})?$/.test(text)

  if (forceTextKeys.includes(lowerKey) || looksLikeLongNumber || looksLikeDateTime) return text

  const numeric = Number(text)
  if (!Number.isNaN(numeric) && text !== '') return numeric
  return text
}

export const exportXlsx = (rows, columns, filename = 'export.xlsx', sheetName = 'Sheet1') => {
  const headerRow = columns.map(col => col.label)
  const dataRows = rows.map(row => columns.map(col => normalizeExcelValue(row[col.key], col.key)))

  const doExport = async () => {
    try {
      const moduleName = 'xlsx'
      const mod = await import(/* @vite-ignore */ moduleName)
      const XLSX = mod?.default?.utils ? mod.default : mod

      const worksheet = XLSX.utils.aoa_to_sheet([headerRow, ...dataRows])
      worksheet['!cols'] = columns.map(() => ({ wch: 20 }))

      const workbook = XLSX.utils.book_new()
      XLSX.utils.book_append_sheet(workbook, worksheet, sheetName)
      XLSX.writeFile(workbook, filename)
    } catch (e) {
      const fallbackName = filename.replace(/\.xlsx$/i, '.csv')
      exportCsv(rows, columns, fallbackName)
      console.warn('xlsx 依赖不可用，已回退为 CSV 导出', e)
    }
  }

  return doExport()
}

export const downloadBlob = (data, filename, mimeType) => {
  const blob = data instanceof Blob ? data : new Blob([data], { type: mimeType || 'application/octet-stream' })
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', filename)
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}