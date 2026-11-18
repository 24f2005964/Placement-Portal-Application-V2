<template>
  <div>
    <!-- Hero Header Banner -->
    <div class="card mb-4 border-0 shadow-sm overflow-hidden text-white rounded-3">
      <div
        class="p-4 d-flex flex-column flex-md-row justify-content-between align-items-md-center gap-3"
        style="background: linear-gradient(90deg, rgba(2, 132, 199, 0.88) 0%, rgba(3, 105, 161, 0.75) 100%), url('/images/trekker_bg.jpg') center/cover no-repeat; min-height: 150px;"
      >
        <div>
          <h2 class="fw-bold mb-1"><i class="bi bi-compass-fill me-2"></i> Discover Your Next Mountain Expedition</h2>
          <p class="mb-0 text-white-75">Explore certified treks across the Himalayas & Western Ghats with real-time slot booking</p>
        </div>
        <button
          class="btn btn-light rounded-pill px-3 py-2 text-primary fw-semibold small shadow-sm flex-shrink-0"
          @click="exportCSV"
          :disabled="exporting"
        >
          <span v-if="exporting" class="spinner-border spinner-border-sm me-1"></span>
          <i v-else class="bi bi-file-earmark-arrow-down me-1"></i>
          {{ exporting ? 'Triggering Job...' : 'Export History (CSV)' }}
        </button>
      </div>
    </div>

    <!-- Alert Notification for Asynchronous Batch Job -->
    <div v-if="alertMsg" class="alert alert-dismissible fade show rounded-3 shadow-sm mb-4" :class="`alert-${alertType}`">
      <i class="bi bi-info-circle-fill me-2"></i>{{ alertMsg }}
      <button type="button" class="btn-close" @click="alertMsg = ''"></button>
    </div>

    <!-- Search & Filter Controls -->
    <div class="card border-0 shadow-sm rounded-3 p-3 mb-4 bg-white">
      <div class="row g-3 align-items-center">
        <div class="col-md-5">
          <div class="input-group">
            <span class="input-group-text bg-white"><i class="bi bi-search text-muted"></i></span>
            <input
              type="text"
              class="form-control"
              v-model="searchQuery"
              @input="fetchTreks"
              placeholder="Search by trek name or location..."
            />
          </div>
        </div>
        <div class="col-md-4">
          <div class="d-flex gap-1">
            <button
              v-for="d in ['All', 'Easy', 'Moderate', 'Hard']"
              :key="d"
              class="btn btn-sm flex-grow-1"
              :class="difficultyFilter === d ? 'btn-primary' : 'btn-outline-secondary'"
              @click="difficultyFilter = d; fetchTreks()"
            >
              {{ d }}
            </button>
          </div>
        </div>
        <div class="col-md-3 text-end text-muted small">
          Showing <strong>{{ treks.length }}</strong> active expeditions
        </div>
      </div>
    </div>

    <!-- Treks Grid -->
    <div v-if="loading" class="py-5 text-center">
      <div class="spinner-border text-primary" role="status"></div>
    </div>

    <div v-else-if="treks.length > 0" class="row g-4">
      <div class="col-md-6 col-lg-4" v-for="t in treks" :key="t.id">
        <TrekCard :trek="t" @book="openBookModal" />
      </div>
    </div>

    <div v-else class="text-center py-5 bg-white rounded-3 shadow-sm">
      <i class="bi bi-compass text-muted display-4"></i>
      <p class="text-muted mt-2">No expeditions match your current search or filter criteria.</p>
    </div>

    <!-- Book Trek Modal -->
    <div class="modal fade" id="bookModal" tabindex="-1">
      <div class="modal-dialog">
        <div class="modal-content" v-if="selectedTrek">
          <div class="modal-header">
            <h5 class="modal-title fw-bold">Reserve Trek: {{ selectedTrek.name }}</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>
          <form @submit.prevent="confirmBooking">
            <div class="modal-body">
              <div class="alert alert-info py-2 small mb-3">
                <i class="bi bi-info-circle me-1"></i>
                Available Slots: <strong>{{ selectedTrek.available_slots }}</strong> of {{ selectedTrek.total_slots }}
              </div>
              <!-- Success banner inside modal -->
              <div v-if="bookingSuccess" class="alert alert-success py-2 small mb-3">
                <i class="bi bi-check-circle me-1"></i>{{ bookingSuccess }}
              </div>
              <!-- Error banner inside modal -->
              <div v-if="bookingError" class="alert alert-danger py-2 small mb-3">
                <i class="bi bi-exclamation-triangle me-1"></i>{{ bookingError }}
              </div>

              <div class="mb-3">
                <label class="form-label small fw-semibold">Number of Seats to Reserve</label>
                <input
                  type="number"
                  class="form-control"
                  v-model.number="bookingSeats"
                  min="1"
                  :max="selectedTrek.available_slots"
                  required
                />
                <div class="form-text">Overbooking protection enforced in real-time.</div>
              </div>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
              <button type="submit" class="btn btn-primary px-4" :disabled="bookingLoading">
                <span v-if="bookingLoading" class="spinner-border spinner-border-sm me-1"></span>
                Confirm Reservation
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/api'
import TrekCard from '@/components/TrekCard.vue'
import { Modal } from 'bootstrap'

