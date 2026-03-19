import client from './client'

export const getIncidents = (params = {}) =>
  client.get('/incidents', { params })

export const getIncident = (id) =>
  client.get(`/incidents/${id}`)

export const updateStatus = (id, status, reason = '') =>
  client.patch(`/incidents/${id}/status`, { status, reason })

export const getAuditLog = (id) =>
  client.get(`/incidents/${id}/audit`)
