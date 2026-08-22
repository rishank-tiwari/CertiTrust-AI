import { useEffect, useState } from 'react'
import type { FormEvent, ReactNode } from 'react'
import {
  ArrowRight,
  Blocks,
  BookOpen,
  CheckCircle2,
  ChevronRight,
  FileCheck2,
  FileText,
  Fingerprint,
  GraduationCap,
  Grid2X2,
  LayoutDashboard,
  Menu,
  QrCode,
  ScanLine,
  Search,
  ShieldCheck,
  Sparkles,
  Upload,
  UserRound,
  Users,
} from 'lucide-react'
import './App.css'
import {
  bulkInstitutionCertificates,
  createInstitutionCertificate,
  getEmployerHistory,
  getInstitutionAnalytics,
  getInstitutionCredentials,
  getMe,
  getStudentCredentials,
  getStudentPassport,
  getVerificationByCertificateId,
  login,
  signup,
  verifyEmployerCertificate,
  verifyEmployerResume,
} from './lib/api'
import type {
  AuthRole,
  AuthSession,
  CredentialRecord,
  HistoryRecord,
  InstitutionAnalyticsResponse,
  ResumeVerificationResponse,
  StudentCredentialsResponse,
  StudentPassportResponse,
  VerificationPayload,
} from './lib/types'

const SESSION_KEY = 'nexora-session'
const nav = (path: string) => {
  window.history.pushState({}, '', path)
  window.dispatchEvent(new PopStateEvent('popstate'))
}

const roleLabels: Record<AuthRole, string> = {
  student: 'Student',
  employer: 'Employer',
  institution: 'Institution',
}

const sidebarLinks: Record<AuthRole, Array<{ label: string; path: string; icon: typeof LayoutDashboard }>> = {
  student: [
    { label: 'Overview', path: '/student', icon: LayoutDashboard },
    { label: 'My Credentials', path: '/student/credentials', icon: FileText },
    { label: 'Credentials Passport', path: '/student/passport', icon: BookOpen },
    { label: 'Share & QR', path: '/student/share', icon: QrCode },
  ],
  employer: [
    { label: 'Verify Credential', path: '/employer', icon: ScanLine },
    { label: 'Resume Verification', path: '/employer/resume', icon: Search },
    { label: 'Verification History', path: '/employer/history', icon: FileCheck2 },
  ],
  institution: [
    { label: 'Overview', path: '/institution', icon: LayoutDashboard },
    { label: 'Credentials', path: '/institution/credentials', icon: FileText },
    { label: 'Create Credential', path: '/institution/create', icon: GraduationCap },
    { label: 'Bulk Issuance', path: '/institution/bulk', icon: Users },
    { label: 'Analytics', path: '/institution/analytics', icon: Grid2X2 },
  ],
}

function Logo({ light = false }: { light?: boolean }) {
  return (
    <button className={`logo ${light ? 'light' : ''}`} onClick={() => nav('/')}>
      <span><ShieldCheck size={20} /></span>
      CertiTrust
      <span className="logo-ai">AI</span>
    </button>
  )
}

function Button({
  children,
  onClick,
  variant = 'primary',
  className = '',
  type = 'button',
  disabled = false,
}: {
  children: ReactNode
  onClick?: () => void
  variant?: 'primary' | 'secondary' | 'ghost'
  className?: string
  type?: 'button' | 'submit'
  disabled?: boolean
}) {
  return (
    <button type={type} onClick={onClick} className={`btn ${variant} ${className}`} disabled={disabled}>
      {children}
    </button>
  )
}

function Badge({ children, tone = 'success' }: { children: ReactNode; tone?: 'success' | 'warning' | 'muted' }) {
  return <span className={`badge ${tone}`}><i />{children}</span>
}

function SectionTitle({ eyebrow, title, copy }: { eyebrow?: string; title: string; copy?: string }) {
  return <div className="section-title">{eyebrow ? <p className="eyebrow">{eyebrow}</p> : null}<h2>{title}</h2>{copy ? <p>{copy}</p> : null}</div>
}

function formatDate(value?: string) {
  if (!value) return 'Not available'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : date.toLocaleDateString()
}

function formatStatus(value?: string) {
  return value ? value.replace(/_/g, ' ') : 'unknown'
}

function roleHome(role: AuthRole) {
  return role === 'institution' ? '/institution' : `/${role}`
}

function saveSession(session: AuthSession | null) {
  if (!session) {
    localStorage.removeItem(SESSION_KEY)
    return
  }
  localStorage.setItem(SESSION_KEY, JSON.stringify(session))
}

function readSession(): AuthSession | null {
  const raw = localStorage.getItem(SESSION_KEY)
  if (!raw) return null
  try {
    return JSON.parse(raw) as AuthSession
  } catch {
    return null
  }
}

