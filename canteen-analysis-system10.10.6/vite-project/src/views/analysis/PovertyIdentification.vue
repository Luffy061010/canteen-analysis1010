<template>
  <div class="user-portrait-analysis">
    <el-alert v-if="loadError" type="error" :closable="false" show-icon style="margin-bottom: 16px;">
      <template #title>用户画像加载失败</template>
      <div class="error-actions">
        <span>{{ loadError }}</span>
        <el-button size="small" type="danger" plain :loading="loading" @click="handleAnalyze(false)">重试</el-button>
      </div>
    </el-alert>

    <el-card>
      <template #header>
        <span>用户画像构建模块</span>
      </template>

      <el-form :model="queryForm" label-width="100px">
        <el-row :gutter="20">
          <el-col :xs="24" :sm="12" :lg="6">
            <el-form-item label="学院">
              <el-select v-model="queryForm.college" placeholder="全部学院" style="width: 100%">
                <el-option label="全部" value="" />
                <el-option v-for="college in colleges" :key="college" :label="college" :value="college" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :lg="6">
            <el-form-item label="专业">
              <el-select v-model="queryForm.major" placeholder="全部专业" style="width: 100%">
                <el-option label="全部" value="" />
                <el-option v-for="major in majors" :key="major" :label="major" :value="major" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :lg="6">
            <el-form-item label="年级">
              <el-select v-model="queryForm.grade" placeholder="全部年级" style="width: 100%">
                <el-option label="全部" value="" />
                <el-option v-for="grade in grades" :key="grade" :label="grade" :value="grade" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :lg="6">
            <el-form-item label="班级">
              <el-select v-model="queryForm.class" placeholder="全部班级" style="width: 100%">
                <el-option label="全部" value="" />
                <el-option v-for="cls in classes" :key="cls" :label="cls" :value="cls" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :xs="24" :md="10" :lg="8">
            <el-form-item label="日期范围">
              <el-date-picker
                v-model="queryForm.dateRange"
                type="daterange"
                range-separator="至"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                value-format="YYYY-MM-DD"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :md="8" :lg="8">
            <el-form-item label="学号">
              <el-input v-model="queryForm.studentId" placeholder="请输入学号" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :md="6" :lg="8">
            <el-form-item>
              <el-button type="primary" :loading="loading" @click="handleAnalyze">分析画像</el-button>
              <el-button :disabled="loading" @click="handleReset">重置</el-button>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>

      <el-row :gutter="20" style="margin-top: 20px;">
        <el-col :xs="24" :lg="16">
          <el-card>
            <template #header>
              <span>消费-频次聚类散点图</span>
            </template>
            <BaseChart :options="scatterOptions" :loading="loading" :container-style="{ width: '100%', height: '360px' }" />
          </el-card>
        </el-col>
        <el-col :xs="24" :lg="8">
          <el-card>
            <template #header>
              <span>消费层级占比</span>
            </template>
            <BaseChart :options="pieOptions" :loading="loading" :container-style="{ width: '100%', height: '360px' }" />
          </el-card>
        </el-col>
      </el-row>

      <el-card style="margin-top: 20px;">
        <template #header>
          <span>聚类分析结果</span>
        </template>
        <el-table v-loading="loading || detailLoading" :data="pagedResults" style="width: 100%" :fit="true" size="small" table-layout="fixed">
          <el-table-column prop="studentId" label="学号" width="130" />
          <el-table-column prop="name" label="姓名" width="100" />
          <el-table-column prop="college" label="学院" min-width="110" show-overflow-tooltip />
          <el-table-column prop="major" label="专业" min-width="120" show-overflow-tooltip />
          <el-table-column prop="grade" label="年级" width="80" />
          <el-table-column prop="dailyAvg" label="日均消费" width="110">
            <template #default="scope">¥{{ Number(scope.row.dailyAvg || 0).toFixed(2) }}</template>
          </el-table-column>
          <el-table-column prop="dailyCount" label="日均次数" width="110">
            <template #default="scope">{{ Number(scope.row.dailyCount || 0).toFixed(2) }}</template>
          </el-table-column>
          <el-table-column prop="monthAvgAmount" label="月均消费额" width="120">
            <template #default="scope">¥{{ Number(scope.row.monthAvgAmount || 0).toFixed(2) }}</template>
          </el-table-column>
          <el-table-column prop="favoriteWindow" label="最常去窗口" min-width="110" show-overflow-tooltip />
          <el-table-column prop="gpa" label="绩点" width="80" />
          <el-table-column prop="level" label="消费层级" width="120">
            <template #default="scope">
              <el-tag :type="tagType(scope.row.level)">{{ scope.row.level }}</el-tag>
            </template>
          </el-table-column>
        </el-table>
        <div class="pagination">
          <el-pagination
            v-model:current-page="resultPagination.currentPage"
            v-model:page-size="resultPagination.pageSize"
            :page-sizes="[20, 50, 100]"
            :total="resultPagination.total"
            layout="total, sizes, prev, pager, next, jumper"
            @current-change="handlePageChange"
            @size-change="handleSizeChange"
          />
        </div>
      </el-card>

      <el-card style="margin-top: 16px;">
        <template #header>
          <span>大模型画像解释</span>
        </template>
        <el-empty v-if="!llmExplanationItems.length && !llmLoading" description="暂无解释内容，请先执行画像分析" />
        <div v-else class="explain-list" v-loading="llmLoading">
          <div v-for="item in llmExplanationItems" :key="item.title" class="explain-item">
            <div class="explain-title">{{ item.title }}</div>
            <div class="explain-content">
              <p v-for="(segment, idx) in item.segments" :key="`${item.title}-${idx}`" class="explain-paragraph">{{ segment }}</p>
            </div>
          </div>
        </div>
      </el-card>
    </el-card>
  </div>
