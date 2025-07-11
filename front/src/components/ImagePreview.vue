<template>
  <div class="image-preview-container">
    <div v-if="loading" class="loading">正在加载影像...</div>
    <div v-if="error" class="error">{{ error }}</div>

    <div v-if="!loading && !error && imageInfo" class="preview-content">
      
      <!-- Image Display & Annotation Area -->
      <div class="image-display-area">
        <div 
          class="image-frame" 
          :class="{ 'drawing-cursor': showAnnotations && isDrawing }"
          ref="imageFrame"
        >
          <!-- Non-annotation mode: simple img tag -->
          <template v-if="!showAnnotations">
            <div v-if="isSimpleImageLoading" class="canvas-loading-overlay">
              <div class="loading-spinner"></div>
              <span>正在加载预览图...</span>
            </div>
            <img 
              v-if="currentImageUrl"
              :src="currentImageUrl" 
              @load="handleImageLoad" 
              @error="handleImageError" 
              class="preview-image"
            />
            <div v-else class="placeholder">无可用预览</div>
          </template>

          <!-- Annotation mode: Konva canvas -->
          <template v-else>
            <div v-if="isCanvasImageLoading" class="canvas-loading-overlay">
              <div class="loading-spinner"></div>
              <span>正在加载标注画布...</span>
            </div>
            <v-stage
              :config="konvaConfig"
              @mousedown="handleMouseDown"
              @mousemove="handleMouseMove"
              @mouseup="handleMouseUp"
            >
              <v-layer>
                <v-image :config="{ image: konvaImage }" />
              </v-layer>
              <v-layer>
                <!-- Existing annotations -->
                <template v-for="anno in annotations" :key="anno.id">
                  <v-rect 
                    :config="getRectConfig(anno)"
                    @click="handleAnnotationClick(anno)"
                    @mouseover="handleAnnotationMouseOver"
                    @mouseout="handleAnnotationMouseOut"
                  />
                  <v-text :config="getTextConfig(anno)" />
                </template>
                <!-- New annotation being drawn -->
                <v-rect v-if="newAnnotation" :config="getRectConfig(newAnnotation)" />
              </v-layer>
            </v-stage>
          </template>
        </div>

        <!-- Controls for 3D -->
        <div v-if="dim === '3D'" class="controls-3d">
            <div class="direction-selector">
              <span>方向:</span>
              <button @click="changeDirection('x')" :class="{ active: currentDirection === 'x' }">X (矢状位)</button>
              <button @click="changeDirection('y')" :class="{ active: currentDirection === 'y' }">Y (冠状位)</button>
              <button @click="changeDirection('z')" :class="{ active: currentDirection === 'z' }">Z (轴位)</button>
            </div>
            <div class="slice-slider">
              <el-input-number 
                v-model="currentSliceDisplayIndex" 
                :min="1" 
                :max="slicePreviews.length"
                size="small"
                controls-position="right"
                class="slice-input"
              />
              <el-slider
                v-model="currentSliceIndex"
                :min="0"
                :max="maxSliceIndex"
                class="slider"
                :show-tooltip="false"
                :marks="sliderMarks"
              />
              <span class="slice-count">{{ currentSliceIndex + 1 }} / {{ slicePreviews.length }}</span>
            </div>
        </div>
        
        <!-- Action Buttons -->
        <div class="action-controls">
          <el-button v-if="imageInfo" @click="handleEditNote" type="info" plain>
            <el-icon><Edit /></el-icon>
            编辑备注
          </el-button>
          <el-button v-if="isSegReady" @click="openSegDialog" type="primary" plain>
            <el-icon><MagicStick /></el-icon>
            AI智能分割
          </el-button>
        </div>
      </div>

      <!-- Information & Annotation Panel -->
      <div class="info-panel">
        <h3>影像信息</h3>
        <ul>
          <li><strong>名称:</strong> {{ imageInfo.name }}</li>
          <li><strong>类型:</strong> {{ imageInfo.type }}</li>
          <li><strong>格式:</strong> {{ imageInfo.format == 'picture' ? '图片' : imageInfo.format }}</li>
          <li><strong>维度:</strong> {{ imageInfo.dim }}</li>
          <li v-if="dim === '3D'">
            <strong>尺寸:</strong> 
            {{ imageInfo.slice_x }} (x) &times; 
            {{ imageInfo.slice_y }} (y) &times; 
            {{ imageInfo.slice_z }} (z)
          </li>
          <li v-if="dim === '2D' && imageInfo.slice_x">
            <strong>尺寸:</strong> 
            {{ imageInfo.slice_x }} &times; {{ imageInfo.slice_y }}
          </li>
          <li><strong>大小:</strong> {{ imageInfo.size ? imageInfo.size.toFixed(2) : 'N/A' }} KB</li>
          <li><strong>上传时间:</strong> {{ imageInfo.created_at }}</li>
          <li><strong>备注:</strong> {{ imageInfo.note || '无' }}</li>
        </ul>
        <a :href="sourceUrl" target="_blank" download class="download-button">下载源文件</a>

        <div class="annotation-section">
          <h3>标注管理</h3>
          <div class="anno-controls">
            <el-checkbox v-model="showAnnotations" label="显示标注" border />
            <el-button @click="toggleDrawing" :type="isDrawing ? 'danger' : 'primary'" size="small" :disabled="!showAnnotations">
              {{ isDrawing ? '取消标注' : '新增标注' }}
            </el-button>
          </div>
        </div>
      </div>
    </div>
    <AIReasonSeg 
      v-if="currentImageIdForAnnotation"
      :image-id="currentImageIdForAnnotation" 
      v-model:visible="showSegDialog" 
    />
  </div>
