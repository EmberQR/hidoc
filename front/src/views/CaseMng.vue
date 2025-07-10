<template>
  <div class="case-management">
    <!-- 页面头部 -->
    <div class="page-header">
      <h1 class="page-title">病历管理</h1>
      <p class="page-description">在这里管理、查询和创建病历。默认显示所有医生创建的病历。</p>
    </div>

    <!-- 搜索和操作栏 -->
    <el-card class="action-bar-card" shadow="never">
      <el-form :inline="true" :model="searchForm" @submit.prevent="handleSearch">
        <el-form-item label="科室选择">
          <el-cascader
            v-model="searchForm.office_id"
            :options="officeOptions"
            :props="{ checkStrictly: true, value: 'id', label: 'name', emitPath: false }"
            placeholder="请选择科室"
            clearable
            style="width: 250px;"
          />
        </el-form-item>
        <el-form-item label="病人姓名">
          <el-input v-model="searchForm.patient_name" placeholder="输入病人姓名模糊查询" clearable />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch" :icon="Search">搜索病历</el-button>
        </el-form-item>
      </el-form>
      <div class="action-buttons">
        <el-checkbox v-model="searchForm.my_case" label="只显示我创建的" border @change="handleSearch" style="margin-right: 15px;" />
        <el-button @click="handleAddPatient" :icon="User">添加病人</el-button>
        <el-button type="success" @click="handleAddCase" :icon="DocumentAdd">添加病历</el-button>
      </div>
    </el-card>

    <!-- 病历表格 -->
    <el-card class="case-table-card" shadow="never">
       <el-table :data="caseList" v-loading="loading" style="width: 100%">
        <el-table-column prop="case_date" label="就诊日期" width="120" />
        <el-table-column prop="patient_name" label="病人姓名" width="120">
          <template #default="scope">
            <el-button link type="primary" @click="showPatientInfo(scope.row.patient_id)">
              {{ scope.row.patient_name }}
            </el-button>
          </template>
        </el-table-column>
        <el-table-column prop="doctor_name" label="主治医生" width="100" />
        <el-table-column prop="office_name" label="所属科室" width="150" />
        <el-table-column prop="chief_complaint" label="主诉" show-overflow-tooltip />
        <el-table-column prop="diagnosis" label="诊断结果" show-overflow-tooltip />
        <el-table-column label="影像" width="140">
          <template #default="scope">
            <el-button 
              size="small" 
              @click="handleImageManagement(scope.row)"
              :type="scope.row.images && scope.row.images.length > 0 ? 'success' : 'default'"
              plain
            >
              影像管理 ({{ scope.row.images ? scope.row.images.length : 0 }})
            </el-button>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="scope">
            <el-button size="small" type="primary" :icon="View" @click="handleViewCase(scope.row)">查看</el-button>
            <el-button size="small" :icon="Edit" @click="handleEditCase(scope.row)">编辑</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination
        v-if="pagination.total > 0"
        class="table-pagination"
        background
        layout="total, sizes, prev, pager, next, jumper"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.per_page"
        @size-change="handleSearch"
        @current-change="fetchCases"
      />
    </el-card>

    <!-- 添加/编辑病历弹窗 -->
    <el-dialog v-model="caseDialogVisible" :title="caseForm.id ? '编辑病历' : '添加病历'" width="60%" top="5vh">
      <el-form :model="caseForm" ref="caseFormRef" label-position="top" :rules="caseFormRules">
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="病人" prop="patient_id">
              <el-select v-model="caseForm.patient_id" filterable remote :remote-method="searchPatients" placeholder="搜索并选择病人" style="width: 100%;">
                <el-option v-for="item in patientOptions" :key="item.id" :label="item.name" :value="item.id">
                  <div class="patient-option">
                    <div class="patient-option-info">
                      <span>{{ item.name }}</span>
                      <span class="patient-option-meta">
                        ({{ item.gender }}{{ calculateAge(item.birthday) ? `，${calculateAge(item.birthday)}` : '' }})
                      </span>
                    </div>
                    <el-button link type="primary" size="small" @click.stop="showPatientInfo(item.id)">
                      查看详情
                    </el-button>
                  </div>
                </el-option>
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="就诊科室" prop="office_id">
              <el-cascader v-model="caseForm.office_id" :options="officeOptions" :props="{ checkStrictly: true, value: 'id', label: 'name', emitPath: false }" placeholder="请选择科室" style="width: 100%;" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="就诊日期" prop="case_date">
              <el-date-picker v-model="caseForm.case_date" type="date" value-format="YYYY-MM-DD" placeholder="选择日期" style="width: 100%;" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="主诉" prop="chief_complaint">
          <el-input v-model="caseForm.chief_complaint" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="现病史" prop="present_illness_history">
          <el-input v-model="caseForm.present_illness_history" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="既往史" prop="past_medical_history">
          <el-input v-model="caseForm.past_medical_history" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="诊断结果" prop="diagnosis">
          <el-input v-model="caseForm.diagnosis" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="治疗方案" prop="treatment_plan">
          <el-input v-model="caseForm.treatment_plan" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="caseDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitCase">提交</el-button>
      </template>
    </el-dialog>

    <!-- 添加病人弹窗 -->
    <el-dialog v-model="patientDialogVisible" title="添加新病人" width="400px">
      <el-form :model="patientForm" ref="patientFormRef" label-position="top" :rules="patientFormRules">
        <el-form-item label="姓名" prop="name">
          <el-input v-model="patientForm.name" placeholder="请输入病人姓名" />
        </el-form-item>
        <el-form-item label="性别" prop="gender">
          <el-select v-model="patientForm.gender" placeholder="请选择性别" style="width: 100%;">
            <el-option label="男" value="男" />
            <el-option label="女" value="女" />
            <el-option label="未知" value="未知" />
          </el-select>
        </el-form-item>
        <el-form-item label="出生日期" prop="birthday">
          <el-date-picker v-model="patientForm.birthday" type="date" value-format="YYYY-MM-DD" placeholder="选填" style="width: 100%;" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="patientDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitPatient">创建</el-button>
      </template>
    </el-dialog>

    <!-- 影像管理弹窗 -->
    <el-dialog v-model="imageManagementDialogVisible" title="病历影像管理" width="50%" top="10vh">
      <template #header>
        <div class="dialog-header">
          <h3 class="dialog-title">病历影像管理</h3>
          <el-button type="primary" :icon="Plus" @click="handleAddImageForCase">为此病历添加影像</el-button>
        </div>
      </template>
      <el-table :data="currentCase?.images" style="width: 100%" height="400px">
        <el-table-column label="预览图" width="120">
          <template #default="scope">
            <el-image :src="scope.row.preview_url" style="width: 80px; height: 80px; border-radius: 4px;" fit="cover" :preview-src-list="[scope.row.preview_url]" hide-on-click-modal />
          </template>
        </el-table-column>
        <el-table-column prop="name" label="影像名称" />
        <el-table-column prop="dim" label="影像类型" />
        <el-table-column label="操作" width="180">
          <template #default="scope">
            <el-button size="small" @click="handlePreviewImage(scope.row.image_id)">查看/标注</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <!-- 添加影像弹窗 -->
    <el-dialog v-model="addImageDialogVisible" title="为此病历添加影像" width="40%" @close="resetAddImageForm">
      <el-form :model="addImageForm" :rules="addImageFormRules" ref="addImageFormRef" label-width="80px">
        <el-form-item label="影像名称" prop="name">
          <el-input v-model="addImageForm.name" placeholder="请输入影像名称"></el-input>
        </el-form-item>
        <el-form-item label="影像类型" prop="type">
           <el-select v-model="addImageForm.type" placeholder="请选择影像类型">
            <el-option label="X-ray" value="X-ray" />
            <el-option label="CT" value="CT" />
            <el-option label="MRI" value="MRI" />
            <el-option label="PET" value="PET" />
            <el-option label="US" value="US" />
            <el-option label="其他" value="其他" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注" prop="note">
          <el-input v-model="addImageForm.note" type="textarea" placeholder="请输入备注信息"></el-input>
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
              <div class="el-upload__tip">支持 jpg, png, dcm, nii, nii.gz 等格式.</div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
       <template #footer>
        <el-button @click="addImageDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitAddImage" :loading="uploading">上传</el-button>
      </template>
    </el-dialog>

    <!-- 影像预览/标注弹窗 -->
    <el-dialog v-model="imagePreviewDialogVisible" title="影像预览与标注" width="85%" top="5vh" destroy-on-close>
      <ImagePreview v-if="imagePreviewDialogVisible && selectedImageId" :image-id="selectedImageId" />
    </el-dialog>

    <!-- 病历详情预览弹窗 -->
    <el-dialog v-model="casePreviewDialogVisible" title="病历详情" width="85%" top="5vh" destroy-on-close>
      <CasePreview 
        v-if="casePreviewDialogVisible && selectedCaseIdForPreview" 
        :case-id="selectedCaseIdForPreview"
        @view-patient="handleViewPatientFromPreview" />
    </el-dialog>

    <!-- 病人详情预览弹窗 -->
    <el-dialog v-model="patientInfoDialogVisible" title="病人综合信息" width="90%" top="5vh" destroy-on-close>
      <PatientInfo v-if="patientInfoDialogVisible && selectedPatientIdForInfo" :patient-id="selectedPatientIdForInfo" />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { ElMessage, genFileId } from 'element-plus';
