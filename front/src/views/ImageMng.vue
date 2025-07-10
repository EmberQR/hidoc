<template>
  <div class="image-mng-container">
    <div class="header">
      <h2>我的影像</h2>
      <el-button type="primary" :icon="Plus" @click="handleAdd">上传影像</el-button>
    </div>

    <el-table :data="imageList" v-loading="loading" style="width: 100%" stripe>
      <el-table-column label="预览图" width="120">
        <template #default="scope">
          <el-image
            style="width: 100px; height: 100px; border-radius: 4px;"
            :src="scope.row.preview_url"
            :preview-src-list="[scope.row.preview_url]"
            fit="cover"
            hide-on-click-modal
          />
        </template>
      </el-table-column>
      <el-table-column prop="name" label="名称" width="180" />
      <el-table-column prop="type" label="类型" width="100" />
      <el-table-column prop="format" label="格式" width="100" />
      <el-table-column prop="dim" label="维度" width="80" />
      <el-table-column prop="note" label="备注" show-overflow-tooltip />
      <el-table-column prop="created_at" label="上传时间" width="180" sortable />
      <el-table-column label="操作" width="360" fixed="right">
        <template #default="scope">
          <el-button v-if="scope.row.case_id" size="small" type="primary" @click="handleViewCase(scope.row)">查看关联病历</el-button>
          <el-button size="small" type="success" @click="handlePreview(scope.row)">预览/标注</el-button>
          <el-button size="small" @click="handleEdit(scope.row)">编辑备注</el-button>
          <el-button size="small" type="danger" @click="handleDelete(scope.row)">删除</el-button>
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

    <!-- 预览/标注 Dialog -->
    <el-dialog v-model="previewDialogVisible" title="影像预览与标注" width="85%" top="5vh" destroy-on-close>
      <ImagePreview v-if="previewDialogVisible && currentImage" :image-id="currentImage.id" />
    </el-dialog>

    <!-- 关联病历详情 Dialog -->
    <el-dialog v-model="casePreviewDialogVisible" title="关联病历详情" width="85%" top="5vh" destroy-on-close>
      <CasePreview 
        v-if="casePreviewDialogVisible && selectedCaseId" 
        :case-id="selectedCaseId"
        @view-patient="handleViewPatientFromPreview"
      />
    </el-dialog>

    <!-- 病人信息 Dialog -->
    <el-dialog v-model="patientInfoDialogVisible" title="病人综合信息" width="90%" top="5vh" destroy-on-close>
      <PatientInfo v-if="patientInfoDialogVisible && selectedPatientId" :patient-id="selectedPatientId" />
    </el-dialog>

    <!-- 编辑备注 Dialog -->
    <el-dialog v-model="editDialogVisible" title="编辑影像备注" width="30%">
      <el-form :model="editForm">
        <el-form-item label="备注">
          <el-input v-model="editForm.note" type="textarea" :rows="4" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitEdit">确定</el-button>
      </template>
    </el-dialog>

    <!-- 上传影像 Dialog -->
    <el-dialog v-model="addDialogVisible" title="上传新影像" width="40%" @close="resetAddForm">
      <el-form :model="addForm" :rules="addFormRules" ref="addFormRef" label-width="80px">
        <el-form-item label="影像名称" prop="name">
          <el-input v-model="addForm.name" placeholder="请输入影像名称"></el-input>
        </el-form-item>
        <el-form-item label="影像类型" prop="type">
           <el-select v-model="addForm.type" placeholder="请选择影像类型">
            <el-option label="X-ray" value="X-ray" />
            <el-option label="CT" value="CT" />
            <el-option label="MRI" value="MRI" />
            <el-option label="PET" value="PET" />
            <el-option label="US" value="US" />
            <el-option label="其他" value="其他" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注" prop="note">
          <el-input v-model="addForm.note" type="textarea" placeholder="请输入备注信息"></el-input>
        </el-form-item>
        <el-form-item label="选择文件" prop="file">
          <el-upload
            ref="uploadRef"
            :limit="1"
            :auto-upload="false"
            :on-exceed="handleExceed"
            :on-change="handleFileChange"
          >
            <template #trigger>
              <el-button type="primary">选择文件</el-button>
            </template>
            <template #tip>
              <div class="el-upload__tip">
                支持 jpg, png, dcm, nii, nii.gz 等格式.
              </div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
       <template #footer>
        <el-button @click="addDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitAdd" :loading="uploading">上传</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue';
import { listImages, deleteImage, updateImage, addImage } from '@/api/image';
import ImagePreview from '@/components/ImagePreview.vue';
import CasePreview from '@/components/CasePreview.vue';
import PatientInfo from '@/components/PatientInfo.vue';
import { ElMessage, ElMessageBox, genFileId } from 'element-plus';
import { Plus } from '@element-plus/icons-vue'

