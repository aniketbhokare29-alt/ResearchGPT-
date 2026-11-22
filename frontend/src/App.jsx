import { useEffect, useState } from 'react'
import { Link, Navigate, NavLink, Route, Routes, useLocation, useNavigate, useParams } from 'react-router-dom'
import {
  Activity, ArrowDownRight, ArrowUpRight, BookOpen, Bot, Check, ChevronDown,
  FileText, FlaskConical, FolderKanban, GitCompareArrows, LayoutDashboard,
  LoaderCircle, LogOut, Plus, Search, Settings, Sparkles, Trash2, Upload, X,
} from 'lucide-react'
import { useAuth } from './auth/AuthContext.jsx'
import { api } from './services/api.js'

const navigation = [
  { label: 'Dashboard', path: '/', icon: LayoutDashboard },
  { label: 'My papers', path: '/papers', icon: FileText },
  { label: 'Collections', path: '/collections', icon: FolderKanban },
  { label: 'Research chat', path: '/chat', icon: Sparkles },
  { label: 'Compare papers', path: '/compare', icon: GitCompareArrows },
  { label: 'Gap analyzer', path: '/gaps', icon: FlaskConical },
  { label: 'Literature review', path: '/literature-review', icon: BookOpen },
  { label: 'Agent activity', path: '/activity', icon: Activity },
]

const metrics = [
  { key: 'papers', label: 'Papers in library', note: 'Your research library', icon: FileText, tone: 'violet' },
  { key: 'analyzed_papers', label: 'Analyzed papers', note: 'Ready for exploration', icon: Sparkles, tone: 'blue' },
  { key: 'collections', label: 'Collections', note: 'Organize by research topic', icon: FolderKanban, tone: 'mint' },
  { key: 'reports', label: 'Reports created', note: 'Literature reviews and more', icon: BookOpen, tone: 'amber' },
]

function Sidebar() {
  const { user, logout } = useAuth()
  const initials = (user?.full_name || user?.email || 'R').slice(0, 1).toUpperCase()
  return <aside className="sidebar">
    <div className="brand"><div className="brand-mark"><FlaskConical size={19} /></div><span>Research<span className="brand-light">GPT</span></span></div>
    <div className="workspace-switch"><div className="workspace-avatar">{initials}</div><div className="workspace-copy"><strong>{user?.full_name || 'Research workspace'}</strong><span>Personal workspace</span></div><ChevronDown size={15} /></div>
    <div className="nav-caption">WORKSPACE</div>
    <nav className="nav-list">{navigation.map(({ label, path, icon: Icon }) => <NavLink key={path} to={path} end={path === '/'} className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}><Icon size={17} /><span>{label}</span></NavLink>)}</nav>
    <div className="sidebar-bottom"><div className="nav-caption">PREFERENCES</div><NavLink to="/settings" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}><Settings size={17} /><span>Settings</span></NavLink><div className="profile"><div className="profile-avatar">{initials}</div><div className="profile-copy"><strong>{user?.full_name || 'Researcher'}</strong><span>{user?.email}</span></div><button className="icon-button logout-button" title="Log out" aria-label="Log out" onClick={() => logout().catch(() => {})}><LogOut size={15} /></button></div></div>
  </aside>
}

function Header({ title }) {
  const { user } = useAuth()
  const initials = (user?.full_name || user?.email || 'R').slice(0, 1).toUpperCase()
  return <header className="topbar"><div className="mobile-brand"><div className="brand-mark"><FlaskConical size={18} /></div>ResearchGPT</div><div className="breadcrumb"><span>Workspace</span><span className="crumb-sep">/</span><strong>{title}</strong></div><div className="top-actions"><div className="header-avatar">{initials}</div></div></header>
}

