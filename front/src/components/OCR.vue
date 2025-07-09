<template>
  <el-dialog 
    v-model="visible" 
    title="图片文字识别" 
    width="900px"
    :before-close="handleClose"
    @closed="handleClosed"
  >
    <div class="ocr-container">
      <!-- 左侧图片显示区域 -->
      <div class="image-section">
        <div class="image-wrapper">
          <el-image
            :src="imageUrl"
            fit="contain"
            class="ocr-image"
            :preview-src-list="[imageUrl]"
          >
            <template #error>
              <div class="image-error">
                <el-icon><PictureFilled /></el-icon>
                <span>图片加载失败</span>
              </div>
            </template>
          </el-image>
        </div>
      </div>

      <!-- 右侧文字识别结果区域 -->
      <div class="text-section">
        <div class="section-header">
          <h4>识别结果</h4>
          <div class="header-actions">
            <el-button 
              v-if="!loading && recognizedText" 
              type="primary" 
              size="small" 
              @click="copyText"
              :icon="DocumentCopyIcon"
            >
              复制文字
            </el-button>
            <el-button 
              v-if="!loading && recognizedText" 
              type="success" 
              size="small" 
              @click="useRecognizedText"
            >
              使用此文字
            </el-button>
          </div>
        </div>

        <div class="text-content">
          <!-- 加载状态 -->
          <div v-if="loading" class="loading-state">
            <el-icon class="loading-icon"><Loading /></el-icon>
            <p>正在识别文字，请稍后...</p>
          </div>

          <!-- 错误状态 -->
          <div v-else-if="error" class="error-state">
            <el-icon class="error-icon"><WarningFilled /></el-icon>
            <p>{{ error }}</p>
            <el-button type="primary" @click="startRecognition">重试识别</el-button>
          </div>

          <!-- 识别结果 -->
          <div v-else-if="recognizedText" class="result-content">
            <!-- Markdown预览 -->
            <div class="markdown-preview" v-html="renderedMarkdown"></div>
            
            <!-- 原始文本（隐藏） -->
            <textarea 
              ref="textareaRef" 
              v-model="recognizedText" 
              style="position: absolute; left: -9999px; opacity: 0;"
              readonly
            ></textarea>
          </div>

          <!-- 初始状态 -->
          <div v-else class="initial-state">
            <el-icon class="initial-icon"><Document /></el-icon>
            <p>点击"开始识别"按钮开始文字识别</p>
            <el-button type="primary" @click="startRecognition">开始识别</el-button>
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">关闭</el-button>
        <el-button 
          v-if="!loading" 
          type="primary" 
          @click="startRecognition"
          :disabled="!imageUrl"
        >
          重新识别
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script>
import { ref, computed, nextTick, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  PictureFilled, Loading, WarningFilled, Document, DocumentCopy 
} from '@element-plus/icons-vue'
import { marked } from 'marked'
import { analyzeImage } from '@/api/knowledge'
import MarkdownIt from 'markdown-it'

export default {
  name: 'OCR',
  components: {
    PictureFilled, Loading, WarningFilled, Document, DocumentCopy
  },
  props: {
    modelValue: {
      type: Boolean,
      default: false
    },
    imageUrl: {
      type: String,
      required: true
    }
  },
  emits: ['update:modelValue', 'text-recognized'],
  setup(props, { emit }) {
    // Icon for the template
    const DocumentCopyIcon = DocumentCopy;

    // Responsive data
    const visible = ref(false)
    const loading = ref(false)
    const error = ref('')
    const recognizedText = ref('')
    const textareaRef = ref(null)
    const md = new MarkdownIt(); // Initialize markdown-it

    // 计算属性 - Markdown渲染
    const renderedMarkdown = computed(() => {
      if (!recognizedText.value) return ''
      try {
        return md.render(recognizedText.value); // Use markdown-it
      } catch (e) {
        // Fallback for safety, though markdown-it is generally robust
        return recognizedText.value.replace(/\n/g, '<br>');
      }
    })

    // 监听modelValue变化
    watch(() => props.modelValue, (newVal) => {
      visible.value = newVal
      if (newVal && props.imageUrl) {
        // 自动开始识别
        nextTick(() => {
          startRecognition()
        })
      }
    })

    // 监听visible变化
    watch(visible, (newVal) => {
      emit('update:modelValue', newVal)
    })

    // 开始文字识别
    const startRecognition = async () => {
      if (!props.imageUrl) {
        ElMessage.error('图片地址无效')
        return
      }

      try {
        loading.value = true
        error.value = ''
        recognizedText.value = ''

        // 调用AI分析接口，直接传递URL
        const requestData = {
          imageData: props.imageUrl,
          imageType: 'url',
          temperature: 0.3,
          maxTokens: 10000,
          stream: false
        }

        const response = await analyzeImage(requestData)
        
        if (response.code === 200 && response.data) {
          recognizedText.value = response.data.content || response.data.analysisResult || '未识别到文字内容'
          ElMessage.success('文字识别完成')
        } else {
          throw new Error(response.message || '识别失败')
        }
      } catch (err) {
        console.error('文字识别失败:', err)
        error.value = err.message || '文字识别失败，请重试'
        ElMessage.error(error.value)
      } finally {
        loading.value = false
      }
    }

    // 复制文字
    const copyText = async () => {
      if (!recognizedText.value) return
      
      try {
        await navigator.clipboard.writeText(recognizedText.value)
        ElMessage.success('文字已复制到剪贴板')
      } catch (err) {
        // 降级方案
        try {
          textareaRef.value.select()
          document.execCommand('copy')
          ElMessage.success('文字已复制到剪贴板')
        } catch (fallbackErr) {
          ElMessage.error('复制失败，请手动复制')
        }
      }
    }

    // 使用识别的文字
    const useRecognizedText = () => {
      if (!recognizedText.value) return
      
      emit('text-recognized', recognizedText.value)
      ElMessage.success('已应用识别的文字')
      handleClose()
    }

    // 关闭对话框
    const handleClose = () => {
      visible.value = false
    }

    // 对话框关闭后的清理
    const handleClosed = () => {
      loading.value = false
      error.value = ''
      recognizedText.value = ''
    }

    return {
      visible,
      loading,
      error,
      recognizedText,
      renderedMarkdown,
      textareaRef,
      startRecognition,
      copyText,
      useRecognizedText,
      handleClose,
      handleClosed,
      DocumentCopyIcon
    }
  }
}
</script>

