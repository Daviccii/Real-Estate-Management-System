import React, { useState } from 'react'
import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom'
import ThemeToggle from '../components/ThemeToggle'
import LanguageToggle from '../components/LanguageToggle'
import { useAuth } from '../contexts/AuthContext'
import { useTranslation } from '../i18n/LanguageContext'

const ProviderSidebar: React.FC = () => {
  const { t } = useTranslation()
  const location = useLocation()
  const [collapsed, setCollapsed] = useState(false)

  const menuItems = [
    { path: '/provider/dashboard', labelKey: 'navitem.dashboard', icon: '📊' },
    { path: '/provider/open-jobs', labelKey: 'navitem.openJobs', icon: '📢' },
    { path: '/provider/work-orders', labelKey: 'navitem.workOrders', icon: '🔧' },
    { path: '/provider/quotes', labelKey: 'navitem.quoteBids', icon: '📝' },
    { path: '/provider/profile', labelKey: 'navitem.tradeProfile', icon: '🛡️' }
  ]

  return (
    <aside className={`sidebar provider-sidebar ${collapsed ? 'collapsed' : ''}`} aria-hidden={collapsed}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div className="brand">
          <span style={{ color: 'var(--primary)' }}>PropNoxa</span>
          <span style={{ color: 'var(--muted)', fontSize: 12, marginLeft: 4 }}>{t('layout.role.provider')}</span>
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

      <div className="provider-workspace-label">{t('layout.workspace.provider')}</div>
      <nav className="nav" aria-label={t('layout.aria.providerNav')}>
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

const ProviderHeader: React.FC = () => {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { user, logout } = useAuth()

  return (
    <header className="header provider-header" role="banner">
      <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
        <div>
          <div style={{ fontSize: 14, fontWeight: 700 }}>
            {t('layout.greeting.day')} {user?.full_name || user?.email || t('layout.fallback.provider')}
          </div>
          <div style={{ fontSize: 12, color: 'var(--muted)' }}>{t('layout.subtitle.provider')}</div>
        </div>
      </div>

      <div className="provider-header-meta" style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
        <ThemeToggle />
        <LanguageToggle />
        <div className="provider-sync-status"><span /> {t('layout.sync.provider')}</div>
        <span
          style={{
            background: '#d97706',
            color: 'white',
            padding: '4px 12px',
            borderRadius: 12,
            fontSize: 12,
            fontWeight: 600
          }}
        >
          CONTRACTOR
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

export const ProviderLayout: React.FC = () => {
  return (
    <div className="app-shell provider-shell">
      <ProviderSidebar />
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <ProviderHeader />
        <main className="content provider-content">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

export default ProviderLayout