function AuthPage({ mode }) {
  const { authenticate } = useAuth()
  const navigate = useNavigate()
  const [values, setValues] = useState({ email: '', password: '', full_name: '' })
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const isRegister = mode === 'register'

  async function submit(event) {
    event.preventDefault()
    setBusy(true)
    setError('')
    try {
      await authenticate(mode, values)
      navigate('/', { replace: true })
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not connect. Check the API and try again.')
    } finally {
      setBusy(false)
    }
  }

  return <main className="auth-page"><section className="auth-card"><div className="auth-brand"><div className="brand-mark"><FlaskConical size={19} /></div><span>Research<span className="brand-light">GPT</span></span></div><div className="eyebrow">YOUR ACADEMIC WORKSPACE</div><h1>{isRegister ? 'Create your account' : 'Welcome back'}</h1><p className="subheading">{isRegister ? 'Save and organize your research papers in one place.' : 'Sign in to continue to your research workspace.'}</p>
    <form className="auth-form" onSubmit={submit}>{isRegister && <label>Full name<input autoComplete="name" value={values.full_name} onChange={e => setValues({ ...values, full_name: e.target.value })} maxLength={160} /></label>}<label>Email<input type="email" required autoComplete="email" value={values.email} onChange={e => setValues({ ...values, email: e.target.value })} /></label><label>Password<input type="password" required minLength={isRegister ? 10 : 1} maxLength={128} autoComplete={isRegister ? 'new-password' : 'current-password'} value={values.password} onChange={e => setValues({ ...values, password: e.target.value })} />{isRegister && <span className="field-hint">Use at least 10 characters.</span>}</label>{error && <div className="form-error" role="alert">{error}</div>}<button className="primary-button auth-submit" disabled={busy}>{busy && <LoaderCircle className="spin" size={16} />}{isRegister ? 'Create account' : 'Sign in'}</button></form>
    <div className="auth-switch">{isRegister ? 'Already have an account?' : 'New to ResearchGPT?'} <NavLink to={isRegister ? '/login' : '/register'}>{isRegister ? 'Sign in' : 'Create account'}</NavLink></div><div className="auth-security">Passwords are stored as secure hashes. Your research library is private to your account.</div>
  </section></main>
}

function ProtectedApp() {
  const { user, ready } = useAuth()
  const location = useLocation()
  if (!ready) return <div className="full-loading"><LoaderCircle className="spin" /> Loading your workspace…</div>
  if (!user) return <Navigate to="/login" replace state={{ from: location }} />
  return <div className="app-shell"><Sidebar /><div className="app-main"><Routes>
    <Route path="/" element={<Dashboard />} />
    <Route path="/papers" element={<PapersPage />} />
    <Route path="/papers/:paperId" element={<PaperDetailPage />} />
    <Route path="/collections" element={<CollectionsPage />} />
    <Route path="/settings" element={<SettingsPage />} />
    {navigation.filter(item => !['/', '/papers', '/collections'].includes(item.path)).map(({ label, path }) => <Route key={path} path={path} element={<Placeholder title={label} />} />)}
  </Routes></div></div>
}

