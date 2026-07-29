import api from './api'

export async function getQuiz(specId) {
  try {
    const { data } = await api.get(`/quizzes/specialization/${specId}`)
    return data
  } catch (err) {
    if (err.response?.status === 404) return null
    throw err
  }
}

export async function submitQuiz(quizId, answers) {
  const { data } = await api.post(`/quizzes/${quizId}/submit`, { answers })
  return data
}