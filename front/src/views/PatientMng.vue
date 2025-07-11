<template>
  <div class="patient-mng-container">
    <div class="page-header">
      <h2 class="page-title">病人管理</h2>
      <p class="page-description">我负责过的所有病人的病历记录、影像记录、AI诊断记录等。</p>
    </div>

    <el-table :data="patientList" v-loading="loading" style="width: 100%" stripe>
      <!-- <el-table-column prop="id" label="ID" width="80" /> -->
      <el-table-column prop="name" label="姓名" width="150" />
      <el-table-column prop="gender" label="性别" width="100" />
      <el-table-column prop="birthday" label="出生日期" width="180" />
      <el-table-column prop="created_at" label="初次建档时间" sortable />
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="scope">
          <el-button size="small" type="primary" @click="handleViewDetails(scope.row)">
            查看详情
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination-container">
      <el-pagination
        v-if="pagination.total_items > 0"
        background
        layout="prev, pager, next, jumper, ->, total"
        :total="pagination.total_items"
        :current-page="pagination.page"
        :page-size="pagination.per_page"
        @current-change="handlePageChange"
      />
    </div>

    <!-- 病人详情 Dialog -->
    <el-dialog 
      v-model="detailsDialogVisible" 
      title="病人综合信息" 
      width="90%" 
      top="5vh" 
      destroy-on-close
    >
      <PatientInfo v-if="detailsDialogVisible && selectedPatientId" :patient-id="selectedPatientId" />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue';
import { getPatientList } from '@/api/patient';
import PatientInfo from '@/components/PatientInfo.vue';
import { ElMessage } from 'element-plus';

const patientList = ref([]);
const loading = ref(false);

const pagination = ref({
  page: 1,
  per_page: 10,
  total_items: 0,
});

const detailsDialogVisible = ref(false);
const selectedPatientId = ref(null);

const fetchPatients = async (page = 1) => {
  loading.value = true;
  try {
    const res = await getPatientList({ page, per_page: pagination.value.per_page });
    if (res.code === 200) {
      patientList.value = res.data;
      pagination.value = res.pagination;
    } else {
      ElMessage.error(res.message || '获取病人列表失败');
    }
  } catch (err) {
    ElMessage.error('网络错误，无法获取病人列表');
    console.error(err);
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  fetchPatients();
});

const handlePageChange = (newPage) => {
  fetchPatients(newPage);
};

const handleViewDetails = (row) => {
  selectedPatientId.value = row.id;
  detailsDialogVisible.value = true;
};
</script>

<style scoped>
.patient-mng-container {
  padding: 20px;
}
.page-header {
  margin-bottom: 20px;
}
.page-title {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 8px 0;
}
.page-description {
  font-size: 14px;
  color: #909399;
  margin: 0;
}
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.header h2 {
  margin: 0;
  color: #303133;
}
.el-table {
  border-radius: 4px;
}
.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}
</style>
