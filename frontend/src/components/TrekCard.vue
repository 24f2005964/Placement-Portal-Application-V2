<template>
  <div class="card h-100 border-0 shadow-sm rounded-3 overflow-hidden trek-card">
    <div class="card-body d-flex flex-column p-4">
      <div class="d-flex justify-content-between align-items-start mb-2">
        <StatusBadge :status="trek.difficulty" />
        <StatusBadge :status="trek.status" />
      </div>

      <h5 class="fw-bold text-dark mt-2 mb-1">{{ trek.name }}</h5>
      <p class="text-muted small mb-2"><i class="bi bi-geo-alt-fill text-danger me-1"></i>{{ trek.location }}</p>

      <p class="text-secondary small mb-3 flex-grow-1" style="display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">
        {{ trek.description || 'Experience an unforgettable Himalayan journey through panoramic landscapes.' }}
      </p>

      <div class="row g-2 text-center py-2 bg-light rounded-2 mb-3 small">
        <div class="col-4 border-end">
          <div class="text-muted">Duration</div>
          <div class="fw-bold">{{ trek.duration_days }} Days</div>
        </div>
        <div class="col-4 border-end">
          <div class="text-muted">Available</div>
          <div class="fw-bold" :class="trek.available_slots > 0 ? 'text-success' : 'text-danger'">
            {{ trek.available_slots }} / {{ trek.total_slots }}
          </div>
        </div>
        <div class="col-4">
          <div class="text-muted">Start Date</div>
          <div class="fw-bold">{{ trek.start_date }}</div>
        </div>
      </div>

      <div class="d-flex justify-content-between align-items-center mt-auto pt-2 border-top">
        <span class="small text-muted">
          <i class="bi bi-person-badge text-primary me-1"></i>Guide: {{ trek.assigned_staff_name || 'Assigned Guide' }}
        </span>
        <button
          v-if="showBookButton"
          class="btn btn-sm btn-primary px-3 rounded-pill"
          :disabled="trek.status !== 'Open' || trek.available_slots === 0"
          @click="$emit('book', trek)"
        >
          <i class="bi bi-ticket-perforated me-1"></i>{{ trek.available_slots > 0 ? 'Book Now' : 'Full' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import StatusBadge from '@/components/StatusBadge.vue'

defineProps({
  trek: { type: Object, required: true },
  showBookButton: { type: Boolean, default: true }
})

defineEmits(['book'])
</script>

<style scoped>
.trek-card {
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.trek-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 10px 20px rgba(0,0,0,0.08) !important;
}
</style>

