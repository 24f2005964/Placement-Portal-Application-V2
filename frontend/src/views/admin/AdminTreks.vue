<template>
  <div>
    <div class="d-flex justify-content-between align-items-center mb-4">
      <div>
        <h3 class="fw-bold text-dark mb-0"><i class="bi bi-map-fill text-primary me-2"></i>Trek Route Management</h3>
        <p class="text-muted small mb-0">Create, edit, schedule, and assign staff to trek routes</p>
      </div>
      <button class="btn btn-primary rounded-pill px-3" @click="openCreateModal">
        <i class="bi bi-plus-circle me-1"></i>Create New Trek
      </button>
    </div>

    <!-- Alert Banner -->
    <div v-if="alertMsg" class="alert alert-dismissible fade show py-2 small shadow-sm mb-3" :class="'alert-' + alertType">
      <i class="bi me-1" :class="alertType === 'success' ? 'bi-check-circle-fill' : 'bi-exclamation-triangle-fill'"></i>
      {{ alertMsg }}
      <button type="button" class="btn-close" @click="alertMsg = ''"></button>
    </div>

    <!-- Search & Filter Controls -->
    <div class="card border-0 shadow-sm rounded-3 p-3 mb-3 bg-white">
      <div class="row g-2 align-items-center">
        <div class="col-md-5">
          <div class="input-group">
            <span class="input-group-text bg-white"><i class="bi bi-search text-muted"></i></span>
            <input
              type="text"
              class="form-control"
              v-model="searchQuery"
              placeholder="Search treks by name or location..."
            />
          </div>
        </div>
        <div class="col-md-3">
          <select class="form-select" v-model="difficultyFilter">
            <option value="All">All Difficulties</option>
            <option value="Easy">Easy</option>
            <option value="Moderate">Moderate</option>
            <option value="Hard">Hard</option>
          </select>
        </div>
        <div class="col-md-2">
          <select class="form-select" v-model="statusFilter">
            <option value="All">All Statuses</option>
            <option value="Open">Open</option>
            <option value="Closed">Closed</option>
            <option value="Completed">Completed</option>
          </select>
        </div>
        <div class="col-md-2 text-end text-muted small">
          Showing <strong>{{ filteredTreks.length }}</strong> of {{ treks.length }}
        </div>
      </div>
    </div>

    <!-- Treks Table Card -->
    <div class="card border-0 shadow-sm rounded-3">
      <div class="card-body p-0">
        <div class="table-responsive">
          <table class="table table-hover align-middle mb-0">
            <thead class="table-light">
              <tr>
                <th class="ps-3">Trek Name & Location</th>
                <th>Difficulty</th>
                <th>Dates</th>
                <th>Slots</th>
                <th>Status</th>
                <th>Assigned Guide</th>
                <th class="text-end pe-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="t in filteredTreks" :key="t.id">
                <td class="ps-3">
                  <div class="fw-bold text-dark">{{ t.name }}</div>
                  <div class="small text-muted"><i class="bi bi-geo-alt me-1"></i>{{ t.location }} ({{ t.duration_days }} days)</div>
                </td>
                <td><StatusBadge :status="t.difficulty" /></td>
                <td class="small">
                  <div>{{ t.start_date }}</div>
                  <div class="text-muted">to {{ t.end_date }}</div>
                </td>
                <td>
                  <span class="fw-semibold">{{ t.available_slots }}</span> / <span class="text-muted">{{ t.total_slots }}</span>
                </td>
                <td><StatusBadge :status="t.status" /></td>
                <td>
                  <span v-if="t.assigned_staff_name && t.assigned_staff_name !== 'Unassigned'" class="badge bg-light text-dark border">
                    <i class="bi bi-person-badge text-primary me-1"></i>{{ t.assigned_staff_name }}
                  </span>
                  <span v-else class="text-muted small italic">Unassigned</span>
                </td>
                <td class="text-end pe-3">
                  <button class="btn btn-sm btn-outline-primary me-1 rounded-pill" @click="openAssignModal(t)" title="Assign Guide">
                    <i class="bi bi-person-plus me-1"></i>Guide
                  </button>
                  <button class="btn btn-sm btn-outline-secondary me-1 rounded-pill" @click="openEditModal(t)" title="Edit Trek">
                    <i class="bi bi-pencil"></i>
                  </button>
                  <button class="btn btn-sm btn-outline-danger rounded-pill" @click="openDeleteModal(t)" title="Delete Trek">
                    <i class="bi bi-trash"></i>
                  </button>
                </td>
              </tr>
              <tr v-if="filteredTreks.length === 0">
                <td colspan="7" class="text-center py-4 text-muted">
                  <i class="bi bi-inbox fs-4 d-block mb-1"></i>
                  No trekking routes found matching your search or filter criteria.
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- ============================================================= -->
    <!-- POP-UP MODAL 1: CREATE / EDIT TREK -->
    <!-- ============================================================= -->
    <div class="modal fade" id="trekModal" tabindex="-1">
      <div class="modal-dialog modal-lg modal-dialog-centered">
        <div class="modal-content border-0 shadow">
          <div class="modal-header bg-light">
            <h5 class="modal-title fw-bold text-dark">{{ isEditing ? 'Edit Trek Route' : 'Create New Trek Route' }}</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>
          <form @submit.prevent="saveTrek">
            <div class="modal-body p-4">
              <div class="row g-3">
                <div class="col-md-8">
                  <label class="form-label small fw-semibold">Trek Name</label>
                  <input type="text" class="form-control" v-model="form.name" required />
                </div>
                <div class="col-md-4">
                  <label class="form-label small fw-semibold">Difficulty</label>
                  <select class="form-select" v-model="form.difficulty">
                    <option value="Easy">Easy</option>
                    <option value="Moderate">Moderate</option>
                    <option value="Hard">Hard</option>
                  </select>
                </div>
                <div class="col-md-6">
                  <label class="form-label small fw-semibold">Location</label>
                  <input type="text" class="form-control" v-model="form.location" required />
                </div>
                <div class="col-md-3">
                  <label class="form-label small fw-semibold">Duration (Days)</label>
                  <input type="number" class="form-control" v-model.number="form.duration_days" min="1" required />
                </div>
                <div class="col-md-3">
                  <label class="form-label small fw-semibold">Total Capacity Slots</label>
                  <input type="number" class="form-control" v-model.number="form.total_slots" min="1" required />
                </div>
                <div class="col-md-6">
                  <label class="form-label small fw-semibold">Start Date</label>
                  <input type="date" class="form-control" v-model="form.start_date" required />
                </div>
                <div class="col-md-6">
                  <label class="form-label small fw-semibold">End Date</label>
                  <input type="date" class="form-control" v-model="form.end_date" required />
                </div>
                <div class="col-md-6">
                  <label class="form-label small fw-semibold">Status</label>
                  <select class="form-select" v-model="form.status">
                    <option value="Open">Open</option>
                    <option value="Closed">Closed</option>
                    <option value="Completed">Completed</option>
                  </select>
                </div>
                <div class="col-md-6">
                  <label class="form-label small fw-semibold">Assign Staff Guide</label>
                  <select class="form-select" v-model="form.assigned_staff_id">
                    <option :value="null">-- Unassigned --</option>
                    <option v-for="s in staffList" :key="s.id" :value="s.id">{{ s.name }} ({{ s.email }})</option>
                  </select>
                </div>
                <div class="col-12">
                  <label class="form-label small fw-semibold">Description</label>
                  <textarea class="form-control" v-model="form.description" rows="3"></textarea>
                </div>
              </div>
            </div>
            <div class="modal-footer bg-light">
              <button type="button" class="btn btn-secondary rounded-pill px-3" data-bs-dismiss="modal">Cancel</button>
              <button type="submit" class="btn btn-primary rounded-pill px-4">Save Trek</button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- ============================================================= -->
    <!-- POP-UP MODAL 2: ASSIGN GUIDE (POP-UP WINDOW) -->
    <!-- ============================================================= -->
    <div class="modal fade" id="assignGuideModal" tabindex="-1">
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content border-0 shadow">
          <div class="modal-header bg-light">
            <h5 class="modal-title fw-bold text-dark">
              <i class="bi bi-person-plus text-primary me-2"></i>Assign Trek Guide
            </h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>
          <form @submit.prevent="saveAssignedGuide">
            <div class="modal-body p-4" v-if="assignTrekTarget">
              <h6 class="fw-bold mb-1">{{ assignTrekTarget.name }}</h6>
              <p class="text-muted small mb-3">{{ assignTrekTarget.location }}</p>

              <div class="mb-3">
                <label class="form-label small fw-semibold">Select Certified Staff Member</label>
                <select class="form-select form-select-lg" v-model="selectedStaffId">
                  <option :value="null">-- Leave Unassigned --</option>
                  <option v-for="s in staffList" :key="s.id" :value="s.id">
                    {{ s.name }} ({{ s.email }})
                  </option>
                </select>
                <div class="form-text small">Only approved and active staff members appear in this list.</div>
              </div>
            </div>
            <div class="modal-footer bg-light">
              <button type="button" class="btn btn-secondary rounded-pill px-3" data-bs-dismiss="modal">Cancel</button>
              <button type="submit" class="btn btn-primary rounded-pill px-4">Save Assignment</button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- ============================================================= -->
    <!-- POP-UP MODAL 3: DELETE CONFIRMATION (POP-UP WINDOW) -->
    <!-- ============================================================= -->
    <div class="modal fade" id="deleteConfirmModal" tabindex="-1">
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content border-0 shadow">
          <div class="modal-header bg-light">
            <h5 class="modal-title fw-bold text-danger">
              <i class="bi bi-exclamation-triangle-fill me-2"></i>Delete Trek Route
            </h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>
          <div class="modal-body p-4" v-if="deleteTarget">
            <p class="mb-2">Are you sure you want to permanently remove this trek route?</p>
            <div class="card bg-light p-3 border-0">
              <div class="fw-bold">{{ deleteTarget.name }}</div>
              <div class="text-muted small">{{ deleteTarget.location }}</div>
            </div>
            <p class="small text-danger mt-3 mb-0">
              <i class="bi bi-info-circle me-1"></i>All linked reservations and history for this route will also be removed.
            </p>
          </div>
          <div class="modal-footer bg-light">
            <button type="button" class="btn btn-secondary rounded-pill px-3" data-bs-dismiss="modal">Cancel</button>
            <button type="button" class="btn btn-danger rounded-pill px-4" @click="confirmDelete">Confirm Delete</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/services/api'
