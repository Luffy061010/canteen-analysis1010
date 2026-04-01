<template>
  <div class="consumption-drift">
    <el-card>
      <template #header>
        <span>概念漂移检测</span>
      </template>

      <el-radio-group v-model="mode" size="large" style="margin-bottom: 16px;">
        <el-radio-button label="interval">时序间隔式概念漂移检测</el-radio-button>
        <el-radio-button label="period-compare">双时段对比式漂移检测</el-radio-button>
      </el-radio-group>

      <template v-if="mode === 'interval'">
        <el-form :model="intervalForm" label-width="120px">
          <el-row :gutter="20">
            <el-col :span="6">
              <el-form-item label="学院">
                <el-select v-model="intervalForm.college" placeholder="全部学院" style="width: 100%">
                  <el-option label="全部" value="" />
                  <el-option v-for="college in colleges" :key="college" :label="college" :value="college" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="专业">
                <el-select v-model="intervalForm.major" placeholder="全部专业" style="width: 100%">
                  <el-option label="全部" value="" />
                  <el-option v-for="major in majors" :key="major" :label="major" :value="major" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="年级">
                <el-select v-model="intervalForm.grade" placeholder="全部年级" style="width: 100%">
                  <el-option label="全部" value="" />
                  <el-option v-for="grade in grades" :key="grade" :label="grade" :value="grade" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="班级">
                <el-select v-model="intervalForm.class" placeholder="全部班级" style="width: 100%">
                  <el-option label="全部" value="" />
                  <el-option v-for="cls in classes" :key="cls" :label="cls" :value="cls" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :span="8">
              <el-form-item label="日期范围">
                <el-date-picker
                  v-model="intervalForm.dateRange"
                  type="daterange"
                  value-format="YYYY-MM-DD"
                  range-separator="至"
                  start-placeholder="开始日期"
                  end-placeholder="结束日期"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
            <el-col :span="4">
              <el-form-item label="时间窗口">
                <el-select v-model="intervalForm.timeWindow">
                  <el-option label="7天" :value="7" />
                  <el-option label="14天" :value="14" />
                  <el-option label="30天" :value="30" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="4">
              <el-form-item label="判定阈值">
                <el-select v-model="intervalForm.pThreshold">
                  <el-option label="0.01" :value="0.01" />
                  <el-option label="0.03" :value="0.03" />
                  <el-option label="0.05" :value="0.05" />
                  <el-option label="0.08" :value="0.08" />
                  <el-option label="0.10" :value="0.1" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="4">
              <el-form-item label="学号">
                <el-input v-model="intervalForm.studentId" placeholder="可选" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item>
                <el-button type="primary" :loading="loading" @click="detectIntervalDrift">检测</el-button>
                <el-button :disabled="loading" @click="resetInterval">重置</el-button>
              </el-form-item>
            </el-col>
          </el-row>
        </el-form>

        <el-card style="margin-top: 12px;">
          <template #header>
            <span>概念漂移检测结果</span>
          </template>
          <div id="intervalDriftChart" class="drift-chart"></div>
        </el-card>

        <el-alert
          style="margin-top: 12px;"
          type="info"
          :closable="false"
          :title="`检测窗口数 ${intervalSummary.windows}，触发漂移 ${intervalSummary.driftCount} 次，漂移占比 ${intervalSummary.ratio}%`"
        />
      </template>

      <template v-else>
        <el-form :model="periodForm" label-width="120px">
          <el-row :gutter="20">
            <el-col :span="8">
              <el-form-item label="对比时段A">
                <el-date-picker
                  v-model="periodForm.periodA"
                  type="daterange"
                  value-format="YYYY-MM-DD"
                  range-separator="至"
                  start-placeholder="开始日期"
                  end-placeholder="结束日期"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="对比时段B">
                <el-date-picker
                  v-model="periodForm.periodB"
                  type="daterange"
                  value-format="YYYY-MM-DD"
                  range-separator="至"
                  start-placeholder="开始日期"
                  end-placeholder="结束日期"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="检测算法">
                <el-input value="MinMax + KMeans（自适应K）" disabled />
              </el-form-item>
            </el-col>
          </el-row>

          <el-row :gutter="20">
            <el-col :span="8">
              <el-form-item>
                <el-button type="primary" :loading="loading" @click="detectPeriodDrift">对比检测</el-button>
                <el-button :disabled="loading" @click="resetPeriod">重置</el-button>
              </el-form-item>
            </el-col>
          </el-row>
        </el-form>

        <el-row :gutter="20">
          <el-col :span="6">
            <el-card>
              <div class="metric-title">时段A均值</div>
              <div class="metric-value">¥{{ periodSummary.meanA }}</div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card>
              <div class="metric-title">时段B均值</div>
              <div class="metric-value">¥{{ periodSummary.meanB }}</div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card>
              <div class="metric-title">漂移指数</div>
              <div class="metric-value">{{ periodSummary.driftIndex }}%</div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card>
              <div class="metric-title">漂移等级</div>
              <div class="metric-value">{{ periodSummary.levelText }}</div>
            </el-card>
          </el-col>
        </el-row>

        <el-row :gutter="20" style="margin-top: 12px;">
          <el-col :span="8">
            <el-card>
              <div class="metric-title">自适应聚类数 K</div>
              <div class="metric-value">{{ periodSummary.adaptiveK }}</div>
            </el-card>
          </el-col>
          <el-col :span="8">
            <el-card>
              <div class="metric-title">簇占比漂移 (Cluster PSI)</div>
              <div class="metric-value">{{ periodSummary.psi }}</div>
            </el-card>
          </el-col>
          <el-col :span="8">
            <el-card>
              <div class="metric-title">簇中心位移</div>
              <div class="metric-value">{{ periodSummary.centerShift }}</div>
            </el-card>
          </el-col>
        </el-row>

        <el-card style="margin-top: 12px;">
          <template #header>
            <span>双时段分布对比（金额分布 + 小时分布）</span>
          </template>
          <div id="periodDriftChart" class="drift-chart"></div>
        </el-card>

        <el-alert
          style="margin-top: 12px;"
          type="info"
          :closable="false"
          :title="periodPrincipleText"
        />
      </template>
    </el-card>
  </div>