function Dashboard() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  async function loadSummary() {
    setLoading(true); setError('')
    try { const { data } = await api.get('/dashboard/summary'); setSummary(data) }
    catch { setError('Could not load workspace totals. Check that the API and database are running.') }
    finally { setLoading(false) }
  }
  useEffect(() => { loadSummary() }, [])
  return <><Header title="Dashboard" /><main className="content"><section className="welcome-row"><div><div className="eyebrow">YOUR RESEARCH, IN ONE PLACE</div><h1>Good morning, {user?.full_name?.split(' ')[0] || 'researcher'} <span className="wave">✳</span></h1><p className="subheading">Build your knowledge base and uncover what your papers have to say.</p></div><button className="primary-button" onClick={() => navigate('/papers')}><Upload size={16} /> Upload papers</button></section>
    {error && <div className="dashboard-error" role="alert"><span>{error}</span><button className="text-button" onClick={loadSummary}>Retry</button></div>}
    <section className="metric-grid">{metrics.map(({ key, label, note, icon: Icon, tone }) => <article className="metric-card" key={key}><div className={`metric-icon ${tone}`}><Icon size={18} /></div><div className="metric-label">{label}</div><div className="metric-value">{loading ? '…' : error ? '—' : summary?.[key] ?? 0}</div><div className="metric-note">{note}</div></article>)}</section>
    <section className="main-grid"><article className="panel getting-started"><div className="panel-heading"><div><div className="eyebrow">GET STARTED</div><h2>Start with your research papers</h2></div></div><p className="panel-intro">Upload a paper to build your knowledge base. Analysis and grounded chat arrive in the next phase.</p><div className="setup-list"><div className="setup-item"><div className="setup-number">01</div><div className="setup-copy"><strong>Upload your first paper</strong><span>Add PDF research papers to your library.</span></div><ArrowUpRight size={17} /></div><div className="setup-item"><div className="setup-number">02</div><div className="setup-copy"><strong>Organize your library</strong><span>Group papers into research collections.</span></div><ArrowUpRight size={17} /></div><div className="setup-item"><div className="setup-number">03</div><div className="setup-copy"><strong>Analyze your papers</strong><span>PDF extraction and AI analysis are next.</span></div></div></div><button className="secondary-button" onClick={() => navigate('/papers')}><Upload size={15} /> Manage papers</button></article>
      <aside className="right-column"><article className="panel quick-panel"><div className="panel-heading"><div><div className="eyebrow">QUICK ACCESS</div><h2>Research tools</h2></div><div className="small-spark"><Sparkles size={16} /></div></div><div className="quick-list"><QuickLink icon={Sparkles} title="Ask your papers" text="Grounded chat arrives in Phase 4" /><QuickLink icon={GitCompareArrows} title="Compare studies" text="Paper analysis arrives in Phase 6" /><QuickLink icon={BookOpen} title="Draft a literature review" text="Report generation arrives in Phase 6" /></div></article><article className="agent-card"><div className="agent-orbit"><Bot size={19} /></div><div className="agent-copy"><strong>Your research team is ready</strong><span>Agent workflows will be added in a later phase.</span></div><ArrowDownRight className="agent-arrow" size={17} /></article></aside></section>
    <section className="panel activity-panel"><div className="panel-heading"><div><div className="eyebrow">RECENT ACTIVITY</div><h2>Your latest work</h2></div></div><div className="empty-activity"><div className="empty-icon"><Activity size={18} /></div><div><strong>Paper activity appears here</strong><span>Uploads and analyses will be tracked in this workspace.</span></div></div></section>
    <footer className="footer-note">Private to your account <span className="footer-separator">·</span> Evidence first, always</footer>
  </main></>
}

