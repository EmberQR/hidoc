<template>
  <div class="home-container">
    <div class="welcome-banner">
      <div class="banner-content">
        <h1 class="welcome-title">欢迎使用 HiDoc 智能预诊系统</h1>
        <p class="welcome-subtitle">高效智能的诊断辅助工具，为您的诊断提供专业支持</p>
      </div>
    </div>
    
    <div class="dashboard-container">
      <el-row :gutter="20">
        <el-col :xs="24" :sm="12" :md="6">
          <el-card shadow="hover" class="dashboard-card">
            <template #header>
              <div class="card-header">
                <span>今日预诊</span>
                <el-button class="card-button" text>查看详情</el-button>
              </div>
            </template>
            <div class="card-content">
              <div class="statistics-value">8</div>
              <div class="statistics-label">较昨日 <span class="statistics-change increase">+2</span></div>
            </div>
          </el-card>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <el-card shadow="hover" class="dashboard-card">
            <template #header>
              <div class="card-header">
                <span>患者总数</span>
                <el-button class="card-button" text>查看详情</el-button>
              </div>
            </template>
            <div class="card-content">
              <div class="statistics-value">127</div>
              <div class="statistics-label">本周新增 <span class="statistics-change increase">+14</span></div>
            </div>
          </el-card>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <el-card shadow="hover" class="dashboard-card">
            <template #header>
              <div class="card-header">
                <span>诊断准确率</span>
                <el-button class="card-button" text>查看详情</el-button>
              </div>
            </template>
            <div class="card-content">
              <div class="statistics-value">92.5%</div>
              <div class="statistics-label">较上月 <span class="statistics-change increase">+1.2%</span></div>
            </div>
          </el-card>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <el-card shadow="hover" class="dashboard-card">
            <template #header>
              <div class="card-header">
                <span>平均诊断时间</span>
                <el-button class="card-button" text>查看详情</el-button>
              </div>
            </template>
            <div class="card-content">
              <div class="statistics-value">3.5<span class="unit">分钟</span></div>
              <div class="statistics-label">较上月 <span class="statistics-change decrease">-0.8分钟</span></div>
            </div>
          </el-card>
        </el-col>
      </el-row>
      
      <el-row :gutter="20" class="mt-20">
        <el-col :xs="24" :md="16">
          <el-card shadow="hover" class="chart-card">
            <template #header>
              <div class="card-header">
                <span>近7天诊断趋势</span>
                <el-radio-group v-model="timeRange" size="small">
                  <el-radio-button label="week">近7天</el-radio-button>
                  <el-radio-button label="month">近30天</el-radio-button>
                </el-radio-group>
              </div>
            </template>
            <div class="chart-container">
              <div class="chart-placeholder">
                [此处将显示趋势图表]
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :xs="24" :md="8">
          <el-card shadow="hover" class="quick-actions">
            <template #header>
              <div class="card-header">
                <span>快捷操作</span>
              </div>
            </template>
            <div class="action-list">
              <el-button type="primary" class="action-button" @click="$router.push('/diagnosis/new')">
                <el-icon><Plus /></el-icon>新建诊断
              </el-button>
              <el-button type="success" class="action-button" @click="$router.push('/patients/add')">
                <el-icon><Plus /></el-icon>添加患者
              </el-button>
              <el-button type="info" class="action-button" @click="$router.push('/knowledge')">
                <el-icon><Reading /></el-icon>浏览知识库
              </el-button>
              <el-button type="warning" class="action-button" @click="$router.push('/statistics')">
                <el-icon><TrendCharts /></el-icon>查看统计数据
              </el-button>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import { Plus, Reading, TrendCharts } from '@element-plus/icons-vue'

export default {
  name: 'HomeView',
  components: {
    Plus,
    Reading,
    TrendCharts
  },
  setup() {
    const timeRange = ref('week')
    
    return {
      timeRange
    }
  }
}
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
  height: 350px;
  margin-bottom: 20px;
}

.chart-container {
  height: 280px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chart-placeholder {
  color: #909399;
  font-size: 16px;
  text-align: center;
}

.quick-actions {
  height: 350px;
  margin-bottom: 20px;
}

.action-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
  padding: 10px 0;
}

.action-button {
  width: 100%;
  height: 50px;
  font-size: 16px;
}

.mt-20 {
  margin-top: 20px;
}

@media (max-width: 768px) {
  .welcome-title {
    font-size: 24px;
  }
  
  .welcome-subtitle {
    font-size: 14px;
  }
  
  .chart-card, .quick-actions {
    height: auto;
  }
  
  .chart-container {
    height: 200px;
  }
}
</style>
