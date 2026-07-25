import api from './api'

// ---- Fields ----------------------------------------------------------

export async function getFields() {
  const { data } = await api.get('/fields')
  return data // PaginatedResponse<FieldResponse>
}

export async function getField(fieldId) {
  const { data } = await api.get(`/fields/${fieldId}`)
  return data
}

export async function getFieldSpecializations(fieldId, { page, size } = {}) {
  const { data } = await api.get(`/fields/${fieldId}/specializations`, {
    params: { page, size },
  })
  return data // PaginatedResponse<SpecializationResponse>
}

// ---- Specializations ---------------------------------------------------

export async function searchSpecializations({ fieldId, search, page, size } = {}) {
  const { data } = await api.get('/specializations', {
    params: { field_id: fieldId, search, page, size },
  })
  return data // PaginatedResponse<SpecializationResponse>
}

export async function getSpecialization(specId) {
  const { data } = await api.get(`/specializations/${specId}`)
  return data
}

/**
 * Protected. 400s if the user is already exploring this specialization —
 * the calling page should catch that and treat it as "already started"
 * rather than a real error (see SpecializationDetail's Continue Learning case).
 */
export async function exploreSpecialization(specId, roadmapId) {
  const { data } = await api.post(`/specializations/${specId}/explore`, roadmapId ? { roadmap_id: roadmapId } : {})
  return data // UserProgressResponse
}