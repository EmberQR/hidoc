<template>
  <div class="navbar-container" :class="{ 'is-collapsed': isCollapsed }">
    <!-- 顶部Logo区域 -->
    <div class="logo-container">
      <img src="https://cdn.ember.ac.cn/hidoc/logo/hidoc.png" alt="HiDoc Logo" class="logo-image" v-if="!isCollapsed" />
      <img src="https://cdn.ember.ac.cn/hidoc/logo/hidoc_small.png" alt="HiDoc Logo" class="logo-small" v-else />
      <el-icon class="toggle-button" @click="toggleCollapse">
        <fold v-if="!isCollapsed" />
        <expand v-else />
      </el-icon>
    </div>

    <!-- 导航菜单 -->
    <el-scrollbar class="menu-scrollbar">
      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapsed"
        :collapse-transition="false"
        :unique-opened="true"
        class="nav-menu"
        text-color="#303133"
        active-text-color="#409EFF"
        background-color="transparent"
      >
        <el-menu-item index="dashboard" @click="navigateTo('/')">
          <el-icon><HomeFilled /></el-icon>
          <template #title>首页</template>
        </el-menu-item>

        <el-menu-item index="patient" @click="navigateTo('/patient')">
          <el-icon><User /></el-icon>
          <template #title>病人管理</template>
        </el-menu-item>

        <el-menu-item index="case" @click="navigateTo('/case')">
          <el-icon><DocumentAdd /></el-icon>
          <template #title>病历管理</template>
        </el-menu-item>

        <el-menu-item index="image" @click="navigateTo('/image')">
          <el-icon><Picture /></el-icon>
          <template #title>影像管理</template>
        </el-menu-item>

        <!-- <el-menu-item index="statistics" @click="navigateTo('/statistics')">
          <el-icon><TrendCharts /></el-icon>
          <template #title>统计分析</template>
        </el-menu-item>

        <el-menu-item index="settings" @click="navigateTo('/settings')">
          <el-icon><Setting /></el-icon>
          <template #title>系统设置</template>
        </el-menu-item> -->
      </el-menu>
    </el-scrollbar>

    <!-- 底部用户信息 -->
    <div class="user-container">
      <div class="user-info" v-if="!isCollapsed">
        <div class="avatar-wrapper">
          <el-avatar :size="44" :src="userAvatar" class="user-avatar"></el-avatar>
          <div class="gender-badge" :class="genderClass" v-if="userGender !== '未知'">
            <el-icon v-if="userGender === '男'"><Male /></el-icon>
            <el-icon v-else-if="userGender === '女'"><Female /></el-icon>
          </div>
        </div>
        <div class="user-details">
          <div class="user-name">{{ userName }}</div>
          <el-dropdown trigger="click" @command="handleCommand">
            <span class="user-role">
              {{ userRole }}
              <el-icon class="el-icon--right"><arrow-down /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">个人信息</el-dropdown-item>
                <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
      <div class="user-collapsed" v-else>
        <el-dropdown trigger="click" @command="handleCommand">
          <div class="avatar-wrapper">
            <el-avatar :size="40" :src="userAvatar" class="user-avatar"></el-avatar>
            <div class="gender-badge small" :class="genderClass" v-if="userGender !== '未知'">
              <el-icon v-if="userGender === '男'"><Male /></el-icon>
              <el-icon v-else-if="userGender === '女'"><Female /></el-icon>
            </div>
          </div>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="profile">个人信息</el-dropdown-item>
              <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
      
      <!-- 版权信息 -->
      <div class="copyright" v-if="!isCollapsed">
        © 2025 HiDoc 智能影像辅诊系统
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { 
  HomeFilled, User, Setting, Fold, Expand, List, Plus, DocumentAdd, Clock, 
  Folder, TrendCharts, ArrowDown, Male, Female, ChatDotRound, Management, Picture
} from '@element-plus/icons-vue'
import { getStoredUserInfo, clearUserInfo } from '@/utils/auth'
import { logout, getUserInfo } from '@/api/user'
import { ElMessage, ElMessageBox } from 'element-plus'

// 临时图标组件，后续需替换为实际图标库
const Stethoscope = HomeFilled

