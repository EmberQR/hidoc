<template>
  <el-dialog
    v-model="dialogVisible"
    title="AI智能分割"
    width="80%"
    :before-close="handleClose"
    top="5vh"
    class="ai-seg-dialog"
  >
    <div class="dialog-content">
      <!-- Left Panel: Segmentation History -->
      <div class="history-panel">
        <el-card shadow="never">
          <template #header>
            <div class="card-header">
              <span>分割历史记录</span>
              <el-button :icon="Refresh" circle @click="fetchSegs" :loading="loading"></el-button>
            </div>
          </template>
          <el-scrollbar height="55vh">
            <div v-if="loading" class="loading-state">加载中...</div>
            <el-empty v-if="!loading && segList.length === 0" description="暂无历史记录"></el-empty>
            <el-collapse v-else v-model="activeCollapse" accordion>
              <el-collapse-item 
                v-for="seg in segList" 
                :key="seg.id" 
                :name="seg.id"
                @click="handleSelectSeg(seg)"
              >
                <template #title>
                  <div class="custom-collapse-title">
                    <span class="collapse-query">{{ seg.query }}</span>
                    <span class="collapse-time">{{ seg.created_at }}</span>
                  </div>
                </template>
                <div class="reasoning-details">
                    <div v-for="item in parseReasoning(seg.reasoning)" :key="item.id" class="reasoning-item-small">
                        <el-tag size="small" :type="item.tagType">{{ item.title }}</el-tag>
                        <p>{{ item.content }}</p>
                    </div>
                    <el-image 
                        :src="getResultImageUrl(seg.oss_key)" 
                        :preview-src-list="[getResultImageUrl(seg.oss_key)]"
                        class="result-image" 
                        fit="contain"
                        preview-teleported
                        hide-on-click-modal
                    />
                </div>
              </el-collapse-item>
            </el-collapse>
          </el-scrollbar>
          <div class="pagination-container">
            <el-pagination
              small
              background
              layout="prev, pager, next"
              :total="paginationInfo.total_items"
              :page-size="paginationInfo.per_page"
              v-model:current-page="paginationInfo.page"
              @current-change="handlePageChange"
              :hide-on-single-page="true"
            />
          </div>
        </el-card>
      </div>

      <!-- Right Panel: New Segmentation & Viewer -->
      <div class="main-panel">
        <!-- New Segmentation Request -->
        <el-card shadow="never" class="new-seg-card">
          <template #header>
            <span>发起新的分割</span>
          </template>
          <div class="new-seg-form">
            <el-input
              v-model="newQuery"
              placeholder="请输入您想分割或查询的目标，例如：病灶区域"
              clearable
              class="query-input"
            ></el-input>
            <el-button type="primary" @click="handleSubmit" :loading="isSubmitting">
              {{ isSubmitting ? '处理中...' : '开始处理' }}
            </el-button>
          </div>
        </el-card>

        <!-- Viewer for Selected/Current Image -->
        <el-card shadow="never" class="viewer-card">
            <template #header>
                <span>结果预览</span>
            </template>
            <div class="image-viewer">
                <div v-if="!selectedSeg" class="placeholder">请从左侧选择一个历史记录查看</div>
                <div v-else>
                    <p><strong>查询:</strong> {{ selectedSeg.query }}</p>
                     <div class="reasoning-details">
                        <div v-for="item in parseReasoning(selectedSeg.reasoning)" :key="item.id" class="reasoning-item-large">
                             <el-tag effect="dark" round class="reasoning-title" :type="item.tagType">{{ item.title }}</el-tag>
                             <p class="reasoning-content">{{ item.content }}</p>
                        </div>
                    </div>
                    <el-image 
                        :src="getResultImageUrl(selectedSeg.oss_key)" 
                        :preview-src-list="[getResultImageUrl(selectedSeg.oss_key)]"
                        class="result-image" 
                        fit="contain"
                        preview-teleported
                        hide-on-click-modal
                    />
                </div>
            </div>
        </el-card>
      </div>
    </div>
  </el-dialog>
</template>

<script setup>
import { ref, watch, defineProps, defineEmits } from 'vue';
import { ElMessage } from 'element-plus';
import { Refresh } from '@element-plus/icons-vue';
import { addImageSeg, getImageSegList } from '@/api/image';