import StatusBadge from '@/components/StatusBadge.vue'
import { Modal } from 'bootstrap'

const treks = ref([])
const staffList = ref([])
const isEditing = ref(false)
const editingId = ref(null)
const alertMsg = ref('')
const alertType = ref('success')

const searchQuery = ref('')
const difficultyFilter = ref('All')
const statusFilter = ref('All')

const filteredTreks = computed(() => {
  return treks.value.filter(t => {
    const q = searchQuery.value.trim().toLowerCase()
    const matchesQuery = !q || (t.name && t.name.toLowerCase().includes(q)) || (t.location && t.location.toLowerCase().includes(q))
    const matchesDiff = difficultyFilter.value === 'All' || t.difficulty === difficultyFilter.value
    const matchesStatus = statusFilter.value === 'All' || t.status === statusFilter.value
    return matchesQuery && matchesDiff && matchesStatus
  })
})

const form = ref({
  name: '',
  location: '',
  difficulty: 'Moderate',
  duration_days: 3,
  total_slots: 20,
  start_date: '',
  end_date: '',
  status: 'Open',
  assigned_staff_id: null,
  description: ''
})

const assignTrekTarget = ref(null)
const selectedStaffId = ref(null)
const deleteTarget = ref(null)

let trekModal = null
let assignModal = null
let deleteModal = null

