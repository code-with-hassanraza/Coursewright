import api from './api'

export async function sendMessage({ message, specializationId, roadmapId }) {
  const { data } = await api.post('/chat/message', {
    message,
    specialization_id: specializationId || undefined,
    roadmap_id: roadmapId || undefined,
  })
  return data // { reply: string, source: string }
}