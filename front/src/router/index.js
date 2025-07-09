import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import { checkLoginStatus, isLoggedIn } from '@/utils/auth'
import { ElMessage } from 'element-plus'
import MainLayout from '@/layouts/MainLayout.vue'

const routes = [
  {
    path: '/',
    component: MainLayout,
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'home',
        component: HomeView,
        meta: { title: '首页', icon: 'home' }
      },
      {
        path: 'profile',
        name: 'profile',
        component: () => import('@/views/UserCenter.vue'),
        meta: { title: '个人中心', icon: 'user' }
      },
      {
        path: '/patient',
        name: 'patient',
        component: () => import('@/views/CaseMng.vue'),
        meta: { title: '病历管理', icon: 'document-add' }
      },
      {
        path: '/image',
        name: 'image',
        component: () => import('@/views/ImageMng.vue'),
        meta: { title: '影像管理', icon: 'image' }
      }
      // {
      //   path: 'patients',
      //   name: 'patients',
      //   component: () => import('@/views/patients/PatientList.vue'),
      //   meta: { title: '患者列表', icon: 'user' }
      // },
      // {
      //   path: 'patients/add',
      //   name: 'patientAdd',
      //   component: () => import('@/views/patients/PatientAdd.vue'),
      //   meta: { title: '添加患者', icon: 'plus' }
      // },
      // {
      //   path: 'diagnosis/new',
      //   name: 'diagnosisNew',
      //   component: () => import('@/views/diagnosis/DiagnosisNew.vue'),
      //   meta: { title: '新建诊断', icon: 'stethoscope' }
      // },
      // {
      //   path: 'diagnosis/history',
      //   name: 'diagnosisHistory',
      //   component: () => import('@/views/diagnosis/DiagnosisHistory.vue'),
      //   meta: { title: '诊断历史', icon: 'clock' }
      // },
      // {
      //   path: 'knowledge',
      //   name: 'knowledge',
      //   component: () => import('@/views/knowledge/KnowledgeBase.vue'),
      //   meta: { title: '知识库', icon: 'reading' }
      // },
      // {
      //   path: 'statistics',
      //   name: 'statistics',
      //   component: () => import('@/views/statistics/StatisticsView.vue'),
      //   meta: { title: '统计分析', icon: 'trend-charts' }
      // },
      // {
      //   path: 'settings',
      //   name: 'settings',
      //   component: () => import('@/views/settings/SettingsView.vue'),
      //   meta: { title: '系统设置', icon: 'setting' }
      // },
      // {
      //   path: 'profile',
      //   name: 'profile',
      //   component: () => import('@/views/profile/ProfileView.vue'),
      //   meta: { title: '个人信息', icon: 'user' }
      // },
      // {
      //   path: 'about',
      //   name: 'about',
      //   component: () => import('@/views/AboutView.vue'),
      //   meta: { title: '关于', icon: 'info' }
      // }
    ]
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/LoginView.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue'),
    meta: { requiresAuth: false }
  },

]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
})

// 全局前置守卫
router.beforeEach(async (to, from, next) => {
  // 如果前往的是登录页且已登录，重定向到首页
  if (to.path === '/login' && isLoggedIn()) {
    try {
      // 验证登录状态是否有效
      const isValid = await checkLoginStatus()
      if (isValid) {
        next({ path: '/' })
        return
      }
      // 如果登录无效，继续前往登录页
    } catch (error) {
      console.error('验证登录状态失败', error)
    }
  }

  // 检查路由是否需要登录权限
  if (to.matched.some(record => record.meta.requiresAuth)) {
    // 验证登录状态
    try {
      const isValid = await checkLoginStatus()
      if (isValid) {
        // 已登录，继续导航
        next()
      } else {
        // 未登录，重定向到登录页
        ElMessage.warning('请先登录')
        next({ path: '/login', query: { redirect: to.fullPath } })
      }
    } catch (error) {
      console.error('验证登录状态失败', error)
      next({ path: '/login', query: { redirect: to.fullPath } })
    }
  } else {
    // 不需要登录权限的页面直接放行
    next()
  }
})

export default router