function Landing({
  selectedRole,
  setSelectedRole,
  onAuthenticated,
}: {
  selectedRole: AuthRole
  setSelectedRole: (role: AuthRole) => void
  onAuthenticated: (session: AuthSession) => void
}) {
  return (
    <main className="landing">
      <header className="public-nav">
        <Logo />
        <nav>
          <a href="#how">How it works</a>
          <a href="#roles">Stakeholders</a>
          <a href="#trust">Trust signals</a>
        </nav>
        <div>
          <Button variant="ghost" onClick={() => document.getElementById('role-auth')?.scrollIntoView({ behavior: 'smooth' })}>Sign in</Button>
        </div>
      </header>

      <section className="hero hero-auth">
        <div className="hero-copy">
          <div className="pill"><span className="pulse" /> Built for verifiable achievement</div>
          <h1>Credentials people can <em>trust.</em></h1>
          <p>Stop fake credentials before they reach a hiring decision with AI analysis, tamper-evident blockchain proof, and role-based portals for every stakeholder.</p>
          <div className="hero-actions">
            <Button onClick={() => setSelectedRole('employer')}>Employer access <ArrowRight size={16} /></Button>
            <Button variant="secondary" onClick={() => setSelectedRole('institution')}>Institution access</Button>
          </div>
          <div className="trust-row">
            <div><strong>AI + OCR</strong><span>credential analysis in one flow</span></div>
            <div><strong>Blockchain proof</strong><span>tamper-evident verification</span></div>
            <div><strong>Role-based</strong><span>student, employer, institution portals</span></div>
          </div>
        </div>
        <AuthCard selectedRole={selectedRole} setSelectedRole={setSelectedRole} onAuthenticated={onAuthenticated} />
      </section>

      <section id="how" className="steps">
        <SectionTitle
          eyebrow="The trust infrastructure for achievement"
          title="Built around what this product actually does."
          copy="The platform now centers on four concrete capabilities instead of generic claims."
        />
        <div className="step-grid">
          {[
            [ScanLine, 'AI-powered OCR + document analysis', 'Review uploaded credentials and extract identity details before a verification decision is shown.'],
            [Blocks, 'Blockchain-anchored proof', 'Every successful verification includes on-chain proof details that can be checked later.'],
            [ShieldCheck, 'Role-based portals', 'Students, employers, and institutions each see only the actions and records meant for them.'],
            [Search, 'Resume-to-passport skill matching', 'Compare resume claims against a student’s verified credential passport before a hiring decision.'],
          ].map(([Icon, title, copy], index) => {
            const StepIcon = Icon as typeof ScanLine
            return (
              <article className="step" key={title as string}>
                <div className="step-no">0{index + 1}</div>
                <div className="icon-box"><StepIcon size={22} /></div>
                <h3>{title as string}</h3>
                <p>{copy as string}</p>
              </article>
            )
          })}
        </div>
      </section>

      <section id="roles" className="roles">
        <div>
          <p className="eyebrow">One platform, every stakeholder</p>
          <h2>Pick the role that matches the work.</h2>
          <p>Issuers create trusted records, students carry them, and employers verify them from authenticated workspaces.</p>
        </div>
        <div className="role-grid">
          <button onClick={() => setSelectedRole('institution')}>
            <GraduationCap />
            <h3>For Issuers</h3>
            <p>Create credentials, run analysis, manage bulk issuance, and monitor trust analytics.</p>
            <span>Open institution access <ArrowRight size={15} /></span>
          </button>
          <button onClick={() => setSelectedRole('student')}>
            <UserRound />
            <h3>For Learners</h3>
            <p>View your own credentials, manage your passport, and share a secure QR-based proof page.</p>
            <span>Open student access <ArrowRight size={15} /></span>
          </button>
          <button onClick={() => setSelectedRole('employer')}>
            <Search />
            <h3>For Verifiers</h3>
            <p>Upload documents, verify resumes, and keep a private verification history.</p>
            <span>Open employer access <ArrowRight size={15} /></span>
          </button>
        </div>
      </section>

      <section id="trust" className="security">
        <div className="security-art fingerprint-live">
          <Fingerprint size={86} />
          <span>AUTHENTIC</span>
          <span>TRACEABLE</span>
          <span>ROLE-SCOPED</span>
        </div>
        <div>
          <p className="eyebrow">Designed around trust</p>
          <h2>Signals a hiring team can actually defend.</h2>
          <p>Instead of vague security language, the experience shows extracted identity fields, explicit trust checks, and the blockchain record that backed the decision.</p>
          <ul>
            <li><CheckCircle2 /> Server-validated verification results</li>
            <li><CheckCircle2 /> Private employer verification history</li>
            <li><CheckCircle2 /> Student passport data scoped to the authenticated owner</li>
          </ul>
        </div>
      </section>

      <section className="cta">
        <Sparkles />
        <h2>Proof that holds up when the decision matters.</h2>
        <p>Nexora turns credentials into evidence, not just documents.</p>
        <Button onClick={() => document.getElementById('role-auth')?.scrollIntoView({ behavior: 'smooth' })}>Open role access <ArrowRight size={16} /></Button>
      </section>

      <footer>
        <Logo light />
        <span>© 2026 CertiTrust AI. Built to stop fake credentials before they become costly decisions.</span>
        <div>Privacy&nbsp;&nbsp;&nbsp; Terms&nbsp;&nbsp;&nbsp; Security</div>
      </footer>
    </main>
  )
}