const props = defineProps({
  imageId: {
    type: [Number, String],
    required: true,
  },
  visible: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(['update:visible']);

const dialogVisible = ref(props.visible);
const loading = ref(false);
const isSubmitting = ref(false);
const segList = ref([]);
const selectedSeg = ref(null);
const newQuery = ref('');
const activeCollapse = ref('');
const paginationInfo = ref({
  page: 1,
  per_page: 10,
  total_items: 0,
});
const CDN_URL = 'https://cdn.ember.ac.cn';
const TAG_TYPES = ['', 'success', 'info', 'warning', 'danger'];

const parseReasoning = (text) => {
    if (!text || typeof text !== 'string') {
        return [];
    }
    const regex = /(\d+)\.【(.+?)】:\s*([\s\S]*?)(?=\s*\d+\.【|$)/g;
    const matches = [...text.matchAll(regex)];

    if (matches.length > 0) {
        return matches.map((match, index) => ({
            id: match[1],
            title: match[2],
            content: match[3].trim(),
            tagType: TAG_TYPES[index % TAG_TYPES.length],
        }));
    } else {
        // Fallback for unstructured text
        return [{ id: 'raw', title: '推理结果', content: text, tagType: 'info' }];
    }
};

const fetchSegs = async () => {
  if (!props.imageId) return;
  loading.value = true;
  try {
    const res = await getImageSegList({ 
      image_id: props.imageId, 
      page: paginationInfo.value.page, 
      per_page: paginationInfo.value.per_page 
    });
    if (res.code === 200) {
      segList.value = res.data;
      paginationInfo.value.total_items = res.pagination.total_items;
      
      // Automatically select the first item on the current page if nothing is selected
      if (segList.value.length > 0) {
        handleSelectSeg(segList.value[0]);
        activeCollapse.value = segList.value[0].id;
      } else {
        selectedSeg.value = null;
      }
    } else {
      ElMessage.error(res.message || '获取分割记录失败');
    }
  } catch (error) {
    console.error(error);
    ElMessage.error('获取分割记录时发生网络错误');
  } finally {
    loading.value = false;
  }
};

const handlePageChange = (newPage) => {
  paginationInfo.value.page = newPage;
  selectedSeg.value = null; // Clear selection when changing page
  activeCollapse.value = '';
  fetchSegs();
};

const handleSelectSeg = (seg) => {
    selectedSeg.value = seg;
};

const handleSubmit = async () => {
  if (!newQuery.value) {
    ElMessage.warning('请输入查询内容');
    return;
  }
  isSubmitting.value = true;
  try {
    const payload = {
      image_id: props.imageId,
      query: newQuery.value,
    };
    const res = await addImageSeg(payload);
    if (res.code === 201) {
      ElMessage.success('分割任务已成功发起');
      newQuery.value = '';
      await fetchSegs(); // Refresh the list
    } else {
      ElMessage.error(res.message || '分割失败');
    }
  } catch (error) {
    console.error(error);
    ElMessage.error('分割任务发起时发生网络错误');
  } finally {
    isSubmitting.value = false;
  }
};

const getResultImageUrl = (ossKey) => {
  if (!ossKey) return '';
  return `${CDN_URL}/${ossKey}`;
};

const handleClose = () => {
  emit('update:visible', false);
};

watch(() => props.visible, (newVal) => {
    dialogVisible.value = newVal;
    if (newVal) {
        selectedSeg.value = null; // reset selection
        paginationInfo.value.page = 1; // reset to first page
        fetchSegs();
    }
});
</script>

<style scoped>
.ai-seg-dialog .dialog-content {
  display: flex;
  gap: 20px;
  height: 75vh;
}

.history-panel {
  flex: 2;
  display: flex;
  flex-direction: column;
}

.history-panel .el-card {
  flex-grow: 1;
}

.main-panel {
  flex: 3;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.el-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.el-card__body {
    flex-grow: 1;
    overflow-y: auto;
}

.custom-collapse-title {
  display: flex;
  flex-direction: column;
  line-height: 1.4;
  /* Adjust width to prevent overflow from pushing the expand icon */
  width: calc(100% - 30px); 
}

.collapse-query {
  font-weight: 500;
  color: #303133;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 4px;
}

.pagination-container {
  padding-top: 10px;
  display: flex;
  justify-content: center;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.collapse-title {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-right: 10px;
}

.collapse-time {
  font-size: 0.8em;
  color: #999;
}

.new-seg-card {
    flex-shrink: 0;
}

.new-seg-form {
  display: flex;
  gap: 10px;
}

.viewer-card {
    flex-grow: 1;
}

.image-viewer {
  height: 100%;
  overflow-y: auto;
}

.image-viewer .placeholder {
    text-align: center;
    color: #999;
    padding-top: 50px;
}

.result-image {
  max-width: 100%;
  border-radius: 4px;
  margin-top: 10px;
  border: 1px solid #ebeef5;
}

.reasoning-details {
  margin-bottom: 10px;
}

.reasoning-item-small {
  margin-bottom: 8px;
}

.reasoning-item-small p {
  font-size: 13px;
  color: #606266;
  margin: 4px 0 0 0;
  line-height: 1.4;
}

.reasoning-item-large {
  margin-bottom: 15px;
}

.reasoning-title {
  margin-bottom: 8px;
  display: inline-block;
}

.reasoning-content {
  font-size: 14px;
  color: #303133;
  line-height: 1.6;
  background-color: #f5f7fa;
  padding: 10px;
  border-radius: 4px;
  margin: 0;
  white-space: pre-wrap;
}
</style>
