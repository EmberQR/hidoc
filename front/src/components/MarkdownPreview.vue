<template>
  <el-dialog
    v-model="dialogVisible"
    title="文字识别结果"
    width="800px"
    :before-close="handleClose"
    class="markdown-preview-dialog"
  >
    <div class="markdown-preview-container">
      <div v-if="loading" class="loading-wrapper">
        <el-skeleton :rows="10" animated />
      </div>
      <div v-else class="markdown-content" v-html="renderedContent"></div>
    </div>
    <template #footer>
      <el-button @click="dialogVisible = false">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script>
import { ref, computed, watch, onMounted } from 'vue'
import MarkdownIt from 'markdown-it'

export default {
  name: 'MarkdownPreview',
  props: {
    modelValue: {
      type: Boolean,
      default: false
    },
    content: {
      type: String,
      default: ''
    }
  },
  emits: ['update:modelValue'],
  setup(props, { emit }) {
    const dialogVisible = computed({
      get: () => props.modelValue,
      set: (value) => emit('update:modelValue', value)
    })

    const loading = ref(true)
    const md = new MarkdownIt({
      html: true,
      linkify: true,
      typographer: true,
      breaks: true
    })

    const renderedContent = ref('')

    const renderMarkdown = () => {
      if (!props.content) {
        renderedContent.value = '<p>无内容</p>'
        return
      }
      
      loading.value = true
      try {
        renderedContent.value = md.render(props.content)
      } catch (error) {
        console.error('Markdown 渲染错误:', error)
        renderedContent.value = '<p class="error">内容渲染失败</p>'
      } finally {
        loading.value = false
      }
    }

    const handleClose = () => {
      dialogVisible.value = false
    }

    watch(() => props.content, () => {
      renderMarkdown()
    }, { immediate: true })

    watch(() => props.modelValue, (newVal) => {
      if (newVal) {
        renderMarkdown()
      }
    })

    onMounted(() => {
      // 初始渲染
      if (props.modelValue && props.content) {
        renderMarkdown()
      }
      
      // 短暂延迟后结束加载状态，防止闪烁
      setTimeout(() => {
        loading.value = false
      }, 300)
    })

    return {
      dialogVisible,
      loading,
      renderedContent,
      handleClose
    }
  }
}
</script>

<style scoped>
.markdown-preview-container {
  max-height: 70vh;
  overflow-y: auto;
  padding: 0 10px;
}

.markdown-content {
  font-size: 14px;
  line-height: 1.6;
  color: #303133;
  overflow-x: auto;
}

.loading-wrapper {
  padding: 20px 0;
}

:deep(.markdown-content h1) {
  font-size: 1.8em;
  margin-top: 16px;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #eaecef;
}

:deep(.markdown-content h2) {
  font-size: 1.5em;
  margin-top: 14px;
  margin-bottom: 10px;
  padding-bottom: 6px;
  border-bottom: 1px solid #eaecef;
}

:deep(.markdown-content h3) {
  font-size: 1.3em;
  margin-top: 12px;
  margin-bottom: 8px;
}

:deep(.markdown-content h4) {
  font-size: 1.1em;
  margin-top: 10px;
  margin-bottom: 6px;
}

:deep(.markdown-content p) {
  margin: 8px 0;
}

:deep(.markdown-content ul, .markdown-content ol) {
  padding-left: 20px;
}

:deep(.markdown-content li) {
  margin: 4px 0;
}

:deep(.markdown-content code) {
  padding: 2px 4px;
  background-color: #f6f8fa;
  border-radius: 3px;
  font-family: monospace;
  font-size: 0.9em;
}

:deep(.markdown-content pre) {
  padding: 16px;
  overflow: auto;
  background-color: #f6f8fa;
  border-radius: 6px;
  margin: 12px 0;
}

:deep(.markdown-content pre code) {
  background-color: transparent;
  padding: 0;
}

:deep(.markdown-content blockquote) {
  padding: 0 16px;
  color: #6a737d;
  border-left: 4px solid #dfe2e5;
  margin: 12px 0;
}

:deep(.markdown-content table) {
  border-collapse: collapse;
  width: 100%;
  margin: 12px 0;
  display: block;
  overflow-x: auto;
}

:deep(.markdown-content table th, .markdown-content table td) {
  border: 1px solid #dfe2e5;
  padding: 8px 12px;
  text-align: left;
}

:deep(.markdown-content table th) {
  background-color: #f6f8fa;
}

:deep(.markdown-content img) {
  max-width: 100%;
  height: auto;
}

:deep(.markdown-content hr) {
  height: 1px;
  background-color: #e1e4e8;
  border: none;
  margin: 16px 0;
}

:deep(.markdown-content a) {
  color: #409eff;
  text-decoration: none;
}

:deep(.markdown-content a:hover) {
  text-decoration: underline;
}

:deep(.error) {
  color: #f56c6c;
  font-style: italic;
}

/* 对话框样式，匹配KbView中的样式 */
:deep(.el-dialog) {
  border-radius: 12px;
  padding: 0;
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
  padding: 30px;
}

:deep(.el-dialog__footer) {
  padding: 20px 30px;
  background: #f8f9fa;
  border-radius: 0 0 12px 12px;
}
</style>