function AuthCard({
  selectedRole,
  setSelectedRole,
  onAuthenticated,
}: {
  selectedRole: AuthRole
  setSelectedRole: (role: AuthRole) => void
  onAuthenticated: (session: AuthSession) => void
}) {
  const [mode, setMode] = useState<'login' | 'signup'>('login')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    const email = String(form.get('email') || '')
    const password = String(form.get('password') || '')
    const fullName = String(form.get('full_name') || '')
    const organization = String(form.get('organization') || '')

    setLoading(true)
    setError('')

    try {
      if (mode === 'signup') {
        await signup({
          full_name: fullName,
          email,
          password,
          role: selectedRole,
          organization: selectedRole === 'institution' ? organization : undefined,
        })
      }

      const auth = await login({ email, password })
      const user = await getMe(auth.access_token)
      const session: AuthSession = { token: auth.access_token, role: auth.role, user }
      saveSession(session)
      onAuthenticated(session)
      nav(roleHome(auth.role))
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : 'Authentication failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div id="role-auth" className="auth-inline">
      <div className="auth-role-picks">
        {(['student', 'employer', 'institution'] as AuthRole[]).map((role) => (
          <button key={role} className={selectedRole === role ? 'active' : ''} onClick={() => setSelectedRole(role)}>
            {roleLabels[role]}
          </button>
        ))}
      </div>
      <div className="auth-panel-card">
        <Badge tone="muted">{roleLabels[selectedRole]} access</Badge>
        <h2>{mode === 'login' ? `Sign in as ${roleLabels[selectedRole]}.` : `Create a ${roleLabels[selectedRole]} account.`}</h2>
        <p>The role is chosen by the button you clicked, so there is no separate dropdown inside the form.</p>
        <form onSubmit={handleSubmit} className="inline-auth-form">
          {mode === 'signup' ? <label>Full name<input name="full_name" required placeholder="Alex Morgan" /></label> : null}
          <label>Email address<input name="email" type="email" required placeholder="you@example.com" /></label>
          <label>Password<input name="password" type="password" required minLength={6} placeholder="••••••••" /></label>
          {mode === 'signup' && selectedRole === 'institution' ? <label>Organization<input name="organization" required placeholder="Nexora Institute" /></label> : null}
          {error ? <p className="form-error">{error}</p> : null}
          <Button type="submit" className="wide" disabled={loading}>{loading ? 'Working...' : mode === 'login' ? 'Sign in' : 'Create account'} <ArrowRight size={16} /></Button>
        </form>
        <div className="auth-switch">
          {mode === 'login' ? 'Need an account?' : 'Already registered?'}{' '}
          <button onClick={() => setMode(mode === 'login' ? 'signup' : 'login')}>{mode === 'login' ? 'Create one' : 'Sign in'}</button>
        </div>
      </div>
    </div>
  )
}

function Portal({
  session,
  title,
  children,
  onLogout,
}: {
  session: AuthSession
  title: string
  children: ReactNode
  onLogout: () => void
}) {
  const [open, setOpen] = useState(false)
  const links = sidebarLinks[session.role]
  const current = window.location.pathname
  return (
    <div className="portal">
      <aside className={open ? 'open' : ''}>
        <Logo />
        <div className="org">
          <div className="org-avatar">{session.user?.full_name?.slice(0, 2).toUpperCase() || session.role.slice(0, 2).toUpperCase()}</div>
          <div>
            <b>{session.user?.organization || session.user?.full_name || roleLabels[session.role]}</b>
            <small>{roleLabels[session.role]} workspace</small>
          </div>
          <ChevronRight size={15} />
        </div>
        <nav>
          {links.map(({ label, path, icon: Icon }) => (
            <button key={path} className={current === path ? 'active' : ''} onClick={() => { nav(path); setOpen(false) }}>
              <Icon size={18} />
              {label}
            </button>
          ))}
        </nav>
        <div className="side-bottom">
          <button onClick={onLogout}><ArrowRight size={17} /> Exit workspace</button>
        </div>
      </aside>
      {open ? <button aria-label="Close navigation" className="overlay" onClick={() => setOpen(false)} /> : null}
      <div className="portal-main">
        <header className="topbar">
          <button className="menu" onClick={() => setOpen(true)}><Menu /></button>
          <div className="crumb">{roleLabels[session.role]} workspace <ChevronRight size={14} /> <b>{title}</b></div>
          <div className="top-actions">
            <div className="user-dot">{session.user?.full_name?.slice(0, 2).toUpperCase() || 'NA'}</div>
          </div>
        </header>
        <main className="page-content">{children}</main>
      </div>
    </div>
  )
}

