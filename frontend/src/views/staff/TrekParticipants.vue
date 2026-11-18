<template>
  <div>
    <div class="d-flex justify-content-between align-items-center mb-4">
      <div>
        <router-link to="/staff/dashboard" class="btn btn-sm btn-outline-secondary mb-2">&larr; Back to Dashboard</router-link>
        <h3 class="fw-bold text-dark mb-0"><i class="bi bi-people-fill text-success me-2"></i>Participant Roster</h3>
        <p class="text-muted small mb-0">{{ rosterData.trek_name }} (Capacity: {{ rosterData.available_slots }}/{{ rosterData.total_slots }} available)</p>
      </div>
      <span class="badge bg-primary fs-6 px-3 py-2">
        {{ rosterData.participants_count || 0 }} Confirmed Trekkers
      </span>
    </div>

    <div class="card border-0 shadow-sm rounded-3">
      <div class="card-body p-0">
        <div class="table-responsive" v-if="rosterData.roster && rosterData.roster.length > 0">
          <table class="table table-hover align-middle mb-0">
            <thead class="table-light">
              <tr>
                <th class="ps-3">Trekker Name</th>
                <th>Email</th>
                <th>Phone</th>
                <th>Seats Reserved</th>
                <th>Booking Date</th>
                <th class="text-end pe-3">Status</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="p in rosterData.roster" :key="p.booking_id">
                <td class="ps-3 fw-bold text-dark">{{ p.trekker_name }}</td>
                <td>{{ p.email }}</td>
                <td>{{ p.phone || 'N/A' }}</td>
                <td><span class="badge bg-secondary">{{ p.seats_booked }}</span></td>
                <td class="small text-muted">{{ p.booking_date }}</td>
                <td class="text-end pe-3"><StatusBadge :status="p.status" /></td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-else class="text-center py-5 text-muted">
          No trekkers have booked this trek yet.
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/services/api'
import StatusBadge from '@/components/StatusBadge.vue'

const route = useRoute()
const rosterData = ref({})

const fetchRoster = async () => {
  try {
    const res = await api.get(`/staff/treks/${route.params.id}/participants`)
    rosterData.value = res.data || {}
  } catch (err) {
    console.error(err)
  }
}

onMounted(fetchRoster)
</script>

