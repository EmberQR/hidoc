<template>
  <div class="home-container">
    <div class="welcome-banner">
      <div class="banner-content">
        <h1 class="welcome-title">欢迎使用 HiDoc 智能影像辅诊系统</h1>
        <p class="welcome-subtitle">AI集成的高效智能诊断辅助工具，为您的诊断提供专业支持</p>
      </div>
    </div>
    
    <div class="dashboard-container">
      <el-row :gutter="20">
        <!-- 病历总数 -->
        <el-col :xs="24" :sm="12" :md="6">
          <el-card shadow="hover" class="dashboard-card">
            <template #header>
              <div class="card-header">
                <span>病历总数</span>
                <el-button class="card-button" text @click="$router.push('/case')">查看详情</el-button>
              </div>
            </template>
            <div class="card-content">
              <div class="statistics-value">{{ dashboardData.total_cases }}</div>
              <div class="statistics-label">今日 <span class="statistics-change increase">{{ dashboardData.today_cases > 0 ? '+' : '' }}{{ dashboardData.today_cases }}</span></div>
            </div>
          </el-card>
        </el-col>
        <!-- 共接待病人 -->
        <el-col :xs="24" :sm="12" :md="6">
          <el-card shadow="hover" class="dashboard-card">
            <template #header>
              <div class="card-header">
                <span>共接待病人</span>
                <el-button class="card-button" text @click="$router.push('/patient')">查看详情</el-button>
              </div>
            </template>
            <div class="card-content">
              <div class="statistics-value">{{ dashboardData.total_patients }}<span class="unit">人</span></div>
              <div class="statistics-label">&nbsp;</div>
            </div>
          </el-card>
        </el-col>
        <!-- 调用AI影像分割 -->
        <el-col :xs="24" :sm="12" :md="6">
          <el-card shadow="hover" class="dashboard-card">
            <template #header>
              <div class="card-header">
                <span>AI影像分割</span>
                <el-button class="card-button" text @click="$router.push('/image')">查看详情</el-button>
              </div>
            </template>
            <div class="card-content">
              <div class="statistics-value">{{ dashboardData.ai_seg }}<span class="unit">次</span></div>
              <div class="statistics-label">今日 <span class="statistics-change increase">{{ dashboardData.today_ai_seg > 0 ? '+' : '' }}{{ dashboardData.today_ai_seg }}</span></div>
            </div>
          </el-card>
        </el-col>
        <!-- 获取AI辅诊建议 -->
        <el-col :xs="24" :sm="12" :md="6">
          <el-card shadow="hover" class="dashboard-card">
            <template #header>
              <div class="card-header">
                <span>AI辅诊建议</span>
                <el-button class="card-button" text @click="$router.push('/patient')">查看详情</el-button>
              </div>
            </template>
            <div class="card-content">
              <div class="statistics-value">{{ dashboardData.ai_advice }}<span class="unit">次</span></div>
              <div class="statistics-label">今日 <span class="statistics-change increase">{{ dashboardData.today_ai_advice > 0 ? '+' : '' }}{{ dashboardData.today_ai_advice }}</span></div>
            </div>
          </el-card>
        </el-col>
      </el-row>
      
      <el-row :gutter="20" class="mt-20">
        <el-col :span="24">
          <el-card shadow="hover" class="chart-card">
            <template #header>
              <div class="card-header">
                <span>近7天我的病历数</span>
              </div>
            </template>
            <div class="chart-container" ref="chartContainer">
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive, nextTick } from 'vue';
import { useRouter } from 'vue-router';
// 按需引入 ECharts
import * as echarts from 'echarts/core';
import { TooltipComponent, GridComponent, AxisPointerComponent } from 'echarts/components';
import { LineChart } from 'echarts/charts';
import { CanvasRenderer } from 'echarts/renderers';
import { getHomeData } from '@/api/home';
import { ElMessage } from 'element-plus';

// 注册 ECharts 组件
echarts.use([
  TooltipComponent,
  GridComponent,
  AxisPointerComponent,
  LineChart,
  CanvasRenderer
]);

const router = useRouter();
const chartContainer = ref(null);
let myChart = null;

