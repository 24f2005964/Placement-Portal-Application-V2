<template>
  <div>
    <!-- Hero Header Banner -->
    <div class="card mb-4 border-0 shadow-sm overflow-hidden text-white rounded-3">
      <div
        class="p-4 d-flex flex-column justify-content-center"
        style="background: linear-gradient(90deg, rgba(15, 23, 42, 0.88) 0%, rgba(30, 41, 59, 0.78) 100%), url('/images/admin_bg.jpg') center/cover no-repeat; min-height: 140px;"
      >
        <h2 class="fw-bold mb-1"><i class="bi bi-shield-lock me-2"></i> Admin Command Center</h2>
        <p class="mb-0 text-white-75">Trekking Operations, Routes, Staffing & Approvals Overview</p>
      </div>
    </div>

    <div v-if="loading" class="py-5 text-center">
      <div class="spinner-border text-primary" role="status"></div>
    </div>

    <div v-else>
      <!-- Stat Cards Row -->
      <div class="row g-3 mb-4">
        <!-- Total Treks -->
        <div class="col-md-3">
          <div @click="$router.push('/admin/treks')" class="card text-center border-primary shadow-sm p-3 bg-white h-100 cursor-pointer">
            <div class="text-primary fs-3 mb-1"><i class="bi bi-map-fill"></i></div>
            <h6 class="text-uppercase text-muted fw-bold mb-1 small">Total Treks</h6>
            <h2 class="fw-bold text-dark mb-1">{{ counts.total_treks }}</h2>
            <div class="small text-muted mb-2">({{ counts.open_treks }} Open | {{ counts.completed_treks }} Done)</div>
            <span class="btn btn-outline-primary btn-sm mt-auto">Manage Routes &rarr;</span>
          </div>
        </div>

        <!-- Trekkers -->
        <div class="col-md-3">
          <div @click="$router.push('/admin/users')" class="card text-center border-success shadow-sm p-3 bg-white h-100 cursor-pointer">
            <div class="text-success fs-3 mb-1"><i class="bi bi-people-fill"></i></div>
            <h6 class="text-uppercase text-muted fw-bold mb-1 small">Registered Trekkers</h6>
            <h2 class="fw-bold text-dark mb-1">{{ counts.total_trekkers }}</h2>
            <div class="small text-muted mb-2">Active Participants</div>
            <span class="btn btn-outline-success btn-sm mt-auto">View Users &rarr;</span>
          </div>
        </div>

        <!-- Staff -->
        <div class="col-md-3">
          <div @click="$router.push('/admin/users')" class="card text-center border-warning shadow-sm p-3 bg-white h-100 cursor-pointer">
            <div class="text-warning fs-3 mb-1"><i class="bi bi-person-badge-fill"></i></div>
            <h6 class="text-uppercase text-muted fw-bold mb-1 small">Trek Staff</h6>
            <h2 class="fw-bold text-dark mb-1">{{ counts.total_staff }}</h2>
            <div class="small text-muted mb-2">
              <span v-if="counts.pending_staff > 0" class="badge bg-danger">{{ counts.pending_staff }} Pending Approval</span>
              <span v-else class="text-success">All Approved</span>
            </div>
            <span class="btn btn-outline-warning btn-sm mt-auto">Staff Roster &rarr;</span>
          </div>
        </div>

        <!-- Bookings -->
        <div class="col-md-3">
          <div @click="$router.push('/admin/reports')" class="card text-center border-info shadow-sm p-3 bg-white h-100 cursor-pointer">
            <div class="text-info fs-3 mb-1"><i class="bi bi-ticket-perforated-fill"></i></div>
            <h6 class="text-uppercase text-muted fw-bold mb-1 small">Total Bookings</h6>
            <h2 class="fw-bold text-dark mb-1">{{ counts.total_bookings }}</h2>
            <div class="small text-muted mb-2">({{ counts.confirmed_bookings }} Confirmed)</div>
            <span class="btn btn-outline-info btn-sm mt-auto">Reports & Analytics &rarr;</span>
          </div>
        </div>
      </div>

      <!-- Analytics Charts Row -->
      <div class="row g-4 mb-4">
        <div class="col-md-6">
          <AnalyticsChart
            title="Trek Operations Breakdown"
            type="doughnut"
            :data="trekStatusChartData"
          />
        </div>
        <div class="col-md-6">
          <AnalyticsChart
            title="Bookings & Reservations Status"
            type="bar"
            :data="bookingsChartData"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import api from '@/services/api'
import AnalyticsChart from '@/components/AnalyticsChart.vue'

const loading = ref(true)
const counts = ref({})

const fetchStats = async () => {
  loading.value = true
  try {
    const res = await api.get('/admin/dashboard')
    counts.value = res.data.counts || {}
  } catch (err) {
    console.error('Error fetching admin dashboard stats:', err)
  } finally {
    loading.value = false
  }
}

const trekStatusChartData = computed(() => ({
  labels: ['Open Treks', 'Completed Treks', 'Other / Closed'],
  datasets: [{
    data: [
      counts.value.open_treks || 0,
      counts.value.completed_treks || 0,
      Math.max(0, (counts.value.total_treks || 0) - (counts.value.open_treks || 0) - (counts.value.completed_treks || 0))
    ],
    backgroundColor: ['#10b981', '#0ea5e9', '#f59e0b']
  }]
}))

const bookingsChartData = computed(() => ({
  labels: ['Confirmed', 'Cancelled'],
  datasets: [{
    label: 'Bookings Count',
    data: [counts.value.confirmed_bookings || 0, counts.value.cancelled_bookings || 0],
    backgroundColor: ['#10b981', '#ef4444']
  }]
}))

onMounted(fetchStats)
</script>

<style scoped>
.cursor-pointer {
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}
.cursor-pointer:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 16px rgba(0,0,0,0.1) !important;
}
</style>

