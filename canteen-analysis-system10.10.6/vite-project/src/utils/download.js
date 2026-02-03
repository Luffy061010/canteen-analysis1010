const escapeCsv = (value) => {
  if (value === null || value === undefined) return ''
  const str = String(value)
  if (str.includes('"') || str.includes(',') || str.includes('\n')) {
    return `"${str.replace(/"/g, '""')}"`
  }
  return str
}

export const exportCsv = (rows, columns, filename = 'export.csv') => {
  const headers = columns.map(col => escapeCsv(col.label)).join(',')
  const lines = rows.map(row => columns.map(col => escapeCsv(row[col.key])).join(','))
  const csvContent = `\uFEFF${headers}\n${lines.join('\n')}`
  downloadBlob(new Blob([csvContent], { type: 'text/csv;charset=utf-8;' }), filename)
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