import api from './api'

/**
 * Public — only returns a roadmap if its status is "published". Used for
 * previews (SpecializationDetail) and will be extended at Step 13 with the
 * protected GET /roadmaps/{id} (any status) for the main Roadmap page.
 *
 * Assumes 404 (standard REST convention, matching every other single-resource
 * GET in this API) when no published roadmap exists yet, and treats that as
 * a normal "not yet available" state rather than an error.
 */
export async function getRoadmapBySpecialization(specId) {
  try {
    const { data } = await api.get(`/roadmaps/specialization/${specId}`)
    return data
  } catch (err) {
    if (err.response?.status === 404) return null
    throw err
  }
}