</template>

<script>
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import { exportConsumptionData, getConsumptionData, getConsumptionDrift } from '@/api/user.js'
import { COLLEGES_MAJORS, generateClassNames } from '@/utils/const_value.js'

export default {
  name: 'ConsumptionDrift',
  data() {
    return {
      mode: 'interval',
      loading: false,
      colleges: Object.keys(COLLEGES_MAJORS),
      majors: [],
      grades: ['2021', '2022', '2023', '2024'],
      classes: [],
      intervalForm: {
        college: '',
        major: '',
        grade: '',
        class: '',
        studentId: '',
        dateRange: ['2024-09-01', '2024-09-30'],
        timeWindow: 7,
        pThreshold: 0.05
      },
      periodForm: {
        periodA: [],
        periodB: []
      },
      intervalSummary: {
        windows: 0,
        driftCount: 0,
        ratio: 0
      },
      periodSummary: {
        meanA: 0,
        meanB: 0,
        driftIndex: 0,
        levelText: '稳定',
        psi: 0,
        centerShift: 0,
        adaptiveK: 0,
        sampleA: 0,
        sampleB: 0
      },
      charts: {
        interval: null,
        period: null
      },
      resizeHandler: null
    }
  },
  mounted() {
    this.detectIntervalDrift()
    this.resizeHandler = () => {
      Object.values(this.charts).forEach((c) => c && c.resize && c.resize())
    }
    window.addEventListener('resize', this.resizeHandler)
  },
  beforeUnmount() {
    window.removeEventListener('resize', this.resizeHandler)
    Object.values(this.charts).forEach((c) => c && c.dispose && c.dispose())
  },
  watch: {
    'intervalForm.college'(newVal) {
      if (newVal && COLLEGES_MAJORS[newVal]) {
        this.majors = COLLEGES_MAJORS[newVal].majors || []
      } else {
        this.majors = []
      }
      this.intervalForm.major = ''
      this.intervalForm.class = ''
      this.classes = []
    },
    'intervalForm.major'(newVal) {
      if (newVal && this.intervalForm.grade) {
        this.classes = generateClassNames(newVal, this.intervalForm.grade + '级')
      } else {
        this.classes = []
      }
      this.intervalForm.class = ''
    },
    'intervalForm.grade'(newVal) {
      if (newVal && this.intervalForm.major) {
        this.classes = generateClassNames(this.intervalForm.major, newVal + '级')
      } else {
        this.classes = []
      }
      this.intervalForm.class = ''
    }
  },
  methods: {
    clamp(v, min, max) {
      return Math.min(max, Math.max(min, v))
    },

    mean(arr) {
      if (!arr.length) return 0
      return arr.reduce((s, v) => s + v, 0) / arr.length
    },

    std(arr) {
      if (!arr.length) return 0
      const m = this.mean(arr)
      const variance = arr.reduce((s, v) => s + (v - m) * (v - m), 0) / arr.length
      return Math.sqrt(variance)
    },

    parseAmountRows(rows) {
      const list = Array.isArray(rows) ? rows : []
      return list
        .map(i => Number(i.amount || i.money || 0))
        .filter(v => !Number.isNaN(v))
    },

    parseConsumptionRows(rows) {
      const list = Array.isArray(rows) ? rows : []
      return list
        .map((i) => {
          const amount = Number(i.amount || i.money || 0)
          const timeRaw = i.consumptionTime || i.consumption_time || i.consume_time || i.consumeTime || ''
          const dt = new Date(String(timeRaw).replace(' ', 'T'))
          const hour = Number.isNaN(dt.getTime()) ? null : dt.getHours()
          const meal = i.mealType || i.meal_type || '未知'
          return {
            amount: Number.isNaN(amount) ? 0 : amount,
            hour,
            meal
          }
        })
        .filter(i => i.amount >= 0)
    },

    extractRows(res) {
      const rows = res?.records || res?.data?.records || res?.data || []
      return Array.isArray(rows) ? rows : []
    },

    extractTotal(res, fallback = 0) {
      const n = Number(res?.total || res?.totalCount || res?.data?.total || fallback || 0)
      return Number.isNaN(n) ? fallback : n
    },

    parseCsvLine(line) {
      const out = []
      let current = ''
      let inQuotes = false
      for (let i = 0; i < line.length; i += 1) {
        const ch = line[i]
        if (ch === '"') {
          if (inQuotes && line[i + 1] === '"') {
            current += '"'
            i += 1
          } else {
            inQuotes = !inQuotes
          }
        } else if (ch === ',' && !inQuotes) {
          out.push(current)
          current = ''
        } else {
          current += ch
        }
      }
      out.push(current)
      return out
    },

    async fetchAllByExport(params) {
      const blob = await exportConsumptionData(params)
      const text = await new Response(blob).text()
      const lines = String(text || '').replace(/^\uFEFF/, '').split(/\r?\n/).filter(Boolean)
      if (lines.length <= 1) return []

      const headers = this.parseCsvLine(lines[0])
      const headerIndex = headers.reduce((acc, key, idx) => {
        acc[String(key || '').trim()] = idx
        return acc
      }, {})
      const getByKey = (cols, key) => {
        const idx = headerIndex[key]
        if (idx === undefined) return ''
        return cols[idx] ?? ''
      }

      const rows = []
      for (let i = 1; i < lines.length; i += 1) {
        const cols = this.parseCsvLine(lines[i])
        if (!cols.length) continue
        rows.push({
          studentId: getByKey(cols, 'studentId'),
          consumptionTime: getByKey(cols, 'consumptionTime'),
          amount: getByKey(cols, 'amount'),
          mealType: getByKey(cols, 'mealType'),
          windowId: getByKey(cols, 'windowId')
        })
      }
      return rows
    },

    async fetchAllConsumptionByParams(params) {
      try {
        return await this.fetchAllByExport(params)
      } catch (e) {
        console.warn('后端导出通道不可用，回退分页拉取', e)
      }

      const pageSize = 1000
      const maxPages = 60
      let page = 1
      let allRows = []
      let total = 0

      while (page <= maxPages) {
        const res = await getConsumptionData({ ...params, page, pageSize })
        const rows = this.extractRows(res)
        if (!rows.length) break
        allRows = allRows.concat(rows)
        total = this.extractTotal(res, allRows.length)

        if (allRows.length >= total) break
        if (rows.length < pageSize) break
        page += 1
      }

      return allRows
    },

    normalizeDist(arr) {
      const sum = arr.reduce((s, v) => s + v, 0)
      if (!sum) return arr.map(() => 0)
      return arr.map(v => v / sum)
    },

    klDivergence(p, q) {
      const eps = 1e-10
      let s = 0
      for (let i = 0; i < p.length; i += 1) {
        const pi = Math.max(eps, Number(p[i] || 0))
        const qi = Math.max(eps, Number(q[i] || 0))
        s += pi * Math.log(pi / qi)
      }
      return s
    },

    jsDivergence(p, q) {
      const m = p.map((v, i) => (Number(v || 0) + Number(q[i] || 0)) / 2)
      return 0.5 * this.klDivergence(p, m) + 0.5 * this.klDivergence(q, m)
    },

    psiIndex(p, q) {
      const eps = 1e-10
      let s = 0
      for (let i = 0; i < p.length; i += 1) {
        const pi = Math.max(eps, Number(p[i] || 0))
        const qi = Math.max(eps, Number(q[i] || 0))
        s += (pi - qi) * Math.log(pi / qi)
      }
      return s
    },

    buildHistogram(values, minVal, maxVal, binCount = 12) {
      const bins = new Array(binCount).fill(0)
      if (!values.length) {
        return { bins, labels: Array.from({ length: binCount }, (_, i) => `区间${i + 1}`) }
      }

      const step = maxVal === minVal ? 1 : (maxVal - minVal) / binCount
      values.forEach((v) => {
        const rawIdx = step === 0 ? 0 : Math.floor((v - minVal) / step)
        const idx = this.clamp(rawIdx, 0, binCount - 1)
        bins[idx] += 1
      })

      const labels = Array.from({ length: binCount }, (_, i) => {
        const l = minVal + i * step
        const r = i === binCount - 1 ? maxVal : minVal + (i + 1) * step
        return `${l.toFixed(1)}-${r.toFixed(1)}`
      })

      return { bins, labels }
    },

    buildHourDist(rows) {
      const counts = new Array(24).fill(0)
      rows.forEach((r) => {
        if (r.hour === null || r.hour === undefined) return
        counts[r.hour] += 1
      })
      return counts
    },

    buildMealDist(rows) {
      const map = { 早餐: 0, 午餐: 0, 晚餐: 0, 夜宵: 0, 其他: 0 }
      rows.forEach((r) => {
        const m = String(r.meal || '')
        if (m.includes('早')) map.早餐 += 1
        else if (m.includes('中') || m.includes('午')) map.午餐 += 1
        else if (m.includes('晚')) map.晚餐 += 1
        else if (m.includes('夜')) map.夜宵 += 1
        else map.其他 += 1
      })
      return [map.早餐, map.午餐, map.晚餐, map.夜宵, map.其他]
    },

    buildFeaturePoints(rows) {
      return rows.map((r) => [
        Number(r.amount || 0),
        Number(r.hour === null || r.hour === undefined ? 12 : r.hour)
      ])
    },

    fitMinMax(points) {
      const dims = points[0]?.length || 0
      const minVals = new Array(dims).fill(Number.POSITIVE_INFINITY)
      const maxVals = new Array(dims).fill(Number.NEGATIVE_INFINITY)

      points.forEach((p) => {
        for (let i = 0; i < dims; i += 1) {
          minVals[i] = Math.min(minVals[i], Number(p[i] || 0))
          maxVals[i] = Math.max(maxVals[i], Number(p[i] || 0))
        }
      })

      return { minVals, maxVals }
    },

    transformMinMax(points, scaler) {
      const { minVals, maxVals } = scaler
      return points.map((p) => p.map((v, i) => {
        const minV = minVals[i]
        const maxV = maxVals[i]
        if (maxV === minV) return 0
        return (Number(v || 0) - minV) / (maxV - minV)
      }))
    },

    distance2d(a, b) {
      const dx = Number(a[0] || 0) - Number(b[0] || 0)
      const dy = Number(a[1] || 0) - Number(b[1] || 0)
      return Math.sqrt(dx * dx + dy * dy)
    },

    assignKMeansLabels(data, centers) {
      return data.map((point) => {
        let bestIdx = 0
        let bestDist = Number.POSITIVE_INFINITY
        centers.forEach((c, idx) => {
          const d = this.distance2d(point, c)
          if (d < bestDist) {
            bestDist = d
            bestIdx = idx
          }
        })
        return bestIdx
      })
    },

    runKMeans(data, k, maxIter = 50) {
      if (!data.length) return { centers: [], labels: [] }

      const n = data.length
      const actualK = this.clamp(Number(k || 4), 1, Math.max(1, Math.min(8, n)))

      const sortedIdx = data
        .map((p, i) => ({ i, v: Number(p[0] || 0) + Number(p[1] || 0) }))
        .sort((a, b) => a.v - b.v)
        .map(i => i.i)

      let centers = Array.from({ length: actualK }, (_, idx) => {
        const pick = sortedIdx[Math.floor(idx * (n - 1) / Math.max(1, actualK - 1))]
        return [...data[pick]]
      })

      let labels = this.assignKMeansLabels(data, centers)

      for (let iter = 0; iter < maxIter; iter += 1) {
        const bucket = Array.from({ length: actualK }, () => ({ sx: 0, sy: 0, c: 0 }))
        labels.forEach((lb, i) => {
          bucket[lb].sx += Number(data[i][0] || 0)
          bucket[lb].sy += Number(data[i][1] || 0)
          bucket[lb].c += 1
        })

        const newCenters = centers.map((c, idx) => {
          if (!bucket[idx].c) return c
          return [bucket[idx].sx / bucket[idx].c, bucket[idx].sy / bucket[idx].c]
        })

        const shift = newCenters.reduce((s, c, i) => s + this.distance2d(c, centers[i]), 0)
        centers = newCenters
        labels = this.assignKMeansLabels(data, centers)
        if (shift < 1e-6) break
      }

      return { centers, labels, k: actualK }
    },

    calcSSE(data, labels, centers) {
      let sse = 0
      labels.forEach((lb, i) => {
        const d = this.distance2d(data[i], centers[lb])
        sse += d * d
      })
      return sse
    },

    chooseAdaptiveK(data, minK = 2, maxK = 8) {
      if (!data.length) return 1
      const upper = this.clamp(maxK, minK, Math.min(8, data.length))
      if (upper <= minK) return upper

      const trials = []
      for (let k = minK; k <= upper; k += 1) {
        const km = this.runKMeans(data, k)
        const sse = this.calcSSE(data, km.labels, km.centers)
        trials.push({ k, sse })
      }

      // 肘部法：当继续增大K带来的相对收益显著下降时停止。
      for (let i = 1; i < trials.length; i += 1) {
        const prev = trials[i - 1]
        const cur = trials[i]
        const improve = prev.sse <= 0 ? 0 : (prev.sse - cur.sse) / prev.sse
        if (improve < 0.12) {
          return prev.k
        }
      }
      return trials[trials.length - 1].k
    },

    clusterProportion(labels, k) {
      const cnt = new Array(k).fill(0)
      labels.forEach((lb) => { cnt[lb] += 1 })
      return this.normalizeDist(cnt)
    },

    periodCentersByCluster(data, labels, k) {
      const buckets = Array.from({ length: k }, () => ({ sx: 0, sy: 0, c: 0 }))
      labels.forEach((lb, i) => {
        buckets[lb].sx += Number(data[i][0] || 0)
        buckets[lb].sy += Number(data[i][1] || 0)
        buckets[lb].c += 1
      })
      return buckets.map((b) => (b.c ? [b.sx / b.c, b.sy / b.c] : [0, 0]))
    },

    renderPeriodClusterChart(clusterData) {
      const chart = this.getChart('periodDriftChart', 'period')
      if (!chart) return

      const k = Number(clusterData.k || 0)
      const xLabels = Array.from({ length: k }, (_, i) => `C${i + 1}`)
      const pA = clusterData.pA || []
      const pB = clusterData.pB || []
      const centerShiftByCluster = clusterData.centerShiftByCluster || []

      chart.setOption({
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
        legend: { top: 10, data: ['A簇占比', 'B簇占比', '簇中心位移'] },
        grid: [
          { left: '6%', right: '5%', top: 48, height: 145 },
          { left: '6%', right: '5%', top: 248, height: 108 }
        ],
        xAxis: [
          { type: 'category', data: xLabels, gridIndex: 0 },
          { type: 'category', data: xLabels, gridIndex: 1 }
        ],
        yAxis: [
          {
            type: 'value',
            name: '簇占比',
            gridIndex: 0,
            axisLabel: { formatter: (v) => `${Number(v * 100).toFixed(0)}%` },
            splitLine: { lineStyle: { type: 'dashed', color: '#e7edf5' } }
          },
          {
            type: 'value',
            name: '位移距离',
            gridIndex: 1,
            splitLine: { lineStyle: { type: 'dashed', color: '#e7edf5' } }
          }
        ],
        series: [
          {
            name: 'A簇占比',
            type: 'bar',
            xAxisIndex: 0,
            yAxisIndex: 0,
            data: pA,
            barMaxWidth: 18,
            itemStyle: { color: '#3A7AFE' }
          },
          {
            name: 'B簇占比',
            type: 'bar',
            xAxisIndex: 0,
            yAxisIndex: 0,
            data: pB,
            barMaxWidth: 18,
            itemStyle: { color: '#F59E0B' }
          },
          {
            name: '簇中心位移',
            type: 'line',
            smooth: true,
            xAxisIndex: 1,
            yAxisIndex: 1,
            data: centerShiftByCluster,
            lineStyle: { width: 3, color: '#EF4444' },
            areaStyle: { color: 'rgba(239,68,68,0.10)' }
          }
        ]
      })
    },

    driftLevelText(score) {
      if (score < 20) return '稳定'
      if (score < 40) return '轻微漂移'
      if (score < 65) return '中等漂移'
      return '显著漂移'
    },

    buildParams(range) {
      if (!Array.isArray(range) || range.length !== 2) return null
      return { timeBegin: range[0], timeEnd: range[1], page: 1, pageSize: 5000 }
    },

    getChart(id, key) {
      const el = document.getElementById(id)
      if (!el) return null
      const old = echarts.getInstanceByDom(el)
      this.charts[key] = old || echarts.init(el)
      this.charts[key].clear()
      return this.charts[key]
    },

    renderIntervalChart(dates, values, threshold) {
      const chart = this.getChart('intervalDriftChart', 'interval')
      if (!chart) return
      chart.setOption({
        tooltip: { trigger: 'axis' },
        legend: { data: ['p值', '阈值'] },
        grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
        xAxis: { type: 'category', data: dates },
        yAxis: { type: 'value', min: 0, max: 1 },
        series: [
          {
            name: 'p值',
            type: 'line',
            data: values,
            smooth: true,
            lineStyle: { width: 3, color: '#409EFF' }
          },
          {
            name: '阈值',
            type: 'line',
            data: new Array(values.length).fill(threshold),
            symbol: 'none',
            lineStyle: { type: 'dashed', color: '#F56C6C' }
          }
        ]
      })
    },

    renderPeriodChart(periodData) {
      const chart = this.getChart('periodDriftChart', 'period')
      if (!chart) return

      const amountLabels = periodData.amountLabels || []
      const densityA = periodData.amountDistA || []
      const densityB = periodData.amountDistB || []
      const hourDistA = periodData.hourDistA || []
      const hourDistB = periodData.hourDistB || []
      const diffByBin = densityA.map((v, i) => Number((Math.abs(v - (densityB[i] || 0)) * 100).toFixed(2)))

      chart.setOption({
        tooltip: {
          trigger: 'axis',
          axisPointer: { type: 'cross' }
        },
        legend: {
          top: 8,
          data: ['时段A金额分布', '时段B金额分布', '分布差异(%)', '时段A小时分布', '时段B小时分布']
        },
        grid: [
          { left: '5%', right: '6%', top: 48, height: 130 },
          { left: '5%', right: '6%', top: 245, height: 120 }
        ],
        xAxis: [
          {
            type: 'category',
            data: amountLabels,
            gridIndex: 0,
            axisLabel: { rotate: 35, fontSize: 11 }
          },
          {
            type: 'category',
            data: Array.from({ length: 24 }, (_, i) => `${i}时`),
            gridIndex: 1,
            axisLabel: { interval: 1 }
          }
        ],
        yAxis: [
          {
            type: 'value',
            name: '金额分布占比',
            gridIndex: 0,
            axisLabel: { formatter: (v) => `${Number(v * 100).toFixed(0)}%` },
            splitLine: { lineStyle: { type: 'dashed', color: '#e7edf5' } }
          },
          {
            type: 'value',
            name: '分布差异(%)',
            gridIndex: 0,
            axisLabel: { formatter: '{value}%' }
          },
          {
            type: 'value',
            name: '小时分布占比',
            gridIndex: 1,
            axisLabel: { formatter: (v) => `${Number(v * 100).toFixed(0)}%` },
            splitLine: { lineStyle: { type: 'dashed', color: '#e7edf5' } }
          }
        ],
        series: [
          {
            name: '时段A金额分布',
            type: 'line',
            smooth: true,
            xAxisIndex: 0,
            yAxisIndex: 0,
            data: densityA,
            lineStyle: { width: 3, color: '#3A7AFE' },
            areaStyle: { color: 'rgba(58,122,254,0.12)' }
          },
          {
            name: '时段B金额分布',
            type: 'line',
            smooth: true,
            xAxisIndex: 0,
            yAxisIndex: 0,
            data: densityB,
            lineStyle: { width: 3, color: '#F59E0B' },
            areaStyle: { color: 'rgba(245,158,11,0.10)' }
          },
          {
            name: '分布差异(%)',
            type: 'bar',
            xAxisIndex: 0,
            yAxisIndex: 1,
            data: diffByBin,
            barMaxWidth: 14,
            itemStyle: { color: 'rgba(239,68,68,0.45)' }
          },
          {
            name: '时段A小时分布',
            type: 'line',
            smooth: true,
            xAxisIndex: 1,
            yAxisIndex: 2,
            data: hourDistA,
            lineStyle: { width: 2, color: '#22C55E' }
          },
          {
            name: '时段B小时分布',
            type: 'line',
            smooth: true,
            xAxisIndex: 1,
            yAxisIndex: 2,
            data: hourDistB,
            lineStyle: { width: 2, color: '#A855F7' }
          }
        ]
      })
    },

    async detectIntervalDrift() {
      const range = this.intervalForm.dateRange
      if (!Array.isArray(range) || range.length !== 2) {
        ElMessage.warning('请选择日期范围')
        return
      }

      this.loading = true
      try {
        const result = await getConsumptionDrift({
          college: this.intervalForm.college || undefined,
          major: this.intervalForm.major || undefined,
          grade: this.intervalForm.grade || undefined,
          className: this.intervalForm.class || undefined,
          studentId: this.intervalForm.studentId || undefined,
          timeBegin: range[0],
          timeEnd: range[1],
          timeWindow: this.intervalForm.timeWindow,
          pThreshold: this.intervalForm.pThreshold
        })

        const pValues = Array.isArray(result?.p_values)
          ? result.p_values.map(v => Number(v)).filter(v => !Number.isNaN(v))
          : []

        const driftCount = pValues.filter(v => v < this.intervalForm.pThreshold).length
        const ratio = pValues.length ? (driftCount / pValues.length) * 100 : 0

        this.intervalSummary = {
          windows: pValues.length,
          driftCount,
          ratio: Number(ratio.toFixed(2))
        }

        const dates = Array.isArray(result?.chartData?.dates)
          ? result.chartData.dates
          : pValues.map((_, idx) => `窗口${idx + 1}`)

        this.$nextTick(() => {
          this.renderIntervalChart(dates, pValues, Number(this.intervalForm.pThreshold))
        })
      } catch (error) {
        console.error('时序间隔式漂移检测失败:', error)
        ElMessage.error('时序间隔式漂移检测失败')
      } finally {
        this.loading = false
      }
    },

    async detectPeriodDrift() {
      const paramsA = this.buildParams(this.periodForm.periodA)
      const paramsB = this.buildParams(this.periodForm.periodB)
      if (!paramsA || !paramsB) {
        ElMessage.warning('请完整选择两个对比时段')
        return
      }

      this.loading = true
      try {
        const [rowsA, rowsB] = await Promise.all([
          this.fetchAllConsumptionByParams(paramsA),
          this.fetchAllConsumptionByParams(paramsB)
        ])

        const parsedA = this.parseConsumptionRows(rowsA)
        const parsedB = this.parseConsumptionRows(rowsB)
        const valuesA = parsedA.map(i => i.amount)
        const valuesB = parsedB.map(i => i.amount)

        if (!valuesA.length || !valuesB.length) {
          ElMessage.warning('双时段至少各需要一段有效消费数据')
          return
        }

        const meanA = this.mean(valuesA)
        const meanB = this.mean(valuesB)

        const meanDiffRate = meanA === 0 ? 0 : Math.abs(meanB - meanA) / Math.abs(meanA)
        const ptsA = this.buildFeaturePoints(parsedA)
        const ptsB = this.buildFeaturePoints(parsedB)
        const merged = ptsA.concat(ptsB)
        const scaler = this.fitMinMax(merged)
        const normA = this.transformMinMax(ptsA, scaler)
        const normB = this.transformMinMax(ptsB, scaler)
        const normAll = normA.concat(normB)

        const adaptiveK = this.chooseAdaptiveK(normAll, 2, 8)
        const km = this.runKMeans(normAll, adaptiveK)
        const k = Number(km.k || 1)
        const labelsA = this.assignKMeansLabels(normA, km.centers)
        const labelsB = this.assignKMeansLabels(normB, km.centers)

        const pA = this.clusterProportion(labelsA, k)
        const pB = this.clusterProportion(labelsB, k)
        const clusterPsi = this.psiIndex(pA, pB)

        const cA = this.periodCentersByCluster(normA, labelsA, k)
        const cB = this.periodCentersByCluster(normB, labelsB, k)
        const centerShiftByCluster = cA.map((c, i) => Number(this.distance2d(c, cB[i]).toFixed(4)))
        const centerShift = centerShiftByCluster.reduce((s, v) => s + v, 0) / Math.max(1, centerShiftByCluster.length)

        const clusterScore = this.clamp(clusterPsi * 120, 0, 100)
        const centerScore = this.clamp(centerShift * 100, 0, 100)
        const meanScore = this.clamp(meanDiffRate * 100, 0, 100)
        const driftIndex = this.clamp(clusterScore * 0.5 + centerScore * 0.3 + meanScore * 0.2, 0, 100)

        this.periodSummary = {
          meanA: Number(meanA.toFixed(2)),
          meanB: Number(meanB.toFixed(2)),
          driftIndex: Number(driftIndex.toFixed(2)),
          levelText: this.driftLevelText(driftIndex),
          psi: Number(clusterPsi.toFixed(4)),
          centerShift: Number(centerShift.toFixed(4)),
          adaptiveK: k,
          sampleA: valuesA.length,
          sampleB: valuesB.length
        }

        this.$nextTick(() => {
          this.renderPeriodClusterChart({ k, pA, pB, centerShiftByCluster })
        })
      } catch (error) {
        console.error('双时段漂移检测失败:', error)
        ElMessage.error('双时段漂移检测失败')
      } finally {
        this.loading = false
      }
    },

    resetInterval() {
      this.intervalForm = {
        college: '',
        major: '',
        grade: '',
        class: '',
        studentId: '',
        dateRange: ['2024-09-01', '2024-09-30'],
        timeWindow: 7,
        pThreshold: 0.05
      }
      this.majors = []
      this.classes = []
      this.intervalSummary = { windows: 0, driftCount: 0, ratio: 0 }
      const chart = this.charts.interval
      if (chart) chart.clear()
    },

    resetPeriod() {
      this.periodForm = {
        periodA: [],
        periodB: []
      }
      this.periodSummary = {
        meanA: 0,
        meanB: 0,
        driftIndex: 0,
        levelText: '稳定',
        psi: 0,
        centerShift: 0,
        adaptiveK: 0,
        sampleA: 0,
        sampleB: 0
      }
      const chart = this.charts.period
      if (chart) chart.clear()
    }
  },
  computed: {
    periodPrincipleText() {
      return '检测原理（固定MinMax+KMeans）：先将双时段样本特征做MinMax归一化，再通过肘部法自适应选择聚类数K并在统一空间做KMeans聚类；随后比较两时段簇占比漂移（Cluster PSI）与簇中心位移，并结合均值变化率融合为0-100漂移指数。指数越高说明行为结构变化越明显。'
    }
  }
}
</script>

<style scoped>
.consumption-drift {
  padding: 20px;
}

.drift-chart {
  width: 100%;
  height: 390px;
}

.metric-title {
  color: #909399;
}

.metric-value {
  margin-top: 8px;
  font-size: 22px;
  font-weight: 700;
  color: #303133;
}

.consumption-drift :deep(.el-card) {
  border-radius: 12px;
}
</style>
