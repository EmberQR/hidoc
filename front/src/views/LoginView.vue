<template>
    <div class="login-container">
      <!-- 背景装饰 -->
      <div class="bg-decoration">
        <div class="circle circle1"></div>
        <div class="circle circle2"></div>
        <div class="circle circle3"></div>
      </div>
  
      <!-- 登录卡片 -->
      <div class="login-card">
        <div class="login-header">
          <h1 class="login-title">欢迎使用HiDoc智能影像辅诊系统</h1>
          <p class="login-subtitle">请输入您的账户信息</p>
        </div>
  
        <!-- 登录表单 -->
        <el-form
          ref="loginFormRef"
          :model="loginForm"
          :rules="loginRules"
          class="login-form"
          size="large"
        >
          <el-form-item prop="phone">
            <el-input
              v-model="loginForm.phone"
              placeholder="请输入手机号"
              prefix-icon="Iphone"
              clearable
            />
          </el-form-item>
  
          <el-form-item prop="password">
            <el-input
              v-model="loginForm.password"
              type="password"
              placeholder="请输入密码"
              prefix-icon="Lock"
              show-password
              @keyup.enter="handleLogin"
            />
          </el-form-item>
  
          <el-form-item>
            <el-button
              type="primary"
              class="login-button"
              :loading="loading"
              @click="handleLogin"
            >
              {{ loading ? '登录中...' : '登录' }}
            </el-button>
          </el-form-item>
        </el-form>
      </div>
      
      <!-- 选择医院对话框 -->
      <el-dialog
        v-model="hospitalDialogVisible"
        title="请选择医院"
        width="400px"
        :close-on-click-modal="false"
        :close-on-press-escape="false"
        :show-close="false"
      >
        <div v-if="hospitals.length > 0">
          <p class="hospital-tip">请选择您要进入的医院：</p>
          <el-radio-group v-model="selectedHospitalId" class="hospital-radio-group">
            <el-radio 
              v-for="hospital in hospitals" 
              :key="hospital.id" 
              :label="hospital.id"
              class="hospital-radio-item"
              border
            >
              {{ hospital.name }}
            </el-radio>
          </el-radio-group>
          <div class="dialog-footer">
            <el-button type="primary" @click="confirmHospital" :disabled="!selectedHospitalId">
              确认
            </el-button>
          </div>
        </div>
        <div v-else class="no-hospital">
          <el-empty description="您暂未关联任何医院，请联系管理员" />
        </div>
      </el-dialog>
    </div>
  </template>
  
  <script>
  import { ref, reactive } from 'vue'
  import { ElMessage } from 'element-plus'
  import { login, getUserHospitals } from '@/api/user'
  import { useRouter } from 'vue-router'
  
  export default {
    name: 'ElementLogin',
    setup() {
      const loginFormRef = ref(null)
      const loading = ref(false)
      const router = useRouter()
      const hospitalDialogVisible = ref(false)
      const hospitals = ref([])
      const selectedHospitalId = ref(null)
  
      // 登录表单数据
      const loginForm = reactive({
        phone: '',
        password: ''
      })
  
      // 表单验证规则
      const loginRules = reactive({
        phone: [
          { required: true, message: '请输入手机号', trigger: 'blur' },
          { 
            validator: (rule, value, callback) => {
              // 手机号正则表达式（中国大陆11位手机号）
              const phoneRegex = /^1[3-9]\d{9}$/;
              
              if (phoneRegex.test(value)) {
                callback();
              } else {
                callback(new Error('请输入正确的手机号格式'));
              }
            },
            trigger: 'blur'
          }
        ],
        password: [
          { required: true, message: '请输入密码', trigger: 'blur' },
          { min: 6, max: 20, message: '密码长度在 6 到 20 个字符', trigger: 'blur' }
        ]
      })
      
      // 登录处理
      const handleLogin = () => {
        loginFormRef.value.validate((valid) => {
          if (valid) {
            loading.value = true
            
            // 使用API登录
            login({
              phone: loginForm.phone,
              password: loginForm.password
            }).then(res => {
              loading.value = false
              ElMessage.success('登录成功！')
              // 保存用户信息
              localStorage.setItem('userInfo', JSON.stringify(res.data))
              
              // 获取医院列表
              fetchHospitals()
            }).catch(() => {
              loading.value = false
            })
          } else {
            ElMessage.error('请检查输入信息！')
          }
        })
      }
      
      // 获取医院列表
      const fetchHospitals = () => {
        loading.value = true
        getUserHospitals().then(res => {
          loading.value = false
          hospitals.value = res.data || []
          
          if (hospitals.value.length === 0) {
            ElMessage.warning('您暂未关联任何医院，请联系管理员')
          } else if (hospitals.value.length === 1) {
            // 如果只有一家医院，自动选择
            selectedHospitalId.value = hospitals.value[0].id
            confirmHospital()
          } else {
            // 显示选择医院对话框
            hospitalDialogVisible.value = true
          }
        }).catch(() => {
          loading.value = false
          ElMessage.error('获取医院列表失败')
        })
      }
      
      // 确认选择医院
      const confirmHospital = () => {
        if (!selectedHospitalId.value) {
          ElMessage.warning('请选择一家医院')
          return
        }
        
        // 保存选择的医院信息
        const selectedHospital = hospitals.value.find(h => h.id === selectedHospitalId.value)
        localStorage.setItem('currentHospital', JSON.stringify(selectedHospital))
        
        // 关闭对话框
        hospitalDialogVisible.value = false
        
        // 获取redirect参数，如果有则跳转到指定页面，否则跳转到首页
        const redirect = router.currentRoute.value.query.redirect || '/'
        router.push(redirect)
      }
  
      return {
        loginFormRef,
        loginForm,
        loginRules,
        loading,
        handleLogin,
        hospitalDialogVisible,
        hospitals,
        selectedHospitalId,
        confirmHospital
      }
    }
  }
  </script>
  
  <style scoped>
  .login-container {
    position: relative;
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #099c6b 0%, #109684 100%);
    overflow: hidden;
  }
  
  /* 背景装饰 */
  .bg-decoration {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
  }
  
  .circle {
    position: absolute;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.1);
    animation: float 6s ease-in-out infinite;
  }
  
  .circle1 {
    width: 200px;
    height: 200px;
    top: 10%;
    left: 10%;
    animation-delay: 0s;
  }
  
  .circle2 {
    width: 150px;
    height: 150px;
    top: 60%;
    right: 10%;
    animation-delay: 2s;
  }
  
  .circle3 {
    width: 100px;
    height: 100px;
    bottom: 20%;
    left: 50%;
    animation-delay: 4s;
  }
  
  @keyframes float {
    0%, 100% {
      transform: translateY(0px);
      opacity: 0.7;
    }
    50% {
      transform: translateY(-20px);
      opacity: 1;
    }
  }
  
  /* 登录卡片 */
  .login-card {
    width: 100%;
    max-width: 400px;
    padding: 40px;
    background: rgba(255, 255, 255, 0.15);
    backdrop-filter: blur(10px);
    border-radius: 20px;
    border: 1px solid rgba(255, 255, 255, 0.2);
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
    z-index: 1;
  }
  
  /* 登录头部 */
  .login-header {
    text-align: center;
    margin-bottom: 30px;
  }
  
  .login-title {
    font-size: 25px;
    font-weight: 600;
    color: #fff;
    margin: 0 0 10px 0;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }
  
  .login-subtitle {
    font-size: 14px;
    color: rgba(255, 255, 255, 0.8);
    margin: 0;
  }
  
  /* 登录表单 */
  .login-form {
    margin-top: 20px;
  }
  
  .login-form :deep(.el-input__wrapper) {
    background: rgba(255, 255, 255, 0.2);
    border: 1px solid rgba(255, 255, 255, 0.3);
    border-radius: 12px;
    backdrop-filter: blur(5px);
    box-shadow: none;
    transition: all 0.3s ease;
  }
  
  .login-form :deep(.el-input__wrapper:hover) {
    background: rgba(255, 255, 255, 0.25);
    border-color: rgba(255, 255, 255, 0.5);
  }
  
  .login-form :deep(.el-input__wrapper.is-focus) {
    background: rgba(255, 255, 255, 0.3);
    border-color: #409eff;
    box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
  }
  
  .login-form :deep(.el-input__inner) {
    color: #fff;
    font-weight: 500;
  }
  
  .login-form :deep(.el-input__inner::placeholder) {
    color: rgba(255, 255, 255, 0.7);
  }
  
  .login-form :deep(.el-input__prefix) {
    color: rgba(255, 255, 255, 0.8);
  }
  
  .login-form :deep(.el-input__suffix) {
    color: rgba(255, 255, 255, 0.8);
  }
  
  /* 登录按钮 */
  .login-button {
    width: 100%;
    height: 48px;
    font-size: 16px;
    font-weight: 600;
    border-radius: 12px;
    background: linear-gradient(90deg, #409eff 0%, #36cfc9 50%, #409eff 100%);
    background-size: 300% 100%;
    background-position: 100% 0;
    border: none;
    box-shadow: 0 4px 15px rgba(64, 158, 255, 0.3);
    transition: all 0.8s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
  }
  
  .login-button::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
    transition: left 0.8s cubic-bezier(0.4, 0, 0.2, 1);
  }
  
  .login-button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(64, 158, 255, 0.4);
    background-position: 0% 0;
  }
  
  .login-button:hover::before {
    left: 100%;
  }
  
  .login-button:active {
    transform: translateY(-1px);
    transition: transform 0.1s ease;
  }
  
  /* 医院选择对话框 */
  .hospital-tip {
    margin-bottom: 15px;
    font-size: 14px;
    color: #606266;
    text-align: center;
  }
  
  .hospital-radio-group {
    display: flex;
    flex-direction: column;
    gap: 12px;
    margin-bottom: 20px;
    width: 100%;
  }
  
  .hospital-radio-item {
    width: 100%;
    margin-left: 0 !important;
    margin-right: 0 !important;
    text-align: center;
  }
  
  .hospital-radio-item :deep(.el-radio__label) {
    font-size: 16px;
    padding-left: 10px;
  }
  
  .dialog-footer {
    text-align: center;
    margin-top: 20px;
  }
  
  .dialog-footer .el-button {
    min-width: 120px;
  }
  
  .no-hospital {
    padding: 20px 0;
  }
  
  /* 响应式设计 */
  @media (max-width: 768px) {
    .login-card {
      max-width: 350px;
      padding: 30px 25px;
      margin: 20px;
    }
    
    .login-title {
      font-size: 24px;
    }
    
    .circle1, .circle2, .circle3 {
      display: none;
    }
  }
  
  @media (max-width: 480px) {
    .login-card {
      max-width: 300px;
      padding: 25px 20px;
    }
    
    .login-title {
      font-size: 22px;
    }
  }
  </style>
  