<template>
  <span :class="badgeClass" class="badge rounded-pill fw-semibold text-uppercase px-2 py-1">
    {{ status }}
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  status: {
    type: String,
    required: true
  }
})

const badgeClass = computed(() => {
  const s = props.status?.toLowerCase() || ''
  switch (s) {
    case 'open':
    case 'confirmed':
    case 'active':
    case 'approved':
      return 'bg-success'
    case 'closed':
    case 'pending':
    case 'moderate':
      return 'bg-warning text-dark'
    case 'completed':
    case 'easy':
      return 'bg-info text-dark'
    case 'cancelled':
    case 'hard':
    case 'inactive':
      return 'bg-danger'
    default:
      return 'bg-secondary'
  }
})
</script>