const imageList = ref([]);
const loading = ref(false);
const uploading = ref(false);

const pagination = ref({
  page: 1,
  per_page: 10,
  total_items: 0,
});

const previewDialogVisible = ref(false);
const editDialogVisible = ref(false);
const addDialogVisible = ref(false);
const casePreviewDialogVisible = ref(false);
const patientInfoDialogVisible = ref(false);

const currentImage = ref(null);
const selectedCaseId = ref(null);
const selectedPatientId = ref(null);
const addFormRef = ref(null);
const uploadRef = ref(null);

const editForm = reactive({
  id: null,
  note: ''
});

const addForm = reactive({
  name: '',
  type: '',
  note: '',
  file: null,
});

const addFormRules = {
  name: [{ required: true, message: '请输入影像名称', trigger: 'blur' }],
  type: [{ required: true, message: '请选择影像类型', trigger: 'change' }],
  file: [{ required: true, message: '请选择一个文件', trigger: 'change' }],
};

const fetchImages = async (page = 1) => {
  loading.value = true;
  try {
    const res = await listImages({ page, per_page: pagination.value.per_page });
    if (res.code === 200) {
      imageList.value = res.data;
      pagination.value = res.pagination;
    } else {
      ElMessage.error(res.message || '获取影像列表失败');
    }
  } catch (err) {
    ElMessage.error('网络错误，无法获取影像列表');
    console.error(err);
  } finally {
    loading.value = false;
  }
};

const handlePageChange = (newPage) => {
  fetchImages(newPage);
};

onMounted(fetchImages);

const handleAdd = () => {
  addDialogVisible.value = true;
};

const handleViewCase = (row) => {
  selectedCaseId.value = row.case_id;
  casePreviewDialogVisible.value = true;
};

const handleViewPatientFromPreview = (patientId) => {
  casePreviewDialogVisible.value = false;
  selectedPatientId.value = patientId;
  patientInfoDialogVisible.value = true;
};

const handlePreview = (row) => {
  currentImage.value = row;
  previewDialogVisible.value = true;
};

const handleEdit = (row) => {
  currentImage.value = row;
  editForm.id = row.id;
  editForm.note = row.note;
  editDialogVisible.value = true;
};

const submitEdit = async () => {
  try {
    const res = await updateImage(editForm.id, { note: editForm.note });
    if (res.code === 200) {
      ElMessage.success('备注更新成功');
      editDialogVisible.value = false;
      fetchImages();
    } else {
      ElMessage.error(res.message || '更新失败');
    }
  } catch (err) {
    ElMessage.error('网络错误，更新失败');
    console.error(err);
  }
};

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要删除影像 "${row.name}" 吗？此操作不可逆。`, '警告', {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'warning',
    });
    
    const res = await deleteImage(row.id);
    if (res.code === 200) {
      ElMessage.success('影像删除成功');
      fetchImages();
    } else {
      ElMessage.error(res.message || '删除失败');
    }
  } catch (err) {
    if (err !== 'cancel') {
        ElMessage.error('网络错误，删除失败');
        console.error(err);
    }
  }
};

const handleFileChange = (file) => {
  addForm.file = file.raw;
  if (addFormRef.value) {
    addFormRef.value.validateField('file');
  }
};

const handleExceed = (files) => {
  if (uploadRef.value) {
    uploadRef.value.clearFiles();
    const file = files[0];
    file.uid = genFileId();
    uploadRef.value.handleStart(file);
    addForm.file = file.raw;
  }
};

const resetAddForm = () => {
  if (addFormRef.value) {
    addFormRef.value.resetFields();
  }
  if (uploadRef.value) {
    uploadRef.value.clearFiles();
  }
  addForm.file = null;
};

const submitAdd = () => {
  addFormRef.value.validate(async (valid) => {
    if (valid) {
      uploading.value = true;
      const formData = new FormData();
      formData.append('file', addForm.file);
      formData.append('name', addForm.name);
      formData.append('type', addForm.type);
      formData.append('note', addForm.note);
      
      try {
        const res = await addImage(formData);
        if (res.code === 201) {
          ElMessage.success('影像上传成功');
          addDialogVisible.value = false;
          fetchImages();
        } else {
          ElMessage.error(res.message || '上传失败');
        }
      } catch (err) {
        ElMessage.error('网络错误，上传失败');
        console.error(err);
      } finally {
        uploading.value = false;
      }
    } else {
      ElMessage.error('请填写所有必填项');
      return false;
    }
  });
};

</script>

<style scoped>
.image-mng-container {
  padding: 20px;
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
