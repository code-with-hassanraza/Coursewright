import api from './api'

/**
 * Public — only returns a roadmap if its status is "published". Used for
 * previews (SpecializationDetail) and as a fallback on the main Roadmap
 * page when there's no progress record pinning a specific version yet.
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

/**
 * Protected — returns a roadmap regardless of status (draft/in_review/
 * published), keyed by the roadmap's OWN id rather than a specialization.
 * Used to keep a student pinned to the exact version they started on
 * (via UserProgressResponse.roadmap_id) even if a newer version has since
 * been published with different/reordered node ids.
 */
export async function getRoadmapById(roadmapId) {
  const { data } = await api.get(`/roadmaps/${roadmapId}`)
  return data
}