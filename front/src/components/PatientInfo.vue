<template>
  <div class="patient-info-container" v-loading="analysisLoading" element-loading-text="正在为您生成AI辅助诊断报告...">
    <div v-if="patientInfo" class="patient-details-card">
       <el-descriptions :title="`病人档案: ${patientInfo.name}`" :column="3" border>
        <el-descriptions-item label="姓名">{{ patientInfo.name }}</el-descriptions-item>
        <el-descriptions-item label="性别">{{ patientInfo.gender }}</el-descriptions-item>
        <el-descriptions-item label="出生日期">{{ patientInfo.birthday || '未提供' }}</el-descriptions-item>
      </el-descriptions>
    </div>

    <div class="header-bar">
      <h2>病历与AI诊断记录</h2>
      <el-button 
        type="primary" 
        @click="handleStartAnalysis" 
        :icon="MagicStick"
        :loading="analysisLoading"
      >
        发起新的AI辅助诊断
      </el-button>
    </div>

    <el-row :gutter="20">
      <!-- 病历列表 -->
      <el-col :span="12">
        <el-card class="box-card">
          <template #header>
            <div class="card-header">
              <span>病历列表</span>
            </div>
          </template>
          <div v-loading="casesLoading">
            <el-table :data="cases" stripe style="width: 100%" height="400">
              <el-table-column prop="case_date" label="就诊日期" width="120" />
              <el-table-column prop="doctor_name" label="主治医师" width="100" />
              <el-table-column prop="office_name" label="就诊科室" width="120" />
              <el-table-column prop="diagnosis" label="诊断结果" show-overflow-tooltip />
              <el-table-column label="操作" width="90" fixed="right">
                <template #default="scope">
                  <el-button link type="primary" size="small" @click="showCasePreview(scope.row.id)">
                    查看详情
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
            <el-pagination
              background
              layout="prev, pager, next"
              :total="casesPagination.total_items"
              :current-page="casesPagination.page"
              :page-size="casesPagination.per_page"
              @current-change="handleCasePageChange"
              class="pagination-bar"
            />
          </div>
        </el-card>
      </el-col>

      <!-- AI辅诊记录 -->
      <el-col :span="12">
        <el-card class="box-card">
          <template #header>
            <div class="card-header">
              <span>AI智能辅诊记录</span>
            </div>
          </template>
          <div v-loading="advicesLoading" class="advice-list-container">
            <el-scrollbar height="400px">
              <div v-if="advices.length === 0" class="empty-state">暂无记录</div>
              <div v-for="advice in advices" :key="advice.id" class="advice-item">
                <div class="advice-header">
                  <span>由 <strong>{{ advice.creator_name }}</strong> 于 {{ advice.created_at }} 创建</span>
                  <el-button link type="primary" @click="showAdvicePreview(advice)">查看详情</el-button>
                </div>
              </div>
            </el-scrollbar>
            <el-pagination
              background
              layout="prev, pager, next"
              :total="advicesPagination.total_items"
              :current-page="advicesPagination.page"
              :page-size="advicesPagination.per_page"
              @current-change="handleAdvicePageChange"
              class="pagination-bar"
            />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 弹窗区域 -->
    <el-dialog v-model="casePreviewVisible" title="病历详情" width="60%" top="5vh" destroy-on-close>
      <CasePreview 
        v-if="casePreviewVisible" 
        :case-id="selectedCaseId"
        @view-patient="handleViewPatientFromPreview"
      />
    </el-dialog>

    <el-dialog v-model="imagePreviewVisible" title="影像预览与标注" width="85%" top="5vh" destroy-on-close>
      <ImagePreview v-if="imagePreviewVisible" :image-id="selectedImageId" />
    </el-dialog>

    <el-dialog v-model="advicePreviewVisible" title="AI辅诊报告详情" width="70%" top="5vh">
       <div v-if="selectedAdvice" class="advice-content">
        <el-tabs>
          <el-tab-pane label="疾病分析">
            <div class="content-panel">
              <template v-for="(part, index) in parsedDiseaseContent" :key="index">
                <span v-if="part.type === 'text'">{{ part.content }}</span>
                <el-button v-else-if="part.type === 'case'" link type="primary" @click="showCasePreview(part.id)">{{ part.text }}</el-button>
                <el-button v-else-if="part.type === 'image'" link type="success" @click="showImagePreview(part.id)">{{ part.text }}</el-button>
              </template>
            </div>
          </el-tab-pane>
          <el-tab-pane label="治疗建议">
            <div class="content-panel">
              <template v-for="(part, index) in parsedTherapyContent" :key="index">
                <span v-if="part.type === 'text'">{{ part.content }}</span>
                <el-button v-else-if="part.type === 'case'" link type="primary" @click="showCasePreview(part.id)">{{ part.text }}</el-button>
                <el-button v-else-if="part.type === 'image'" link type="success" @click="showImagePreview(part.id)">{{ part.text }}</el-button>
              </template>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </el-dialog>

  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue';
import { getPatientCases, getPatientAnalyses, startPatientAnalysis, getPatientDetail } from '@/api/patient';
import CasePreview from './CasePreview.vue';
import ImagePreview from './ImagePreview.vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { MagicStick } from '@element-plus/icons-vue';

const props = defineProps({
  patientId: {
    type: [Number, String],
    required: true,
    default: 1
  }
});

// State for data and loading
const patientInfo = ref(null);
const patientInfoLoading = ref(false);

const cases = ref([]);
const casesPagination = ref({ page: 1, per_page: 10, total_items: 0 });
const casesLoading = ref(false);

const advices = ref([]);
const advicesPagination = ref({ page: 1, per_page: 10, total_items: 0 });
const advicesLoading = ref(false);
const analysisLoading = ref(false);

