import React, { useState } from 'react'
import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom'
import ThemeToggle from '../components/ThemeToggle'
import LanguageToggle from '../components/LanguageToggle'
import { useAuth } from '../contexts/AuthContext'
import { useTranslation } from '../i18n/LanguageContext'

const AdminSidebar: React.FC = () => {
  const { t } = useTranslation()
  const location = useLocation()
  const [collapsed, setCollapsed] = useState(false)

  const menuItems = [
    { path: '/admin/dashboard', labelKey: 'navitem.dashboard', icon: '📊' },
    { path: '/admin/analytics', labelKey: 'navitem.analytics', icon: '📉' },
    { path: '/admin/properties', labelKey: 'navitem.properties', icon: '🏠' },
    { path: '/admin/buildings', labelKey: 'navitem.buildings', icon: '🏙️' },
    { path: '/admin/units', labelKey: 'navitem.units', icon: '🏢' },
    { path: '/admin/leases', labelKey: 'navitem.leases', icon: '📄' },
    { path: '/admin/payments', labelKey: 'navitem.payments', icon: '💰' },
    { path: '/admin/maintenance', labelKey: 'navitem.maintenance', icon: '🔧' },
    { path: '/admin/marketplace', labelKey: 'navitem.marketplace', icon: '🛠️' },
    { path: '/admin/verifications', labelKey: 'navitem.verifications', icon: '🛡️' },
    { path: '/admin/audit-logs', labelKey: 'navitem.auditTrail', icon: '📋' },
    { path: '/admin/privacy', labelKey: 'navitem.deletionRequests', icon: '🔐' },
    { path: '/admin/users', labelKey: 'navitem.users', icon: '👥' },
    { path: '/admin/inquiries', labelKey: 'navitem.inquiries', icon: '💬' },
    { path: '/admin/agents', labelKey: 'navitem.agents', icon: '🤝' },
    { path: '/admin/managers', labelKey: 'navitem.managers', icon: '👔' },
    { path: '/admin/tenants', labelKey: 'navitem.tenants', icon: '🔑' },
    { path: '/admin/market-insights', labelKey: 'navitem.marketInsights', icon: '📈' },
    { path: '/admin/settings', labelKey: 'navitem.settings', icon: '⚙️' },
  ]

  return (
    <aside className={`sidebar admin-sidebar ${collapsed ? 'collapsed' : ''}`} aria-hidden={collapsed}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div className="brand">
          <span style={{ color: 'var(--primary)' }}>PropNoxa</span>
          <span style={{ color: 'var(--muted)', fontSize: 12, marginLeft: 4 }}>{t('layout.role.admin')}</span>
        </div>
        <button 
          className="button muted" 
          onClick={() => setCollapsed(c => !c)} 
          aria-pressed={collapsed}
          style={{ padding: '4px 8px', fontSize: 12 }}
        >
          {collapsed ? '▶' : '◀'}
        </button>
      </div>
      
      <div className="admin-workspace-label">{t('layout.workspace.admin')}</div>
      <nav className="nav" aria-label={t('layout.aria.adminNav')}>
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

const AdminHeader: React.FC = () => {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { user, logout } = useAuth()

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  return (
    <header className="header admin-header" role="banner">
      <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
        <div>
          <div style={{ fontSize: 14, fontWeight: 700 }}>
            {t('layout.greeting.morning')} {user?.full_name || user?.email || t('layout.fallback.admin')}
          </div>
          <div style={{ fontSize: 12, color: 'var(--muted)' }}>
            {t('layout.subtitle.admin')}
          </div>
        </div>
      </div>
      
      <div className="admin-header-meta" style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
        <ThemeToggle />
        <LanguageToggle />
        <div className="admin-live-status"><span /> {t('layout.sync.admin')}</div>
        <div className="admin-badge" style={{ 
          background: 'var(--primary)', 
          color: 'white', 
          padding: '4px 12px', 
          borderRadius: 12, 
          fontSize: 12, 
          fontWeight: 600 
        }}>
          ADMIN
        </div>
        
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontWeight: 700, fontSize: 14 }}>
            {user?.full_name || user?.email || t('layout.fallback.admin')}
          </div>
          <div style={{ fontSize: 12, color: 'var(--muted)' }}>
            {user?.role || 'admin'}
          </div>
        </div>
        
        <button 
          onClick={handleLogout} 
          className="button"
          style={{ marginLeft: 12 }}
        >
          {t('common.logout')}
        </button>
      </div>
    </header>
  )
}

const AdminLayout: React.FC = () => {
  return (
    <div className="app-shell admin-shell">
      <AdminSidebar />
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <AdminHeader />
        <main className="content admin-content">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

export default AdminLayout