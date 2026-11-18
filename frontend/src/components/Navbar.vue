<template>
  <nav class="navbar navbar-expand-lg navbar-dark bg-primary sticky-top shadow-sm">
    <div class="container">
      <router-link class="navbar-brand fw-bold fs-5" :to="homePath">
        <i class="bi bi-compass-fill me-2"></i>TrekSync <span class="badge bg-light text-primary fs-6">V2</span>
      </router-link>

      <button
        class="navbar-toggler border-0"
        type="button"
        data-bs-toggle="collapse"
        data-bs-target="#navbarNav"
      >
        <span class="navbar-toggler-icon"></span>
      </button>

      <div class="collapse navbar-collapse mt-2 mt-lg-0" id="navbarNav">
        <ul class="navbar-nav me-auto mb-2 mb-lg-0" v-if="auth.isAuthenticated">
          <!-- Admin Links -->
          <template v-if="auth.isAdmin">
            <li class="nav-item"><router-link class="nav-link px-2" to="/admin/dashboard"><i class="bi bi-speedometer2 me-1"></i>Dashboard</router-link></li>
            <li class="nav-item"><router-link class="nav-link px-2" to="/admin/treks"><i class="bi bi-map me-1"></i>Manage Treks</router-link></li>
            <li class="nav-item"><router-link class="nav-link px-2" to="/admin/users"><i class="bi bi-people me-1"></i>Manage Users</router-link></li>
            <li class="nav-item"><router-link class="nav-link px-2" to="/admin/reports"><i class="bi bi-file-earmark-bar-graph me-1"></i>Reports</router-link></li>
          </template>

          <!-- Staff Links -->
          <template v-if="auth.isStaff">
            <li class="nav-item"><router-link class="nav-link px-2" to="/staff/dashboard"><i class="bi bi-person-badge me-1"></i>Assigned Treks</router-link></li>
          </template>

          <!-- Trekker Links -->
          <template v-if="auth.isTrekker">
            <li class="nav-item"><router-link class="nav-link px-2" to="/trekker/dashboard"><i class="bi bi-binoculars me-1"></i>Explore Treks</router-link></li>
            <li class="nav-item"><router-link class="nav-link px-2" to="/trekker/bookings"><i class="bi bi-ticket-perforated me-1"></i>My Bookings</router-link></li>
          </template>
        </ul>

        <div class="d-flex flex-column flex-lg-row align-items-lg-center gap-2 gap-lg-3 ms-auto pt-2 pt-lg-0 border-top border-primary-subtle border-lg-0" v-if="auth.isAuthenticated">
          <!-- Trekker Notification Bell -->
          <button
            v-if="auth.isTrekker"
            class="btn btn-outline-light btn-sm position-relative rounded-pill px-3 py-1 d-flex align-items-center"
            @click="openInboxModal"
            title="My Notifications & Email Inbox"
          >
            <i class="bi bi-bell-fill me-1"></i>
            <span>Inbox</span>
            <span v-if="unreadCount > 0" class="badge bg-warning text-dark ms-2 rounded-pill fw-bold">
              {{ unreadCount }}
            </span>
          </button>

          <router-link v-if="auth.isTrekker" to="/trekker/profile" class="text-white text-decoration-none small py-1">
            <i class="bi bi-person-circle me-1"></i> Profile: <strong>{{ auth.user?.name || auth.user?.email }}</strong>
          </router-link>
          <span v-else class="text-white-50 small py-1">
            <i class="bi bi-shield-check me-1"></i> Logged in: <strong class="text-white text-uppercase">{{ auth.userRole }}</strong> ({{ auth.user?.name }})
          </span>
          <button @click="handleLogout" class="btn btn-outline-light btn-sm rounded-pill px-3 align-self-start align-self-lg-center mt-1 mt-lg-0">
            <i class="bi bi-box-arrow-right me-1"></i> Logout
          </button>
        </div>

        <div v-else class="d-flex gap-2 ms-auto pt-2 pt-lg-0">
          <router-link to="/login" class="btn btn-outline-light btn-sm rounded-pill px-3">Login</router-link>
          <router-link to="/register" class="btn btn-light btn-sm rounded-pill px-3">Register</router-link>
        </div>
      </div>
    </div>
  </nav>

  <!-- TREKKER INBOX & NOTIFICATIONS MODAL -->
  <div class="modal fade" id="trekkerInboxModal" tabindex="-1">
    <div class="modal-dialog modal-lg modal-dialog-centered modal-dialog-scrollable">
      <div class="modal-content border-0 shadow">
        <div class="modal-header bg-light">
          <div class="d-flex align-items-center gap-2">
            <i class="bi bi-bell-fill text-primary fs-5"></i>
            <h5 class="modal-title fw-bold text-dark mb-0">My Notifications & Trek Notices</h5>
            <span v-if="unreadCount > 0" class="badge bg-warning text-dark">{{ unreadCount }} Unread</span>
          </div>
          <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
        </div>

        <div class="modal-body p-0 bg-white">
          <div v-if="loadingNotifs" class="text-center py-5">
            <div class="spinner-border text-primary" role="status"></div>
          </div>

          <div v-else-if="notifications.length === 0" class="text-center py-5 px-3 text-muted">
            <i class="bi bi-envelope-open display-4 text-muted d-block mb-3"></i>
            <h6 class="fw-semibold">No Notifications Yet</h6>
            <p class="small text-muted mb-0">When trek reminders, departure alerts, or staff announcements are sent, they will appear here in your inbox.</p>
          </div>

          <div v-else class="list-group list-group-flush">
            <div
              v-for="n in notifications"
              :key="n.id"
              class="list-group-item p-3 border-bottom list-group-item-action"
              :class="{ 'bg-light': !n.is_read }"
              @click="toggleNotificationDetail(n)"
              style="cursor: pointer;"
            >
              <div class="d-flex w-100 justify-content-between align-items-start mb-1">
                <div class="d-flex align-items-center gap-2">
                  <span v-if="!n.is_read" class="badge bg-primary rounded-circle p-1" style="width: 8px; height: 8px;"></span>
                  <h6 class="mb-0 fw-bold" :class="!n.is_read ? 'text-primary' : 'text-dark'">
                    {{ n.subject }}
                  </h6>
                </div>
                <small class="text-muted text-nowrap ms-2">{{ n.created_at }}</small>
              </div>

              <div class="d-flex justify-content-between align-items-center mb-2">
                <small class="text-secondary">
                  <i class="bi bi-person-fill me-1"></i>From: <strong>{{ n.sender }}</strong>
                  <span v-if="n.trek_name" class="ms-2 badge bg-secondary-subtle text-dark">
                    🏔️ {{ n.trek_name }}
                  </span>
                </small>
                <button
                  v-if="!n.is_read"
                  class="btn btn-sm btn-outline-primary py-0 px-2 rounded-pill small"
                  @click.stop="markAsRead(n.id)"
                  title="Mark as Read"
                >
                  Mark Read
                </button>
              </div>

              <!-- Message preview or expanded body -->
              <div class="p-3 bg-white border rounded-3 mt-2 text-dark" style="white-space: pre-line; font-size: 0.92rem; line-height: 1.5;">
                {{ n.message }}
              </div>
            </div>
          </div>
        </div>

        <div class="modal-footer bg-light d-flex justify-content-between">
          <div>
            <button
              v-if="unreadCount > 0"
              class="btn btn-sm btn-outline-secondary rounded-pill px-3"
              @click="markAllAsRead"
            >
              <i class="bi bi-check2-all me-1"></i>Mark All as Read
            </button>
          </div>
          <button type="button" class="btn btn-secondary rounded-pill px-4" data-bs-dismiss="modal">Close</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import api from '@/services/api'