import { Search, Edit, User, DocumentAdd, Plus, View } from '@element-plus/icons-vue';
import { getOffices, getCases, addPatient, addCase, updateCase, searchPatients as searchPatientsApi } from '@/api/hospital';
import { addImage } from '@/api/image';
import { getCurrentHospital } from '@/utils/auth';
import ImagePreview from '@/components/ImagePreview.vue';
import CasePreview from '@/components/CasePreview.vue';
import PatientInfo from '@/components/PatientInfo.vue';

// --- 响应式状态定义 ---

const loading = ref(false);
const searchForm = reactive({
  office_id: null,
  patient_name: '',
  my_case: false
});
const caseList = ref([]);
const pagination = reactive({
  page: 1,
  per_page: 10,
  total: 0
});
const officeOptions = ref([]);

// 病历弹窗
const caseDialogVisible = ref(false);
const caseFormRef = ref(null);
const initialCaseForm = {
    id: null,
    patient_id: '',
    office_id: '',
    case_date: '',
    chief_complaint: '',
    present_illness_history: '',
    past_medical_history: '',
    diagnosis: '',
    treatment_plan: ''
};
const caseForm = reactive({ ...initialCaseForm });
const caseFormRules = {
  patient_id: [{ required: true, message: '请选择病人', trigger: 'change' }],
  office_id: [{ required: true, message: '请选择科室', trigger: 'change' }],
  case_date: [{ required: true, message: '请选择就诊日期', trigger: 'change' }]
};
const patientOptions = ref([]);

