<template>
  <div>
    <div class="d-flex justify-content-between align-items-center mb-4">
      <div>
        <h3 class="fw-bold text-dark mb-0"><i class="bi bi-ticket-perforated-fill text-primary me-2"></i>My Trek Reservations</h3>
        <p class="text-muted small mb-0">View booking status, manage cancellations, and export trekking history</p>
      </div>
      <button class="btn btn-outline-primary rounded-pill px-3" @click="exportCSV" :disabled="exporting">
        <span v-if="exporting" class="spinner-border spinner-border-sm me-1"></span>
        <i v-else class="bi bi-download me-1"></i>Export History (CSV)
      </button>
    </div>

    <!-- Alert Banner -->
    <div v-if="alertMsg" class="alert alert-dismissible fade show py-2 small shadow-sm mb-3" :class="'alert-' + alertType">
      <i class="bi me-1" :class="alertType === 'success' ? 'bi-check-circle-fill' : 'bi-exclamation-triangle-fill'"></i>
      {{ alertMsg }}
      <button type="button" class="btn-close" @click="alertMsg = ''"></button>
    </div>

    <!-- Bookings Table Card -->
    <div class="card border-0 shadow-sm rounded-3">
      <div class="card-body p-0">
        <div class="table-responsive" v-if="bookings.length > 0">
          <table class="table table-hover align-middle mb-0">
            <thead class="table-light">
              <tr>
                <th class="ps-3">Trek Name & Location</th>
                <th>Difficulty</th>
                <th>Dates</th>
                <th>Seats</th>
                <th>Booking Date</th>
                <th>Status</th>
                <th class="text-end pe-3">Action</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="b in bookings" :key="b.id">
                <td class="ps-3">
                  <div class="fw-bold text-dark">{{ b.trek_name }}</div>
                  <div class="small text-muted"><i class="bi bi-geo-alt me-1"></i>{{ b.trek_location }}</div>
                </td>
                <td><StatusBadge :status="b.trek_difficulty" /></td>
                <td class="small">
                  <div>{{ b.trek_start_date }}</div>
                  <div class="text-muted">to {{ b.trek_end_date }}</div>
                </td>
                <td><span class="badge bg-secondary">{{ b.seats_booked }}</span></td>
                <td class="small text-muted">{{ b.booking_date }}</td>
                <td><StatusBadge :status="b.status" /></td>
                <td class="text-end pe-3">
                  <button
                    v-if="b.status === 'Confirmed'"
                    class="btn btn-sm btn-outline-danger rounded-pill px-3"
                    @click="openCancelModal(b)"
                  >
                    Cancel Booking
                  </button>
                  <span v-else class="text-muted small">&mdash;</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-else class="text-center py-5 text-muted">
          <p class="mb-2">You haven't booked any treks yet.</p>
          <router-link to="/trekker/dashboard" class="btn btn-primary btn-sm rounded-pill px-3">
            Explore Treks Now
          </router-link>
        </div>
      </div>
    </div>

    <!-- ============================================================= -->
    <!-- POP-UP MODAL: CANCEL RESERVATION CONFIRMATION -->
    <!-- ============================================================= -->
    <div class="modal fade" id="cancelBookingModal" tabindex="-1">
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content border-0 shadow">
          <div class="modal-header bg-light">
            <h5 class="modal-title fw-bold text-danger">
              <i class="bi bi-x-circle-fill me-2"></i>Cancel Trek Reservation
            </h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>
          <div class="modal-body p-4" v-if="cancelTarget">
            <p class="mb-2">Are you sure you want to cancel your reservation for:</p>
            <div class="card bg-light p-3 border-0 mb-3">
              <div class="fw-bold text-dark">{{ cancelTarget.trek_name }}</div>
              <div class="text-muted small"><i class="bi bi-geo-alt me-1"></i>{{ cancelTarget.trek_location }}</div>
              <div class="small mt-2">
                Reserved Seats: <strong>{{ cancelTarget.seats_booked }}</strong> | Date: <strong>{{ cancelTarget.trek_start_date }}</strong>
              </div>
            </div>
            <p class="small text-muted mb-0">
              <i class="bi bi-info-circle me-1 text-primary"></i>
              Your reserved seats will be immediately returned to the public slot availability pool.
            </p>
          </div>
          <div class="modal-footer bg-light">
            <button type="button" class="btn btn-secondary rounded-pill px-3" data-bs-dismiss="modal">Keep Booking</button>
            <button type="button" class="btn btn-danger rounded-pill px-4" @click="confirmCancelBooking" :disabled="cancelling">
              <span v-if="cancelling" class="spinner-border spinner-border-sm me-1"></span>
              Confirm Cancellation
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/services/api'
import StatusBadge from '@/components/StatusBadge.vue'
import { Modal } from 'bootstrap'

const bookings = ref([])
const exporting = ref(false)
const cancelling = ref(false)
const cancelTarget = ref(null)
const alertMsg = ref('')
const alertType = ref('success')

let cancelModalInstance = null

const showAlert = (msg, type = 'success') => {
  alertMsg.value = msg
  alertType.value = type
  setTimeout(() => { alertMsg.value = '' }, 4000)
}

const fetchBookings = async () => {
  try {
    const res = await api.get('/trekker/bookings')
    bookings.value = res.data.bookings || []
  } catch (err) {
    console.error(err)
  }
}

const openCancelModal = (b) => {
  cancelTarget.value = b
  cancelModalInstance = new Modal(document.getElementById('cancelBookingModal'))
  cancelModalInstance.show()
}

const confirmCancelBooking = async () => {
  if (!cancelTarget.value) return
  cancelling.value = true
  try {
    await api.put(`/trekker/bookings/${cancelTarget.value.id}/cancel`)
    cancelModalInstance?.hide()
    showAlert(`Reservation for "${cancelTarget.value.trek_name}" has been cancelled.`, 'info')
    fetchBookings()
  } catch (err) {
    showAlert(err.response?.data?.error || 'Failed to cancel booking', 'danger')
  } finally {
    cancelling.value = false
  }
}

const exportCSV = async () => {
  exporting.value = true
  showAlert('Submitting Celery async batch export task...', 'info')
  try {
    const res = await api.post('/trekker/bookings/export')
    const taskId = res.data.task_id
    showAlert(`Export job #${taskId} submitted! Downloading CSV file...`, 'success')

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
    showAlert(err.response?.data?.error || 'Failed to trigger CSV export', 'danger')
  } finally {
    exporting.value = false
  }
}

onMounted(fetchBookings)
</script>
