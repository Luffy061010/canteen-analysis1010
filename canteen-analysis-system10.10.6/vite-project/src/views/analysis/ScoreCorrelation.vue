<template>
  <div class="score-correlation">
    <el-alert v-if="loadError" type="error" :closable="false" show-icon style="margin-bottom: 16px;">
      <template #title>成绩关联分析失败</template>
      <div class="error-actions">
        <span>{{ loadError }}</span>
        <el-button size="small" type="danger" plain :loading="loading" @click="handleAnalyze">重试</el-button>
      </div>
    </el-alert>

    <el-alert v-if="backendHint" type="warning" :closable="false" show-icon style="margin-bottom: 16px;">
      <template #title>当前筛选暂无可分析数据</template>
      <span>{{ backendHint }}</span>
    </el-alert>

    <el-card>
      <template #header>
        <span>成绩关联性分析</span>
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
              <el-input v-model="queryForm.studentId" placeholder="可选：输入学号" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :md="6" :lg="8">
            <el-form-item>
              <el-button type="primary" :loading="loading" @click="handleAnalyze">分析</el-button>
              <el-button :disabled="loading" @click="handleReset">重置</el-button>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>

      <el-row :gutter="20" style="margin-top: 20px;">
        <el-col :span="24">
          <el-card>
            <template #header>
              <span>{{ chartTitle }}</span>
            </template>
            <BaseChart :options="chartOptions" :loading="loading" :container-style="{ width: '100%', height: '420px' }" />
          </el-card>
        </el-col>
      </el-row>

      <el-card style="margin-top: 20px;" v-loading="llmLoading">
        <template #header>
          <span>{{ isPersonalScope ? 'DeepSeek 个人解释' : 'DeepSeek 群体解释' }}</span>
        </template>
        <div class="explain-text">{{ explainText }}</div>
        <div class="hint-text">说明：这里强调的是“相关关系”，不是“因果关系”；个人模式会与同筛选群体均值对比。</div>
      </el-card>
    </el-card>
  </div>
</template>

<script>
import BaseChart from '@/components/Charts/BaseChart.vue'
import { ElMessage } from 'element-plus'
import { getDeepSeekExplanation, getScoreCorrelation } from '@/api/user.js'
import { COLLEGES_MAJORS, generateClassNames } from '@/utils/const_value.js'

