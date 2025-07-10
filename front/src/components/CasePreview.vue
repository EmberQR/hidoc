<template>
  <div class="case-preview-container" v-loading="loading">
    <el-alert v-if="error" :title="error" type="error" show-icon :closable="false" />

    <div v-if="caseData" class="content">
      <el-descriptions :column="2" border>
        <template #title>
          <div class="descriptions-title">
            <span>{{ `${caseData.patient_name}的病历` }}</span>
            <el-button type="primary" size="small" @click="handleViewPatientInfo">查看病人信息</el-button>
          </div>
        </template>
        <el-descriptions-item label="就诊日期">{{ caseData.case_date }}</el-descriptions-item>
        <el-descriptions-item label="主治医师">{{ caseData.doctor_name }}</el-descriptions-item>
        <el-descriptions-item label="就诊科室">{{ caseData.office_name }}</el-descriptions-item>
        <el-descriptions-item label="更新时间">{{ caseData.updated_at }}</el-descriptions-item>
        
        <el-descriptions-item label="主诉" :span="2">{{ caseData.chief_complaint }}</el-descriptions-item>
        <el-descriptions-item label="诊断结果" :span="2">{{ caseData.diagnosis }}</el-descriptions-item>
        <el-descriptions-item label="治疗方案" :span="2">{{ caseData.treatment_plan }}</el-descriptions-item>
        <el-descriptions-item label="用药详情" :span="2">{{ caseData.medication_details }}</el-descriptions-item>

        <el-descriptions-item label="现病史" :span="2">{{ caseData.present_illness_history }}</el-descriptions-item>
        <el-descriptions-item label="既往史" :span="2">{{ caseData.past_medical_history }}</el-descriptions-item>
        <el-descriptions-item label="个人史" :span="2">{{ caseData.personal_history }}</el-descriptions-item>
        <el-descriptions-item label="家族史" :span="2">{{ caseData.family_history }}</el-descriptions-item>
        <el-descriptions-item label="体格检查" :span="2">{{ caseData.physical_examination }}</el-descriptions-item>

        <el-descriptions-item label="备注" :span="2">{{ caseData.notes }}</el-descriptions-item>
      </el-descriptions>

      <div class="image-gallery">
        <h3>相关影像 ({{ caseData.images.length }})</h3>
        <el-scrollbar>
          <div class="image-list">
            <div v-for="image in caseData.images" :key="image.image_id" class="image-card" @click="handleImagePreview(image)">
              <el-image :src="image.preview_url" fit="cover" class="thumbnail" />
              <div class="image-name">{{ image.name }}</div>
            </div>
            <div v-if="caseData.images.length === 0" class="no-images">
              暂无影像记录
            </div>
          </div>
        </el-scrollbar>
      </div>
    </div>

    <!-- 影像预览 Dialog -->
    <el-dialog v-model="previewDialogVisible" title="影像预览与标注" width="85%" top="5vh" destroy-on-close>
      <ImagePreview v-if="previewDialogVisible && currentImageId" :image-id="currentImageId" />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, defineProps, defineEmits } from 'vue';
import { getCaseById } from '@/api/hospital';
import ImagePreview from '@/components/ImagePreview.vue';
import { ElMessage } from 'element-plus';

const props = defineProps({
  caseId: {
    type: [Number, String],
    required: true,
  }
});

const emit = defineEmits(['view-patient']);

const loading = ref(false);
const error = ref(null);
const caseData = ref(null);

const previewDialogVisible = ref(false);
const currentImageId = ref(null);

const fetchCaseDetails = async (id) => {
  if (!id) return;
  loading.value = true;
  error.value = null;
  caseData.value = null;
  try {
    const res = await getCaseById(id);
    if (res.code === 200) {
      caseData.value = res.data;
    } else {
      throw new Error(res.message || '获取病历信息失败');
    }
  } catch (err) {
    error.value = err.message || '网络错误，无法加载病历详情';
    ElMessage.error(error.value);
    console.error(err);
  } finally {
    loading.value = false;
  }
};

const handleImagePreview = (image) => {
  currentImageId.value = image.image_id;
  previewDialogVisible.value = true;
};

const handleViewPatientInfo = () => {
  if (caseData.value) {
    emit('view-patient', caseData.value.patient_id);
  }
};

watch(() => props.caseId, (newId) => {
  fetchCaseDetails(newId);
}, { immediate: true });

onMounted(() => {
  if (!props.caseId) {
    loading.value = false;
    error.value = "未提供病历ID";
  }
});
</script>

<style scoped>
.case-preview-container {
  padding: 20px;
  background-color: #f9fafb;
}

.content {
  background-color: #fff;
  padding: 24px;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0,0,0,0.1);
}

.descriptions-title {
  display: flex;
  align-items: center;
  gap: 16px;
}

.el-descriptions {
  margin-bottom: 24px;
}

.image-gallery h3 {
  margin-top: 0;
  margin-bottom: 16px;
  font-size: 18px;
  color: #303133;
}

.image-list {
  display: flex;
  gap: 16px;
  padding-bottom: 10px; /* For scrollbar */
}

.image-card {
  flex-shrink: 0;
  width: 150px;
  height: 150px;
  border-radius: 8px;
  overflow: hidden;
  position: relative;
  cursor: pointer;
  box-shadow: 0 2px 4px rgba(0,0,0,0.08);
  transition: transform 0.3s, box-shadow 0.3s;
}

.image-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.12);
}

.thumbnail {
  width: 100%;
  height: 100%;
}

.image-name {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background-color: rgba(0, 0, 0, 0.5);
  color: white;
  padding: 8px;
  font-size: 12px;
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.no-images {
  color: #909399;
  font-size: 14px;
  text-align: center;
  width: 100%;
  padding: 20px;
}
</style>
