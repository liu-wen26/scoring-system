import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { public: true }
  },
  {
    path: '/',
    name: 'Layout',
    component: () => import('@/views/Layout.vue'),
    redirect: '/exam',
    children: [
      {
        path: '/exam',
        name: 'ExamList',
        component: () => import('@/views/exam/ExamList.vue'),
        meta: { title: '考试列表' }
      },
      {
        path: '/exam/create',
        name: 'ExamCreate',
        component: () => import('@/views/exam/ExamCreate.vue'),
        meta: { title: '新建考试' }
      },
      {
        path: '/exam/:id',
        name: 'ExamDetail',
        component: () => import('@/views/exam/ExamDetail.vue'),
        meta: { title: '考试详情' }
      },
      {
        path: '/exam/:id/answer-card',
        name: 'AnswerCardConfig',
        component: () => import('@/views/answer-card/AnswerCardConfig.vue'),
        meta: { title: '答题卡配置' }
      },
      {
        path: '/scan',
        name: 'ScanUpload',
        component: () => import('@/views/scan/ScanUpload.vue'),
        meta: { title: '扫描上传' }
      },
      {
        path: '/mark',
        name: 'MarkMonitor',
        component: () => import('@/views/mark/MarkMonitor.vue'),
        meta: { title: '阅卷监控' }
      },
      {
        path: '/mark/assign',
        name: 'MarkAssignment',
        component: () => import('@/views/mark/MarkAssignment.vue'),
        meta: { title: '阅卷分工' }
      },
      {
        path: '/mark/my-tasks',
        name: 'MyMarkTasks',
        component: () => import('@/views/mark/MyMarkTasks.vue'),
        meta: { title: '我的阅卷任务' }
      },
      {
        path: '/mark/question',
        name: 'QuestionMark',
        component: () => import('@/views/mark/QuestionMark.vue'),
        meta: { title: '按题阅卷' }
      },
      {
        path: '/report',
        name: 'ClassReport',
        component: () => import('@/views/report/ClassReport.vue'),
        meta: { title: '成绩报告' }
      },
      {
        path: '/report/student/:studentId',
        name: 'StudentReport',
        component: () => import('@/views/report/StudentReport.vue'),
        meta: { title: '学生个人报告' }
      },
      {
        path: '/user',
        name: 'UserList',
        component: () => import('@/views/user/UserList.vue'),
        meta: { title: '用户管理' }
      },
      {
        path: '/answer-card',
        name: 'AnswerCardList',
        component: () => import('@/views/answer-card/AnswerCardList.vue'),
        meta: { title: '答题卡制作' }
      },
      {
        path: '/answer-card/editor/:id',
        name: 'AnswerCardEditor',
        component: () => import('@/views/answer-card/AnswerCardEditor.vue'),
        meta: { title: '答题卡编辑' }
      },
      {
        path: '/answer-card/third-party',
        name: 'ThirdPartyAnswerCard',
        component: () => import('@/views/answer-card/ThirdPartyAnswerCard.vue'),
        meta: { title: '第三方答题卡' }
      },
      {
        path: '/wrong-question',
        name: 'WrongQuestionList',
        component: () => import('@/views/wrong-question/WrongQuestionList.vue'),
        meta: { title: '错题管理' }
      },
      {
        path: '/profile',
        name: 'Profile',
        component: () => import('@/views/profile/Profile.vue'),
        meta: { title: '个人中心' }
      },
      {
        path: '/archive/student',
        name: 'StudentArchive',
        component: () => import('@/views/archive/StudentArchive.vue'),
        meta: { title: '学生档案' }
      },
      {
        path: '/archive/teacher',
        name: 'TeacherArchive',
        component: () => import('@/views/archive/TeacherArchive.vue'),
        meta: { title: '教师档案' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  
  if (!to.meta.public && !userStore.token) {
    next('/login')
  } else {
    next()
  }
})

export default router