// 病人弹窗
const patientDialogVisible = ref(false);
const patientFormRef = ref(null);
const patientForm = reactive({
  name: '',
  gender: '',
  birthday: ''
});
const patientFormRules = {
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  gender: [{ required: true, message: '请选择性别', trigger: 'change' }]
};

// 影像相关
const imageManagementDialogVisible = ref(false);
const addImageDialogVisible = ref(false);
const imagePreviewDialogVisible = ref(false);
const currentCase = ref(null);
const selectedImageId = ref(null);
const uploading = ref(false);
const addImageFormRef = ref(null);
const uploadRef = ref(null);
const addImageForm = reactive({
  name: '',
  type: '',
  note: '',
  file: null,
});
const addImageFormRules = {
  name: [{ required: true, message: '请输入影像名称', trigger: 'blur' }],
  type: [{ required: true, message: '请选择影像类型', trigger: 'change' }],
  file: [{ required: true, message: '请选择一个文件', trigger: 'change' }],
};

// 病历预览弹窗
const casePreviewDialogVisible = ref(false);
const selectedCaseIdForPreview = ref(null);

// 病人详情弹窗
const patientInfoDialogVisible = ref(false);
const selectedPatientIdForInfo = ref(null);

// --- 数据获取与处理 ---

// 获取科室列表并构建层级结构
const fetchOffices = async () => {
  const currentHospital = getCurrentHospital();
  const hospitalId = currentHospital?.id;
  if (!hospitalId) {
    ElMessage.warning('请先在导航栏选择您所在的医院');
    return;
  }
  try {
    const res = await getOffices({ hospital_id: hospitalId });
    if (res.code === 200) {
      officeOptions.value = buildOfficeTree(res.data);
    } else {
      ElMessage.error(res.message || '获取科室列表失败');
    }
  } catch (error) {
    console.error(error);
  }
};