export default {
  name: 'NavBar',
  components: {
    HomeFilled, User, Setting, Fold, Expand, List, Plus, DocumentAdd, 
    Clock, Folder, TrendCharts, ArrowDown, Male, Female, Stethoscope, ChatDotRound, Picture
  },
  setup() {
    const router = useRouter()
    const route = useRoute()
    
    // 菜单折叠状态
    const isCollapsed = ref(false)
    
    // 当前激活的菜单项
    const activeMenu = computed(() => {
      const { path } = route
      
      if (path === '/') return 'dashboard'
      if (path.startsWith('/patient')) return 'patient'
      if (path.startsWith('/case')) return 'case'
      if (path.startsWith('/statistics')) return 'statistics'
      if (path.startsWith('/settings')) return 'settings'
      if (path.startsWith('/image')) return 'image'
      
      return 'dashboard'
    })
    
    // 用户信息
    const userInfo = ref(null)
    const userName = computed(() => userInfo.value?.name || '未登录用户')
    const userRole = computed(() => {
      // 从本地存储获取当前医院信息
      const hospitalInfo = localStorage.getItem('currentHospital')
      if (hospitalInfo) {
        try {
          const hospital = JSON.parse(hospitalInfo)
          return hospital.name || '医生'
        } catch (e) {
          return '医生'
        }
      }
      return '医生'
    })
    const userAvatar = computed(() => 'https://cdn.ember.ac.cn/hidoc/avatar/default_avatar.png')
    const userGender = computed(() => userInfo.value?.gender || '未知')
    const genderClass = computed(() => {
      if (userGender.value === '男') return 'male'
      if (userGender.value === '女') return 'female'
      return ''
    })
    
    // 折叠/展开菜单
    const toggleCollapse = () => {
      isCollapsed.value = !isCollapsed.value
    }
    
    // 跳转页面
    const navigateTo = (path) => {
      router.push(path)
    }
    
    // 处理下拉菜单命令
    const handleCommand = (command) => {
      if (command === 'profile') {
        router.push('/profile')
      } else if (command === 'logout') {
        ElMessageBox.confirm('确定要退出登录吗?', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
          .then(() => {
            logout().then(() => {
              clearUserInfo()
              localStorage.removeItem('currentHospital')
              ElMessage.success('退出登录成功')
              router.push('/login')
            }).catch(() => {
              // 即使后端接口失败，也清除本地登录状态
              clearUserInfo()
              localStorage.removeItem('currentHospital')
              router.push('/login')
            })
          })
          .catch(() => {})
      }
    }
    
    // 获取用户信息
    const fetchUserInfo = async () => {
      try {
        const response = await getUserInfo()
        if (response.code === 200) {
          userInfo.value = response.data
        } else {
          // 如果API调用失败，尝试从本地存储获取
          userInfo.value = getStoredUserInfo()
        }
      } catch (error) {
        console.error('获取用户信息失败:', error)
        // 如果API调用失败，尝试从本地存储获取
        userInfo.value = getStoredUserInfo()
      }
    }
    
    // 获取用户信息
    onMounted(() => {
      fetchUserInfo()
    })
    
    return {
      isCollapsed,
      activeMenu,
      userInfo,
      userName,
      userRole,
      userAvatar,
      userGender,
      genderClass,
      toggleCollapse,
      navigateTo,
      handleCommand
    }
  }
}
</script>

<style scoped>
.navbar-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 240px;
  transition: width 0.3s;
  background: linear-gradient(to bottom, #f5f7fa, #f0f3f8);
  box-shadow: 2px 0 10px rgba(0, 0, 0, 0.05);
  position: relative;
}

.navbar-container.is-collapsed {
  width: 64px;
}

/* Logo区域样式 */
.logo-container {
  height: 60px;
  padding: 10px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.logo-image {
  height: 32px;
  margin-left: 8px;
}

.logo-small {
  width: 32px;
  height: 32px;
  margin: 0 auto;
}

.toggle-button {
  font-size: 20px;
  cursor: pointer;
  color: #909399;
  transition: color 0.3s;
}

.toggle-button:hover {
  color: #409EFF;
}

/* 菜单区域样式 */
.menu-scrollbar {
  flex: 1;
  overflow: hidden;
}

.nav-menu {
  border-right: none;
}

.nav-menu :deep(.el-menu-item),
.nav-menu :deep(.el-sub-menu__title) {
  height: 50px;
  line-height: 50px;
  margin: 4px 0;
  border-radius: 8px;
  margin-right: 8px;
  margin-left: 8px;
}

.nav-menu :deep(.el-menu-item.is-active) {
  background: rgba(64, 158, 255, 0.1);
  color: #409EFF;
  font-weight: 500;
}

.nav-menu :deep(.el-menu-item:hover),
.nav-menu :deep(.el-sub-menu__title:hover) {
  background: rgba(0, 0, 0, 0.03);
}

.nav-menu :deep(.el-menu-item) .el-icon,
.nav-menu :deep(.el-sub-menu__title) .el-icon {
  margin-right: 10px;
  font-size: 18px;
}

/* 折叠菜单样式调整 */
.navbar-container.is-collapsed .nav-menu:not(.el-menu--collapse) {
  width: 64px;
}

/* 用户信息区域 */
.user-container {
  padding: 16px;
  border-top: 1px solid rgba(0, 0, 0, 0.05);
  background: rgba(255, 255, 255, 0.5);
}

.user-info {
  display: flex;
  align-items: center;
}

.avatar-wrapper {
  position: relative;
}

.user-avatar {
  flex-shrink: 0;
  border: 2px solid #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.gender-badge {
  position: absolute;
  bottom: -2px;
  right: -2px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  border: 2px solid #fff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.gender-badge .el-icon {
  font-size: 12px;
  line-height: 1;
}

.gender-badge.small {
  width: 16px;
  height: 16px;
  bottom: -1px;
  right: -1px;
}

.gender-badge.small .el-icon {
  font-size: 10px;
}

.gender-badge.male {
  background-color: #87CEEB; /* 浅蓝色 */
}

.gender-badge.female {
  background-color: #FFB6C1; /* 浅粉色 */
}

.user-details {
  margin-left: 12px;
  overflow: hidden;
}

.user-name {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 3px;
}

.user-role {
  font-size: 12px;
  color: #909399;
  display: flex;
  align-items: center;
  cursor: pointer;
}

.user-collapsed {
  display: flex;
  justify-content: center;
}

/* 版权信息 */
.copyright {
  margin-top: 12px;
  font-size: 12px;
  color: #909399;
  text-align: center;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .navbar-container {
    width: 200px;
  }
}
</style>
