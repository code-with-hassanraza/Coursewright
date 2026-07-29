import api from './api'

export async function getTasksBySpecialization(specId, { page, size } = {}) {
  const { data } = await api.get(`/tasks/specialization/${specId}`, {
    params: { page, size },
  })
  return data
}

export async function getTask(taskId) {
  const { data } = await api.get(`/tasks/${taskId}`)
  return data
}

export async function completeTask(taskId) {
  const { data } = await api.post(`/tasks/${taskId}/complete`, {})
  return data
}