// 获取病历列表
const fetchCases = async () => {
  if (!searchForm.office_id) {
    ElMessage.warning('请先选择一个科室进行查询');
    caseList.value = [];
    pagination.total = 0;
    return;
  }
  loading.value = true;
  try {
    const params = {
      ...searchForm,
      // 将布尔值转换为后端期望的字符串 'true' 或 'false'
      my_case: searchForm.my_case ? 'true' : 'false',
      page: pagination.page,
      per_page: pagination.per_page
    };
    const res = await getCases(params);
    if (res.code === 200) {
      caseList.value = res.data;
      pagination.total = res.pagination.total_items;
    } else {
      ElMessage.error(res.message || '查询病历失败');
    }
  } catch (error) {
    console.error(error);
  } finally {
    loading.value = false;
  }
};

// 搜索病人（用于表单内选择）
const searchPatients = async (query) => {
  if (!query) {
    patientOptions.value = [];
    return;
  }
  try {
    // 调用新的病人搜索接口
    const res = await searchPatientsApi({ name: query });
    if (res.code === 200) {
      patientOptions.value = res.data;
    } else {
      patientOptions.value = [];
      ElMessage.warning(res.message || '未找到相关病人');
    }
  } catch (error) {
    console.error('搜索病人失败:', error);
    patientOptions.value = [];
  }
};

// --- 事件处理 ---

const handleSearch = () => {
  pagination.page = 1;
  fetchCases();
};

const handleAddPatient = () => {
  patientFormRef.value?.resetFields();
  Object.assign(patientForm, { name: '', gender: '', birthday: '' });
  patientDialogVisible.value = true;
};

const submitPatient = async () => {
  await patientFormRef.value.validate();
  try {
    const res = await addPatient(patientForm);
    if (res.code === 201) {
      ElMessage.success('病人添加成功');
      patientDialogVisible.value = false;
    } else {
      ElMessage.error(res.message || '添加失败');
    }
  } catch (error) {
    console.error(error);
  }
};

const handleAddCase = () => {
  caseFormRef.value?.resetFields();
  Object.assign(caseForm, initialCaseForm);
  // 默认带入搜索栏的科室
  if (searchForm.office_id) {
    caseForm.office_id = searchForm.office_id;
  }
  caseDialogVisible.value = true;
};

const handleEditCase = (row) => {
  caseFormRef.value?.resetFields();
  Object.assign(caseForm, row);
  // 使病人选项中包含当前病人
  patientOptions.value = [{ id: row.patient_id, name: row.patient_name, gender: '', birthday: '' }];
  caseDialogVisible.value = true;
};

const submitCase = async () => {
  await caseFormRef.value.validate();
  try {
    const apiCall = caseForm.id ? updateCase : addCase;
    const res = await apiCall(caseForm);
    if (res.code === 200 || res.code === 201) {
      ElMessage.success(caseForm.id ? '更新成功' : '创建成功');
      caseDialogVisible.value = false;
      fetchCases();
    } else {
      ElMessage.error(res.message || '操作失败');
    }
  } catch (error) {
    console.error(error);
  }
};

const handleViewCase = (row) => {
  selectedCaseIdForPreview.value = row.id;
  casePreviewDialogVisible.value = true;
};

const showPatientInfo = (patientId) => {
  selectedPatientIdForInfo.value = patientId;
  patientInfoDialogVisible.value = true;
};

const handleViewPatientFromPreview = (patientId) => {
  casePreviewDialogVisible.value = false;
  showPatientInfo(patientId);
};

// --- 影像相关事件处理 ---

const handleImageManagement = (row) => {
  currentCase.value = row;
  imageManagementDialogVisible.value = true;
};

const handleAddImageForCase = () => {
  addImageDialogVisible.value = true;
};

const handlePreviewImage = (imageId) => {
  selectedImageId.value = imageId;
  imagePreviewDialogVisible.value = true;
};

const resetAddImageForm = () => {
  addImageFormRef.value?.resetFields();
  uploadRef.value?.clearFiles();
  addImageForm.file = null;
};

const handleFileChange = (file) => {
  addImageForm.file = file.raw;
  addImageFormRef.value?.validateField('file');
};

const handleExceed = (files) => {
  uploadRef.value?.clearFiles();
  const file = files[0];
  file.uid = genFileId();
  uploadRef.value?.handleStart(file);
  addImageForm.file = file.raw;
};

