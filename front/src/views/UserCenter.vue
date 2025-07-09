<template>
  <div class="user-center">
    <div class="user-center-container">
      <!-- 头像区域 -->
      <div class="avatar-section">
        <div class="avatar-wrapper">
          <el-avatar 
            :size="120" 
            :src="'https://cdn.ember.ac.cn/hidoc/avatar/default_avatar.png'" 
            class="user-avatar"
          >
            <el-icon><User /></el-icon>
          </el-avatar>
        </div>
        <h2 class="user-nickname">{{ userInfo.name || '用户' }}</h2>
        <p class="user-phone">{{ userInfo.phone }}</p>
      </div>

      <!-- 用户信息区域 -->
      <div class="info-section">
          <div class="section-header">
            <div class="title-area">
              <h3>个人信息</h3>
              <span class="info-description">您的个人信息仅用于系统识别</span>
            </div>
            <div class="action-buttons">
            <el-button 
              v-if="!isEditing"
              type="primary" 
              size="small" 
              @click="toggleEditMode"
            >
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
            <template v-else>
              <el-button 
                type="primary" 
                size="small" 
                @click="saveUserInfo"
              >
                <el-icon><Check /></el-icon>
                保存
              </el-button>
              <el-button 
                size="small" 
                @click="cancelEdit"
              >
                <el-icon><Close /></el-icon>
                取消
              </el-button>
            </template>
          </div>
        </div>

        <div class="info-grid">
          <!-- 用户名 -->
          <div class="info-item">
            <label class="info-label">姓名</label>
            <div class="info-value">
              <el-input 
                v-if="isEditing" 
                v-model="editForm.name" 
                placeholder="请输入姓名"
                maxlength="64"
                show-word-limit
              />
              <span v-else class="display-value">{{ userInfo.name }}</span>
            </div>
          </div>

          <!-- 手机号 -->
          <div class="info-item">
            <label class="info-label">手机号</label>
            <div class="info-value">
              <span class="display-value">{{ userInfo.phone }}</span>
              <el-tag size="small" type="info">不可修改</el-tag>
            </div>
          </div>

          <!-- 性别 -->
          <div class="info-item">
            <label class="info-label">性别</label>
            <div class="info-value">
              <el-select 
                v-if="isEditing" 
                v-model="editForm.gender" 
                placeholder="请选择性别"
              >
                <el-option label="未知" value="未知" />
                <el-option label="男" value="男" />
                <el-option label="女" value="女" />
              </el-select>
              <span v-else class="display-value">{{ userInfo.gender }}</span>
            </div>
          </div>

          <!-- 注册时间 -->
          <div class="info-item">
            <label class="info-label">注册时间</label>
            <div class="info-value">
              <span class="display-value">{{ formatDateTime(userInfo.created_at) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { User, Edit, Check, Close } from '@element-plus/icons-vue'
import { getUserInfo, editUserInfo } from '@/api/user'

export default {
  name: 'UserCenter',
  components: {
    User,
    Edit,
    Check,
    Close
  },
  mounted() {
    document.title = '用户中心 - HiDoc'
  },
  setup() {
    const userInfo = reactive({
      id: null,
      name: '',
      phone: '',
      gender: '',
      created_at: ''
    })

    const editForm = reactive({
      name: '',
      gender: ''
    })

    const isEditing = ref(false)
    const loading = ref(false)

    // 获取用户信息
    const fetchUserInfo = async () => {
      try {
        loading.value = true
        const response = await getUserInfo()
        if (response.code === 200) {
          Object.assign(userInfo, response.data)
          // 初始化编辑表单
          editForm.name = userInfo.name
          editForm.gender = userInfo.gender
        } else {
          ElMessage.error(response.message || '获取用户信息失败')
        }
      } catch (error) {
        console.error('获取用户信息失败:', error)
        ElMessage.error('获取用户信息失败')
      } finally {
        loading.value = false
      }
    }

    // 切换编辑模式
    const toggleEditMode = () => {
      // 进入编辑模式
      isEditing.value = true
    }

    // 保存用户信息
    const saveUserInfo = async () => {
      try {
        loading.value = true
        const response = await editUserInfo(editForm)
        if (response.code === 200) {
          Object.assign(userInfo, response.data)
          isEditing.value = false
          ElMessage.success('用户信息更新成功')
        } else {
          ElMessage.error(response.message || '更新失败')
        }
      } catch (error) {
        console.error('更新用户信息失败:', error)
        ElMessage.error('更新用户信息失败')
      } finally {
        loading.value = false
      }
    }

    // 格式化日期时间
    const formatDateTime = (dateTime) => {
      if (!dateTime) return '未知'
      return dateTime
    }

    // 取消编辑
    const cancelEdit = () => {
      // 重置表单数据到当前用户信息
      editForm.name = userInfo.name
      editForm.gender = userInfo.gender
      // 退出编辑模式
      isEditing.value = false
      ElMessage.info('已取消编辑')
    }

    onMounted(() => {
      fetchUserInfo()
    })

    return {
      userInfo,
      editForm,
      isEditing,
      loading,
      toggleEditMode,
      saveUserInfo,
      formatDateTime,
      cancelEdit
    }
  }
}
</script>

<style scoped>
.user-center {
  min-height: calc(100vh - 120px); /* 减去头部和内边距的高度 */
  padding: 20px;
  margin: -20px; /* 抵消父容器的 padding */
}

.user-center-container {
  max-width: 900px;
  margin: 0 auto;
  background: white;
  border-radius: 12px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
  overflow: hidden;
}

/* 头像区域 */
.avatar-section {
  text-align: center;
  padding: 40px 20px;
  background: linear-gradient(135deg, #099c6b 0%, #05f1d2 100%);
  color: white;
  position: relative;
}

.avatar-wrapper {
  position: relative;
  display: inline-block;
  margin-bottom: 20px;
}

.user-avatar {
  border: 4px solid rgba(255, 255, 255, 0.3);
}

.user-nickname {
  margin: 0 0 8px 0;
  font-size: 28px;
  font-weight: 600;
}

.user-phone {
  margin: 0;
  opacity: 0.8;
  font-size: 14px;
}

/* 信息区域 */
.info-section {
  padding: 30px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding-bottom: 15px;
  border-bottom: 2px solid #f0f0f0;
}

.section-header h3 {
  margin: 0;
  font-size: 20px;
  color: #303133;
  font-weight: 600;
}

.title-area {
  display: flex;
  align-items: baseline;
  gap: 10px;
}

.info-description {
  margin: 0;
  font-size: 12px;
  color: #909399;
  font-weight: normal;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 25px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.info-label {
  font-weight: 600;
  color: #606266;
  font-size: 14px;
}

.info-value {
  display: flex;
  align-items: center;
  gap: 10px;
}

.display-value {
  color: #303133;
  font-size: 15px;
  padding: 8px 0;
  flex: 1; /* 让显示值占据剩余空间 */
}

.el-tag {
  flex-shrink: 0; /* 防止标签被压缩 */
}

/* 响应式设计 */
@media (max-width: 768px) {
  .user-center {
    padding: 10px;
    margin: -20px -20px; /* 移动端也要抵消父容器padding */
  }
  
  .avatar-section {
    padding: 30px 15px;
  }
  
  .info-section {
    padding: 20px 15px;
  }
  
  .info-grid {
    grid-template-columns: 1fr;
    gap: 20px;
  }
  
  .section-header {
    flex-direction: column;
    gap: 15px;
    align-items: stretch;
  }
  
  .action-buttons {
    margin-top: 10px;
    justify-content: flex-end;
  }
}

.action-buttons {
  display: flex;
  gap: 10px;
}
</style>
