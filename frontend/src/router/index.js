import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

import LoginView from '@/views/auth/LoginView.vue'
import RegisterView from '@/views/auth/RegisterView.vue'

import AdminDashboard from '@/views/admin/AdminDashboard.vue'
import AdminTreks from '@/views/admin/AdminTreks.vue'
import AdminUsers from '@/views/admin/AdminUsers.vue'
import AdminReports from '@/views/admin/AdminReports.vue'

import StaffDashboard from '@/views/staff/StaffDashboard.vue'
import TrekParticipants from '@/views/staff/TrekParticipants.vue'

import TrekkerDashboard from '@/views/trekker/TrekkerDashboard.vue'
import MyBookings from '@/views/trekker/MyBookings.vue'
import TrekkerProfile from '@/views/trekker/TrekkerProfile.vue'

const routes = [
  { path: '/login', name: 'login', component: LoginView, meta: { guest: true } },
  { path: '/register', name: 'register', component: RegisterView, meta: { guest: true } },

  // Admin Routes
  { path: '/admin/dashboard', name: 'admin-dashboard', component: AdminDashboard, meta: { requiresAuth: true, role: 'admin' } },
  { path: '/admin/treks', name: 'admin-treks', component: AdminTreks, meta: { requiresAuth: true, role: 'admin' } },
  { path: '/admin/users', name: 'admin-users', component: AdminUsers, meta: { requiresAuth: true, role: 'admin' } },
  { path: '/admin/reports', name: 'admin-reports', component: AdminReports, meta: { requiresAuth: true, role: 'admin' } },

  // Staff Routes
  { path: '/staff/dashboard', name: 'staff-dashboard', component: StaffDashboard, meta: { requiresAuth: true, role: 'staff' } },
  { path: '/staff/treks/:id/participants', name: 'staff-participants', component: TrekParticipants, meta: { requiresAuth: true, role: 'staff' } },

  // Trekker Routes
  { path: '/trekker/dashboard', name: 'trekker-dashboard', component: TrekkerDashboard, meta: { requiresAuth: true, role: 'user' } },
  { path: '/trekker/bookings', name: 'trekker-bookings', component: MyBookings, meta: { requiresAuth: true, role: 'user' } },
  { path: '/trekker/profile', name: 'trekker-profile', component: TrekkerProfile, meta: { requiresAuth: true, role: 'user' } },

  // Default Fallback
  {
    path: '/:pathMatch(.*)*',
    redirect: () => {
      const auth = useAuthStore()
      if (!auth.isAuthenticated) return '/login'
      if (auth.isAdmin) return '/admin/dashboard'
      if (auth.isStaff) return '/staff/dashboard'
      if (auth.isTrekker) return '/trekker/dashboard'
      return '/login'
    }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const auth = useAuthStore()

  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return next('/login')
  }

  if (to.meta.guest && auth.isAuthenticated) {
    if (auth.isAdmin) return next('/admin/dashboard')
    if (auth.isStaff) return next('/staff/dashboard')
    if (auth.isTrekker) return next('/trekker/dashboard')
  }

  if (to.meta.role && auth.userRole !== to.meta.role) {
    if (auth.isAdmin) return next('/admin/dashboard')
    if (auth.isStaff) return next('/staff/dashboard')
    if (auth.isTrekker) return next('/trekker/dashboard')
    return next('/login')
  }

  next()
})

export default router