const submitAddImage = () => {
  addImageFormRef.value.validate(async (valid) => {
    if (!valid) return;
    if (!currentCase.value) return;

    uploading.value = true;
    const formData = new FormData();
    formData.append('file', addImageForm.file);
    formData.append('name', addImageForm.name);
    formData.append('type', addImageForm.type);
    formData.append('note', addImageForm.note);
    // 自动关联病历信息
    formData.append('case_id', currentCase.value.id);
    formData.append('patient_id', currentCase.value.patient_id);
    formData.append('office_id', currentCase.value.office_id);

    try {
      const res = await addImage(formData);
      if (res.code === 201) {
        ElMessage.success('影像上传成功');
        addImageDialogVisible.value = false;
        // 刷新病历列表以显示更新后的影像信息
        await fetchCases();
        // 更新当前弹窗内的数据
        const updatedCase = caseList.value.find(c => c.id === currentCase.value.id);
        if(updatedCase) {
          currentCase.value = updatedCase;
        }
      } else {
        ElMessage.error(res.message || '上传失败');
      }
    } catch (err) {
      ElMessage.error('网络错误，上传失败');
      console.error(err);
    } finally {
      uploading.value = false;
    }
  });
};


// --- 辅助函数 ---

const calculateAge = (birthday) => {
  if (!birthday) return '';
  try {
    const birthDate = new Date(birthday);
    const today = new Date();
    // Check if birthDate is a valid date
    if (isNaN(birthDate.getTime())) {
      return '';
    }
    let age = today.getFullYear() - birthDate.getFullYear();
    const monthDiff = today.getMonth() - birthDate.getMonth();
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
      age--;
    }
    return age >= 0 ? `${age}岁` : '';
  } catch(e) {
    return '';
  }
};

// 将从接口获取的、带有 parent_path 的科室列表，转换为树形结构
function buildOfficeTree(offices) {
  const officeMap = new Map();
  const tree = [];

  // 辅助函数，确保每个科室节点在 map 中是唯一的
  const addOfficeToMap = (office) => {
    if (!officeMap.has(office.id)) {
      officeMap.set(office.id, { ...office, children: [] });
    }
  };

  // 遍历接口返回的每个科室（这些是医生直接关联的科室）
  offices.forEach(assignedOffice => {
    // 1. 将路径中的所有父科室和当前科室都加入到 Map 中，确保所有节点都被创建
    assignedOffice.parent_path.forEach(p => addOfficeToMap(p));
    addOfficeToMap(assignedOffice);

    // 2. 建立父子关系
    // 将当前科室连接到它的直接父科室上
    if (assignedOffice.parent_id && officeMap.has(assignedOffice.parent_id)) {
      const parent = officeMap.get(assignedOffice.parent_id);
      // 避免重复添加
      if (!parent.children.some(child => child.id === assignedOffice.id)) {
        parent.children.push(officeMap.get(assignedOffice.id));
      }
    }
    
    // 遍历父路径，将路径中的父子关系也连接起来
    assignedOffice.parent_path.forEach(p => {
      if (p.parent_id && officeMap.has(p.parent_id)) {
        const parent = officeMap.get(p.parent_id);
        if (!parent.children.some(child => child.id === p.id)) {
          parent.children.push(officeMap.get(p.id));
        }
      }
    });
  });

  // 3. 找出所有根节点（没有父ID的），它们是树的顶层
  for (const officeNode of officeMap.values()) {
    if (!officeNode.parent_id) {
      tree.push(officeNode);
    }
  }

  return tree;
}

// --- 生命周期钩子 ---

onMounted(() => {
  document.title = '病历管理 - HiDoc';
  fetchOffices();
});
</script>

<style scoped>
.case-management {
  padding: 20px;
  background-color: #f0f2f5;
  min-height: calc(100vh - 50px);
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

.action-bar-card, .case-table-card {
  border-radius: 8px;
  border: none;
  margin-bottom: 20px;
}
.el-form-item {
  margin-bottom: 0; /* 在行内表单中减少下边距 */
}
.action-buttons {
  margin-top: 16px;
}

.table-pagination {
  margin-top: 20px;
  justify-content: flex-end;
}

.el-dialog .el-form-item {
    margin-bottom: 18px;
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dialog-title {
  font-size: 18px;
  color: #303133;
  margin: 0;
}

.patient-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}
.patient-option-info {
  display: flex;
  align-items: center;
}
.patient-option-meta {
  font-size: 13px;
  color: #909399;
  margin-left: 8px;
}
</style>
