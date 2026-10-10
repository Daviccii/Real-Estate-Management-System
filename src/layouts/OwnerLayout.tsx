import React, { useState } from 'react'
import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom'
import ThemeToggle from '../components/ThemeToggle'
import LanguageToggle from '../components/LanguageToggle'
import { useAuth } from '../contexts/AuthContext'
import { useTranslation } from '../i18n/LanguageContext'

const OwnerSidebar: React.FC = () => {
  const { t } = useTranslation()
  const location = useLocation()
  const [collapsed, setCollapsed] = useState(false)

  const menuItems = [
    { path: '/owner/dashboard', labelKey: 'navitem.dashboard', icon: '📊' },
    { path: '/owner/analytics', labelKey: 'navitem.performanceAnalytics', icon: '📉' },
    { path: '/owner/properties', labelKey: 'navitem.portfolioProperties', icon: '🏠' },
    { path: '/owner/units', labelKey: 'navitem.unitDirectory', icon: '🏢' },
    { path: '/owner/tenants', labelKey: 'navitem.activeTenants', icon: '👥' },
    { path: '/owner/leases', labelKey: 'navitem.leaseAgreements', icon: '📄' },
    { path: '/owner/financials', labelKey: 'navitem.financialYield', icon: '💰' },
    { path: '/owner/applications', labelKey: 'navitem.tenantScreening', icon: '📝' },
    { path: '/owner/maintenance', labelKey: 'navitem.repairApprovals', icon: '🔧' },
    { path: '/owner/marketplace', labelKey: 'navitem.serviceMarketplace', icon: '🛠️' },
    { path: '/owner/settings', labelKey: 'navitem.ownershipDeeds', icon: '⚙️' }
  ]

  return (
    <aside className={`sidebar owner-sidebar ${collapsed ? 'collapsed' : ''}`} aria-hidden={collapsed}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div className="brand">
          <span style={{ color: 'var(--primary)' }}>PropNoxa</span>
          <span style={{ color: 'var(--muted)', fontSize: 12, marginLeft: 4 }}>{t('layout.role.owner')}</span>
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

      <div className="owner-workspace-label">{t('layout.workspace.owner')}</div>
      <nav className="nav" aria-label={t('layout.aria.ownerNav')}>
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

const OwnerHeader: React.FC = () => {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { user, logout } = useAuth()

  return (
    <header className="header owner-header" role="banner">
      <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
        <div>
          <div style={{ fontSize: 14, fontWeight: 700 }}>
            {t('layout.greeting.day')} {user?.full_name || user?.email || t('layout.fallback.owner')}
          </div>
          <div style={{ fontSize: 12, color: 'var(--muted)' }}>{t('layout.subtitle.owner')}</div>
        </div>
      </div>

      <div className="owner-header-meta" style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
        <ThemeToggle />
        <LanguageToggle />
        <div className="owner-sync-status"><span /> {t('layout.sync.owner')}</div>
        <span
          style={{
            background: '#4f46e5',
            color: 'white',
            padding: '4px 12px',
            borderRadius: 12,
            fontSize: 12,
            fontWeight: 600
          }}
        >
          OWNER
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

export const OwnerLayout: React.FC = () => {
  return (
    <div className="app-shell owner-shell">
      <OwnerSidebar />
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <OwnerHeader />
        <main className="content owner-content">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

export default OwnerLayout