</template>

<script>
import { getImagePreview, addAnnotation, getAnnotations, deleteAnnotation, updateImage } from '@/api/image';
import { Delete, MagicStick, Edit } from '@element-plus/icons-vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import AIReasonSeg from './AIReasonSeg.vue';

const ANNO_COLORS = ['#FF5733', '#33FF57', '#3357FF', '#FF33A1', '#A133FF', '#33FFA1'];

export default {
  name: 'ImagePreview',
  components: {
    AIReasonSeg,
    MagicStick,
    Edit
  },
  props: {
    imageId: {
      type: [Number, String],
      required: true,
      default: 2
    }
  },
  data() {
    return {
      loading: false,
      error: null,
      
      // Data from API
      imageInfo: null,
      dim: null,
      sourceUrl: null,
      
      // For 2D
      previewUrl: null,
      
      // For 3D
      slicePreviews: [],
      annotatedSlices: [],
      currentDirection: 'x', // Default direction
      currentSliceIndex: 0,

      Delete,
      konvaConfig: { width: 0, height: 0 },
      konvaImage: null,
      
      // Annotation state
      showAnnotations: false,
      isDrawing: false,
      annotations: [],
      newAnnotation: null,
      isCanvasImageLoading: false,
      isSimpleImageLoading: false,
      showSegDialog: false,
    };
  },
  computed: {
    currentImageUrl() {
      if (this.dim === '2D') {
        return this.previewUrl || '';
      }
      if (this.dim === '3D' && this.slicePreviews.length > 0) {
        return this.slicePreviews[this.currentSliceIndex]?.url || '';
      }
      return '';
    },
    maxSliceIndex() {
      return this.slicePreviews.length > 0 ? this.slicePreviews.length - 1 : 0;
    },
    currentImageIdForAnnotation() {
      if (this.dim === '2D') return this.imageInfo.id;
      if (this.dim === '3D' && this.slicePreviews.length > 0) {
        return this.slicePreviews[this.currentSliceIndex]?.id;
      }
      return null;
    },
    currentSliceDisplayIndex: {
      get() {
        return this.currentSliceIndex + 1;
      },
      set(value) {
        if (value > 0) {
          this.currentSliceIndex = value - 1;
        }
      }
    },
    sliderMarks() {
      if (!this.showAnnotations || !this.annotatedSlices) {
        return {};
      }
      const marks = {};
      this.annotatedSlices.forEach(sliceIndex => {
        if (sliceIndex >= 0 && sliceIndex <= this.maxSliceIndex) {
          marks[sliceIndex] = {
            style: {
              width: '12px',
              height: '12px',
              display: 'block',
              backgroundColor: '#f56c6c',
              borderRadius: '50%',
              top: '0px',
              left: '-5px',
              transform: 'translateY(-50%)',
            },
            label: ''
          };
        }
      });
      return marks;
    },
    isSegReady() {
      // AI Seg is ready if it's a 3D image (slices are pictures) or a 2D picture
      if (this.dim === '3D') return true;
      if (this.dim === '2D' && this.imageInfo && this.imageInfo.format === 'picture') return true;
      return false;
    }
  },
  watch: {
    imageId: {
      immediate: true,
      handler(newId) {
        if (newId) {
          this.fetchImageData(this.currentDirection);
        }
      }
    },
    currentImageUrl(newUrl) {
      if (newUrl) {
        if (this.showAnnotations) {
          this.updateKonvaImage(newUrl);
        } else {
          this.isSimpleImageLoading = true;
        }
      }
    },
    showAnnotations(visible, oldVisible) {
      if (visible) {
        this.fetchAnnotations();
        // If switching from non-anno to anno mode, load image to canvas
        if (!oldVisible) {
          this.$nextTick(() => {
            this.setKonvaSize();
            this.updateKonvaImage(this.currentImageUrl);
          });
        }
      } else {
        this.annotations = [];
      }
    },
    currentImageIdForAnnotation(newId, oldId) {
        if (newId !== oldId && this.showAnnotations) {
            this.fetchAnnotations();
        }
    }
  },
  mounted() {
    this.setKonvaSize();
    window.addEventListener('resize', this.setKonvaSize);
  },
  beforeUnmount() {
    window.removeEventListener('resize', this.setKonvaSize);
  },
  methods: {
    async handleEditNote() {
      if (!this.imageInfo) return;

      try {
        const { value } = await ElMessageBox.prompt('请输入新的备注信息', '编辑备注', {
          confirmButtonText: '保存',
          cancelButtonText: '取消',
          inputValue: this.imageInfo.note || '',
          inputType: 'textarea',
        });

        const res = await updateImage(this.imageInfo.id, { note: value });

        if (res.code === 200) {
          ElMessage.success('备注更新成功');
          this.imageInfo.note = value;
        } else {
          ElMessage.error(res.message || '更新失败');
        }
      } catch (error) {
        if (error === 'cancel') {
          ElMessage.info('已取消编辑');
        } else {
          console.error('更新备注失败:', error);
          ElMessage.error('更新备注失败，请稍后重试');
        }
      }
    },
    openSegDialog() {
      this.showSegDialog = true;
    },
    handleImageLoad() {
      this.isSimpleImageLoading = false;
    },
    handleImageError() {
      this.isSimpleImageLoading = false;
      console.error("无法加载预览图");
    },
    async fetchImageData(direction) {
      if (!this.imageId) return;
      
      this.loading = true;
      this.error = null;
      
      try {
        const response = await getImagePreview(this.imageId, { direction });
        if (response.code === 200) {
          const data = response.data;
          this.imageInfo = data.image_info;
          this.dim = data.dim;
          this.sourceUrl = data.source_url;
          
          if (this.dim === '2D') {
            this.previewUrl = data.preview_url;
          } else if (this.dim === '3D') {
            this.slicePreviews = data.slice_previews;
            this.annotatedSlices = data.annotated_slices || [];
            this.currentDirection = data.direction;
            this.currentSliceIndex = 0; // Reset slider
          }
        } else {
          throw new Error(response.message || '获取影像信息失败');
        }
      } catch (err) {
        this.error = err.message || '加载失败，请检查网络连接';
        console.error(err);
      } finally {
        this.loading = false;
      }
    },
    changeDirection(newDirection) {
      if (this.currentDirection !== newDirection) {
        this.fetchImageData(newDirection);
      }
    },
    setKonvaSize() {
        if (this.$refs.imageFrame) {
            this.konvaConfig.width = this.$refs.imageFrame.clientWidth;
            this.konvaConfig.height = this.$refs.imageFrame.clientHeight;
        }
    },
    updateKonvaImage(url) {
      if (!url) {
        this.konvaImage = null;
        return;
      }
      this.isCanvasImageLoading = true;
      const image = new Image();
      image.crossOrigin = "Anonymous"; // Handle potential CORS issues with canvas
      image.src = url;
      image.onload = () => {
        this.konvaImage = image;
        this.isCanvasImageLoading = false;
      };
      image.onerror = () => {
        console.error("无法加载用于Canvas的影像");
        this.isCanvasImageLoading = false;
        // Optionally show an error message on the canvas
      }
    },
    async fetchAnnotations() {
        const imageId = this.currentImageIdForAnnotation;
        if (!imageId) return;
        try {
            const res = await getAnnotations({ image_id: imageId, anno_type: 'bbox' });
            if (res.code === 200) {
                this.annotations = res.data.map((anno, index) => ({
                    ...anno,
                    color: ANNO_COLORS[index % ANNO_COLORS.length],
                }));
            } else {
                ElMessage.error('获取标注失败');
            }
        } catch (error) {
            console.error(error);
        }
    },
    toggleDrawing() {
      this.isDrawing = !this.isDrawing;
      this.newAnnotation = null;
    },
    getRectConfig(anno) {
      return {
        x: anno.up_left_x,
        y: anno.up_left_y,
        width: anno.bottom_right_x - anno.up_left_x,
        height: anno.bottom_right_y - anno.up_left_y,
        stroke: anno.color || '#FF0000',
        strokeWidth: 2,
      };
    },
    getTextConfig(anno) {
      return {
        x: anno.up_left_x,
        y: anno.up_left_y - 20, // Position text above the box
        text: anno.note || '',
        fontSize: 16,
        fontStyle: 'bold',
        fill: anno.color,
        shadowColor: 'black',
        shadowBlur: 1,
        shadowOffsetX: 1,
        shadowOffsetY: 1,
        shadowOpacity: 0.7,
      };
    },
    handleMouseDown(e) {
      if (!this.isDrawing) return;
      const pos = e.target.getStage().getPointerPosition();
      this.newAnnotation = {
        up_left_x: pos.x,
        up_left_y: pos.y,
        bottom_right_x: pos.x,
        bottom_right_y: pos.y,
        color: '#FF0000', // Drawing color
      };
    },
    handleMouseMove(e) {
      if (!this.isDrawing || !this.newAnnotation) return;
      const pos = e.target.getStage().getPointerPosition();
      this.newAnnotation.bottom_right_x = pos.x;
      this.newAnnotation.bottom_right_y = pos.y;
    },
    handleMouseUp() {
      if (!this.isDrawing || !this.newAnnotation) return;
      
      // Prevent creating tiny boxes on click
      if (Math.abs(this.newAnnotation.width) < 5 || Math.abs(this.newAnnotation.height) < 5) {
          this.newAnnotation = null;
          return;
      }
      
      ElMessageBox.prompt('请输入标注备注', '新增标注', {
        confirmButtonText: '保存',
        cancelButtonText: '取消',
        inputPattern: /.*/,
        inputErrorMessage: '',
      }).then(({ value }) => {
        this.saveAnnotation(value);
      }).catch(() => {
        ElMessage.info('取消标注');
        this.newAnnotation = null;
      });
      
      this.isDrawing = false;
    },
    async saveAnnotation(note) {
      const imageId = this.currentImageIdForAnnotation;
      if (!imageId || !this.newAnnotation) return;
      
      const payload = {
          image_id: imageId,
          anno_type: 'bbox',
          note: note,
          up_left_x: Math.min(this.newAnnotation.up_left_x, this.newAnnotation.bottom_right_x),
          up_left_y: Math.min(this.newAnnotation.up_left_y, this.newAnnotation.bottom_right_y),
          bottom_right_x: Math.max(this.newAnnotation.up_left_x, this.newAnnotation.bottom_right_x),
          bottom_right_y: Math.max(this.newAnnotation.up_left_y, this.newAnnotation.bottom_right_y),
      };
      
      try {
        const res = await addAnnotation(payload);
        if (res.code === 201) {
            ElMessage.success('标注成功');
            this.newAnnotation = null;
            if(this.showAnnotations) {
              this.fetchAnnotations();
              // 标注成功后，重新获取影像信息以更新滑块标记
              this.fetchImageData(this.currentDirection);
            }
        } else {
            ElMessage.error(res.message);
        }
      } catch (error) {
          console.error(error);
          ElMessage.error('标注失败');
      }
    },
    async deleteAnnotation(annoId) {
        try {
            await ElMessageBox.confirm('确定要删除这条标注吗?', '警告', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning',
            });
            
            const res = await deleteAnnotation({ anno_id: annoId, anno_type: 'bbox' });
            if (res.code === 200) {
                ElMessage.success('删除成功');
                this.fetchAnnotations();
                // 标注删除后，重新获取影像信息以更新滑块标记
                this.fetchImageData(this.currentDirection);
            } else {
                ElMessage.error(res.message);
            }
        } catch (error) {
            // Catches MessageBox cancel
            if (error !== 'cancel') {
                ElMessage.error('删除失败');
                console.error(error);
            }
        }
    },
    handleAnnotationMouseOver(e) {
      if (!this.isDrawing) {
        e.target.getStage().container().style.cursor = 'pointer';
      }
    },
    handleAnnotationMouseOut(e) {
      if (!this.isDrawing) {
        e.target.getStage().container().style.cursor = 'default';
      }
    },
    handleAnnotationClick(anno) {
      if (this.isDrawing) return;
      this.deleteAnnotation(anno.id);
    }
  },
}
</script>

