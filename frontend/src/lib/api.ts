import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
})

// 序列相关
export interface Series {
  id: string
  patient_id?: string
  patient_name?: string
  patient_sex?: string
  patient_birth_date?: string
  study_instance_uid?: string
  study_date?: string
  series_instance_uid?: string
  series_number?: number
  series_description?: string
  modality?: string
  protocol_name?: string
  manufacturer?: string
  manufacturer_model?: string
  ct_params?: Record<string, any>
  mr_params?: Record<string, any>
  dx_params?: Record<string, any>
  file_path?: string
  file_count?: number
  file_size_total?: number
  file_modified_date?: string
  created_at?: string
  is_active?: boolean
}

export interface ScanConfig {
  id: number
  scan_path: string
  description?: string
  is_active: boolean
  schedule_type: string
  last_scan_at?: string
  filter_rules?: Record<string, any>
}

export interface Scan {
  id: string
  scan_path: string
  scan_type: string
  started_at?: string
  finished_at?: string
  series_found: number
  series_new: number
  series_duplicated: number
  status: string
}

export interface FilterRule {
  id: number
  modality: string
  min_slice_thickness?: number
  min_image_count?: number
  is_active: boolean
}

export const seriesApi = {
  list: (params: {
    page?: number
    page_size?: number
    patient_id?: string
    patient_name?: string
    modality?: string
    protocol_name?: string
  }) => api.get<{ data: Series[] }>('/series', { params }),

  getById: (id: string) => api.get<Series>(`/series/${id}`),

  count: (params?: {
    patient_id?: string
    patient_name?: string
    modality?: string
  }) => api.get<{ total: number }>('/series/count', { params }),
}

export const configApi = {
  list: () => api.get<ScanConfig[]>('/configs'),

  create: (data: {
    scan_path: string
    description?: string
    schedule_type: string
    filter_rules?: Record<string, any>
  }) => api.post<ScanConfig>('/configs', data),

  update: (id: number, data: Partial<ScanConfig>) => api.put<ScanConfig>(`/configs/${id}`, data),

  delete: (id: number) => api.delete(`/configs/${id}`),
}

export const scanApi = {
  run: (configId: number) => api.post<Scan>(`/scan/${configId}`),

  list: (params?: { page?: number; page_size?: number }) =>
    api.get<Scan[]>('/scans', { params }),
}

export const filterRuleApi = {
  list: () => api.get<FilterRule[]>('/filter-rules'),

  create: (data: {
    modality: string
    min_slice_thickness?: number
    min_image_count?: number
  }) => api.post<FilterRule>('/filter-rules', data),

  delete: (id: number) => api.delete(`/filter-rules/${id}`),
}

export const exportApi = {
  export: (seriesIds: string[], targetDir: string) =>
    api.post('/export', { series_ids: seriesIds, target_dir: targetDir }),
}

export const statsApi = {
  modality: () => api.get<{ modality: string; count: number }[]>('/stats/modality'),

  date: () => api.get<{ date: string; count: number }[]>('/stats/date'),
}