function PapersPage() {
  const [papers, setPapers] = useState([])
  const [collections, setCollections] = useState([])
  const [files, setFiles] = useState([])
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [targetCollection, setTargetCollection] = useState({})
  const [message, setMessage] = useState('')
  const [searchText, setSearchText] = useState('')
  const [searchResults, setSearchResults] = useState(null)
  const [searching, setSearching] = useState(false)

  async function loadLibrary() {
    setLoading(true); setError('')
    try {
      const [paperResponse, collectionResponse] = await Promise.all([api.get('/papers'), api.get('/collections')])
      setPapers(paperResponse.data); setCollections(collectionResponse.data)
    } catch (err) { setError(err.response?.data?.detail || 'Could not load your library.') }
    finally { setLoading(false) }
  }
  useEffect(() => { loadLibrary() }, [])

  async function upload(event) {
    event.preventDefault()
    if (!files.length) return
    setBusy(true); setError(''); setResults([])
    try {
      const form = new FormData()
      files.forEach(file => form.append('files', file))
      const { data } = await api.post('/papers/upload', form)
      setResults(data.results); setFiles([]); event.target.reset(); await loadLibrary()
    } catch (err) { setError(err.response?.data?.detail || 'Upload could not be completed.') }
    finally { setBusy(false) }
  }

  async function removePaper(paper) {
    if (!window.confirm(`Delete “${paper.original_filename}” from your library?`)) return
    setError('')
    try { await api.delete(`/papers/${paper.id}`); await loadLibrary() }
    catch (err) { setError(err.response?.data?.detail || 'Could not delete this paper.') }
  }

  async function addToCollection(paper) {
    const collectionId = targetCollection[paper.id]
    if (!collectionId) return
    setMessage('')
    try { await api.put(`/collections/${collectionId}/papers/${paper.id}`); setMessage('Paper added to collection.') }
    catch (err) { setError(err.response?.data?.detail || 'Could not update the collection.') }
  }

  async function searchLibrary(event) {
    event.preventDefault()
    if (searchText.trim().length < 2) return
    setSearching(true); setError('')
    try { const { data } = await api.get('/papers/search', { params: { q: searchText.trim(), top_k: 8 } }); setSearchResults(data) }
    catch (err) { setError(err.response?.data?.detail || 'Semantic search is unavailable. Process papers first.') }
    finally { setSearching(false) }
  }

  return <><Header title="My papers" /><main className="content"><section className="welcome-row"><div><div className="eyebrow">YOUR LIBRARY</div><h1>My research papers</h1><p className="subheading">Upload, organize, and manage your PDF papers.</p></div><span className="step-label">{papers.length} paper{papers.length === 1 ? '' : 's'}</span></section>
    <section className="panel upload-panel"><div className="panel-heading"><div><div className="eyebrow">ADD TO LIBRARY</div><h2>Upload research PDFs</h2></div><div className="upload-limit">PDF · up to 25 MB each · 20 files per batch</div></div><form className="upload-form" onSubmit={upload}><label className="file-picker"><Upload size={18} /><span>{files.length ? `${files.length} PDF${files.length === 1 ? '' : 's'} selected` : 'Choose one or more PDF files'}</span><input type="file" accept=".pdf,application/pdf" multiple onChange={e => setFiles(Array.from(e.target.files || []))} /></label><button className="primary-button" disabled={busy || !files.length}>{busy ? <LoaderCircle className="spin" size={16} /> : <Upload size={16} />}{busy ? 'Uploading…' : 'Upload PDFs'}</button></form>
    {results.length > 0 && <div className="upload-results">{results.map((item, index) => <div className={`upload-result ${item.status}`} key={`${item.filename}-${index}`}><span>{item.status === 'uploaded' ? <Check size={15} /> : item.status === 'duplicate' ? <FolderKanban size={15} /> : <X size={15} />}</span><div><strong>{item.filename}</strong><small>{item.message}</small></div><span className="result-status">{item.status}</span></div>)}</div>}</section>
    {error && <div className="dashboard-error" role="alert"><span>{error}</span><button className="text-button" onClick={loadLibrary}>Retry</button></div>}{message && <div className="success-note">{message}</div>}
    <section className="panel search-panel"><div><div className="eyebrow">SEMANTIC SEARCH</div><h2>Find passages across your papers</h2></div><form className="library-search-form" onSubmit={searchLibrary}><input value={searchText} onChange={e => setSearchText(e.target.value)} placeholder="Ask a research question or describe a concept…" minLength={2} /><button className="primary-button" disabled={searching || searchText.trim().length < 2}>{searching ? <LoaderCircle className="spin" size={16} /> : <Search size={16} />}{searching ? 'Searching…' : 'Search'}</button></form>{searchResults && <div className="search-results">{searchResults.length === 0 ? <div className="search-empty">No matching passages found in processed papers.</div> : searchResults.map(result => <article className="search-result" key={result.chunk_id}><div className="search-result-heading"><Link to={`/papers/${result.paper_id}`}><strong>{result.paper_title || 'Untitled paper'}</strong></Link><span>Pages {result.page_start}{result.page_end !== result.page_start ? `–${result.page_end}` : ''}</span></div><p>{result.text}</p></article>)}</div>}</section>
    <section className="panel library-panel"><div className="panel-heading"><div><div className="eyebrow">PAPER RECORDS</div><h2>Library</h2></div><button className="text-button" onClick={loadLibrary}>Refresh</button></div>
    {loading ? <div className="library-empty"><LoaderCircle className="spin" /> Loading papers…</div> : papers.length === 0 ? <div className="library-empty"><div className="empty-icon"><FileText size={18} /></div><strong>No papers yet</strong><span>Your uploaded PDFs will be listed here.</span></div> : <div className="paper-list">{papers.map(paper => <article className="paper-row" key={paper.id}><div className="paper-file-icon"><FileText size={18} /></div><div className="paper-info"><Link to={`/papers/${paper.id}`}><strong>{paper.title || paper.original_filename}</strong></Link><span>{formatBytes(paper.file_size_bytes)} · Added {new Date(paper.created_at).toLocaleDateString()}</span>{paper.processing_step && paper.processing_status === 'running' && <small>{paper.processing_step}</small>}</div><span className={`status-pill ${paper.processing_status}`}>{paper.processing_status}</span><div className="paper-actions">{collections.length > 0 && <><select aria-label={`Choose collection for ${paper.original_filename}`} value={targetCollection[paper.id] || ''} onChange={e => setTargetCollection({ ...targetCollection, [paper.id]: e.target.value })}><option value="">Collection…</option>{collections.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}</select><button className="icon-button" aria-label="Add to collection" title="Add to collection" onClick={() => addToCollection(paper)}><Plus size={16} /></button></>}<button className="icon-button danger-button" aria-label="Delete paper" title="Delete paper" onClick={() => removePaper(paper)}><Trash2 size={16} /></button></div></article>)}</div>}</section>
    <p className="phase-note">PDFs are processed in the background. Scanned papers need OCR, which is not enabled yet.</p>
  </main></>
}

