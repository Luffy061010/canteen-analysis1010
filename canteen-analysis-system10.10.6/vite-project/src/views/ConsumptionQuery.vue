<template>
  <!-- 页面：消费信息查询与明细展示 -->
  <div class="consumption-query">
    <el-card>
      <template #header>
        <span>消费数据查询</span>
      </template>

      <el-form :model="queryForm" ref="queryForm" label-width="80px">
        <!-- 第一行：基本信息筛选 -->
        <el-row :gutter="20">
          <el-col :span="6">
            <el-form-item label="学院">
              <el-select
                  v-model="queryForm.college"
                  placeholder="请选择学院"
                  @change="handleCollegeChange"
                  clearable
              >
                <el-option label="全部" value=""></el-option>
                <el-option
                    v-for="college in collegeOptions"
                    :key="college"
                    :label="college"
                    :value="college"
                ></el-option>
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="专业">
              <el-select
                  v-model="queryForm.major"
                  placeholder="请选择专业"
                  @change="handleMajorChange"
                  clearable
                  :disabled="!queryForm.college"
              >
                <el-option label="全部" value=""></el-option>
                <el-option
                    v-for="major in majorOptions"
                    :key="major"
                    :label="major"
                    :value="major"
                ></el-option>
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="年级">
              <el-select
                  v-model="queryForm.grade"
                  placeholder="请选择年级"
                  @change="handleGradeChange"
                  clearable
              >
                <el-option label="全部" value=""></el-option>
                <el-option
                    v-for="grade in gradeOptions"
                    :key="grade"
                    :label="grade"
                    :value="grade"
                ></el-option>
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="班级">
              <el-select
                  v-model="queryForm.class"
                  placeholder="请选择班级"
                  clearable
                  :disabled="!queryForm.major || !queryForm.grade"
              >
                <el-option label="全部" value=""></el-option>
                <el-option
                    v-for="cls in classOptions"
                    :key="cls.value"
                    :label="cls.label"
                    :value="cls.value"
                ></el-option>
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 第二行：日期范围和学号 -->
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="开始日期">
              <el-date-picker
                  v-model="queryForm.startDate"
                  type="date"
                  placeholder="选择开始日期"
                  value-format="YYYY-MM-DD"
                  style="width: 100%"
              ></el-date-picker>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="结束日期">
              <el-date-picker
                  v-model="queryForm.endDate"
                  type="date"
                  placeholder="选择结束日期"
                  value-format="YYYY-MM-DD"
                  style="width: 100%"
              ></el-date-picker>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="学号">
              <el-input v-model="queryForm.studentId" placeholder="请输入学号"></el-input>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row>
          <el-col :span="24" style="text-align: right;">
            <el-button type="primary" @click="handleQuery" :loading="loading">查询</el-button>
            <el-button @click="handleReset">重置</el-button>
            <el-button @click="handleExport" :disabled="tableData.length === 0">导出数据</el-button>
          </el-col>
        </el-row>
      </el-form>
    </el-card>

    <!-- 统计信息 -->
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="6">
        <el-card>
          <div class="stat-item">
            <div class="stat-value">¥{{ totalAmount.toLocaleString() }}</div>
            <div class="stat-label">总消费金额</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <div class="stat-item">
            <div class="stat-value">{{ totalRecords.toLocaleString() }}</div>
            <div class="stat-label">消费记录数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <div class="stat-item">
            <div class="stat-value">¥{{ avgDaily.toLocaleString() }}</div>
            <div class="stat-label">日均消费</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <div class="stat-item">
            <div class="stat-value">{{ studentCount.toLocaleString() }}</div>
            <div class="stat-label">涉及学生数</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 查询结果 -->
    <el-card style="margin-top: 20px;">
      <template #header>
        <span>消费明细 (共 {{ total.toLocaleString() }} 条记录)</span>
      </template>

      <el-alert
          v-if="total > 10000"
          title="数据量较大，建议使用筛选条件缩小查询范围"
          type="info"
          show-icon
          style="margin-bottom: 15px;"
          :closable="false"
      ></el-alert>

      <el-table
          :data="tableData"
          style="width: 100%"
          v-loading="loading"
          :default-sort="{prop: 'consume_time', order: 'descending'}"
          @sort-change="handleSortChange"
      >
        <el-table-column prop="uid" label="学号" width="120" ></el-table-column>
        <el-table-column prop="name" label="姓名" width="100"></el-table-column>
        <el-table-column prop="college" label="学院" width="120" show-overflow-tooltip></el-table-column>
        <el-table-column prop="major" label="专业" width="120" show-overflow-tooltip></el-table-column>
        <el-table-column prop="consume_time" label="消费时间" width="180" ></el-table-column>
        <el-table-column prop="amount" label="消费金额" width="100" >
          <template #default="scope">
            ¥{{ scope.row.amount }}
          </template>
        </el-table-column>
        <el-table-column prop="window" label="消费窗口" width="120"></el-table-column>
      </el-table>

      <el-pagination
          style="margin-top: 20px;"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
          :current-page="currentPage"
          :page-sizes="[10, 20, 50, 100]"
          :page-size="pageSize"
          layout="total, sizes, prev, pager, next, jumper"
          :total="total"
          :disabled="loading">
      </el-pagination>
    </el-card>
  </div>
