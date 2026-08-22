import type {
  AuthResponse,
  AuthRole,
  CredentialRecord,
  HistoryRecord,
  InstitutionAnalyticsResponse,
  ResumeVerificationResponse,
  StudentCredentialsResponse,
  StudentPassportResponse,
  UserProfile,
  VerificationPayload,
} from './types'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

async function request<T>(path: string, init?: RequestInit, token?: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      ...(init?.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init?.headers,
    },
  })

  if (!response.ok) {
    let message = 'Request failed'
    try {
      const data = await response.json()
      message = data.detail ?? data.message ?? message
    } catch {
      message = response.statusText || message
    }
    throw new Error(message)
  }

  return response.json() as Promise<T>
}

export function signup(payload: {
  full_name: string
  email: string
  password: string
  role: AuthRole
  organization?: string
}) {
  return request<UserProfile>('/auth/signup', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function login(payload: { email: string; password: string }) {
  return request<AuthResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function getMe(token: string) {
  return request<UserProfile>('/auth/me', { method: 'GET' }, token)
}

export function getStudentCredentials(token: string) {
  return request<StudentCredentialsResponse>('/student/credentials', { method: 'GET' }, token)
}

export function getStudentPassport(token: string) {
  return request<StudentPassportResponse>('/student/passport', { method: 'GET' }, token)
}

export function getInstitutionCredentials(token: string) {
  return request<{ credentials: CredentialRecord[]; total: number }>('/institution/credentials', { method: 'GET' }, token)
}

export function getInstitutionAnalytics(token: string) {
  return request<InstitutionAnalyticsResponse>('/institution/analytics', { method: 'GET' }, token)
}

export function createInstitutionCertificate(token: string, form: FormData) {
  return request<CredentialRecord>('/institution/certificates', {
    method: 'POST',
    body: form,
  }, token)
}

export function bulkInstitutionCertificates(token: string, rows: Array<Record<string, string>>) {
  return request<{ created: number; certificate_ids: string[] }>('/institution/certificates/bulk', {
    method: 'POST',
    body: JSON.stringify(rows),
  }, token)
}

export function verifyEmployerCertificate(token: string, form: FormData) {
  return request<VerificationPayload>('/employer/verify-certificate', {
    method: 'POST',
    body: form,
  }, token)
}

export function verifyEmployerResume(token: string, form: FormData) {
  return request<ResumeVerificationResponse>('/employer/verify-resume', {
    method: 'POST',
    body: form,
  }, token)
}

export function getEmployerHistory(token: string) {
  return request<{ history: HistoryRecord[]; total: number }>('/employer/verification-history', { method: 'GET' }, token)
}

export function getVerificationByCertificateId(token: string, certificateId: string) {
  return request<VerificationPayload>(`/verify/${certificateId}`, { method: 'GET' }, token)
}
