export type AuthRole = 'student' | 'employer' | 'institution'

export interface UserProfile {
  id: string
  email: string
  full_name: string
  role: AuthRole
  organization?: string
  created_at: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
  role: AuthRole
}

export interface AuthSession {
  token: string
  role: AuthRole
  user: UserProfile | null
}

export interface CredentialRecord {
  id: string
  student_name?: string
  student_email?: string
  university?: string
  degree?: string
  course?: string
  certificate_number?: string
  status?: string
  created_at?: string
  verification?: {
    authenticity_score?: number
    risk_level?: string
  } | null
}

export interface StudentCredentialsResponse {
  credentials: CredentialRecord[]
  total: number
  student: {
    name: string
    email: string
    role: AuthRole
  }
}

export interface StudentPassportResponse {
  student: {
    name: string
    email: string
    id: string
    organization?: string
  }
  verified_credentials: CredentialRecord[]
  pending_credentials: CredentialRecord[]
  total_verified: number
  total_pending: number
  trust_score: number
}

export interface VerificationPayload {
  certificate_id: string
  status: 'verified' | 'not_verified' | 'pending' | string
  identity: {
    name?: string
    institution?: string
    course?: string
    issue_date?: string
    ocr_confidence?: number
  }
  trust_signals: Array<{
    check: string
    result: 'pass' | 'fail' | string
  }>
  blockchain_proof: {
    tx_hash?: string
    block_number?: number
    timestamp?: string
    verified_by?: string
    network?: string
    certificate_hash?: string
    issuer?: string
    status?: string
  }
}

export interface ResumeVerificationResponse {
  verification_id: string
  status: string
  matched_student: {
    id: string
    name: string
    email: string
  } | null
  skill_results: Array<{
    skill: string
    status: 'verified' | 'not_verified' | string
  }>
}

export interface HistoryRecord {
  id: string
  type: string
  status: string
  filename?: string
  verified_at?: string
  certificate_id?: string | null
}

export interface InstitutionAnalyticsResponse {
  institution: {
    name: string
    email: string
  }
  summary: {
    total_credentials: number
    verified: number
    pending: number
    flagged: number
    analyzing: number
    ai_verification_rate: number
    external_verifications: number
  }
}
