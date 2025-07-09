<template>
  <div class="main-layout">
    <NavBar class="main-sidebar" />
    <div class="main-content">
      <div class="header-container">
        <div class="header-left">
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item v-for="(item, index) in breadcrumbs" :key="index">
              {{ item }}
            </el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-right">
          <el-tooltip content="全屏" placement="bottom">
            <el-icon class="header-icon" @click="toggleFullScreen">
              <FullScreen v-if="!isFullScreen" />
              <aim v-else />
            </el-icon>
          </el-tooltip>
          <el-tooltip content="刷新页面" placement="bottom">
            <el-icon class="header-icon" @click="refreshPage">
              <Refresh />
            </el-icon>
          </el-tooltip>
          <!-- <el-tooltip content="消息通知" placement="bottom">
            <el-badge :value="3" class="header-badge">
              <el-icon class="header-icon">
                <Bell />
              </el-icon>
            </el-badge>
          </el-tooltip> -->
        </div>
      </div>
      <div class="page-container">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { Bell, Refresh, FullScreen, Aim } from '@element-plus/icons-vue'
import NavBar from '@/components/NavBar.vue'

export default {
  name: 'MainLayout',
  components: {
    NavBar,
    Bell, 
    Refresh,
    FullScreen,
    Aim
  },
  setup() {
    const route = useRoute()
    const isFullScreen = ref(false)
    
    // 生成面包屑
    const breadcrumbs = computed(() => {
      const { path, meta } = route
      const breadcrumbList = []
      
      if (meta && meta.title) {
        breadcrumbList.push(meta.title)
      } else {
        // 根据路径生成面包屑
        const pathParts = path.split('/').filter(Boolean)
        pathParts.forEach(part => {
          if (part) {
            // 将路径转换为更友好的显示名称
            const formattedPart = part
              .replace(/-/g, ' ')
              .replace(/\b\w/g, l => l.toUpperCase())
            breadcrumbList.push(formattedPart)
          }
        })
      }
      
      return breadcrumbList
    })
    
    // 全屏切换
    const toggleFullScreen = () => {
      if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen().catch(err => {
          console.error(`全屏切换错误: ${err.message}`)
        })
      } else {
        if (document.exitFullscreen) {
          document.exitFullscreen()
        }
      }
    }
    
    // 页面刷新
    const refreshPage = () => {
      window.location.reload()
    }
    
    // 监听全屏状态变化
    const handleFullScreenChange = () => {
      isFullScreen.value = !!document.fullscreenElement
    }
    
    onMounted(() => {
      document.addEventListener('fullscreenchange', handleFullScreenChange)
    })
    
    onBeforeUnmount(() => {
      document.removeEventListener('fullscreenchange', handleFullScreenChange)
    })
    
    return {
      breadcrumbs,
      isFullScreen,
      toggleFullScreen,
      refreshPage
    }
  }
}
</script>

<style scoped>
.main-layout {
  display: flex;
  height: 100vh;
  width: 100%;
  background-color: #f5f7fa;
  overflow: hidden;
}

.main-sidebar {
  flex-shrink: 0;
  height: 100%;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.header-container {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  background: #fff;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
}

.header-left {
  display: flex;
  align-items: center;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-icon {
  font-size: 20px;
  color: #606266;
  cursor: pointer;
  transition: color 0.3s;
}

.header-icon:hover {
  color: #409EFF;
}

.header-badge {
  height: 20px;
  line-height: 20px;
}

.page-container {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

/* 页面切换动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style> 