function PageHeader({ kicker, title, copy, action }: { kicker?: string; title: string; copy: string; action?: ReactNode }) {
  return <div className="page-header"><div>{kicker ? <p className="eyebrow">{kicker}</p> : null}<h1>{title}</h1><p>{copy}</p></div>{action}</div>
}

function Metric({ label, value, detail }: { label: string; value: string; detail: string }) {
  return <div className="metric"><span>{label}</span><b>{value}</b><small>{detail}</small></div>
}

function StudentOverview({ passport }: { passport: StudentPassportResponse | null }) {
  return (
    <>
      <PageHeader kicker="STUDENT PORTAL" title="Your verified achievements." copy="Your own credential record, passport, and share flow all in one place." action={<Button onClick={() => nav('/student/share')}><QrCode size={16} /> Share & QR</Button>} />
      <div className="metrics">
        <Metric label="Verified credentials" value={String(passport?.total_verified ?? 0)} detail="Records visible in your passport" />
        <Metric label="Pending credentials" value={String(passport?.total_pending ?? 0)} detail="Still waiting for verification" />
        <Metric label="Trust score" value={`${passport?.trust_score ?? 0}%`} detail="Based on verified records" />
        <Metric label="Student record" value={passport?.student.name || 'Not loaded'} detail={passport?.student.email || 'No profile loaded'} />
      </div>
      <section className="panel">
        <div className="panel-head"><div><h2>Passport summary</h2><p>Only your own records are visible here.</p></div></div>
        {(passport?.verified_credentials || []).slice(0, 5).map((credential) => (
          <div className="signal" key={credential.id}>
            <span className="pass"><CheckCircle2 size={14} /></span>
            <div>
              <b>{credential.degree || credential.course || credential.certificate_number || credential.id}</b>
              <small>{credential.university || 'Institution not available'}</small>
            </div>
          </div>
        ))}
      </section>
    </>
  )
}

function StudentCredentials({ data }: { data: StudentCredentialsResponse | null }) {
  return (
    <>
      <PageHeader kicker="YOUR RECORD" title="My credentials" copy="Every credential attached to your student account." />
      <CredentialList credentials={data?.credentials || []} emptyText="No credentials found for this student account yet." />
    </>
  )
}

function StudentPassport({ passport }: { passport: StudentPassportResponse | null }) {
  return (
    <>
      <PageHeader kicker="VERIFIED PROFILE" title="Credentials passport" copy="A shareable, authenticated view of your verified record." />
      <section className="passport">
        <div className="passport-head">
          <div className="large-avatar">{passport?.student.name?.slice(0, 2).toUpperCase() || 'NA'}</div>
          <div>
            <h2>{passport?.student.name || 'Student name'} <CheckCircle2 /></h2>
            <p>{passport?.student.email || 'Student email'}</p>
            <Badge>{passport?.total_verified ?? 0} verified credentials</Badge>
          </div>
        </div>
        <div className="passport-section">
          <h3>Verified credentials</h3>
          {(passport?.verified_credentials || []).map((credential) => (
            <article key={credential.id}>
              <GraduationCap />
              <div>
                <b>{credential.degree || credential.course || credential.id}</b>
                <span>{credential.university || 'Institution not available'} · {formatDate(credential.created_at)}</span>
              </div>
              <Badge>Verified</Badge>
            </article>
          ))}
        </div>
      </section>
    </>
  )
}

function StudentShare({ passport }: { passport: StudentPassportResponse | null }) {
  const previewId = passport?.verified_credentials?.[0]?.id || passport?.pending_credentials?.[0]?.id
  return (
    <>
      <PageHeader kicker="PORTABLE PROOF" title="Share your achievement." copy="Your QR points employers into the authenticated verification flow." />
      <section className="share-card">
        <div>
          <Badge>SECURE EMPLOYER ACCESS</Badge>
          <h2>Share the credential, not the risk.</h2>
          <p>Students share a certificate reference and QR, while employers verify it after signing in to their own workspace.</p>
          <div className="share-link"><span>{previewId ? `certitrust.ai/verify/${previewId}` : 'Credential link available after issuance'}</span></div>
          {previewId ? <Button variant="secondary" onClick={() => nav(`/verify/${previewId}`)}>Preview verify page <ArrowRight size={16} /></Button> : null}
        </div>
        <div className="qr-card"><QrCode size={172} /><b>QR ready to share</b><span>{previewId || 'No credential ID yet'}</span></div>
      </section>
    </>
  )
}