const router = useRouter()
const treks = ref([])
const loading = ref(true)
const searchQuery = ref('')
const difficultyFilter = ref('All')

const selectedTrek = ref(null)
const bookingSeats = ref(1)
const bookingLoading = ref(false)
const bookingSuccess = ref('')
const bookingError = ref('')
let bookModal = null

const exporting = ref(false)
const alertMsg = ref('')
const alertType = ref('info')

const showAlert = (msg, type = 'info') => {
  alertMsg.value = msg
  alertType.value = type
  if (type === 'success') {
    setTimeout(() => {
      alertMsg.value = ''
    }, 6000)
  }
}

const exportCSV = async () => {
  exporting.value = true
  showAlert('Triggering Celery async batch export task...', 'info')
  try {
    const res = await api.post('/trekker/bookings/export')
    const taskId = res.data.task_id
    showAlert(`Batch export job #${taskId} completed! Downloading CSV history...`, 'success')
    
    // Download via authenticated API call (sends JWT Authorization header)
    const downloadRes = await api.get(`/trekker/exports/${taskId}/download`, {
      responseType: 'blob'
    })
    const blob = new Blob([downloadRes.data], { type: 'text/csv;charset=utf-8;' })
    const downloadUrl = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = downloadUrl
    link.setAttribute('download', `bookings_export_${taskId}.csv`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(downloadUrl)
  } catch (err) {
    showAlert(err.response?.data?.error || 'Failed to trigger batch CSV export.', 'danger')
  } finally {
    exporting.value = false
  }
}

const fetchTreks = async () => {
  loading.value = true
  try {
    const res = await api.get(`/trekker/treks?q=${searchQuery.value}&difficulty=${difficultyFilter.value}`)
    treks.value = res.data.treks || []
  } catch (err) {
    console.error(err)
  } finally {
    loading.value = false
  }
}

const openBookModal = (trek) => {
  selectedTrek.value = trek
  bookingSeats.value = 1
  bookingSuccess.value = ''
  bookingError.value = ''
  bookModal = new Modal(document.getElementById('bookModal'))
  bookModal.show()
}

const confirmBooking = async () => {
  bookingLoading.value = true
  bookingSuccess.value = ''
  bookingError.value = ''
  try {
    const res = await api.post(`/trekker/treks/${selectedTrek.value.id}/book`, { seats: bookingSeats.value })
    bookingSuccess.value = '🎉 Booking confirmed! Redirecting to your bookings...'
    await fetchTreks()
    setTimeout(() => {
      bookModal?.hide()
      router.push('/trekker/bookings')
    }, 1500)
  } catch (err) {
    bookingError.value = err.response?.data?.error || 'Booking reservation failed. Please try again.'
  } finally {
    bookingLoading.value = false
  }
}

onMounted(fetchTreks)
</script>