<style scoped>
.image-preview-container {
  font-family: 'Helvetica Neue', Arial, sans-serif;
  color: #606266;
  background-color: #fff;
  border-radius: 4px;
  padding: 20px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
  margin: auto;
  width: 96%;
}

.loading, .error {
  text-align: center;
  padding: 40px;
  font-size: 1.2em;
}

.error {
  color: #f56c6c;
}

.preview-content {
  display: flex;
  gap: 20px;
}

.image-display-area {
  flex: 3;
  display: flex;
  flex-direction: column;
}

.info-panel {
  flex: 2;
  background-color: #f5f7fa;
  padding: 15px;
  border-radius: 4px;
  border: 1px solid #ebeef5;
}

.image-frame {
  background-color: #000;
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  height: 400px; /* Fixed height for consistency */
  border-radius: 4px;
  overflow: hidden;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  position: relative; /* Needed for overlay positioning */
}

.preview-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.image-frame img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.image-frame .placeholder {
  color: #fff;
}

.canvas-loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.7);
  color: white;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  z-index: 10;
  border-radius: 4px;
}

.loading-spinner {
  border: 4px solid #f3f3f3;
  border-top: 4px solid #409EFF;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin-bottom: 15px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Controls */
.controls-3d {
  margin-top: 15px;
  background-color: #f5f7fa;
  padding: 15px;
  border-radius: 4px;
  border: 1px solid #ebeef5;
}

.direction-selector {
  margin-bottom: 15px;
}

.direction-selector span {
  font-weight: bold;
  margin-right: 10px;
  color: #303133;
}

.direction-selector button {
  background-color: #fff;
  border: 1px solid #dcdfe6;
  padding: 8px 15px;
  cursor: pointer;
  border-radius: 4px;
  margin-right: 5px;
  transition: all 0.3s;
  color: #606266;
  font-size: 14px;
}

.direction-selector button:hover {
  color: #409EFF;
  border-color: #c6e2ff;
  background-color: #ecf5ff;
}

.direction-selector button.active {
  background-color: #409EFF;
  color: white;
  border-color: #409EFF;
}

.slice-slider {
  display: flex;
  align-items: center;
  gap: 15px;
}

.slice-slider label {
  white-space: nowrap;
  color: #303133;
}

.slice-input {
  width: 100px;
}

.slice-count {
  white-space: nowrap;
  min-width: 60px;
  text-align: right;
}

.slider {
  width: 100%;
  cursor: pointer;
  height: 6px;
  -webkit-appearance: none;
  background-color: #e4e7ed;
  border-radius: 3px;
  flex-grow: 1;
}

.slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background-color: #409EFF;
  cursor: pointer;
  border: none;
}

