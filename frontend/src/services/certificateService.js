import api from './api'

export async function getMyCertificates() {
  const { data } = await api.get('/certificates/me')
  return data
}

export async function generateCertificate(specializationId) {
  const { data } = await api.post('/certificates/generate', { specialization_id: specializationId })
  return data
}

export async function verifyCertificate(code) {
  const { data } = await api.get(`/certificates/verify/${code}`)
  return data
}