// State for dialogs
const selectedCaseId = ref(null);
const casePreviewVisible = ref(false);

const selectedImageId = ref(null);
const imagePreviewVisible = ref(false);

const selectedAdvice = ref(null);
const advicePreviewVisible = ref(false);

// --- Data Fetching ---
const fetchPatientDetail = async () => {
  if (!props.patientId) return;
  patientInfoLoading.value = true;
  try {
    const res = await getPatientDetail(props.patientId);
    if (res.code === 200) {
      patientInfo.value = res.data;
    } else {
      ElMessage.error(res.message || '获取病人信息失败');
    }
  } catch (error) {
    console.error(error);
    ElMessage.error('网络错误，无法加载病人信息');
  } finally {
    patientInfoLoading.value = false;
  }
};

const fetchCases = async (page = 1) => {
  if (!props.patientId) return;
  casesLoading.value = true;
  try {
    const res = await getPatientCases({ patient_id: props.patientId, page });
    if (res.code === 200) {
      cases.value = res.data;
      casesPagination.value = res.pagination;
    } else {
      ElMessage.error(res.message || '获取病历列表失败');
    }
  } catch (error) {
    console.error(error);
    ElMessage.error('网络错误，无法加载病历列表');
  } finally {
    casesLoading.value = false;
  }
};

const fetchAdvices = async (page = 1) => {
  if (!props.patientId) return;
  advicesLoading.value = true;
  try {
    const res = await getPatientAnalyses({ patient_id: props.patientId, page });
    if (res.code === 200) {
      advices.value = res.data;
      advicesPagination.value = res.pagination;
    } else {
      ElMessage.error(res.message || '获取AI辅诊记录失败');
    }
  } catch (error) {
    console.error(error);
    ElMessage.error('网络错误，无法加载AI辅诊记录');
  } finally {
    advicesLoading.value = false;
  }
};

// --- Event Handlers ---
const handleCasePageChange = (newPage) => {
  fetchCases(newPage);
};

const handleAdvicePageChange = (newPage) => {
  fetchAdvices(newPage);
};

const handleStartAnalysis = async () => {
  try {
    await ElMessageBox.confirm('将基于该病人的全部现有病历和影像生成一份新的诊断建议。是否继续？', '发起AI辅助诊断', {
      confirmButtonText: '继续',
      cancelButtonText: '取消',
      type: 'info',
    });

    analysisLoading.value = true;
    const res = await startPatientAnalysis(props.patientId);
    if (res.code === 201) {
      ElMessage.success('AI辅助诊断已成功发起并生成记录！');
      fetchAdvices(1); // Refresh the list
    } else {
      ElMessage.error(res.message || '发起AI诊断失败');
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error(error);
      ElMessage.error('操作失败');
    } else {
      ElMessage.info('已取消操作');
    }
  } finally {
    analysisLoading.value = false;
  }
};

// --- Dialog Triggers ---
const showCasePreview = (id) => {
  selectedCaseId.value = id;
  casePreviewVisible.value = true;
};

const showImagePreview = (id) => {
  selectedImageId.value = id;
  imagePreviewVisible.value = true;
};

const showAdvicePreview = (advice) => {
  selectedAdvice.value = advice;
  advicePreviewVisible.value = true;
};

const handleViewPatientFromPreview = () => {
  // User is already on the patient info page, just close the case preview.
  casePreviewVisible.value = false;
  ElMessage.info('已返回病人综合信息');
}

// --- Content Parsing ---
const parseContent = (text) => {
  if (!text) return [{ type: 'text', content: '无内容' }];
  
  const regex = /\[([^\]]+)\]\((case|image),(\d+)\)/g;
  const parts = [];
  let lastIndex = 0;
  let match;

  while ((match = regex.exec(text)) !== null) {
    // Add text before the link
    if (match.index > lastIndex) {
      parts.push({ type: 'text', content: text.substring(lastIndex, match.index) });
    }
    // Add the link part
    parts.push({
      type: match[2], // 'case' or 'image'
      text: match[1],
      id: parseInt(match[3], 10)
    });
    lastIndex = match.index + match[0].length;
  }

  // Add any remaining text after the last link
  if (lastIndex < text.length) {
    parts.push({ type: 'text', content: text.substring(lastIndex) });
  }

  return parts;
};

const parsedDiseaseContent = computed(() => {
  return selectedAdvice.value ? parseContent(selectedAdvice.value.disease) : [];
});

const parsedTherapyContent = computed(() => {
  return selectedAdvice.value ? parseContent(selectedAdvice.value.therapy) : [];
});


// --- Watcher ---
watch(() => props.patientId, (newId) => {
  if (newId) {
    fetchPatientDetail();
    fetchCases(1);
    fetchAdvices(1);
  } else {
    patientInfo.value = null;
    cases.value = [];
    advices.value = [];
  }
}, { immediate: true });

</script>

<style scoped>
.patient-info-container {
  padding: 20px;
}
.patient-details-card {
  margin-bottom: 20px;
  background: #fff;
  padding: 16px;
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}
.header-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.card-header {
  font-weight: bold;
}
.pagination-bar {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
.advice-list-container {
  height: 448px; /* table height + pagination height */
  display: flex;
  flex-direction: column;
}
.advice-item {
  padding: 10px 15px;
  border-bottom: 1px solid #ebeef5;
}
.advice-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.advice-header span {
  font-size: 14px;
  color: #606266;
}
.advice-item:last-child {
  border-bottom: none;
}
.empty-state {
  color: #909399;
  text-align: center;
  padding-top: 100px;
}
.advice-content {
  line-height: 1.8;
}
.content-panel {
  background-color: #f9fafb;
  padding: 15px;
  border-radius: 4px;
  min-height: 200px;
  white-space: pre-wrap;
}
</style>