function PaperDetailPage() {
  const { paperId } = useParams()
  const [paper, setPaper] = useState(null)
  const [page, setPage] = useState(null)
  const [pageNumber, setPageNumber] = useState(1)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)

  async function loadPaper() {
    try {
      const { data } = await api.get(`/papers/${paperId}`)
      setPaper(data)
      setError('')
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not load this paper.')
    } finally { setLoading(false) }
  }
  useEffect(() => {
    loadPaper()
    const timer = window.setInterval(loadPaper, 2500)
    return () => window.clearInterval(timer)
  }, [paperId])
  useEffect(() => {
    if (!paper || paper.processing_status !== 'completed') { setPage(null); return }
    api.get(`/papers/${paperId}/pages`, { params: { offset: pageNumber - 1, limit: 1 } })
      .then(({ data }) => setPage(data[0] || null))
      .catch(() => setPage(null))
  }, [paperId, pageNumber, paper?.processing_status, paper?.page_count])

  async function retryProcessing() {
    setBusy(true); setError('')
    try { await api.post(`/papers/${paperId}/process`); await loadPaper() }
    catch (err) { setError(err.response?.data?.detail || 'Could not queue paper processing.') }
    finally { setBusy(false) }
  }
  async function requestSummary(detail) {
    setBusy(true); setError('')
    try { await api.post(`/papers/${paperId}/summary`, null, { params: { detail } }); await loadPaper() }
    catch (err) { setError(err.response?.data?.detail || 'Could not generate the summary.') }
    finally { setBusy(false) }
  }

  if (loading) return <><Header title="Paper details" /><main className="content"><div className="library-empty">Loading paper…</div></main></>
  if (!paper) return <><Header title="Paper details" /><main className="content"><div className="dashboard-error" role="alert">{error || 'Paper not found.'}</div><Link className="text-button" to="/papers">Back to papers</Link></main></>
  const summaryLabels = [
    ['research_objective', 'Research objective'], ['problem_statement', 'Problem statement'],
    ['proposed_methodology', 'Proposed methodology'], ['transformer_architecture_or_algorithm', 'Architecture or algorithm'],
    ['dataset_used', 'Dataset'], ['experimental_results', 'Experimental results'], ['advantages', 'Advantages'],
    ['limitations', 'Limitations'], ['future_scope', 'Future scope'],
  ]
  return <><Header title="Paper details" /><main className="content"><Link className="back-link" to="/papers">← My papers</Link><section className="paper-detail-heading"><div className="paper-file-icon large"><FileText size={21} /></div><div><div className="eyebrow">RESEARCH PAPER</div><h1>{paper.title || paper.original_filename}</h1><p className="subheading">{paper.authors?.join(', ') || 'Authors not extracted'}{paper.publication_year ? ` · ${paper.publication_year}` : ''} · {formatBytes(paper.file_size_bytes)}</p></div><span className={`status-pill ${paper.processing_status}`}>{paper.processing_status}</span></section>
    {(error || paper.processing_error) && <div className="dashboard-error" role="alert"><span>{error || paper.processing_error}</span>{paper.processing_status === 'failed' && <button className="text-button" onClick={retryProcessing}>Retry processing</button>}</div>}
    <div className="paper-detail-grid"><section className="panel page-viewer"><div className="panel-heading"><div><div className="eyebrow">DOCUMENT TEXT</div><h2>{paper.processing_status === 'completed' ? `Page ${pageNumber} of ${paper.page_count}` : paper.processing_step || 'Waiting for processing'}</h2></div>{paper.processing_status === 'completed' && <div className="page-controls"><button className="secondary-button" disabled={pageNumber <= 1} onClick={() => setPageNumber(pageNumber - 1)}>Previous</button><button className="secondary-button" disabled={pageNumber >= (paper.page_count || 1)} onClick={() => setPageNumber(pageNumber + 1)}>Next</button></div>}</div>
      {paper.processing_status === 'completed' ? page ? <article className="page-text">{page.text || <span className="muted">No selectable text on this page.</span>}</article> : <div className="library-empty">Page text not available.</div> : <div className="processing-state"><LoaderCircle className={paper.processing_status === 'running' || (paper.processing_status === 'pending' && paper.processing_step === 'queued') ? 'spin' : ''} size={18} /><div><strong>{paper.processing_status === 'running' ? `Processing: ${paper.processing_step || 'working'}` : paper.processing_status === 'pending' ? paper.processing_step === 'queued' ? 'Queued for processing' : 'Waiting for processing' : 'Paper needs processing'}</strong><span>PDF text will appear here when extraction and indexing finish.</span></div>{paper.processing_status !== 'running' && !(paper.processing_status === 'pending' && paper.processing_step === 'queued') && <button className="secondary-button" disabled={busy} onClick={retryProcessing}>{busy ? 'Queueing…' : 'Process paper'}</button>}</div>}</section>
      <section className="panel paper-metadata"><div className="eyebrow">PAPER METADATA</div><h2>Extracted details</h2><div className="metadata-row"><span>Title</span><strong>{paper.title || 'Not found'}</strong></div><div className="metadata-row"><span>Authors</span><strong>{paper.authors?.join(', ') || 'Not found'}</strong></div><div className="metadata-row"><span>Year</span><strong>{paper.publication_year || 'Not found'}</strong></div><div className="metadata-row"><span>Pages</span><strong>{paper.page_count ?? 'Pending'}</strong></div>{paper.abstract && <div className="abstract-block"><span>Abstract</span><p>{paper.abstract}</p></div>}</section></div>
    <section className="panel summary-panel"><div className="panel-heading"><div><div className="eyebrow">PRETRAINED MODEL SUMMARY</div><h2>Structured summary</h2></div><div className="summary-actions"><button className="secondary-button" disabled={paper.processing_status !== 'completed' || busy || paper.summary_status === 'running'} onClick={() => requestSummary('short')}>Short</button><button className="secondary-button" disabled={paper.processing_status !== 'completed' || busy || paper.summary_status === 'running'} onClick={() => requestSummary('detailed')}>Detailed</button></div></div>
      {paper.summary_status === 'running' || paper.summary_status === 'pending' ? <div className="processing-state"><LoaderCircle className="spin" size={18} /><span>Generating a hierarchical summary with {paper.summary?.detail || 'the requested'} detail…</span></div> : paper.summary_status === 'failed' ? <div className="summary-error" role="alert">Summary unavailable: {paper.summary_error || 'Check that the configured summary model can be downloaded and loaded.'}</div> : paper.summary ? <><div className="summary-overview"><span>Overview · {paper.summary.detail}</span><p>{paper.summary.overview}</p></div><div className="summary-fields">{summaryLabels.map(([key, label]) => <article key={key}><h3>{label}</h3><p>{paper.summary[key] || 'Not stated in the extracted paper text.'}</p></article>)}</div><p className="summary-note">{paper.summary.note}</p></> : <div className="library-empty"><div className="empty-icon"><Sparkles size={18} /></div><strong>No summary generated yet</strong><span>Choose short or detailed. Model weights download on first use.</span></div>}
    </section>
    <p className="phase-note">Overview summaries use the configured pretrained model. Structured fields are extracted from paper text; missing information is labeled instead of guessed.</p>
  </main></>
}