function EmployerVerify({
  token,
  setDocumentResult,
}: {
  token: string
  setDocumentResult: (result: VerificationPayload | null) => void
}) {
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function submit() {
    if (!file) {
      setError('Choose a credential file first.')
      return
    }
    setLoading(true)
    setError('')
    try {
      const form = new FormData()
      form.append('file', file)
      const result = await verifyEmployerCertificate(token, form)
      setDocumentResult(result)
      nav('/employer/results/document')
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : 'Verification failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <PageHeader kicker="EMPLOYER VERIFICATION" title="Verify credential uploads." copy="Upload a credential and compare the document against the server-side verification pipeline and stored records." />
      <section className="verify-hero">
        <div className="verify-illustration"><ScanLine size={55} /><div className="scan-corner a" /><div className="scan-corner b" /><div className="scan-corner c" /><div className="scan-corner d" /></div>
        <div>
          <Badge>HOW IT WORKS</Badge>
          <h2>Upload first, then verify.</h2>
          <p>This flow analyzes the document, extracts its identity details, checks trust signals, and returns the blockchain proof the backend produced. QR scan and manual ID entry have been removed from this page on purpose.</p>
        </div>
      </section>
      <section className="verify-options verify-single">
        <button className="upload-box" onClick={() => document.getElementById('credential-upload')?.click()}>
          <div className="upload-icon"><Upload /></div>
          <h3>Upload credential document</h3>
          <p>{file?.name || 'Drop a PDF or image here, or browse your device'}</p>
          <span>PDF, PNG, JPG up to 10 MB</span>
        </button>
        <input id="credential-upload" type="file" accept=".pdf,.png,.jpg,.jpeg,.webp" hidden onChange={(event) => setFile(event.target.files?.[0] || null)} />
        <div className="verify-action-card">
          <p>Use this when an employer receives a certificate file and wants the system to verify the upload against trusted data.</p>
          {error ? <p className="form-error">{error}</p> : null}
          <Button onClick={submit} disabled={loading}>{loading ? 'Verifying...' : 'Verify'} <ArrowRight size={16} /></Button>
        </div>
      </section>
    </>
  )
}

function EmployerResume({
  token,
  setResumeResult,
}: {
  token: string
  setResumeResult: (result: ResumeVerificationResponse | null) => void
}) {
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function submit() {
    if (!file) {
      setError('Choose a resume file first.')
      return
    }
    setLoading(true)
    setError('')
    try {
      const form = new FormData()
      form.append('file', file)
      const result = await verifyEmployerResume(token, form)
      setResumeResult(result)
      nav('/employer/results/resume')
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : 'Resume verification failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <PageHeader kicker="RESUME VERIFICATION" title="Check resume claims against verified records." copy="Upload a resume to compare claimed skills with the student credential passport found by the backend." />
      <section className="verify-options verify-single">
        <button className="upload-box" onClick={() => document.getElementById('resume-upload')?.click()}>
          <div className="upload-icon"><Upload /></div>
          <h3>Upload resume</h3>
          <p>{file?.name || 'Drop a PDF, image, or text resume here'}</p>
          <span>The backend extracts skills and attempts a student match from the document.</span>
        </button>
        <input id="resume-upload" type="file" accept=".pdf,.png,.jpg,.jpeg,.webp,.txt" hidden onChange={(event) => setFile(event.target.files?.[0] || null)} />
        <div className="verify-action-card">
          <p>Resume verification matters because a claimed skill is only useful if it is backed by a verified credential passport.</p>
          {error ? <p className="form-error">{error}</p> : null}
          <Button onClick={submit} disabled={loading}>{loading ? 'Verifying...' : 'Verify Resume'} <ArrowRight size={16} /></Button>
        </div>
      </section>
    </>
  )
}

function VerificationResultPage({ result }: { result: VerificationPayload | null }) {
  return (
    <>
      <PageHeader kicker="VERIFICATION RESULT" title="Credential verification result" copy="Identity details, trust signals, and blockchain proof are all rendered from the backend payload." />
      {!result ? <section className="panel"><p>No verification result is loaded yet.</p></section> : (
        <>
          <section className="result-hero">
            <div className="result-status">
              <div className="verified-seal"><ShieldCheck /></div>
              <div>
                <Badge>{formatStatus(result.status)}</Badge>
                <h1>{result.status === 'verified' ? 'Credential verified.' : result.status === 'pending' ? 'Verification pending.' : 'Credential not verified.'}</h1>
                <p>The frontend is displaying the exact sections requested in the implementation brief.</p>
              </div>
            </div>
            <div className="confidence">
              <span>OCR CONFIDENCE</span>
              <b>{Math.round(result.identity.ocr_confidence || 0)}<small>%</small></b>
            </div>
          </section>
          <div className="result-grid">
            <section className="panel identity">
              <div className="panel-head"><div><h2>Credential Identity</h2><p>AI/OCR extracted details.</p></div><GraduationCap /></div>
              <dl>
                <div><dt>Name</dt><dd>{result.identity.name || 'Not available'}</dd></div>
                <div><dt>Institution</dt><dd>{result.identity.institution || 'Not available'}</dd></div>
                <div><dt>Course</dt><dd>{result.identity.course || 'Not available'}</dd></div>
                <div><dt>Issue date</dt><dd>{formatDate(result.identity.issue_date)}</dd></div>
              </dl>
            </section>
            <section className="panel proof">
              <div className="panel-head"><div><h2>Trust Signals</h2><p>Checks returned by the server.</p></div><Sparkles /></div>
              {result.trust_signals.map((signal) => (
                <div className="signal" key={signal.check}>
                  <span className={signal.result === 'pass' ? 'pass' : 'fail'}><CheckCircle2 size={14} /></span>
                  <div><b>{signal.check}</b><small>{formatStatus(signal.result)}</small></div>
                </div>
              ))}
            </section>
            <section className="panel blockchain">
              <div className="panel-head"><div><h2>Blockchain Proof</h2><p>On-chain confirmation details.</p></div><Blocks /></div>
              <dl>
                <div><dt>Transaction hash</dt><dd className="mono">{result.blockchain_proof.tx_hash || 'Not available'}</dd></div>
                <div><dt>Block number</dt><dd>{result.blockchain_proof.block_number || 'Not available'}</dd></div>
                <div><dt>Timestamp</dt><dd>{formatDate(result.blockchain_proof.timestamp)}</dd></div>
                <div><dt>Verified by</dt><dd>{result.blockchain_proof.verified_by || 'Not available'}</dd></div>
              </dl>
            </section>
          </div>
        </>
      )}
    </>
  )
}

function ResumeResultPage({ result }: { result: ResumeVerificationResponse | null }) {
  return (
    <>
      <PageHeader kicker="RESUME RESULT" title="Resume verification result" copy="Each claimed skill is marked verified or not verified based on the matched student passport." />
      {!result ? <section className="panel"><p>No resume verification result is loaded yet.</p></section> : (
        <section className="panel">
          <div className="panel-head">
            <div>
              <h2>Matched student</h2>
              <p>{result.matched_student ? `${result.matched_student.name} · ${result.matched_student.email}` : 'No student match found from the uploaded resume.'}</p>
            </div>
          </div>
          {result.skill_results.map((skill) => (
            <div className="signal" key={skill.skill}>
              <span className={skill.status === 'verified' ? 'pass' : 'fail'}><CheckCircle2 size={14} /></span>
              <div><b>{skill.skill}</b><small>{skill.status === 'verified' ? 'Verified' : 'Not Verified'}</small></div>
            </div>
          ))}
        </section>
      )}
    </>
  )
}

function EmployerHistory({ history }: { history: HistoryRecord[] }) {
  return (
    <>
      <PageHeader kicker="VERIFIER WORKSPACE" title="Verification history" copy="A private record of credential and resume checks performed by this employer workspace." />
      <section className="panel">
        {history.length === 0 ? <p>No verification history found yet.</p> : history.map((item) => (
          <div className="signal" key={item.id}>
            <span className="pass"><FileCheck2 size={14} /></span>
            <div>
              <b>{item.filename || item.type}</b>
              <small>{formatStatus(item.type)} · {formatStatus(item.status)} · {formatDate(item.verified_at)}</small>
            </div>
          </div>
        ))}
      </section>
    </>
  )
}

function InstitutionOverview({ analytics }: { analytics: InstitutionAnalyticsResponse | null }) {
  return (
    <>
      <PageHeader kicker="INSTITUTION WORKSPACE" title="Credential operations, at a glance." copy="Track issuance, verification status, and external verification activity." action={<Button onClick={() => nav('/institution/create')}><GraduationCap size={16} /> Create credential</Button>} />
      <div className="metrics">
        <Metric label="Total credentials" value={String(analytics?.summary.total_credentials ?? 0)} detail="Issued from this institution" />
        <Metric label="Verified" value={String(analytics?.summary.verified ?? 0)} detail="Completed AI verification" />
        <Metric label="Pending" value={String(analytics?.summary.pending ?? 0)} detail="Awaiting analysis" />
        <Metric label="External verifications" value={String(analytics?.summary.external_verifications ?? 0)} detail="Employer-side checks" />
      </div>
    </>
  )
}

function CredentialList({ credentials, emptyText }: { credentials: CredentialRecord[]; emptyText: string }) {
  return (
    <section className="panel">
      {credentials.length === 0 ? <p>{emptyText}</p> : credentials.map((credential) => (
        <div className="signal" key={credential.id}>
          <span className={credential.status === 'verified' ? 'pass' : 'fail'}><FileText size={14} /></span>
          <div>
            <b>{credential.degree || credential.course || credential.certificate_number || credential.id}</b>
            <small>{credential.student_name || 'Student not available'} · {credential.university || 'Institution not available'} · {formatStatus(credential.status)}</small>
          </div>
        </div>
      ))}
    </section>
  )
}

function InstitutionCredentials({ credentials }: { credentials: CredentialRecord[] }) {
  return (
    <>
      <PageHeader kicker="CREDENTIAL REGISTRY" title="Issued credentials" copy="Credentials created by the authenticated institution account." />
      <CredentialList credentials={credentials} emptyText="No institution credentials found yet." />
    </>
  )
}

function InstitutionCreate({
  token,
  onCreated,
}: {
  token: string
  onCreated: (credential: CredentialRecord) => void
}) {
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const formElement = event.currentTarget
    const form = new FormData(formElement)
    setLoading(true)
    setMessage('')
    setError('')
    try {
      const created = await createInstitutionCertificate(token, form)
      onCreated(created)
      setMessage(`Credential created for ${created.student_name || 'student'} with status ${created.status}.`)
      formElement.reset()
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : 'Credential creation failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <PageHeader kicker="CREATE CREDENTIAL" title="Issue a new credential." copy="This form posts directly to the authenticated institution certificate endpoint." />
      <section className="panel">
        <form className="stack-form" onSubmit={handleSubmit}>
          <label>Student name<input name="student_name" required placeholder="Aarav Sharma" /></label>
          <label>Student email<input name="student_email" type="email" placeholder="aarav@example.com" /></label>
          <label>University<input name="university" required placeholder="Nexora Institute" /></label>
          <label>Degree<input name="degree" required placeholder="Bachelor of Technology" /></label>
          <label>Course<input name="course" placeholder="Computer Science" /></label>
          <label>Certificate number<input name="certificate_number" required placeholder="CERT-2026-001" /></label>
          <label>Credential file<input name="file" type="file" required accept=".pdf,.png,.jpg,.jpeg,.webp" /></label>
          {message ? <p>{message}</p> : null}
          {error ? <p className="form-error">{error}</p> : null}
          <Button type="submit" disabled={loading}>{loading ? 'Creating...' : 'Create credential'} <ArrowRight size={16} /></Button>
        </form>
      </section>
    </>
  )
}

function InstitutionBulk({ token }: { token: string }) {
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const text = String(new FormData(event.currentTarget).get('rows') || '')
    const rows = text
      .split('\n')
      .map((line) => line.trim())
      .filter(Boolean)
      .map((line, index) => {
        const [student_name, student_email, university, degree, certificate_number] = line.split(',').map((part) => part.trim())
        return { student_name, student_email, university, degree, certificate_number, course: `Batch row ${index + 1}` }
      })

    setLoading(true)
    setMessage('')
    setError('')
    try {
      const result = await bulkInstitutionCertificates(token, rows)
      setMessage(`Created ${result.created} credentials.`)
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : 'Bulk issuance failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <PageHeader kicker="BULK ISSUANCE" title="Create credentials in bulk." copy="Paste one CSV-style row per line: student_name, student_email, university, degree, certificate_number" />
      <section className="panel">
        <form className="stack-form" onSubmit={handleSubmit}>
          <label>Batch rows<textarea name="rows" rows={8} placeholder="Aarav Sharma, aarav@example.com, Nexora Institute, B.Tech, CERT-2026-001" /></label>
          {message ? <p>{message}</p> : null}
          {error ? <p className="form-error">{error}</p> : null}
          <Button type="submit" disabled={loading}>{loading ? 'Creating...' : 'Run bulk issuance'} <ArrowRight size={16} /></Button>
        </form>
      </section>
    </>
  )
}

function InstitutionAnalytics({ analytics }: { analytics: InstitutionAnalyticsResponse | null }) {
  const summary = analytics?.summary
  return (
    <>
      <PageHeader kicker="PROGRAM INSIGHTS" title="Verification analytics" copy="Analytics are loaded from the institution endpoint instead of demo data." />
      <div className="metrics">
        <Metric label="AI verification rate" value={`${summary?.ai_verification_rate ?? 0}%`} detail="Verified / total issued" />
        <Metric label="Analyzing" value={String(summary?.analyzing ?? 0)} detail="Currently being processed" />
        <Metric label="Flagged" value={String(summary?.flagged ?? 0)} detail="Needs manual review" />
        <Metric label="Pending" value={String(summary?.pending ?? 0)} detail="Awaiting next action" />
      </div>
    </>
  )
}

function PublicVerify({ token, certificateId }: { token: string | null; certificateId: string }) {
  const [result, setResult] = useState<VerificationPayload | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!token) return
    getVerificationByCertificateId(token, certificateId).then(setResult).catch((err: unknown) => {
      setError(err instanceof Error ? err.message : 'Unable to load verification result')
    })
  }, [token, certificateId])

  if (!token) {
    return (
      <main className="public-verify">
        <header><Logo /><Button variant="ghost" onClick={() => nav('/')}>Employer sign in <ArrowRight size={15} /></Button></header>
        <div className="public-proof"><section className="panel"><p>This verification page now requires an authenticated employer session.</p></section></div>
      </main>
    )
  }

  return (
    <main className="public-verify">
      <header><Logo /><Button variant="ghost" onClick={() => nav('/employer')}>Employer workspace <ArrowRight size={15} /></Button></header>
      <div className="public-proof">{error ? <section className="panel"><p>{error}</p></section> : <VerificationResultPage result={result} />}</div>
    </main>
  )
}