const dashboardData = reactive({
  total_cases: 0,
  today_cases: 0,
  total_patients: 0,
  ai_seg: 0,
  today_ai_seg: 0,
  ai_advice: 0,
  today_ai_advice: 0,
  recent_cases: []
});

const fetchData = async () => {
  const hospitalInfo = localStorage.getItem('currentHospital');
  if (!hospitalInfo) {
    ElMessage.error('无法获取当前医院信息，请重新选择医院');
    return;
  }
  
  try {
    const hospital = JSON.parse(hospitalInfo);
    const response = await getHomeData(hospital.id);
    if (response.code === 200) {
      Object.assign(dashboardData, response.data);
      nextTick(() => {
        initChart();
      });
    } else {
      ElMessage.error(response.message || '获取首页数据失败');
    }
  } catch (error) {
    console.error("获取首页数据或解析医院信息失败:", error);
    ElMessage.error('加载数据时出错，请稍后再试');
  }
};

const initChart = () => {
  if (chartContainer.value) {
    // 销毁之前的实例，防止热更新或重复渲染时出错
    if (myChart) {
      myChart.dispose();
    }
    myChart = echarts.init(chartContainer.value);
    const options = {
      tooltip: {
        trigger: 'axis'
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: dashboardData.recent_cases.map(item => item.日期)
      },
      yAxis: {
        type: 'value'
      },
      series: [
        {
          name: '病历数',
          type: 'line',
          stack: '总量',
          areaStyle: {},
          emphasis: {
            focus: 'series'
          },
          data: dashboardData.recent_cases.map(item => item.数量),
          smooth: true,
          itemStyle: {
            color: '#409EFF'
          },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(64, 158, 255, 0.5)' },
              { offset: 1, color: 'rgba(64, 158, 255, 0.1)' }
            ])
          }
        }
      ]
    };
    myChart.setOption(options);
  }
};

onMounted(() => {
  fetchData();
  window.addEventListener('resize', () => {
    if (myChart) {
      myChart.resize();
    }
  });
});

</script>

<style scoped>
.home-container {
  min-height: 100%;
}

.welcome-banner {
  background: linear-gradient(135deg, #409eff, #36cfc9);
  border-radius: 12px;
  padding: 30px;
  margin-bottom: 20px;
  color: white;
  position: relative;
  overflow: hidden;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}

.welcome-banner::before {
  content: '';
  position: absolute;
  top: -50%;
  right: -50%;
  width: 100%;
  height: 200%;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.1) 0%, transparent 70%);
  transform: rotate(30deg);
}

.banner-content {
  position: relative;
  z-index: 1;
}

.welcome-title {
  font-size: 28px;
  margin: 0 0 10px 0;
  font-weight: 600;
}

.welcome-subtitle {
  font-size: 16px;
  font-weight: 300;
  margin: 0;
  opacity: 0.9;
}

.dashboard-container {
  margin-top: 20px;
}

.dashboard-card {
  margin-bottom: 20px;
  transition: transform 0.3s, box-shadow 0.3s;
}

.dashboard-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 16px;
  font-weight: 500;
}

.card-content {
  text-align: center;
  padding: 10px 0;
}

.statistics-value {
  font-size: 36px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 5px;
}

.unit {
  font-size: 16px;
  margin-left: 5px;
}

.statistics-label {
  font-size: 14px;
  color: #909399;
  height: 16px; /* 保证高度一致 */
}

.statistics-change {
  font-weight: 500;
}

.increase {
  color: #67c23a;
}

.decrease {
  color: #f56c6c;
}

.chart-card {
  height: 400px; /* 增加高度以容纳图表 */
  margin-bottom: 20px;
}

.chart-container {
  height: 320px; /* 设置一个明确的高度，避免因父容器高度计算延迟导致初始化失败 */
  width: 100%;
}

.mt-20 {
  margin-top: 5px;
}

@media (max-width: 768px) {
  .welcome-title {
    font-size: 24px;
  }
  
  .welcome-subtitle {
    font-size: 14px;
  }
  
  .chart-card {
    height: 300px;
  }
}
</style>