function CollectionsPage() {
  const [collections, setCollections] = useState([])
  const [papers, setPapers] = useState([])
  const [members, setMembers] = useState({})
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [selections, setSelections] = useState({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  async function loadCollections() {
    setLoading(true); setError('')
    try {
      const [collectionResponse, paperResponse] = await Promise.all([api.get('/collections'), api.get('/papers')])
      setCollections(collectionResponse.data); setPapers(paperResponse.data)
      const pairs = await Promise.all(collectionResponse.data.map(async collection => [collection.id, (await api.get(`/collections/${collection.id}/papers`)).data]))
      setMembers(Object.fromEntries(pairs))
    } catch (err) { setError(err.response?.data?.detail || 'Could not load collections.') }
    finally { setLoading(false) }
  }
  useEffect(() => { loadCollections() }, [])

  async function createCollection(event) {
    event.preventDefault(); setError('')
    try { await api.post('/collections', { name, description: description || null }); setName(''); setDescription(''); await loadCollections() }
    catch (err) { setError(err.response?.data?.detail || 'Could not create this collection.') }
  }
  async function addPaper(collection) {
    const paperId = selections[collection.id]
    if (!paperId) return
    try { await api.put(`/collections/${collection.id}/papers/${paperId}`); setSelections({ ...selections, [collection.id]: '' }); await loadCollections() }
    catch (err) { setError(err.response?.data?.detail || 'Could not add the paper.') }
  }
  async function removePaper(collectionId, paper) {
    try { await api.delete(`/collections/${collectionId}/papers/${paper.id}`); await loadCollections() }
    catch (err) { setError(err.response?.data?.detail || 'Could not remove the paper.') }
  }
  async function removeCollection(collection) {
    if (!window.confirm(`Delete collection “${collection.name}”? The papers remain in your library.`)) return
    try { await api.delete(`/collections/${collection.id}`); await loadCollections() }
    catch (err) { setError(err.response?.data?.detail || 'Could not delete the collection.') }
  }

  return <><Header title="Collections" /><main className="content"><section className="welcome-row"><div><div className="eyebrow">ORGANIZE YOUR LIBRARY</div><h1>Research collections</h1><p className="subheading">Group papers by project, method, or research question.</p></div></section>
    <section className="panel create-collection-panel"><div className="eyebrow">NEW COLLECTION</div><form className="collection-create-form" onSubmit={createCollection}><label>Name<input required maxLength={160} value={name} onChange={e => setName(e.target.value)} placeholder="e.g. Vision transformers" /></label><label>Description <span className="optional-label">optional</span><input maxLength={2000} value={description} onChange={e => setDescription(e.target.value)} placeholder="What are you researching?" /></label><button className="primary-button"><Plus size={16} /> Create collection</button></form></section>
    {error && <div className="dashboard-error" role="alert"><span>{error}</span><button className="text-button" onClick={loadCollections}>Retry</button></div>}
    {loading ? <div className="library-empty"><LoaderCircle className="spin" /> Loading collections…</div> : collections.length === 0 ? <section className="panel library-empty"><div className="empty-icon"><FolderKanban size={18} /></div><strong>No collections yet</strong><span>Create one to organize related papers.</span></section> : <section className="collection-grid">{collections.map(collection => <article className="panel collection-card" key={collection.id}><header><div className="collection-icon"><FolderKanban size={18} /></div><button className="icon-button danger-button" title="Delete collection" aria-label={`Delete ${collection.name}`} onClick={() => removeCollection(collection)}><Trash2 size={16} /></button></header><h2>{collection.name}</h2><p>{collection.description || 'No description'}</p><div className="collection-count">{members[collection.id]?.length ?? 0} papers</div>
      <div className="collection-members">{(members[collection.id] || []).map(paper => <div className="member-row" key={paper.id}><FileText size={14} /><span>{paper.title || paper.original_filename}</span><button className="icon-button" title="Remove paper from collection" onClick={() => removePaper(collection.id, paper)}><X size={14} /></button></div>)}</div>
      {papers.length > 0 && <div className="collection-add"><select aria-label={`Select a paper to add to ${collection.name}`} value={selections[collection.id] || ''} onChange={e => setSelections({ ...selections, [collection.id]: e.target.value })}><option value="">Add a library paper…</option>{papers.filter(p => !(members[collection.id] || []).some(member => member.id === p.id)).map(p => <option key={p.id} value={p.id}>{p.title || p.original_filename}</option>)}</select><button className="icon-button" onClick={() => addPaper(collection)} title="Add paper" disabled={!selections[collection.id]}><Plus size={16} /></button></div>}
    </article>)}</section>}
  </main></>
}

function SettingsPage() {
  const { user, updateProfile, logout } = useAuth()
  const [fullName, setFullName] = useState(user?.full_name || '')
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  async function save(event) {
    event.preventDefault(); setMessage(''); setError('')
    try { await updateProfile({ full_name: fullName || null }); setMessage('Profile saved.') }
    catch (err) { setError(err.response?.data?.detail || 'Could not save profile.') }
  }
  return <><Header title="Settings" /><main className="content"><div className="eyebrow">ACCOUNT</div><h1>Settings</h1><p className="subheading">Manage your account profile and sign-in session.</p><section className="panel settings-panel"><h2>Profile</h2><form className="settings-form" onSubmit={save}><label>Full name<input value={fullName} maxLength={160} onChange={e => setFullName(e.target.value)} /></label><label>Email address<input value={user?.email || ''} disabled /></label>{error && <div className="form-error">{error}</div>}{message && <div className="success-note">{message}</div>}<button className="primary-button">Save profile</button></form></section><section className="panel settings-panel"><h2>Sign-in</h2><p className="subheading">Your token is held in this browser session and expires automatically.</p><button className="secondary-button" onClick={() => logout().catch(() => {})}><LogOut size={15} /> Log out</button></section></main></>
}

function Placeholder({ title }) { return <><Header title={title} /><main className="content"><div className="eyebrow">RESEARCH WORKSPACE</div><h1>{title}</h1><p className="subheading">This workspace is scheduled for a later implementation phase.</p><article className="panel placeholder-panel"><div className="empty-icon"><Sparkles size={18} /></div><strong>Not available yet</strong><span>There is no AI functionality behind this screen yet.</span></article></main></> }
function QuickLink({ icon: Icon, title, text }) { return <div className="quick-link"><div className="quick-icon"><Icon size={16} /></div><div><strong>{title}</strong><span>{text}</span></div><ArrowUpRight size={15} /></div> }
function formatBytes(bytes) { if (bytes < 1024) return `${bytes} B`; if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`; return `${(bytes / (1024 * 1024)).toFixed(1)} MB` }

export default function App() {
  const { user, ready } = useAuth()
  return <Routes><Route path="/login" element={ready && user ? <Navigate to="/" replace /> : <AuthPage mode="login" />} /><Route path="/register" element={ready && user ? <Navigate to="/" replace /> : <AuthPage mode="register" />} /><Route path="/*" element={<ProtectedApp />} /></Routes>
}