</template>

<script>
import { ElMessage } from 'element-plus'
import BaseChart from '@/components/Charts/BaseChart.vue'
import { getClusterDetails, getDeepSeekExplanation, getPovertyIdentification } from '@/api/user.js'
import { COLLEGES_MAJORS, generateClassNames } from '@/utils/const_value.js'

export default {
  name: 'UserPortraitAnalysis',
  components: { BaseChart },
  data() {
    return {
      queryForm: {
        college: '',
        major: '',
        grade: '',
        class: '',
        dateRange: ['2024-09-01', '2024-09-30'],
        studentId: ''
      },
      colleges: Object.keys(COLLEGES_MAJORS),
      majors: [],
      grades: ['2021', '2022', '2023', '2024'],
      classes: [],
      loading: false,
      detailLoading: false,
      llmLoading: false,
      loadError: '',
      portraitResults: [],
      benchmarkRows: [],
      pageDetailsMap: {},
      llmSummaryText: '',
      llmPersonalText: '',
      resultPagination: {
        currentPage: 1,
        pageSize: 20,
        total: 0
      }
    }
  },
  computed: {
    pagedResults() {
      const start = (this.resultPagination.currentPage - 1) * this.resultPagination.pageSize
      const end = start + this.resultPagination.pageSize
      const pageRows = this.portraitResults.slice(start, end)
      return pageRows.map((row) => {
        const detail = this.pageDetailsMap[String(row.studentId || '')] || {}
        return {
          ...row,
          ...detail,
          level: row.level,
          dailyAvg: row.dailyAvg,
          dailyCount: row.dailyCount
        }
      })
    },

    scatterOptions() {
      if (!this.portraitResults.length) {
        return {
          title: { text: '暂无数据', left: 'center', top: 'center', textStyle: { color: '#999' } },
          xAxis: { show: false },
          yAxis: { show: false },
          series: []
        }
      }

      if (this.isPersonalScope) {
        const target = this.personalMergedRow
        const benchmark = this.benchmarkRows.length ? this.benchmarkRows : this.portraitResults
        const benchmarkPoints = benchmark
          .filter(i => String(i.studentId || '') !== String(target.studentId || ''))
          .slice(0, 500)

        return {
          tooltip: {
            trigger: 'item',
            formatter: (params) => {
              const d = params.data || {}
              return `学号: ${d.studentId}<br/>姓名: ${d.name}<br/>日均消费: ¥${Number(d.value?.[0] || 0).toFixed(2)}<br/>日均次数: ${Number(d.value?.[1] || 0).toFixed(2)}<br/>消费层级: ${d.level}`
            }
          },
          legend: { data: ['同筛选群体', '当前学生'], bottom: 0 },
          xAxis: { type: 'value', name: '日均消费(元)' },
          yAxis: { type: 'value', name: '日均次数' },
          grid: { left: '3%', right: '4%', bottom: '10%', containLabel: true },
          series: [
            {
              name: '同筛选群体',
              type: 'scatter',
              data: benchmarkPoints.map(i => ({
                value: [Number(i.dailyAvg || 0), Number(i.dailyCount || 0)],
                studentId: i.studentId,
                name: i.name,
                level: i.level,
                itemStyle: { color: '#BFC7D5', opacity: 0.35 }
              })),
              symbolSize: 7
            },
            {
              name: '当前学生',
              type: 'scatter',
              data: [{
                value: [Number(target.dailyAvg || 0), Number(target.dailyCount || 0)],
                studentId: target.studentId,
                name: target.name,
                level: target.level,
                itemStyle: { color: this.levelColor(target.level), opacity: 1 }
              }],
              symbolSize: 16,
              label: {
                show: true,
                position: 'top',
                formatter: (p) => p?.data?.studentId || ''
              }
            }
          ]
        }
      }

      return {
        tooltip: {
          trigger: 'item',
          formatter: (params) => {
            const d = params.data || {}
            return `学号: ${d.studentId}<br/>姓名: ${d.name}<br/>日均消费: ¥${Number(d.value?.[0] || 0).toFixed(2)}<br/>日均次数: ${Number(d.value?.[1] || 0).toFixed(2)}<br/>消费层级: ${d.level}`
          }
        },
        xAxis: { type: 'value', name: '日均消费(元)' },
        yAxis: { type: 'value', name: '日均次数' },
        grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
        series: [
          {
            type: 'scatter',
            data: this.portraitResults.map(i => ({
              value: [Number(i.dailyAvg || 0), Number(i.dailyCount || 0)],
              studentId: i.studentId,
              name: i.name,
              level: i.level,
              itemStyle: { color: this.levelColor(i.level) }
            })),
            symbolSize: 10
          }
        ]
      }
    },
    pieOptions() {
      if (this.isPersonalScope && this.portraitResults.length) {
        const target = this.personalMergedRow
        const counts = {
          '低消费': 0,
          '较低消费': 0,
          '中消费': 0,
          '高消费': 0
        }
        const benchmark = this.benchmarkRows.length ? this.benchmarkRows : this.portraitResults
        benchmark.forEach((r) => {
          counts[r.level] = (counts[r.level] || 0) + 1
        })
        const levelCount = Number(counts[target.level] || 0)
        const total = Math.max(1, benchmark.length)
        return {
          tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
          title: {
            text: `当前学生：${target.level || '-'}`,
            subtext: `同层级占比 ${(levelCount * 100 / total).toFixed(1)}%`,
            left: 'center',
            top: 10,
            textStyle: { fontSize: 14, color: '#303133' },
            subtextStyle: { color: '#909399' }
          },
          series: [
            {
              type: 'pie',
              center: ['50%', '56%'],
              radius: ['38%', '62%'],
              label: { formatter: '{b}\n{c}人 ({d}%)', fontSize: 11 },
              data: [
                { name: target.level || '当前层级', value: levelCount, itemStyle: { color: this.levelColor(target.level) } },
                { name: '其他层级', value: Math.max(0, total - levelCount), itemStyle: { color: '#D8DEE9' } }
              ]
            }
          ]
        }
      }

      const counts = {
        '低消费': 0,
        '较低消费': 0,
        '中消费': 0,
        '高消费': 0
      }
      this.portraitResults.forEach((r) => {
        counts[r.level] = (counts[r.level] || 0) + 1
      })

      const total = Object.values(counts).reduce((sum, v) => sum + Number(v || 0), 0)
      if (!total) {
        return {
          title: { text: '暂无数据', left: 'center', top: 'center', textStyle: { color: '#999', fontSize: 14 } },
          xAxis: { show: false },
          yAxis: { show: false },
          series: []
        }
      }

      return {
        tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
        legend: { type: 'scroll', bottom: 0, icon: 'circle' },
        series: [
          {
            type: 'pie',
            center: ['50%', '44%'],
            radius: ['34%', '60%'],
            minShowLabelAngle: 10,
            labelLine: { length: 10, length2: 10 },
            labelLayout: { hideOverlap: true },
            label: {
              formatter: (params) => `${params.name}\n${params.value}人 (${Number(params.percent || 0).toFixed(1)}%)`,
              fontSize: 11
            },
            data: Object.keys(counts).map(k => ({ name: k, value: counts[k] }))
          }
        ]
      }
    },

    isPersonalScope() {
      return Boolean(String(this.queryForm.studentId || '').trim())
    },

    personalMergedRow() {
      const first = this.portraitResults[0] || {}
      const sid = String(first.studentId || this.queryForm.studentId || '').trim()
      const detail = this.pageDetailsMap[sid] || {}
      return {
        ...first,
        ...detail,
        studentId: sid || '-',
        level: first.level || detail.level || '-',
        dailyAvg: Number(first.dailyAvg || 0),
        dailyCount: Number(first.dailyCount || 0),
        monthAvgAmount: Number(detail.monthAvgAmount ?? first.monthAvgAmount ?? 0),
        monthAvgCount: Number(detail.monthAvgCount ?? first.monthAvgCount ?? 0),
        gpa: Number(detail.gpa ?? first.gpa ?? 0)
      }
    },

    llmExplanationItems() {
      if (this.isPersonalScope) {
        if (!this.llmPersonalText) return []
        const first = this.portraitResults[0] || {}
        const sid = first.studentId || String(this.queryForm.studentId || '').trim() || '-'
        const name = first.name || ''
        return [{
          title: `个人画像解释：${sid}${name ? ` (${name})` : ''}`,
          segments: this.splitExplanationText(this.llmPersonalText)
        }]
      }

      if (!this.llmSummaryText) return []
      return [{
        title: '群体画像解释（四类消费层级）',
        segments: this.splitExplanationText(this.llmSummaryText)
      }]
    }
  },
  watch: {
    'queryForm.college'(newVal) {
      if (newVal && COLLEGES_MAJORS[newVal]) {
        this.majors = COLLEGES_MAJORS[newVal].majors || []
      } else {
        this.majors = []
      }
      this.queryForm.major = ''
      this.queryForm.class = ''
      this.classes = []
    },
    'queryForm.major'(newVal) {
      if (newVal && this.queryForm.grade) {
        this.classes = generateClassNames(newVal, this.queryForm.grade + '级')
      } else {
        this.classes = []
      }
      this.queryForm.class = ''
    },
    'queryForm.grade'(newVal) {
      if (newVal && this.queryForm.major) {
        this.classes = generateClassNames(this.queryForm.major, newVal + '级')
      } else {
        this.classes = []
      }
      this.queryForm.class = ''
    }
  },
  mounted() {
    // 默认不自动分析，避免进入页面即触发重查询
  },
  methods: {
    withTimeout(promise, timeout = 20000) {
      return Promise.race([
        promise,
        new Promise((_, reject) => {
          setTimeout(() => reject(new Error('请求超时')), timeout)
        })
      ])
    },

    async loadPageDetails() {
      const start = (this.resultPagination.currentPage - 1) * this.resultPagination.pageSize
      const end = start + this.resultPagination.pageSize
      const pageRows = this.portraitResults.slice(start, end)
      const ids = pageRows.map(i => String(i.studentId || '')).filter(Boolean)

      if (!ids.length) {
        this.pageDetailsMap = {}
        return
      }

      this.detailLoading = true
      try {
        const params = {
          studentIds: ids.join(','),
          includeLlm: ids.length <= 20
        }
        if (Array.isArray(this.queryForm.dateRange) && this.queryForm.dateRange.length === 2) {
          params.timeBegin = this.queryForm.dateRange[0]
          params.timeEnd = this.queryForm.dateRange[1]
        }

        const detailRes = await this.withTimeout(getClusterDetails(params), 20000)
        const detailRows = detailRes?.results || detailRes?.data?.results || []
        const nextMap = {}
        if (Array.isArray(detailRows)) {
          detailRows.forEach((r) => {
            const sid = String(r.studentId || r.student_id || '')
            if (!sid) return
            nextMap[sid] = {
              name: r.name || '-',
              gender: r.gender || '-',
              college: r.college || '-',
              major: r.major || '-',
              className: r.className || '-',
              grade: r.grade || '-',
              monthAvgAmount: Number(r.monthAvgAmount ?? 0),
              monthAvgCount: Number(r.monthAvgCount ?? 0),
              favoriteWindow: r.favoriteWindow || '-',
              peakPeriod: r.peakPeriod || '-',
              gpa: Number(r.gpa ?? 0).toFixed(2),
              llmExplanation: r.llmExplanation || ''
            }
          })
        }
        this.pageDetailsMap = nextMap
      } catch (error) {
        console.error('分页详情加载失败:', error)
        ElMessage.warning('分页详情加载较慢，已展示基础聚类结果')
      } finally {
        this.detailLoading = false
      }
    },

    levelColor(level) {
      const colorMap = {
        '低消费': '#5470c6',
        '较低消费': '#91cc75',
        '中消费': '#fac858',
        '高消费': '#ee6666'
      }
      return colorMap[level] || '#909399'
    },

    tagType(level) {
      if (level === '低消费') return 'info'
      if (level === '较低消费') return 'success'
      if (level === '中消费') return 'warning'
      if (level === '高消费') return 'danger'
      return 'info'
    },

    quantile(arr, q) {
      if (!arr.length) return 0
      const sorted = [...arr].sort((a, b) => a - b)
      const idx = Math.floor((sorted.length - 1) * q)
      return sorted[idx]
    },

    mapLevel(value, q1, q2, q3) {
      if (value <= q1) return '低消费'
      if (value <= q2) return '较低消费'
      if (value <= q3) return '中消费'
      return '高消费'
    },

    toFixedNum(v, digit = 2) {
      const n = Number(v || 0)
      return Number.isNaN(n) ? 0 : Number(n.toFixed(digit))
    },

    splitExplanationText(text) {
      const content = String(text || '').trim()
      if (!content) return []

      const normalized = content
        .replace(/\r\n/g, '\n')
        .replace(/[\t ]+/g, ' ')
        .trim()

      const byLine = normalized
        .split('\n')
        .map(s => s.trim())
        .filter(Boolean)

      if (byLine.length > 1) {
        return byLine
      }

      const punctuated = normalized.replace(/([。！？；])/g, '$1\n')
      const fragments = punctuated
        .split('\n')
        .map(s => s.trim())
        .filter(Boolean)

      const segments = []
      let bucket = ''
      fragments.forEach((frag) => {
        const next = bucket ? `${bucket}${frag}` : frag
        if (next.length >= 95) {
          segments.push(next)
          bucket = ''
        } else {
          bucket = next
        }
      })
      if (bucket) segments.push(bucket)
      return segments.length ? segments : [normalized]
    },

    avgBy(rows, key) {
      if (!rows.length) return 0
      const total = rows.reduce((sum, r) => sum + Number(r?.[key] || 0), 0)
      return total / rows.length
    },

    buildGroupSummaryData(rows) {
      const levelOrder = ['低消费', '较低消费', '中消费', '高消费']
      const total = rows.length || 1

      return levelOrder.map((level) => {
        const subset = rows.filter(i => i.level === level)
        return {
          level,
          sampleSize: subset.length,
          ratio: this.toFixedNum((subset.length / total) * 100),
          avgDailyAvg: this.toFixedNum(this.avgBy(subset, 'dailyAvg')),
          avgDailyCount: this.toFixedNum(this.avgBy(subset, 'dailyCount'))
        }
      })
    },

    buildGroupDeterministicText(groups) {
      const order = ['低消费', '较低消费', '中消费', '高消费']
      const map = {}
      groups.forEach((g) => {
        map[g.level] = g
      })

      const lines = order.map((level) => {
        const g = map[level] || {
          sampleSize: 0,
          ratio: 0,
          avgDailyAvg: 0,
          avgDailyCount: 0
        }
        const suggestion = level === '低消费'
          ? '建议优先关注基础餐次保障与预算可持续性，避免因过度压缩影响营养与学习状态。'
          : level === '较低消费'
            ? '建议保持当前节奏，同时监控周内波动，逐步形成更稳定的就餐结构。'
            : level === '中消费'
              ? '建议继续维持结构均衡，并通过固定预算上限控制临时性支出。'
              : '建议重点管理高峰时段与单次高额消费，防止短期波动拉高月度支出。'
        return `${level}群体：样本${g.sampleSize}人，占比${this.toFixedNum(g.ratio)}%，日均消费约¥${this.toFixedNum(g.avgDailyAvg)}、日均次数约${this.toFixedNum(g.avgDailyCount)}。该群体在消费强度和就餐活跃度上呈现分层差异，建议结合班级管理与服务供给做差异化支持。${suggestion}`
      })

      return `四类消费层级解释：${lines.join('')}整体上建议按分层开展预算教育、作息引导与窗口供给优化，并持续跟踪分层迁移趋势。以上结论仅反映群体消费行为特征，不代表任何行政认定。`
    },

    isValidGroupText(text) {
      const content = String(text || '').trim()
      if (!content) return false

      const hasAllLevels = ['低消费', '较低消费', '中消费', '高消费'].every(k => content.includes(k))
      const hasPersonalTone = content.includes('你属于') || content.includes('你的消费') || content.includes('你当前')
      const hasSuggestion = content.includes('建议')
      const hasEnoughLength = content.length >= 220

      return hasAllLevels && !hasPersonalTone && hasSuggestion && hasEnoughLength
    },

    async buildGroupLlmExplanation(rows, fallbackSummary = '') {
      const groups = this.buildGroupSummaryData(rows)
      const strictFallback = this.buildGroupDeterministicText(groups)
      const payload = {
        scene: 'group-portrait',
        style: 'plain-chinese',
        data: {
          scope: 'group',
          sampleSize: rows.length,
          groups
        },
        prompt: '你是高校消费行为分析助手。请按“低消费、较低消费、中消费、高消费”四段输出解释，每段都必须包含：1) 该层级的消费强度与频次特征（结合给定数值）；2) 可能行为成因；3) 对学校管理或学生支持的一条可执行建议。最后再补充一段“整体建议”，总结分层运营重点与后续跟踪指标。语气客观中性，避免标签化和因果夸大，总字数320-500字，并明确“结论仅反映消费行为特征，不代表行政认定”。'
      }

      try {
        const res = await this.withTimeout(getDeepSeekExplanation(payload), 20000)
        const text = res?.text || res?.answer || res?.data?.text || res?.data?.answer || ''
        const normalized = String(text || '').trim()
        this.llmSummaryText = this.isValidGroupText(normalized)
          ? normalized
          : (this.isValidGroupText(fallbackSummary) ? fallbackSummary : strictFallback)
      } catch {
        this.llmSummaryText = this.isValidGroupText(fallbackSummary) ? fallbackSummary : strictFallback
      }
    },

    async buildPersonalLlmExplanation(rows) {
      const row = this.personalMergedRow.studentId !== '-' ? this.personalMergedRow : (rows[0] || {})
      if (row.llmExplanation) {
        this.llmPersonalText = String(row.llmExplanation)
        return
      }

      const payload = {
        scene: 'personal-portrait',
        style: 'plain-chinese',
        data: {
          basicInfo: {
            studentId: row.studentId || String(this.queryForm.studentId || '').trim(),
            name: row.name || '-',
            gender: row.gender || '-',
            college: row.college || '-',
            major: row.major || '-',
            grade: row.grade || '-',
            className: row.className || '-'
          },
          portrait: {
            level: row.level || '-',
            activity: Number(row.dailyCount || 0) >= 3 ? '高频消费' : Number(row.dailyCount || 0) >= 1.5 ? '中频消费' : '低频消费',
            schedule: row.peakPeriod || '-',
            studyState: Number(row.gpa || 0) >= 3.5 ? '学习状态优秀' : Number(row.gpa || 0) >= 3.0 ? '学习状态良好' : Number(row.gpa || 0) > 0 ? '学习状态待提升' : '暂无成绩数据'
          },
          metrics: {
            dailyAvg: this.toFixedNum(row.dailyAvg),
            dailyCount: this.toFixedNum(row.dailyCount),
            monthAvgAmount: this.toFixedNum(row.monthAvgAmount),
            monthAvgCount: this.toFixedNum(row.monthAvgCount),
            favoriteWindow: row.favoriteWindow || '-',
            peakPeriod: row.peakPeriod || '-',
            gpa: this.toFixedNum(row.gpa)
          }
        },
        prompt: '请基于该学生用户画像输出300-450字解释，必须分为四段：1) 画像总览（先说消费层级和活跃度）；2) 指标解读（逐项解释日均消费、日均次数、月均消费、绩点、窗口/时段偏好，避免空话）；3) 与同筛选群体的相对位置（指出高于/低于群体均值的方面）；4) 给出3条可执行建议（预算、餐次结构、波动跟踪）。语气客观中性、通俗易懂，明确“仅反映消费行为特征，不代表行政认定”。'
      }

      const groupRef = this.benchmarkRows.length ? this.benchmarkRows : this.portraitResults
      const avgDaily = this.toFixedNum(this.avgBy(groupRef, 'dailyAvg'))
      const avgCount = this.toFixedNum(this.avgBy(groupRef, 'dailyCount'))
      const avgMonth = this.toFixedNum(this.avgBy(groupRef, 'monthAvgAmount'))
      const avgGpa = this.toFixedNum(this.avgBy(groupRef, 'gpa'))
      const fallback = `该学生当前处于“${row.level || '未知'}”层级，整体属于${Number(row.dailyCount || 0) >= 3 ? '高频消费' : Number(row.dailyCount || 0) >= 1.5 ? '中频消费' : '低频消费'}。从个人指标看，日均消费约¥${this.toFixedNum(row.dailyAvg)}、日均消费次数约${this.toFixedNum(row.dailyCount)}次，月均消费约¥${this.toFixedNum(row.monthAvgAmount)}，月均消费次数约${this.toFixedNum(row.monthAvgCount)}次，绩点约${this.toFixedNum(row.gpa)}。消费高峰主要出现在${row.peakPeriod || '常见时段'}，常去窗口为${row.favoriteWindow || '常用窗口'}。与同筛选群体相比，日均消费${this.toFixedNum(row.dailyAvg) >= avgDaily ? '高于' : '低于'}群体均值（群体约¥${avgDaily}），消费频次${this.toFixedNum(row.dailyCount) >= avgCount ? '高于' : '低于'}群体均值（群体约${avgCount}次），月均消费${this.toFixedNum(row.monthAvgAmount) >= avgMonth ? '高于' : '低于'}群体均值（群体约¥${avgMonth}），绩点${this.toFixedNum(row.gpa) >= avgGpa ? '高于' : '低于'}群体均值（群体约${avgGpa}）。建议一：设置周预算和单次消费上限，控制高峰时段冲动支出；建议二：保持稳定餐次结构，优先保障早餐与晚餐规律性；建议三：连续观察4周消费波动与学习状态变化，再做结构性调整。结论仅反映消费行为特征，不代表行政认定。`

      try {
        payload.prompt = '请基于该学生用户画像输出300-450字解释，结构为：1) 一句话总结整体画像；2) 逐项解读消费金额、频次、月度支出、窗口/时段偏好和绩点；3) 与同筛选群体均值做对比并解释差异；4) 给出3条可执行建议（预算管理、作息/餐次结构、波动跟踪）；5) 明确该结论仅反映消费行为特征，不代表行政认定。要求术语准确、通俗易懂、避免模板化。'
        const res = await this.withTimeout(getDeepSeekExplanation(payload), 20000)
        const text = res?.text || res?.answer || res?.data?.text || res?.data?.answer
        this.llmPersonalText = String(text || '').trim() || fallback
      } catch {
        this.llmPersonalText = fallback
      }
    },

    async refreshLlmInterpretation(rows, fallbackSummary = '') {
      this.llmLoading = true
      this.llmSummaryText = ''
      this.llmPersonalText = ''
      try {
        if (!rows.length) return

        if (this.isPersonalScope) {
          await this.buildPersonalLlmExplanation(rows)
        } else {
          await this.buildGroupLlmExplanation(rows, fallbackSummary)
        }
      } finally {
        this.llmLoading = false
      }
    },

    normalizeRows(res) {
      const raw = res?.results || res?.data?.results || res?.povertyResults || res?.data?.povertyResults || res?.data || res || []
      const arr = Array.isArray(raw) ? raw : []
      const llmMap = res?.llmStudentExplanations || res?.data?.llmStudentExplanations || {}

      const base = arr.map((i) => ({
        studentId: i.studentId || i.student_id || '-',
        name: i.name || i.studentName || i.student_name || '-',
        gender: i.gender || '-',
        college: i.college || i.collegeName || '-',
        major: i.major || i.majorName || '-',
        className: i.className || i.class_name || '-',
        grade: i.grade || '-',
        dailyAvg: Number(i.dailyAvg ?? i.daily_avg ?? i.monthlyAvg ?? i.monthly_avg ?? 0),
        dailyCount: Number(i.dailyCount ?? i.daily_count ?? i.monthAvgCount ?? i.month_avg_count ?? 0),
        monthAvgAmount: Number(i.monthAvgAmount ?? i.month_avg_amount ?? 0),
        monthAvgCount: Number(i.monthAvgCount ?? i.month_avg_count ?? 0),
        favoriteWindow: i.favoriteWindow || i.favorite_window || '-',
        peakPeriod: i.peakPeriod || i.peak_period || '-',
        gpa: Number(i.gpa ?? i.GPA ?? i.score ?? 0).toFixed(2),
        level: i.clusterType || i.consumptionType || i.consumptionGroup || '',
        llmExplanation: i.llmExplanation || llmMap[String(i.studentId || i.student_id || '')] || ''
      }))

      const values = base.map(i => i.dailyAvg).filter(v => v > 0)
      const q1 = this.quantile(values, 0.25)
      const q2 = this.quantile(values, 0.5)
      const q3 = this.quantile(values, 0.75)

      return base.map((i) => ({
        ...i,
        level: i.level || this.mapLevel(i.dailyAvg, q1, q2, q3)
      }))
    },

    applyRelativeLevel(targetRows, referenceRows) {
      const refs = Array.isArray(referenceRows) ? referenceRows : []
      const values = refs.map(i => Number(i.dailyAvg || 0)).filter(v => v > 0)
      if (!values.length) return targetRows
      const q1 = this.quantile(values, 0.25)
      const q2 = this.quantile(values, 0.5)
      const q3 = this.quantile(values, 0.75)
      return targetRows.map((row) => ({
        ...row,
        level: this.mapLevel(Number(row.dailyAvg || 0), q1, q2, q3)
      }))
    },

    async handleAnalyze(resetPage = true) {
      this.loading = true
      this.loadError = ''
      try {
        if (resetPage) {
          this.resultPagination.currentPage = 1
        }

        const params = {
          college: this.queryForm.college || undefined,
          major: this.queryForm.major || undefined,
          grade: this.queryForm.grade || undefined,
          className: this.queryForm.class || undefined,
          studentId: this.queryForm.studentId || undefined,
          clusterMethod: 'kmeans',
          includeDetails: false
        }

        if (Array.isArray(this.queryForm.dateRange) && this.queryForm.dateRange.length === 2) {
          params.timeBegin = this.queryForm.dateRange[0]
          params.timeEnd = this.queryForm.dateRange[1]
        }

        let res = null
        let benchmarkRes = null
        if (this.isPersonalScope) {
          const benchmarkParams = {
            college: this.queryForm.college || undefined,
            major: this.queryForm.major || undefined,
            grade: this.queryForm.grade || undefined,
            className: this.queryForm.class || undefined,
            clusterMethod: 'kmeans',
            includeDetails: false
          }
          if (Array.isArray(this.queryForm.dateRange) && this.queryForm.dateRange.length === 2) {
            benchmarkParams.timeBegin = this.queryForm.dateRange[0]
            benchmarkParams.timeEnd = this.queryForm.dateRange[1]
          }
          const [personalResp, benchmarkResp] = await Promise.all([
            this.withTimeout(getPovertyIdentification(params), 25000),
            this.withTimeout(getPovertyIdentification(benchmarkParams), 25000)
          ])
          res = personalResp
          benchmarkRes = benchmarkResp
        } else {
          res = await this.withTimeout(getPovertyIdentification(params), 25000)
        }

        const normalized = this.normalizeRows(res)
        this.benchmarkRows = benchmarkRes ? this.normalizeRows(benchmarkRes) : normalized
        this.portraitResults = normalized

        const llmSummary = String(res?.llmSummary || res?.data?.llmSummary || '').trim()
        this.resultPagination.total = this.portraitResults.length
        await this.loadPageDetails()
        await this.refreshLlmInterpretation(this.portraitResults, llmSummary)
      } catch (error) {
        console.error('画像分析失败:', error)
        this.loadError = error?.message || '请检查后端服务后重试。'
        ElMessage.error(error?.message === '请求超时' ? '画像分析超时，请缩小筛选范围后重试' : '画像分析失败，请稍后重试')
        this.portraitResults = []
        this.benchmarkRows = []
        this.pageDetailsMap = {}
        this.llmSummaryText = ''
        this.llmPersonalText = ''
      } finally {
        this.loading = false
      }
    },

    handleReset() {
      this.queryForm = {
        college: '',
        major: '',
        grade: '',
        class: '',
        dateRange: ['2024-09-01', '2024-09-30'],
        studentId: ''
      }
      this.majors = []
      this.classes = []
      this.portraitResults = []
      this.benchmarkRows = []
      this.pageDetailsMap = {}
      this.llmSummaryText = ''
      this.llmPersonalText = ''
      this.resultPagination.total = 0
      this.resultPagination.currentPage = 1
    },

    handlePageChange(page) {
      this.resultPagination.currentPage = Number(page || 1)
      this.loadPageDetails()
    },

    handleSizeChange(size) {
      this.resultPagination.pageSize = Number(size || 20)
      this.resultPagination.currentPage = 1
      this.loadPageDetails()
    }
  }
}
</script>

<style scoped>
.user-portrait-analysis {
  padding: 20px;
}

.user-portrait-analysis :deep(.el-card) {
  border-radius: 12px;
  border: 1px solid #edf1f7;
  box-shadow: 0 6px 18px rgba(18, 38, 63, 0.05);
}

.user-portrait-analysis :deep(.el-card__header) {
  font-weight: 600;
  color: #2f3a4f;
}

.user-portrait-analysis :deep(.el-table .cell) {
  white-space: nowrap;
}

.error-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.pagination {
  margin-top: 12px;
  text-align: right;
}

.explain-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.explain-item {
  padding: 10px 12px;
  background: #f7f9fc;
  border: 1px solid #ebeef5;
  border-radius: 8px;
}

.explain-title {
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.explain-content {
  color: #606266;
  line-height: 1.7;
  font-size: 14px;
}

.explain-paragraph {
  margin: 0 0 8px;
}

.explain-paragraph:last-child {
  margin-bottom: 0;
}

@media (max-width: 1200px) {
  .pagination {
    text-align: left;
  }
}
</style>