<style scoped>
.ocr-container {
  display: flex;
  height: 60vh;
  min-height: 400px;
  gap: 20px;
}

/* 左侧图片区域 */
.image-section {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.image-wrapper {
  flex: 1;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  overflow: hidden;
  background: #f8f9fa;
}

.ocr-image {
  width: 100%;
  height: 100%;
}

.image-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #909399;
}

.image-error .el-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

/* 右侧文字区域 */
.text-section {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e4e7ed;
}

.section-header h4 {
  margin: 0;
  color: #303133;
  font-size: 16px;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.text-content {
  flex: 1;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* 各种状态样式 */
.loading-state,
.error-state,
.initial-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  color: #606266;
}

.loading-state .loading-icon {
  font-size: 32px;
  color: #409eff;
  animation: rotate 2s linear infinite;
  margin-bottom: 12px;
}

.error-state .error-icon {
  font-size: 32px;
  color: #f56c6c;
  margin-bottom: 12px;
}

.initial-state .initial-icon {
  font-size: 32px;
  color: #909399;
  margin-bottom: 12px;
}

.loading-state p,
.error-state p,
.initial-state p {
  margin: 0 0 16px 0;
  text-align: center;
}

/* 结果内容 */
.result-content {
  flex: 1;
  overflow: auto;
}

.markdown-preview {
  padding: 20px;
  line-height: 1.6;
  color: #303133;
  overflow: auto;
  max-height: 100%;
  box-sizing: border-box;
}

.markdown-preview h1,
.markdown-preview h2,
.markdown-preview h3,
.markdown-preview h4,
.markdown-preview h5,
.markdown-preview h6 {
  margin: 16px 0 8px 0;
  color: #409eff;
}

.markdown-preview p {
  margin: 8px 0;
}

.markdown-preview ul,
.markdown-preview ol {
  margin: 8px 0;
  padding-left: 20px;
}

.markdown-preview code {
  background: #f1f2f3;
  padding: 2px 4px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
}

.markdown-preview pre {
  background: #f6f8fa;
  padding: 12px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 12px 0;
}

.markdown-preview blockquote {
  border-left: 3px solid #409eff;
  padding-left: 12px;
  margin: 12px 0;
  color: #606266;
}

/* 对话框底部 */
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* 动画 */
@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .ocr-container {
    flex-direction: column;
    height: auto;
    min-height: 300px;
  }
  
  .image-section,
  .text-section {
    flex: none;
  }
  
  .image-wrapper {
    height: 200px;
  }
  
  .text-content {
    height: 300px;
  }
  
  .section-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .header-actions {
    width: 100%;
    justify-content: space-between;
  }
}

/* 对话框样式优化 */
:deep(.el-dialog) {
  border-radius: 12px;
}

:deep(.el-dialog__header) {
  background: linear-gradient(135deg, #409eff, #36cfc9);
  color: white;
  padding: 20px 30px;
  border-radius: 12px 12px 0 0;
}

:deep(.el-dialog__title) {
  color: white;
  font-weight: 600;
}

:deep(.el-dialog__headerbtn .el-dialog__close) {
  color: white;
}

:deep(.el-dialog__body) {
  padding: 20px 30px;
}

:deep(.el-dialog__footer) {
  padding: 20px 30px;
  background: #f8f9fa;
  border-radius: 0 0 12px 12px;
}
</style>
