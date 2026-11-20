import { useEffect, useState } from 'react'
import { NavLink, Route, Routes } from 'react-router-dom'
import {
  Activity, ArrowDownRight, ArrowUpRight, BookOpen, Bot, ChevronDown,
  FileText, FlaskConical, FolderKanban, GitCompareArrows, LayoutDashboard,
  RefreshCw, Search, Settings, Sparkles, Upload,
} from 'lucide-react'
import { api } from './services/api.js'

const navigation = [
  { label: 'Dashboard', path: '/', icon: LayoutDashboard },
  { label: 'My papers', path: '/papers', icon: FileText },
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
  return <aside className="sidebar">
    <div className="brand"><div className="brand-mark"><FlaskConical size={19} /></div><span>Research<span className="brand-light">GPT</span></span></div>
    <div className="workspace-switch"><div className="workspace-avatar">R</div><div className="workspace-copy"><strong>Research workspace</strong><span>Personal plan</span></div><ChevronDown size={15} /></div>
    <div className="nav-caption">WORKSPACE</div>
    <nav className="nav-list">{navigation.map(({ label, path, icon: Icon }) => <NavLink key={path} to={path} end={path === '/'} className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}><Icon size={17} /><span>{label}</span></NavLink>)}</nav>
    <div className="sidebar-bottom"><div className="nav-caption">PREFERENCES</div><NavLink to="/settings" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}><Settings size={17} /><span>Settings</span></NavLink><div className="profile"><div className="profile-avatar">A</div><div className="profile-copy"><strong>Researcher</strong><span>Local workspace</span></div><ChevronDown size={15} /></div></div>
  </aside>
}

function Header({ title }) {
  return <header className="topbar"><div className="mobile-brand"><div className="brand-mark"><FlaskConical size={18} /></div>ResearchGPT</div><div className="breadcrumb"><span>Workspace</span><span className="crumb-sep">/</span><strong>{title}</strong></div><div className="top-actions"><button className="icon-button" aria-label="Search"><Search size={18} /></button><div className="top-divider" /><div className="header-avatar">A</div></div></header>
}

function Dashboard() {
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  async function loadSummary() {
    setLoading(true)
    setError('')
    try {
      const { data } = await api.get('/dashboard/summary')
      setSummary(data)
    } catch {
      setError('Could not load workspace totals. Check that the API and database are running.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadSummary() }, [])

  return <><Header title="Dashboard" /><main className="content"><section className="welcome-row"><div><div className="eyebrow">YOUR RESEARCH, IN ONE PLACE</div><h1>Good morning, researcher <span className="wave">✳</span></h1><p className="subheading">Build your knowledge base and uncover what your papers have to say.</p></div><button className="primary-button" disabled title="Paper upload is part of Phase 2"><Upload size={16} /> Upload papers · Phase 2</button></section>
    {error && <div className="dashboard-error" role="alert"><span>{error}</span><button className="text-button" onClick={loadSummary}><RefreshCw size={14} /> Retry</button></div>}
    <section className="metric-grid">{metrics.map(({ key, label, note, icon: Icon, tone }) => <article className="metric-card" key={key}><div className={`metric-icon ${tone}`}><Icon size={18} /></div><div className="metric-label">{label}</div><div className="metric-value">{loading ? '…' : error ? '—' : summary?.[key] ?? 0}</div><div className="metric-note">{note}</div></article>)}</section>
    <section className="main-grid"><article className="panel getting-started"><div className="panel-heading"><div><div className="eyebrow">GET STARTED</div><h2>Start with your research papers</h2></div><span className="step-label">0 of 3 complete</span></div><p className="panel-intro">Your workspace is ready. Add papers to unlock grounded chat, comparisons, and literature reviews.</p><div className="setup-list"><div className="setup-item"><div className="setup-number">01</div><div className="setup-copy"><strong>Upload your first paper</strong><span>Add PDF research papers to your library.</span></div><ArrowUpRight size={17} /></div><div className="setup-item"><div className="setup-number">02</div><div className="setup-copy"><strong>Let ResearchGPT analyze it</strong><span>Extract key sections and build searchable evidence.</span></div><ArrowUpRight size={17} /></div><div className="setup-item"><div className="setup-number">03</div><div className="setup-copy"><strong>Explore across your papers</strong><span>Ask questions and compare research findings.</span></div><ArrowUpRight size={17} /></div></div><button className="secondary-button" disabled title="Paper upload is part of Phase 2"><Upload size={15} /> PDF upload · Phase 2</button></article>
      <aside className="right-column"><article className="panel quick-panel"><div className="panel-heading"><div><div className="eyebrow">QUICK ACCESS</div><h2>Research tools</h2></div><div className="small-spark"><Sparkles size={16} /></div></div><div className="quick-list"><QuickLink icon={Sparkles} title="Ask your papers" text="Find answers with page citations" /><QuickLink icon={GitCompareArrows} title="Compare studies" text="See methods and results side by side" /><QuickLink icon={BookOpen} title="Draft a literature review" text="Synthesize your selected papers" /></div></article><article className="agent-card"><div className="agent-orbit"><Bot size={19} /></div><div className="agent-copy"><strong>Your research team is ready</strong><span>Specialized agents help analyze evidence across your library.</span></div><ArrowDownRight className="agent-arrow" size={17} /></article></aside></section>
    <section className="panel activity-panel"><div className="panel-heading"><div><div className="eyebrow">RECENT ACTIVITY</div><h2>Your latest work</h2></div><span className="step-label">Activity feed · Phase 2</span></div><div className="empty-activity"><div className="empty-icon"><Activity size={18} /></div><div><strong>No activity yet</strong><span>Uploaded papers and completed analyses will appear here.</span></div></div></section>
    <footer className="footer-note"><span className="status-dot" /> Your workspace is ready to set up <span className="footer-separator">·</span> Evidence first, always</footer>
  </main></>
}

function QuickLink({ icon: Icon, title, text }) { return <div className="quick-link"><div className="quick-icon"><Icon size={16} /></div><div><strong>{title}</strong><span>{text}</span></div><ArrowUpRight size={15} /></div> }
function Placeholder({ title }) { return <><Header title={title} /><main className="content"><div className="eyebrow">RESEARCH WORKSPACE</div><h1>{title}</h1><p className="subheading">This workspace is ready for the next implementation milestone.</p><article className="panel placeholder-panel"><div className="empty-icon"><Sparkles size={18} /></div><strong>Coming in a later phase</strong><span>We’ll connect this page to real paper and analysis data as the backend modules are built.</span></article></main></> }

export default function App() {
  return <div className="app-shell"><Sidebar /><div className="app-main"><Routes><Route path="/" element={<Dashboard />} />{navigation.slice(1).map(({ label, path }) => <Route key={path} path={path} element={<Placeholder title={label} />} />)}<Route path="/settings" element={<Placeholder title="Settings" />} /></Routes></div></div>
}