const showAlert = (msg, type = 'success') => {
  alertMsg.value = msg
  alertType.value = type
  setTimeout(() => { alertMsg.value = '' }, 4000)
}

const fetchTreks = async () => {
  try {
    const res = await api.get('/admin/treks')
    treks.value = res.data.treks || []
  } catch (err) {
    console.error(err)
  }
}

const fetchStaff = async () => {
  try {
    const res = await api.get('/admin/users?role=staff')
    staffList.value = (res.data.users || []).filter(u => u.is_approved)
  } catch (err) {
    console.error(err)
  }
}

const openCreateModal = () => {
  isEditing.value = false
  editingId.value = null
  form.value = {
    name: '',
    location: '',
    difficulty: 'Moderate',
    duration_days: 3,
    total_slots: 20,
    start_date: '',
    end_date: '',
    status: 'Open',
    assigned_staff_id: null,
    description: ''
  }
  trekModal = new Modal(document.getElementById('trekModal'))
  trekModal.show()
}

const openEditModal = (t) => {
  isEditing.value = true
  editingId.value = t.id
  form.value = { ...t }
  trekModal = new Modal(document.getElementById('trekModal'))
  trekModal.show()
}

const saveTrek = async () => {
  try {
    if (isEditing.value) {
      await api.put(`/admin/treks/${editingId.value}`, form.value)
      showAlert(`Trek "${form.value.name}" updated successfully.`, 'success')
    } else {
      await api.post('/admin/treks', form.value)
      showAlert(`Trek "${form.value.name}" created successfully.`, 'success')
    }
    trekModal?.hide()
    fetchTreks()
  } catch (err) {
    showAlert(err.response?.data?.error || 'Failed to save trek', 'danger')
  }
}

const openAssignModal = (t) => {
  assignTrekTarget.value = t
  selectedStaffId.value = t.assigned_staff_id || null
  assignModal = new Modal(document.getElementById('assignGuideModal'))
  assignModal.show()
}

const saveAssignedGuide = async () => {
  if (!assignTrekTarget.value) return
  try {
    await api.put(`/admin/treks/${assignTrekTarget.value.id}/assign-staff`, {
      staff_id: selectedStaffId.value
    })
    assignModal?.hide()
    showAlert(`Guide assigned for "${assignTrekTarget.value.name}".`, 'success')
    fetchTreks()
  } catch (err) {
    showAlert(err.response?.data?.error || 'Failed to assign guide.', 'danger')
  }
}

const openDeleteModal = (t) => {
  deleteTarget.value = t
  deleteModal = new Modal(document.getElementById('deleteConfirmModal'))
  deleteModal.show()
}

const confirmDelete = async () => {
  if (!deleteTarget.value) return
  try {
    await api.delete(`/admin/treks/${deleteTarget.value.id}`)
    deleteModal?.hide()
    showAlert(`Trek "${deleteTarget.value.name}" deleted successfully.`, 'success')
    fetchTreks()
  } catch (err) {
    showAlert(err.response?.data?.error || 'Failed to delete trek', 'danger')
  }
}

onMounted(() => {
  fetchTreks()
  fetchStaff()
})
</script>