</template>

<script>
import { getConsumption, getConsumptionData, getStudentInfo } from '@/api/user.js'
import { exportXlsx } from '@/utils/download'
import { COLLEGES_MAJORS, generateClassNames } from '@/utils/const_value.js'

export default {
  name: 'ConsumptionQuery',
  data() {
    return {
      queryForm: {
        college: '',
        major: '',
        grade: '',
        class: '',
        startDate: '',
        endDate: '',
        studentId: '',
      },
      // 选项数据
      collegeOptions: Object.keys(COLLEGES_MAJORS),
      majorOptions: [],
      gradeOptions: ['2021级', '2022级', '2023级', '2024级'],
      classOptions: [],

      tableData: [],
      loading: false,
      currentPage: 1,
      pageSize: 20, // 默认每页显示20条，适应大数据量
      total: 0,
      totalAmount: 0,
      totalRecords: 0,
      avgDaily: 0,
      studentCount: 0,

      studentInfoCache: new Map(),

      // 排序参数
      sortField: 'consume_time',
      sortOrder: 'desc'
    };
  },
  mounted() {
    this.loadAllData();
  },
  methods: {
    // 学院变化处理
    handleCollegeChange(college) {
      this.queryForm.major = '';
      this.queryForm.grade = '';
      this.queryForm.class = '';
      this.majorOptions = [];
      this.classOptions = [];

      if (college && COLLEGES_MAJORS[college]) {
        this.majorOptions = COLLEGES_MAJORS[college].majors || [];
      }
    },

    // 专业变化处理
    handleMajorChange(major) {
      this.queryForm.grade = '';
      this.queryForm.class = '';
      this.classOptions = [];

      if (major && this.queryForm.grade) {
        this.updateClassOptions(major, this.queryForm.grade);
      }
    },

    // 年级变化处理
    handleGradeChange(grade) {
      this.queryForm.class = '';
      this.classOptions = [];

      if (this.queryForm.major && grade) {
        this.updateClassOptions(this.queryForm.major, grade);
      }
    },

    // 更新班级选项
    updateClassOptions(major, grade) {
      this.classOptions = [];
      const classNames = generateClassNames(major, grade);
      classNames.forEach(className => {
        this.classOptions.push({
          value: className,
          label: className
        });
      });
    },

    // 排序处理
    handleSortChange({ prop, order }) {
      this.sortField = prop || 'consume_time';
      this.sortOrder = order === 'ascending' ? 'asc' : 'desc';
      this.currentPage = 1;
      this.loadAllData();
    },

    async handleQuery() {
      this.loading = true;
      this.currentPage = 1;
      try {
        await this.loadAllData();
      } catch (error) {
        console.error('查询消费数据失败:', error);
        this.$message.error('查询失败，请重试');
      } finally {
        this.loading = false;
      }
    },

    handleReset() {
      this.queryForm = {
        college: '',
        major: '',
        grade: '',
        class: '',
        startDate: '',
        endDate: '',
        studentId: ''
      };
      this.majorOptions = [];
      this.classOptions = [];
      this.currentPage = 1;
      this.sortField = 'consume_time';
      this.sortOrder = 'desc';
      this.loadAllData();
    },

    async handleExport() {
      try {
        this.loading = true
        const rows = await this.fetchExportRecords()
        if (!rows.length) {
          this.$message.warning('无可导出数据')
          return
        }
        await exportXlsx(
          rows,
          [
            { label: '学号', key: 'uid' },
            { label: '姓名', key: 'name' },
            { label: '学院', key: 'college' },
            { label: '专业', key: 'major' },
            { label: '消费时间', key: 'consume_time' },
            { label: '消费金额', key: 'amount' },
            { label: '消费窗口', key: 'window' }
          ],
          `consumption_${Date.now()}.xlsx`,
          '消费明细'
        )
        this.$message.success('导出成功')
      } catch (error) {
        console.error('导出失败:', error)
        this.$message.error('导出失败，请重试')
      } finally {
        this.loading = false
      }
    },

    async fetchExportRecords() {
      const baseParams = this.buildRequestParams()
      const pageSize = 1000
      const maxPages = 100
      let page = 1
      let all = []
      let total = null

      while (page <= maxPages) {
        const params = { ...baseParams, page: String(page), pageSize: String(pageSize) }
        const res = await getConsumptionData(params)
        const data = res?.records ? res : res?.data
        const raw = data?.records || data?.data || data || []
        const records = Array.isArray(raw) ? raw : []
        const totalVal = data?.total || data?.totalCount
        if (totalVal !== undefined && totalVal !== null) total = Number(totalVal)

        const mapped = records.map((item, idx) => {
          const studentId = item.studentId || item.uid || item.student_id || ''
          const timeVal = item.consumptionTime || item.consume_time || item.consumption_time || ''
          const windowVal = item.window || item.windowId || item.window_id || '-'
          const amountVal = item.amount || 0

          return {
            key: `${studentId || idx}-${idx}`,
            uid: studentId || '-',
            name: item.name || item.studentName || item.student_name || '-',
            college: item.college || '-',
            major: item.major || '-',
            consume_time: typeof timeVal === 'string' ? timeVal.replace('T', ' ') : timeVal,
            amount: Number(amountVal).toFixed ? Number(amountVal).toFixed(2) : amountVal,
            window: windowVal
          }
        })

        all = all.concat(mapped)
        if (records.length < pageSize) break
        if (total && all.length >= total) break
        page += 1
      }

      await this.enrichStudentInfo(all)

      return all.map(row => {
        const cached = this.studentInfoCache.get(row.uid) || {}
        return {
          ...row,
          name: row.name !== '-' ? row.name : (cached.name || '-'),
          college: row.college !== '-' ? row.college : (cached.college || '-'),
          major: row.major !== '-' ? row.major : (cached.major || '-'),
        }
      })
    },

    handleSizeChange(val) {
      this.pageSize = val;
      this.currentPage = 1;
      this.loadAllData();
    },

    handleCurrentChange(val) {
      this.currentPage = val;
      this.loadAllData();
    },

     async loadAllData() {
       try {
         const params = this.buildRequestParams();

         // 使用Promise.all同时调用两个API，但添加超时控制
         const apiTimeout = 30000; // 30秒超时
         const statsPromise = getConsumption(params);
         const tablePromise = getConsumptionData(params);

         const timeoutPromise = new Promise((_, reject) => {
           setTimeout(() => reject(new Error('请求超时')), apiTimeout);
         });

         const [statsResponse, tableResponse] = await Promise.race([
           Promise.all([statsPromise, tablePromise]),
           timeoutPromise
         ]);

         this.processStatsData(statsResponse);
         await this.processTableData(tableResponse);

       } catch (error) {
         if (error.message === '请求超时') {
           this.$message.error('请求超时，请尝试缩小查询范围');
         } else {
           console.error('加载消费数据失败:', error);
           this.$message.error('加载数据失败，请重试');
         }
       }
     },


    buildRequestParams() {
      const params = {};

      const normalizeGrade = (val) => {
        if (!val) return ''
        // 后端年级存储多为数字年份，去掉“级”后缀
        return String(val).replace(/级$/, '')
      }

      // 映射参数名以匹配后端接口（根据后端API文档，参数名应该是小驼峰格式）
      if (this.queryForm.college) params.college = String(this.queryForm.college).trim();
      if (this.queryForm.major) params.major = String(this.queryForm.major).trim();
      if (this.queryForm.grade) params.grade = normalizeGrade(this.queryForm.grade);
      if (this.queryForm.class) params.className = String(this.queryForm.class).trim();
      if (this.queryForm.studentId) params.studentId = String(this.queryForm.studentId).trim();
      if (this.queryForm.startDate) params.timeBegin = String(this.queryForm.startDate);
      if (this.queryForm.endDate) params.timeEnd = String(this.queryForm.endDate);

      // 分页参数（根据后端API文档，参数名应该是小驼峰格式）
      params.page = String(this.currentPage);
      params.pageSize = String(this.pageSize);

      return params;
    },

    processStatsData(response) {
      const data = response || {};
      this.totalAmount = data.totalAmount || 0;
      this.totalRecords = data.totalRecords || 0;
      this.avgDaily = data.averageConsumption || 0;
      this.studentCount = data.totalStudents || 0;
    },

    async processTableData(response) {
      const data = response?.records ? response : response?.data;
      const rawRecords = data?.records || data?.data || data || [];
      const records = Array.isArray(rawRecords) ? rawRecords : [];

      // 先做基础映射
      const mapped = records.map((item, idx) => {
        const studentId = item.studentId || item.uid || item.student_id || '';
        const timeVal = item.consumptionTime || item.consume_time || item.consumption_time || '';
        const windowVal = item.window || item.windowId || item.window_id || '-';
        const amountVal = item.amount || 0;

        return {
          key: `${studentId || idx}-${idx}`,
          uid: studentId || '-',
          name: item.name || item.studentName || item.student_name || '-',
          college: item.college || '-',
          major: item.major || '-',
          consume_time: typeof timeVal === 'string' ? timeVal.replace('T', ' ') : timeVal,
          amount: Number(amountVal).toFixed ? Number(amountVal).toFixed(2) : amountVal,
          window: windowVal
        };
      });

      // 补充学生基础信息（姓名/学院/专业）
      await this.enrichStudentInfo(mapped);

      this.tableData = mapped.map(row => {
        const cached = this.studentInfoCache.get(row.uid) || {};
        return {
          ...row,
          name: row.name !== '-' ? row.name : (cached.name || '-'),
          college: row.college !== '-' ? row.college : (cached.college || '-'),
          major: row.major !== '-' ? row.major : (cached.major || '-'),
        };
      });

      this.total = data?.total || data?.totalCount || this.tableData.length || 0;
    },

    async enrichStudentInfo(rows) {
      const ids = Array.from(new Set(rows.map(r => r.uid).filter(Boolean)));
      const missing = ids.filter(id => !this.studentInfoCache.has(id));
      if (!missing.length) return;

      const results = await Promise.all(missing.map(id => getStudentInfo({ studentId: id }).catch(() => null)));
      results.forEach((res, idx) => {
        const id = missing[idx];
        const data = Array.isArray(res?.records)
          ? res.records[0]
          : Array.isArray(res?.data?.records)
            ? res.data.records[0]
            : Array.isArray(res?.data)
              ? res.data[0]
              : Array.isArray(res)
                ? res[0]
                : null;
        if (data) {
          this.studentInfoCache.set(id, {
            name: data.name || data.studentName || data.student_name,
            college: data.college,
            major: data.major
          });
        } else {
          this.studentInfoCache.set(id, { name: '-', college: '-', major: '-' });
        }
      });
    }
  }
};
</script>

<style scoped>
.consumption-query {
  padding: 20px;
}

.stat-item {
  text-align: center;
  padding: 10px 0;
}

.stat-value {
  font-size: 20px;
  font-weight: bold;
  color: #409EFF;
  margin-bottom: 5px;
}

.stat-label {
  font-size: 12px;
  color: #909399;
}
</style>