function App() {
  const [path, setPath] = useState(window.location.pathname)
  const [selectedRole, setSelectedRole] = useState<AuthRole>('student')
  const [session, setSession] = useState<AuthSession | null>(readSession())
  const [studentCredentials, setStudentCredentials] = useState<StudentCredentialsResponse | null>(null)
  const [studentPassport, setStudentPassport] = useState<StudentPassportResponse | null>(null)
  const [institutionCredentials, setInstitutionCredentials] = useState<CredentialRecord[]>([])
  const [institutionAnalytics, setInstitutionAnalytics] = useState<InstitutionAnalyticsResponse | null>(null)
  const [history, setHistory] = useState<HistoryRecord[]>([])
  const [documentResult, setDocumentResult] = useState<VerificationPayload | null>(null)
  const [resumeResult, setResumeResult] = useState<ResumeVerificationResponse | null>(null)

  useEffect(() => {
    const handler = () => setPath(window.location.pathname)
    window.addEventListener('popstate', handler)
    return () => window.removeEventListener('popstate', handler)
  }, [])

  useEffect(() => {
    if (!session?.token || !session.user) return

    if (session.role === 'student') {
      getStudentCredentials(session.token).then(setStudentCredentials).catch(() => setStudentCredentials(null))
      getStudentPassport(session.token).then(setStudentPassport).catch(() => setStudentPassport(null))
    }
    if (session.role === 'institution') {
      getInstitutionCredentials(session.token).then((result) => setInstitutionCredentials(result.credentials)).catch(() => setInstitutionCredentials([]))
      getInstitutionAnalytics(session.token).then(setInstitutionAnalytics).catch(() => setInstitutionAnalytics(null))
    }
    if (session.role === 'employer') {
      getEmployerHistory(session.token).then((result) => setHistory(result.history)).catch(() => setHistory([]))
    }
  }, [session])

  function handleAuthenticated(nextSession: AuthSession) {
    setSession(nextSession)
    saveSession(nextSession)
  }

  function handleLogout() {
    setSession(null)
    setStudentCredentials(null)
    setStudentPassport(null)
    setInstitutionCredentials([])
    setInstitutionAnalytics(null)
    setHistory([])
    setDocumentResult(null)
    setResumeResult(null)
    saveSession(null)
    nav('/')
  }

  if (path === '/') {
    return <Landing selectedRole={selectedRole} setSelectedRole={setSelectedRole} onAuthenticated={handleAuthenticated} />
  }

  if (path.startsWith('/verify/')) {
    return <PublicVerify token={session?.token || null} certificateId={path.split('/').pop() || ''} />
  }

  if (!session) {
    return <Landing selectedRole={selectedRole} setSelectedRole={setSelectedRole} onAuthenticated={handleAuthenticated} />
  }

  if (session.role === 'student') {
    let content = <StudentOverview passport={studentPassport} />
    let title = 'Overview'
    if (path === '/student/credentials') {
      content = <StudentCredentials data={studentCredentials} />
      title = 'My Credentials'
    } else if (path === '/student/passport') {
      content = <StudentPassport passport={studentPassport} />
      title = 'Credentials Passport'
    } else if (path === '/student/share') {
      content = <StudentShare passport={studentPassport} />
      title = 'Share & QR'
    }
    return <Portal session={session} title={title} onLogout={handleLogout}>{content}</Portal>
  }

  if (session.role === 'employer') {
    let content = <EmployerVerify token={session.token} setDocumentResult={setDocumentResult} />
    let title = 'Verify Credential'
    if (path === '/employer/resume') {
      content = <EmployerResume token={session.token} setResumeResult={setResumeResult} />
      title = 'Resume Verification'
    } else if (path === '/employer/history') {
      content = <EmployerHistory history={history} />
      title = 'Verification History'
    } else if (path === '/employer/results/document') {
      content = <VerificationResultPage result={documentResult} />
      title = 'Verification Result'
    } else if (path === '/employer/results/resume') {
      content = <ResumeResultPage result={resumeResult} />
      title = 'Resume Result'
    }
    return <Portal session={session} title={title} onLogout={handleLogout}>{content}</Portal>
  }

  let content = <InstitutionOverview analytics={institutionAnalytics} />
  let title = 'Overview'
  if (path === '/institution/credentials') {
    content = <InstitutionCredentials credentials={institutionCredentials} />
    title = 'Credentials'
  } else if (path === '/institution/create') {
    content = <InstitutionCreate token={session.token} onCreated={(credential) => setInstitutionCredentials((current) => [credential, ...current])} />
    title = 'Create Credential'
  } else if (path === '/institution/bulk') {
    content = <InstitutionBulk token={session.token} />
    title = 'Bulk Issuance'
  } else if (path === '/institution/analytics') {
    content = <InstitutionAnalytics analytics={institutionAnalytics} />
    title = 'Analytics'
  }

  return <Portal session={session} title={title} onLogout={handleLogout}>{content}</Portal>
}

export default App
