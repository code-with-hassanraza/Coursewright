import api from './api'

/**
 * Protected, own-profile only. Body is partial — only send the fields
 * that actually changed (full_name?, degree?, year_of_study?).
 */
export async function updateUser(userId, payload) {
  const { data } = await api.put(`/users/${userId}`, payload)
  return data // UserResponse
}

export async function getUserProgress(userId, { page, size } = {}) {
  const { data } = await api.get(`/users/${userId}/progress`, {
    params: { page, size },
  })
  return data // PaginatedResponse<UserProgressResponse>
}