import { Modal } from 'bootstrap'

const auth = useAuthStore()
const router = useRouter()

const notifications = ref([])
const unreadCount = ref(0)
const loadingNotifs = ref(false)
let inboxModalInstance = null

const homePath = computed(() => {
  if (!auth.isAuthenticated) return '/login'
  if (auth.isAdmin) return '/admin/dashboard'
  if (auth.isStaff) return '/staff/dashboard'
  if (auth.isTrekker) return '/trekker/dashboard'
  return '/login'
})

const handleLogout = () => {
  auth.logout()
  router.push('/login')
}

const fetchNotifications = async () => {
  if (!auth.isTrekker) return
  try {
    const res = await api.get('/trekker/notifications')
    notifications.value = res.data.notifications || []
    unreadCount.value = res.data.unread_count || 0
  } catch (err) {
    // Graceful fallback if endpoint not accessible
  }
}

const openInboxModal = async () => {
  loadingNotifs.value = true
  const modalEl = document.getElementById('trekkerInboxModal')
  if (modalEl) {
    inboxModalInstance = Modal.getOrCreateInstance(modalEl)
    inboxModalInstance.show()
  }
  await fetchNotifications()
  loadingNotifs.value = false
}

const markAsRead = async (notifId) => {
  try {
    await api.put(`/trekker/notifications/${notifId}/read`)
    const n = notifications.value.find(item => item.id === notifId)
    if (n && !n.is_read) {
      n.is_read = true
      unreadCount.value = Math.max(0, unreadCount.value - 1)
    }
  } catch (err) {
    console.error(err)
  }
}

const markAllAsRead = async () => {
  try {
    await api.put('/trekker/notifications/read-all')
    notifications.value.forEach(n => { n.is_read = true })
    unreadCount.value = 0
  } catch (err) {
    console.error(err)
  }
}

const toggleNotificationDetail = (n) => {
  if (!n.is_read) {
    markAsRead(n.id)
  }
}

onMounted(() => {
  if (auth.isTrekker) {
    fetchNotifications()
  }
})

watch(() => auth.isAuthenticated, (newVal) => {
  if (newVal && auth.isTrekker) {
    fetchNotifications()
  }
})
</script>

