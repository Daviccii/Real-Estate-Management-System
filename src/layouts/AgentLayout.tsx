import React, { useState } from 'react'
import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom'
import ThemeToggle from '../components/ThemeToggle'
import LanguageToggle from '../components/LanguageToggle'
import { useAuth } from '../contexts/AuthContext'
import { useTranslation } from '../i18n/LanguageContext'

const AgentSidebar: React.FC = () => {
  const { t } = useTranslation()
  const location = useLocation()
  const [collapsed, setCollapsed] = useState(false)

  const menuItems = [
    { path: '/agent/dashboard', labelKey: 'navitem.dashboard', icon: '📊' },
    { path: '/agent/leads', labelKey: 'navitem.leadsPipeline', icon: '🎯' },
    { path: '/agent/listings', labelKey: 'navitem.assignedListings', icon: '🏠' },
    { path: '/agent/viewings', labelKey: 'navitem.viewingTours', icon: '📅' },
    { path: '/agent/applications', labelKey: 'navitem.rentalApps', icon: '📝' },
    { path: '/agent/commissions', labelKey: 'navitem.commissions', icon: '💵' },
    { path: '/agent/profile', labelKey: 'navitem.earb', icon: '🛡️' }
  ]

  return (
    <aside className={`sidebar agent-sidebar ${collapsed ? 'collapsed' : ''}`} aria-hidden={collapsed}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div className="brand">
          <span style={{ color: 'var(--primary)' }}>PropNoxa</span>
          <span style={{ color: 'var(--muted)', fontSize: 12, marginLeft: 4 }}>{t('layout.role.agent')}</span>
        </div>
        <button
          className="button muted"
          onClick={() => setCollapsed((c) => !c)}
          aria-pressed={collapsed}
          style={{ padding: '4px 8px', fontSize: 12 }}
        >
          {collapsed ? '▶' : '◀'}
        </button>
      </div>

      <div className="agent-workspace-label">{t('layout.workspace.agent')}</div>
      <nav className="nav" aria-label={t('layout.aria.agentNav')}>
        {menuItems.map((item) => (
          <Link
            key={item.path}
            to={item.path}
            className={location.pathname === item.path || location.pathname.startsWith(item.path + '/') ? 'active' : ''}
            style={{ display: 'flex', alignItems: 'center', gap: 8 }}
          >
            <span style={{ fontSize: 16 }}>{item.icon}</span>
            {!collapsed && <span>{t(item.labelKey)}</span>}
          </Link>
        ))}
      </nav>
    </aside>
  )
}

const AgentHeader: React.FC = () => {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { user, logout } = useAuth()

  return (
    <header className="header agent-header" role="banner">
      <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
        <div>
          <div style={{ fontSize: 14, fontWeight: 700 }}>
            {t('layout.greeting.hello')} {user?.full_name || user?.email || t('layout.fallback.agent')}
          </div>
          <div style={{ fontSize: 12, color: 'var(--muted)' }}>{t('layout.subtitle.agent')}</div>
        </div>
      </div>

      <div className="agent-header-meta" style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
        <ThemeToggle />
        <LanguageToggle />
        <div className="agent-sync-status"><span /> {t('layout.sync.agent')}</div>
        <span
          style={{
            background: '#2563eb',
            color: 'white',
            padding: '4px 12px',
            borderRadius: 12,
            fontSize: 12,
            fontWeight: 600
          }}
        >
          AGENT
        </span>

        <button
          onClick={async () => {
            await logout()
            navigate('/login')
          }}
          className="button"
          style={{ marginLeft: 12 }}
        >
          {t('common.logout')}
        </button>
      </div>
    </header>
  )
}

export const AgentLayout: React.FC = () => {
  return (
    <div className="app-shell agent-shell">
      <AgentSidebar />
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <AgentHeader />
        <main className="content agent-content">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

export default AgentLayout