export default {
  name: 'ScoreCorrelation',
  components: { BaseChart },
  data() {
    return {
      queryForm: {
        college: '',
        major: '',
        grade: '',
        class: '',
        dateRange: [],
        studentId: '',
        correlationMethod: 'pearson',
        variable1: 'gpa'
      },
      colleges: Object.keys(COLLEGES_MAJORS),
      majors: [],
      grades: ['2021', '2022', '2023', '2024'],
      classes: [],
      loading: false,
      loadError: '',
      backendHint: '',
      rawRows: [],
      scatterPoints: [],
      studentProfile: null,
      studentPoint: null,
      summary: {
        sampleSize: 0,
        significantCount: 0,
        mainDirection: '暂无',
        mainStrength: '弱',
        avgDaily: 0,
        avgMonthly: 0,
        avgGpa: 0
      },
      llmLoading: false,
      explainText: '点击“分析”后生成通俗解释。'
    }
  },
  computed: {
    isPersonalScope() {
      return Boolean(String(this.queryForm.studentId || '').trim())
    },
    hasPersonalData() {
      return this.isPersonalScope && this.studentProfile && Number(this.summary.sampleSize || 0) > 0
    },
    chartTitle() {
      return this.hasPersonalData ? '个人消费与群体均值对比图' : '消费与绩点关系热力图'
    },
    topRows() {
      return this.rawRows
        .slice(0, 5)
        .map((row) => {
          const corr = Number(row.corr || row.correlation || 0)
          const p = Number(row.pValue || row.p_value || 1)
          return {
            feature: row.feature || row.factor || '未知因素',
            corr: corr.toFixed(3),
            pValue: p.toFixed(4),
            direction: corr >= 0 ? '正相关' : '负相关',
            strength: this.strengthLevel(Math.abs(corr))
          }
        })
    },
    chartOptions() {
      return this.hasPersonalData ? this.personalCompareOptions : this.heatmapOptions
    },
    personalCompareOptions() {
      if (!this.hasPersonalData) {
        return {
          title: {
            text: '暂无个人对比数据',
            left: 'center',
            top: 'center',
            textStyle: { color: '#999', fontSize: 14 }
          },
          xAxis: { show: false },
          yAxis: { show: false },
          series: []
        }
      }

      const profile = this.studentProfile || {}
      const studentDaily = Number(profile.dailyAvg || this.studentPoint?.dailyAvg || 0)
      const studentMonthly = Number(profile.monthlyAvg || (studentDaily * 30))
      const studentGpa = Number(profile.gpa || this.studentPoint?.gpa || 0)

      const groupDaily = Number(this.summary.avgDaily || 0)
      const groupMonthly = Number(this.summary.avgMonthly || (groupDaily * 30))
      const groupGpa = Number(this.summary.avgGpa || 0)

      return {
        tooltip: { trigger: 'axis' },
        legend: { top: 8, data: ['个人', '群体均值'] },
        grid: { left: '6%', right: '4%', bottom: '8%', top: '16%', containLabel: true },
        xAxis: {
          type: 'category',
          data: ['日均消费(元)', '月均消费(元)', 'GPA']
        },
        yAxis: {
          type: 'value'
        },
        series: [
          {
            name: '个人',
            type: 'bar',
            barMaxWidth: 34,
            data: [
              Number(studentDaily.toFixed(2)),
              Number(studentMonthly.toFixed(2)),
              Number(studentGpa.toFixed(2))
            ],
            itemStyle: { color: '#3A7AFE', borderRadius: [6, 6, 0, 0] }
          },
          {
            name: '群体均值',
            type: 'bar',
            barMaxWidth: 34,
            data: [
              Number(groupDaily.toFixed(2)),
              Number(groupMonthly.toFixed(2)),
              Number(groupGpa.toFixed(2))
            ],
            itemStyle: { color: '#9AA4B2', borderRadius: [6, 6, 0, 0] }
          }
        ]
      }
    },
    heatmapOptions() {
      if (!this.scatterPoints.length) {
        return {
          title: {
            text: '暂无可视化数据',
            left: 'center',
            top: 'center',
            textStyle: { color: '#999', fontSize: 14 }
          },
          xAxis: { show: false },
          yAxis: { show: false },
          series: []
        }
      }

      const xBins = 6
      const yBins = 6
      const xs = this.scatterPoints.map(p => Number(p.consumption || 0)).filter(v => !Number.isNaN(v))
      const ys = this.scatterPoints.map(p => Number(p.gpa || 0)).filter(v => !Number.isNaN(v))
      if (!xs.length || !ys.length) return { series: [] }

      const minX = Math.min(...xs)
      const maxX = Math.max(...xs)
      const minY = Math.min(...ys)
      const maxY = Math.max(...ys)
      const stepX = (maxX - minX) / xBins || 1
      const stepY = (maxY - minY) / yBins || 0.1

      const matrix = Array.from({ length: xBins }, () => Array.from({ length: yBins }, () => 0))
      this.scatterPoints.forEach((p) => {
        const x = Number(p.consumption || 0)
        const y = Number(p.gpa || 0)
        let xi = Math.min(xBins - 1, Math.max(0, Math.floor((x - minX) / stepX)))
        let yi = Math.min(yBins - 1, Math.max(0, Math.floor((y - minY) / stepY)))
        matrix[xi][yi] += 1
      })

      const data = []
      for (let i = 0; i < xBins; i += 1) {
        for (let j = 0; j < yBins; j += 1) {
          data.push([i, j, matrix[i][j]])
        }
      }

      const xLabels = Array.from({ length: xBins }, (_, i) => {
        const s = (minX + i * stepX).toFixed(1)
        const e = (i === xBins - 1 ? maxX : minX + (i + 1) * stepX).toFixed(1)
        return `${s}-${e}`
      })
      const yLabels = Array.from({ length: yBins }, (_, i) => {
        const s = (minY + i * stepY).toFixed(2)
        const e = (i === yBins - 1 ? maxY : minY + (i + 1) * stepY).toFixed(2)
        return `${s}-${e}`
      })

      return {
        tooltip: {
          position: 'top',
          formatter: (params) => {
            const [x, y, val] = params.value
            return `消费区间: ${xLabels[x]}<br/>绩点区间: ${yLabels[y]}<br/>人数: ${val}`
          }
        },
        grid: { height: '66%', top: '8%', left: '6%', right: '4%' },
        xAxis: { type: 'category', data: xLabels, name: '消费额区间', splitArea: { show: true }, axisLabel: { rotate: 20, fontSize: 11 } },
        yAxis: { type: 'category', data: yLabels, name: '绩点区间', splitArea: { show: true }, axisLabel: { fontSize: 11 } },
        visualMap: {
          min: 0,
          max: Math.max(...data.map(d => d[2]), 1),
          calculable: true,
          orient: 'horizontal',
          left: 'center',
          bottom: '3%'
        },
        series: [{ name: '密度', type: 'heatmap', data, emphasis: { itemStyle: { borderColor: '#333', borderWidth: 1 } } }]
      }
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
    // 默认不自动分析，避免页面初始加载时触发计算
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

    strengthLevel(absCorr) {
      if (absCorr >= 0.5) return '强'
      if (absCorr >= 0.3) return '中'
      return '弱'
    },

    localExplain() {
      if (this.hasPersonalData) {
        return this.localExplainPersonal()
      }

      return this.localExplainGroup()
    },

    localExplainGroup() {
      if (!this.topRows.length) {
        return '当前筛选下有效样本较少，建议扩大时间范围或取消部分筛选后再分析。'
      }
      const top = this.topRows[0] || {}
      const second = this.topRows[1] || {}
      const third = this.topRows[2] || {}
      const sample = Number(this.summary.sampleSize || 0)
      const sig = Number(this.summary.significantCount || 0)
      const directionTip = top.direction === '正相关'
        ? '在当前样本中，该特征提升时，绩点也更倾向同步提升。'
        : '在当前样本中，该特征提升时，绩点可能呈反向变化。'

      const secondText = second.feature
        ? `其次是“${second.feature}”（${second.direction}，r=${second.corr}）。`
        : ''
      const thirdText = third.feature
        ? `第三是“${third.feature}”（${third.direction}，r=${third.corr}）。`
        : ''

      return `【结论概览】本次分析覆盖${sample}个有效样本，达到统计显著的指标有${sig}项，整体呈现“${this.summary.mainDirection}、${this.summary.mainStrength}相关”的特征。当前关联最强的是“${top.feature || '未知因素'}”（${top.direction || '相关方向待定'}，r=${top.corr || '0.000'}，p=${top.pValue || '1.0000'}）。${directionTip}${secondText}${thirdText}\n\n【业务解读】这意味着在同一筛选群体中，消费行为特征与学业表现存在同步变化的倾向，尤其是头部指标更值得持续关注。若相关方向为正，通常可理解为“该指标升高时，绩点更容易同向变化”；若为负，则提示“该指标升高时，绩点可能反向变化”。请注意这只是统计共变关系，不能直接解释成“消费行为导致成绩变化”。\n\n【风险与边界】本结果可能受到混杂因素影响，例如课程难度差异、阶段性考试压力、考勤情况、作息规律、奖助学金与兼职情况等；同时样本时间窗口若偏短，也可能放大短期波动。\n\n【建议动作】建议一，按周追踪前3个高相关指标，建立趋势看板并设置异常阈值；建议二，把消费指标与考勤、挂科预警、课程负荷联合建模，减少单指标误判；建议三，对高波动群体开展预算管理和学习节律辅导，连续观察4-8周后再评估干预效果。\n\n以上结论仅代表相关关系，不代表因果关系。`
    },

    localExplainPersonal() {
      const profile = this.studentProfile || {}
      const sid = String(profile.studentId || this.queryForm.studentId || '').trim() || '-'
      const daily = Number(profile.dailyAvg || this.studentPoint?.dailyAvg || 0)
      const monthly = Number(profile.monthlyAvg || (daily * 30))
      const gpa = Number(profile.gpa || this.studentPoint?.gpa || 0)
      const groupDaily = Number(this.summary.avgDaily || 0)
      const groupGpa = Number(this.summary.avgGpa || 0)
      const diffDaily = daily - groupDaily
      const diffGpa = gpa - groupGpa
      const dailyTrend = diffDaily >= 0 ? '高于' : '低于'
      const gpaTrend = diffGpa >= 0 ? '高于' : '低于'

      return `【个人画像结论】学号${sid}在当前筛选口径下，日均消费约¥${daily.toFixed(2)}，月均消费约¥${monthly.toFixed(2)}，GPA约${gpa.toFixed(2)}。与同口径群体相比，个人日均消费${dailyTrend}群体${Math.abs(diffDaily).toFixed(2)}元，GPA${gpaTrend}群体${Math.abs(diffGpa).toFixed(2)}。\n\n【位置解读】这说明该学生在“消费水平-学习表现”的二维坐标中，与群体中心存在偏移：若消费偏高且GPA偏低，应优先关注高波动消费是否与学习节律冲突；若消费偏低且GPA偏高，可视为较强自我管理特征，但仍需关注极端节省带来的生活质量风险。\n\n【边界说明】个体结论容易受短期事件影响，如考试周、社团活动、兼职收入变化、节假日消费集中等，因此不宜基于单次分析做定性判断，更不应直接推断因果。\n\n【行动建议】建议一，按周记录消费与课程负荷变化，形成连续观察序列；建议二，对异常高额消费日期做事件标注，排查是否集中在非必要支出；建议三，与考勤、作息、课程难度联合评估，必要时提供个性化预算与学习节奏建议。\n\n以上结论仅代表相关关系，不代表因果关系。`
    },

    isValidCorrelationText(text) {
      const content = String(text || '').trim()
      if (!content) return false
      const hasRiskHint = content.includes('相关') && (content.includes('因果') || content.includes('不代表因果'))
      const hasSuggestion = content.includes('建议')
      const hasStructure = content.includes('样本') || content.includes('群体') || content.includes('个人')
      const hasLength = content.length >= 320
      return hasRiskHint && hasSuggestion && hasStructure && hasLength
    },

    async buildDeepSeekText() {
      this.llmLoading = true
      const scene = this.hasPersonalData ? 'score-correlation-personal' : 'score-correlation'
      const payload = {
        scene,
        style: 'plain-chinese',
        data: {
          scope: {
            college: this.queryForm.college || '全部',
            major: this.queryForm.major || '全部',
            grade: this.queryForm.grade || '全部',
            className: this.queryForm.class || '全部',
            studentId: this.queryForm.studentId || '未指定',
            dateRange: Array.isArray(this.queryForm.dateRange) && this.queryForm.dateRange.length === 2
              ? `${this.queryForm.dateRange[0]} 至 ${this.queryForm.dateRange[1]}`
              : '全量时间'
          },
          summary: this.summary,
          topRows: this.topRows,
          samplePoints: this.scatterPoints.slice(0, 12),
          studentProfile: this.studentProfile,
          studentPoint: this.studentPoint
        },
        prompt: this.hasPersonalData
          ? '请基于给定统计结果，输出520-780字中文解释，面向“单个学生对比群体”场景。写作结构必须分为五段并带段首小标题：1) 个人概况：说明日均/月均消费与GPA；2) 群体对比：明确与同筛选群体均值的高低方向与幅度；3) 位置解读：解释该学生在“消费-成绩”坐标中的位置和可能含义；4) 风险与边界：点明混杂因素、时间窗口局限、样本偏差；5) 行动建议：给出3条可执行建议（短期1条、中期1条、长期1条）。要求语气专业但通俗，适合辅导员直接阅读，避免模板化空话，必须明确“仅代表相关关系，不代表因果关系”。'
          : '请基于给定统计结果，输出520-780字中文解释。写作结构必须分为五段并带段首小标题：1) 概览：样本量、显著指标数、主方向与强度；2) 重点指标：解读相关性绝对值最高前3项（方向、强弱、业务含义）；3) 管理含义：对学业支持和消费治理分别提出可读结论；4) 风险与边界：说明相关不等于因果、混杂变量与时间窗口影响；5) 后续建议：给出3条可执行建议（监测、联动分析、分层干预）。要求语气客观、避免夸大、可直接放进业务分析报告，必须明确“仅代表相关关系，不代表因果关系”。'
      }

      try {
        const result = await this.withTimeout(getDeepSeekExplanation(payload), 20000)
        const text = result?.text || result?.answer || result?.data?.text || result?.data?.answer || ''
        const normalized = String(text || '').trim()
        const fallback = this.localExplain()
        if (this.isValidCorrelationText(normalized)) {
          this.explainText = normalized
          return
        }
        this.explainText = this.isValidCorrelationText(fallback)
          ? fallback
          : `${fallback} 建议在后续评估中补充生活作息、课程难度与出勤数据，以提升解释稳健性。`
      } catch {
        this.explainText = this.localExplain()
      } finally {
        this.llmLoading = false
      }
    },

    normalizeResult(result) {
      const root = result?.data || result || {}
      this.backendHint = root?.message || ''

      let rows = []
      if (Array.isArray(root.correlationResults)) rows = root.correlationResults
      else if (Array.isArray(root.results)) rows = root.results
      else if (Array.isArray(root.correlations)) rows = root.correlations
      else if (Array.isArray(root)) rows = root

      const sampleSize = Number(root.sampleSize || root.meta?.sampleSize || root.mergedCount || 0)
      const significantCount = rows.filter((r) => Number(r.pValue || r.p_value || 1) < 0.05).length

      const sortedRows = [...rows]
        .map((r) => ({ ...r, absCorr: Math.abs(Number(r.corr || r.correlation || 0)) }))
        .sort((a, b) => b.absCorr - a.absCorr)

      const topCorr = Number(sortedRows[0]?.corr || sortedRows[0]?.correlation || 0)

      const pointsRaw = root.scatterData || root.scatterPoints || root.samples || root.points || []
      const points = Array.isArray(pointsRaw)
        ? pointsRaw.map((p) => ({
          consumption: Number(p.consumption || p.amount || p.monthTotalAmount || p.x || 0),
          gpa: Number(p.gpa || p.score || p.y || 0)
        })).filter(p => !Number.isNaN(p.consumption) && !Number.isNaN(p.gpa))
        : []

      this.rawRows = sortedRows
      this.scatterPoints = points
      this.studentProfile = root.studentProfile || null
      this.studentPoint = root.studentPoint || null
      this.summary = {
        sampleSize,
        significantCount,
        mainDirection: topCorr >= 0 ? '正相关为主' : '负相关为主',
        mainStrength: this.strengthLevel(Math.abs(topCorr)),
        avgDaily: Number(root.meta?.avgDaily || 0),
        avgMonthly: Number(root.meta?.avgDaily || 0) * 30,
        avgGpa: Number(root.meta?.avgGpa || 0)
      }
    },

    async handleAnalyze() {
      this.loading = true
      this.loadError = ''
      this.backendHint = ''
      try {
        const params = {
          college: this.queryForm.college || undefined,
          major: this.queryForm.major || undefined,
          grade: this.queryForm.grade || undefined,
          className: this.queryForm.class || undefined,
          studentId: this.queryForm.studentId || undefined,
          correlationMethod: 'pearson',
          variable1: 'gpa'
        }

        const hasDateRange = Array.isArray(this.queryForm.dateRange) && this.queryForm.dateRange.length === 2
        if (hasDateRange) {
          params.timeBegin = this.queryForm.dateRange[0]
          params.timeEnd = this.queryForm.dateRange[1]
        }

        const result = await this.withTimeout(getScoreCorrelation(params), 25000)
        this.normalizeResult(result)
        await this.buildDeepSeekText()
      } catch (error) {
        console.error('成绩关联分析失败:', error)
        this.loadError = error?.message || '请检查后端服务后重试。'
        ElMessage.error(error?.message === '请求超时' ? '成绩关联分析超时，请缩小筛选范围后重试' : '成绩关联分析失败，请稍后重试')
        this.rawRows = []
        this.scatterPoints = []
        this.studentProfile = null
        this.studentPoint = null
        this.explainText = '暂时无法生成解释，请稍后重试。'
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
        dateRange: [],
        studentId: '',
        correlationMethod: 'pearson',
        variable1: 'gpa'
      }
      this.majors = []
      this.classes = []
      this.rawRows = []
      this.scatterPoints = []
      this.studentProfile = null
      this.studentPoint = null
      this.backendHint = ''
      this.summary = {
        sampleSize: 0,
        significantCount: 0,
        mainDirection: '暂无',
        mainStrength: '弱',
        avgDaily: 0,
        avgMonthly: 0,
        avgGpa: 0
      }
      this.explainText = '点击“分析”后生成通俗解释。'
    }
  }
}
</script>

<style scoped>
.score-correlation {
  padding: 20px;
}

.score-correlation :deep(.el-card) {
  border-radius: 12px;
  border: 1px solid #edf1f7;
  box-shadow: 0 6px 18px rgba(18, 38, 63, 0.05);
}

.score-correlation :deep(.el-card__header) {
  font-weight: 600;
  color: #2f3a4f;
}

.error-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.explain-text {
  font-size: 15px;
  color: #303133;
  line-height: 1.8;
  white-space: pre-wrap;
}

.hint-text {
  margin-top: 10px;
  color: #909399;
  font-size: 13px;
}
</style>