.slider::-moz-range-thumb {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background-color: #409EFF;
  cursor: pointer;
  border: none;
}

/* Info Panel */
.info-panel h3 {
  margin-top: 0;
  border-bottom: 1px solid #ebeef5;
  padding-bottom: 10px;
  margin-bottom: 15px;
  color: #303133;
  font-weight: 500;
}

.info-panel ul {
  list-style-type: none;
  padding: 0;
  margin: 0 0 20px 0;
}

.info-panel li {
  padding: 10px 0;
  border-bottom: 1px solid #ebeef5;
  font-size: 14px;
}

.info-panel li:last-child {
  border-bottom: none;
}

.info-panel strong {
  color: #303133;
  font-weight: 500;
}

.download-button {
  display: inline-block;
  background-color: #409EFF;
  color: white;
  padding: 10px 15px;
  text-decoration: none;
  border-radius: 4px;
  text-align: center;
  transition: background-color 0.3s;
  width: 100%;
  box-sizing: border-box;
  font-size: 14px;
}

.download-button:hover {
  background-color: #66b1ff;
}

/* Responsive */
@media (max-width: 768px) {
  .preview-content {
    flex-direction: column;
  }
  
  .image-frame {
    height: 300px;
  }
}

.image-frame.drawing-cursor {
  cursor: crosshair;
}

.annotation-section {
  margin-top: 20px;
  padding-top: 15px;
  border-top: 1px solid #ebeef5;
}

.annotation-section h3 {
  margin-bottom: 10px;
}

.anno-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.anno-list h4 {
  margin-top: 10px;
  margin-bottom: 5px;
  font-weight: 500;
}

.anno-list ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.anno-list li {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px;
  border-left: 4px solid;
  background-color: #fff;
  margin-bottom: 5px;
  border-radius: 2px;
}

.anno-note {
  flex-grow: 1;
}

.action-controls {
  margin-top: 15px;
  display: flex;
  gap: 10px;
}

.ai-seg-control {
  margin-top: 15px;
}
</style>
