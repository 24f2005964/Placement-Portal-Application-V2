<template>
  <div class="row justify-content-center">
    <div class="col-md-6">
      <h3 class="fw-bold text-dark mb-1"><i class="bi bi-person-circle text-primary me-2"></i>My Profile</h3>
      <p class="text-muted small mb-4">Manage your personal information and account security</p>

      <div class="card border-0 shadow-sm rounded-3 p-4">
        <div v-if="successMsg" class="alert alert-success py-2 small mb-3">
          <i class="bi bi-check-circle me-1"></i>{{ successMsg }}
        </div>
        <div v-if="errorMsg" class="alert alert-danger py-2 small mb-3">
          <i class="bi bi-exclamation-triangle me-1"></i>{{ errorMsg }}
        </div>

        <form @submit.prevent="updateProfile">
          <div class="mb-3">
            <label class="form-label small fw-semibold">Full Name</label>
            <input type="text" class="form-control" v-model="form.name" required />
          </div>

          <div class="mb-3">
            <label class="form-label small fw-semibold">Email Address (Read-only)</label>
            <input type="email" class="form-control bg-light" v-model="form.email" readonly />
          </div>

          <div class="mb-3">
            <label class="form-label small fw-semibold">Phone Number</label>
            <input type="tel" class="form-control" v-model="form.phone" placeholder="9876543210" />
          </div>

          <hr class="my-4" />
          <h6 class="fw-bold text-dark mb-3"><i class="bi bi-shield-lock me-1"></i>Change Password (Optional)</h6>

          <div class="mb-3">
            <label class="form-label small fw-semibold">Current Password</label>
            <input type="password" class="form-control" v-model="form.current_password" placeholder="••••••••" />
          </div>

          <div class="mb-3">
            <label class="form-label small fw-semibold">New Password</label>
            <input type="password" class="form-control" v-model="form.new_password" placeholder="Leave blank to keep current" />
          </div>

          <button type="submit" class="btn btn-primary rounded-pill px-4" :disabled="saving">
            <span v-if="saving" class="spinner-border spinner-border-sm me-1"></span>
            Save Profile Changes
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/services/api'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const saving = ref(false)
const successMsg = ref('')
const errorMsg = ref('')

const form = ref({
  name: '',
  email: '',
  phone: '',
  current_password: '',
  new_password: ''
})

const fetchProfile = async () => {
  try {
    const res = await api.get('/trekker/profile')
    const u = res.data.user
    form.value.name = u.name
    form.value.email = u.email
    form.value.phone = u.phone || ''
  } catch (err) {
    console.error(err)
  }
}

const updateProfile = async () => {
  saving.value = true
  successMsg.value = ''
  errorMsg.value = ''
  try {
    const res = await api.put('/trekker/profile', form.value)
    successMsg.value = 'Profile updated successfully!'
    auth.user = res.data.user
    localStorage.setItem('tma_user', JSON.stringify(res.data.user))
    form.value.current_password = ''
    form.value.new_password = ''
  } catch (err) {
    errorMsg.value = err.response?.data?.error || 'Failed to update profile'
  } finally {
    saving.value = false
  }
}

onMounted(fetchProfile)
</script>

