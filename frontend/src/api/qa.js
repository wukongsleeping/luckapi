import request from './request'

export function getQaRecords(params = {}) {
  return request.get('/qa-records', { params })
}

export function getQaRecord(id) {
  return request.get(`/qa-records/${id}`)
}

export function deleteQaRecord(id) {
  return request.delete(`/qa-records/${id}`)
}

export function exportQaRecords(params = {}) {
  return request.get('/qa-records/export', {
    params,
    responseType: 'blob',
  })
}
