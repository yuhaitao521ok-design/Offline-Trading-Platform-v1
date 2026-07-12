export interface ApiErrorDetail {
  code: string
  message: string
  details: Record<string, unknown> | unknown[] | null
}

export interface ApiResponse<T> {
  success: boolean
  data: T | null
  error: ApiErrorDetail | null
  timestamp_utc: string
}

export interface HealthStatus {
  status: 'ok'
  app_name: string
  app_env: 'development' | 'staging' | 'production'
  app_version: string
  server_time_utc: string
}

export interface HttpRequestMeta {
  requestId: string
  startedAt: number
}
